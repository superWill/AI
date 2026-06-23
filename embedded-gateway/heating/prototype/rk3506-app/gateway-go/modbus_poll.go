// ModbusSource 的轮询故障退避状态机（Go 移植自 app.py ModbusSource.poll/_bad_points）。
// 读寄存器(readFn)与时钟(mono/wall)可注入，便于脱离串口、与 Python 逐步对拍。
package main

import (
	"fmt"
	"strconv"
	"strings"
)

type devSt struct {
	fails      int
	offline    bool
	nextDue    float64
	backoffIdx int
	lastSample obj
}

type ModbusSource struct {
	devices        arr
	timeout        float64 // 秒（app.py 默认 1.0）
	offlineAfter   int
	backoffBase    float64
	backoffMax     float64
	defaultRetries int
	devState       map[string]*devSt
	// 注入点
	readFn func(addr, start, count int, timeoutSec float64, retries int) ([]uint16, string)
	mono   func() float64 // 单调钟（退避计时）
	wall   func() float64 // 墙钟秒（ts）
}

func NewModbusSource(devices arr, reliability obj,
	readFn func(int, int, int, float64, int) ([]uint16, string),
	mono, wall func() float64) *ModbusSource {
	m := &ModbusSource{
		devices: devices, timeout: 1.0,
		offlineAfter:   int(toF(getOr(reliability, "offline_after", float64(3)))),
		backoffBase:    toF(getOr(reliability, "backoff_base_s", float64(5))),
		backoffMax:     toF(getOr(reliability, "backoff_max_s", float64(30))),
		defaultRetries: int(toF(getOr(reliability, "retries", float64(1)))),
		devState:       map[string]*devSt{},
		readFn:         readFn, mono: mono, wall: wall,
	}
	for _, di := range devices {
		m.devState[fmt.Sprintf("%v", asObj(di)["addr"])] = &devSt{}
	}
	return m
}

func (m *ModbusSource) badPoints(d obj, q string) obj {
	pts := obj{}
	for _, pi := range asArr(d["points"]) {
		p := asObj(pi)
		pts[asStr(p["id"])] = obj{"v": nil, "u": getOr(p, "unit", ""), "q": q}
	}
	return pts
}

// pyIntStr: backoff 由整数配置算出，Python 里是 int，str(5)="5"（无小数）。
func pyIntStr(x float64) string { return strconv.FormatInt(int64(x), 10) }

// pyFloatStr: next_retry 由浮点时钟算出，Python 里是 float，str(3.0)="3.0"。
func pyFloatStr(x float64) string {
	s := strconv.FormatFloat(x, 'g', -1, 64)
	if !strings.ContainsAny(s, ".eE") {
		s += ".0"
	}
	return s
}

func (m *ModbusSource) Poll() obj {
	out := obj{}
	now := m.mono()
	for _, di := range m.devices {
		d := asObj(di)
		addrKey := fmt.Sprintf("%v", d["addr"])
		st := m.devState[addrKey]

		// 招2：离线设备退避未到期 → 不碰总线，复用上次样本
		if st.offline && now < st.nextDue {
			var s obj
			if st.lastSample != nil {
				s = obj{}
				for k, v := range st.lastSample { // dict(last_sample) 浅拷贝
					s[k] = v
				}
			} else {
				s = obj{"addr": d["addr"], "name": d["name"], "type": getOr(d, "type", ""),
					"ok": false, "points": m.badPoints(d, "offline")}
			}
			s["offline"] = true
			s["fails"] = float64(st.fails)
			nr := pyRound(maxF(0, st.nextDue-now), 1)
			s["next_retry_s"] = nr
			s["health"] = "离线·下次重试 " + pyFloatStr(nr) + "s"
			out[addrKey] = s
			continue
		}

		timeoutSec := toF(getOr(d, "timeout_ms", m.timeout*1000)) / 1000.0
		retries := int(toF(getOr(d, "retries", float64(m.defaultRetries))))
		regs, errc := m.readFn(int(toF(d["addr"])), int(toF(d["start"])), int(toF(d["count"])), timeoutSec, retries)
		ts := int64(m.wall() * 1000)

		if errc != "" {
			st.fails++
			if st.fails >= m.offlineAfter && !st.offline {
				st.offline = true
			}
			var health, q string
			if st.offline { // 进入/维持离线：几何退避降频
				backoff := minF(m.backoffBase*pow2(st.backoffIdx), m.backoffMax)
				st.nextDue = now + backoff
				st.backoffIdx++
				health = "离线·下次重试 " + pyIntStr(backoff) + "s"
				q = "offline"
			} else {
				health = fmt.Sprintf("异常(%s)×%d", errc, st.fails)
				q = "bad"
			}
			nextRetry := float64(0)
			if st.offline {
				nextRetry = pyRound(maxF(0, st.nextDue-now), 1)
			}
			sample := obj{"addr": d["addr"], "name": d["name"], "type": getOr(d, "type", ""),
				"ts": ts, "ok": false, "health": health,
				"fails": float64(st.fails), "offline": st.offline,
				"next_retry_s": nextRetry, "points": m.badPoints(d, q)}
			st.lastSample = sample
			out[addrKey] = sample
			continue
		}

		// 成功：复位故障状态
		st.fails = 0
		st.offline = false
		st.backoffIdx = 0
		st.nextDue = 0.0
		start := int(toF(d["start"]))
		pts := obj{}
		for _, pi := range asArr(d["points"]) {
			p := asObj(pi)
			idx := int(toF(p["reg"])) - start
			v := pyRound(float64(regs[idx])*toF(getOr(p, "scale", float64(1))), 3)
			pts[asStr(p["id"])] = obj{"v": v, "u": getOr(p, "unit", ""), "q": "good"}
		}
		sample := obj{"addr": d["addr"], "name": d["name"], "type": getOr(d, "type", ""),
			"ts": ts, "ok": true, "health": "在线", "fails": float64(0),
			"offline": false, "next_retry_s": float64(0), "points": pts}
		st.lastSample = sample
		out[addrKey] = sample
	}
	return out
}

func maxF(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}
func minF(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
func pow2(n int) float64 {
	r := 1.0
	for i := 0; i < n; i++ {
		r *= 2
	}
	return r
}
