// 控制与安全决策（Go 移植自 app.py safety_check + Controller）。
// 所有外部依赖均由 ControllerDeps 注入，便于与 Python 脱机对拍。
package main

import (
	"encoding/json"
	"fmt"
	"math"
	"strconv"
	"strings"
	"sync"
	"time"
)

var safeRanges = map[string][2]float64{
	"sec_supply_temp_sp": {20, 75},
	"valve_open_sp":      {0, 100},
	"pump_freq_sp":       {0, 50},
}

type ControlWrite struct {
	PointID string  `json:"point_id"`
	Value   float64 `json:"value"`
}

type ControlRecord struct {
	CommandID string      `json:"command_id"`
	PointID   string      `json:"point_id"`
	Value     interface{} `json:"value"`
	Status    string      `json:"status"`
	Reason    string      `json:"reason"`
	Origin    string      `json:"origin"`
	TS        int64       `json:"ts"`
}

type ControlAlarm struct {
	Action string `json:"action"`
	Detail string `json:"detail"`
}

type ControllerDeps struct {
	Snapshot func() obj
	Write    func(pointID string, value float64) bool
	Clock    func() float64
	Sleep    func(seconds float64)
	Record   func(ControlRecord)
	Alarm    func(ControlAlarm)
	Policy   obj
}

type Controller struct {
	deps ControllerDeps
	mu   sync.Mutex
	last map[string]lastCommand
	wg   sync.WaitGroup
}

type lastCommand struct {
	value float64
	at    float64
}

func NewController(deps ControllerDeps) *Controller {
	if deps.Snapshot == nil {
		deps.Snapshot = func() obj { return obj{"devices": arr{}} }
	}
	if deps.Write == nil {
		deps.Write = func(string, float64) bool { return false }
	}
	if deps.Clock == nil {
		deps.Clock = defaultClock
	}
	if deps.Sleep == nil {
		deps.Sleep = func(seconds float64) { time.Sleep(time.Duration(seconds * float64(time.Second))) }
	}
	if deps.Record == nil {
		deps.Record = func(ControlRecord) {}
	}
	if deps.Alarm == nil {
		deps.Alarm = func(ControlAlarm) {}
	}
	return &Controller{deps: deps, last: map[string]lastCommand{}}
}

func (c *Controller) Apply(pointID string, rawValue interface{}, commandID, origin string) (bool, string) {
	ok, reason, value := SafetyCheck(pointID, rawValue, c.deps.Policy)
	if !ok {
		c.record(commandID, pointID, rawValue, "blocked_by_safety", reason, origin)
		return false, reason
	}
	if ok, reason := c.rateCheck(pointID, value); !ok {
		c.record(commandID, pointID, rawValue, "blocked_by_safety", reason, origin)
		return false, reason
	}
	if ok, reason := c.interlockCheck(pointID); !ok {
		c.record(commandID, pointID, rawValue, "blocked_by_interlock", reason, origin)
		return false, reason
	}
	if !c.deps.Write(pointID, value) {
		c.record(commandID, pointID, rawValue, "write_failed", "源写入失败", origin)
		return false, ""
	}
	c.mu.Lock()
	c.last[pointID] = lastCommand{value: value, at: c.deps.Clock()}
	c.mu.Unlock()
	c.record(commandID, pointID, rawValue, "accepted", "", origin)
	if asStr(asObj(c.deps.Policy[pointID])["feedback"]) != "" {
		c.wg.Add(1)
		go func() {
			defer c.wg.Done()
			c.confirmFeedback(pointID, rawValue, value, commandID, origin)
		}()
	}
	return true, ""
}

func (c *Controller) rateCheck(pointID string, value float64) (bool, string) {
	policy := asObj(c.deps.Policy[pointID])
	rateRaw := policy["rate_per_s"]
	rate, hasRate := pythonFloat(rateRaw)
	if !hasRate || rate == 0 {
		return true, ""
	}
	c.mu.Lock()
	prev, exists := c.last[pointID]
	c.mu.Unlock()
	if !exists {
		return true, ""
	}
	dt := math.Max(c.deps.Clock()-prev.at, 1e-3)
	if math.Abs(value-prev.value)/dt > rate {
		return false, fmt.Sprintf("%s 变化速率超限(>%s/s)", pointID, pyNumberString(rateRaw))
	}
	return true, ""
}

func (c *Controller) interlockCheck(pointID string) (bool, string) {
	policy := asObj(c.deps.Policy[pointID])
	for _, raw := range asArr(policy["interlocks"]) {
		il := asObj(raw)
		ilp := asStr(il["point"])
		point := c.point(ilp)
		if point == nil {
			return false, fmt.Sprintf("联锁点 %s 不在快照中", ilp)
		}
		if point["q"] != "good" {
			return false, fmt.Sprintf("联锁点 %s 质量码非 GOOD(%v)", ilp, point["q"])
		}
		value, ok := pythonFloat(point["v"])
		if !ok {
			return false, fmt.Sprintf("联锁点 %s 值非法 %s", ilp, reprStr(point["v"]))
		}
		if expected, exists := il["equals"]; exists {
			f, valid := pythonFloat(expected)
			if valid && value != f {
				return false, fmt.Sprintf("联锁未满足:%s=%s 需=%s",
					ilp, pyFloatString(value), pyNumberString(expected))
			}
		}
		if maximum, exists := il["max"]; exists {
			f, valid := pythonFloat(maximum)
			if valid && value > f {
				return false, fmt.Sprintf("联锁未满足:%s=%s 需≤%s",
					ilp, pyFloatString(value), pyNumberString(maximum))
			}
		}
		if minimum, exists := il["min"]; exists {
			f, valid := pythonFloat(minimum)
			if valid && value < f {
				return false, fmt.Sprintf("联锁未满足:%s=%s 需≥%s",
					ilp, pyFloatString(value), pyNumberString(minimum))
			}
		}
	}
	return true, ""
}

func (c *Controller) point(pointID string) obj {
	for _, rawDevice := range asArr(c.deps.Snapshot()["devices"]) {
		points := asObj(asObj(rawDevice)["points"])
		if point, ok := points[pointID]; ok {
			return asObj(point)
		}
	}
	return nil
}

func (c *Controller) confirmFeedback(pointID string, rawValue interface{}, target float64, commandID, origin string) {
	policy := asObj(c.deps.Policy[pointID])
	feedback := asStr(policy["feedback"])
	if feedback == "" {
		return
	}
	timeout, ok := pythonFloat(policy["confirm_timeout_s"])
	timeoutDisplay := policy["confirm_timeout_s"]
	if !ok || timeout == 0 {
		timeout = 5
		timeoutDisplay = 5
	}
	tolerance, ok := pythonFloat(policy["confirm_tolerance"])
	toleranceDisplay := policy["confirm_tolerance"]
	if !ok {
		tolerance = 1
		toleranceDisplay = 1
	}
	deadline := c.deps.Clock() + timeout
	for c.deps.Clock() < deadline {
		c.deps.Sleep(0.5)
		point := c.point(feedback)
		if point != nil && point["q"] == "good" {
			if value, valid := pythonFloat(point["v"]); valid && math.Abs(value-target) <= tolerance {
				c.record(commandID, pointID, rawValue, "confirmed",
					fmt.Sprintf("反馈 %s=%s 已收敛", feedback, pyString(point["v"])), origin)
				return
			}
		}
	}
	point := c.point(feedback)
	var current interface{}
	if point != nil {
		current = point["v"]
	}
	c.record(commandID, pointID, rawValue, "feedback_timeout",
		fmt.Sprintf("反馈 %s=%s %ss 内未收敛到 %s±%s",
			feedback, pyString(current), pyString(timeoutDisplay),
			pyFloatString(target), pyString(toleranceDisplay)), origin)
	c.deps.Alarm(ControlAlarm{
		Action: "feedback_timeout",
		Detail: fmt.Sprintf("%s←%v 回读确认失败(feedback=%s)", pointID, rawValue, feedback),
	})
}

func (c *Controller) record(commandID, pointID string, value interface{}, status, reason, origin string) {
	c.deps.Record(ControlRecord{
		CommandID: commandID, PointID: pointID, Value: value, Status: status,
		Reason: reason, Origin: origin, TS: int64(c.deps.Clock() * 1000),
	})
}

func SafetyCheck(pointID string, rawValue interface{}, policy obj) (bool, string, float64) {
	var lo, hi interface{}
	if len(policy) > 0 {
		p, ok := policy[pointID]
		if !ok {
			return false, fmt.Sprintf("未知或不可远程设定的点位 %s", pointID), 0
		}
		pm := asObj(p)
		lo, hi = pm["lo"], pm["hi"]
	} else {
		r, ok := safeRanges[pointID]
		if !ok {
			return false, fmt.Sprintf("未知或不可远程设定的点位 %s", pointID), 0
		}
		lo, hi = r[0], r[1]
	}
	if lo == nil || hi == nil {
		return false, fmt.Sprintf("%s 缺少安全限值", pointID), 0
	}
	value, ok := pythonFloat(rawValue)
	if !ok {
		return false, fmt.Sprintf("%s 值非法 %s", pointID, reprStr(rawValue)), 0
	}
	lof, lok := pythonFloat(lo)
	hif, hik := pythonFloat(hi)
	if !lok || !hik {
		return false, fmt.Sprintf("%s 缺少安全限值", pointID), 0
	}
	if math.IsNaN(value) || value < lof || value > hif {
		return false, fmt.Sprintf("%s=%s 超出安全限值 [%s,%s]",
			pointID, pyFloatString(value), pyNumberString(lo), pyNumberString(hi)), 0
	}
	return true, "", value
}

func pythonFloat(v interface{}) (float64, bool) {
	switch x := v.(type) {
	case float64:
		return x, true
	case float32:
		return float64(x), true
	case int:
		return float64(x), true
	case int64:
		return float64(x), true
	case json.Number:
		f, err := x.Float64()
		return f, err == nil
	case bool:
		if x {
			return 1, true
		}
		return 0, true
	case string:
		f, err := strconv.ParseFloat(x, 64)
		return f, err == nil
	default:
		return 0, false
	}
}

func pyFloatString(v float64) string {
	if math.IsInf(v, 1) {
		return "inf"
	}
	if math.IsInf(v, -1) {
		return "-inf"
	}
	if math.IsNaN(v) {
		return "nan"
	}
	// 匹配 Python str(float)：最小可往返表示，整数值保留 ".0"。
	s := strconv.FormatFloat(v, 'g', -1, 64)
	if !strings.ContainsAny(s, ".eE") {
		s += ".0"
	}
	return s
}

func pyNumberString(v interface{}) string {
	if n, ok := v.(json.Number); ok {
		return n.String()
	}
	if f, ok := pythonFloat(v); ok {
		switch v.(type) {
		case int, int64:
			return strconv.FormatInt(int64(f), 10)
		default:
			return pyFloatString(f)
		}
	}
	return fmt.Sprintf("%v", v)
}

func pyString(v interface{}) string {
	switch x := v.(type) {
	case nil:
		return "None"
	case float64:
		return pyFloatString(x)
	case float32:
		return pyFloatString(float64(x))
	case bool:
		if x {
			return "True"
		}
		return "False"
	case json.Number:
		return x.String()
	default:
		return fmt.Sprintf("%v", x)
	}
}

// WaitConfirmations 仅用于测试/有序关停，生产 Apply 的返回仍不等待反馈确认。
func (c *Controller) WaitConfirmations() {
	c.wg.Wait()
}
