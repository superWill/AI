// 内置仿真数据源（Go 移植自 app.py 的 SimSource）。
// 与 compiler/loader 同包，复用 obj/arr/asObj/get/getOr/toF。
// 时钟可注入(clock)，便于与 Python 在相同时刻对拍。
package main

import (
	"fmt"
	"math"
	"time"
)

type SimSource struct {
	t0        float64
	devices   arr
	setpoints map[string]float64
	feedback  map[string]float64
	clock     func() float64 // 秒(epoch)
}

func defaultClock() float64 { return float64(time.Now().UnixNano()) / 1e9 }

func NewSimSource(devices arr, clock func() float64) *SimSource {
	if clock == nil {
		clock = defaultClock
	}
	s := &SimSource{
		devices:   devices,
		setpoints: map[string]float64{"valve_open_sp": 45.0, "pump_freq_sp": 32.0, "sec_supply_temp_sp": 50.0},
		feedback:  map[string]float64{"valve_open": 45.0, "pump_freq": 32.0, "sec_supply_temp": 50.0},
		clock:     clock,
	}
	s.t0 = clock()
	return s
}

func (s *SimSource) wave(base, swing, period float64) float64 {
	return base + swing*0.5*math.Sin(2*math.Pi*(s.clock()-s.t0)/period)
}

func (s *SimSource) WriteSetpoint(pointID string, value float64) bool {
	if _, ok := s.setpoints[pointID]; ok {
		s.setpoints[pointID] = value
		return true
	}
	return false
}

// converge: 反馈量朝设定值收敛一步（一阶滞后 0.25）。返回 feedback 快照。
func (s *SimSource) converge() map[string]float64 {
	for _, p := range [][2]string{{"valve_open", "valve_open_sp"},
		{"pump_freq", "pump_freq_sp"}, {"sec_supply_temp", "sec_supply_temp_sp"}} {
		fb, sp := p[0], p[1]
		s.feedback[fb] += (s.setpoints[sp] - s.feedback[fb]) * 0.25
	}
	out := map[string]float64{}
	for k, v := range s.feedback {
		out[k] = v
	}
	return out
}

// Poll 返回 {addr: sample}，结构同 modbus 源。
func (s *SimSource) Poll() obj {
	fb := s.converge()
	out := obj{}
	for _, di := range s.devices {
		d := asObj(di)
		addrKey := fmt.Sprintf("%v", d["addr"])
		ts := int64(s.clock() * 1000)
		if asStr(get(d, "fault")) == "offline" {
			pts := obj{}
			for _, pi := range asArr(d["points"]) {
				p := asObj(pi)
				pts[asStr(p["id"])] = obj{"v": nil, "u": getOr(p, "unit", ""), "q": "offline"}
			}
			out[addrKey] = obj{"addr": d["addr"], "name": d["name"], "type": d["type"],
				"ts": ts, "ok": false, "health": "离线", "offline": true,
				"fails": float64(0), "next_retry_s": float64(0), "points": pts}
			continue
		}
		pts := obj{}
		for _, pi := range asArr(d["points"]) {
			p := asObj(pi)
			pid := asStr(p["id"])
			var v interface{}
			if fv, ok := fb[pid]; ok { // 可控反馈点：用闭环值
				v = pyRound(fv, 1)
			} else if _, ok := p["fixed"]; ok {
				v = p["fixed"]
			} else {
				rd := 1
				if r, ok := p["round"].(float64); ok {
					rd = int(r)
				}
				v = pyRound(s.wave(toF(getOr(p, "base", float64(0))),
					toF(getOr(p, "swing", float64(0))), toF(getOr(p, "period_s", float64(60)))), rd)
			}
			pts[pid] = obj{"v": v, "u": getOr(p, "unit", ""), "q": "good"}
		}
		out[addrKey] = obj{"addr": d["addr"], "name": d["name"], "type": d["type"],
			"ts": ts, "ok": true, "health": "在线", "offline": false,
			"fails": float64(0), "next_retry_s": float64(0), "points": pts}
	}
	return out
}

// pyRound 模拟 Python3 round()（round half to even / 银行家舍入）。
func pyRound(x float64, digits int) float64 {
	pow := math.Pow(10, float64(digits))
	return math.RoundToEven(x*pow) / pow
}
