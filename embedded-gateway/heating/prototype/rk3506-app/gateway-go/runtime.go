// 运行时状态容器（Go 移植自 app.py Runtime）：线程安全的快照/事件/指令/seq + 看门狗时戳。
// 时钟可注入(mono/wall)便于与 Python 对拍。clock_sync 用真实年份(对齐 Python gmtime 不受 time 影响)。
package main

import (
	"sort"
	"sync"
	"time"
)

type Runtime struct {
	cfg          obj
	mu           sync.Mutex
	snapshot     obj // {addr: sample}
	events       arr // 新→旧,最多 20
	commands     arr // 新→旧,最多 50
	seq          int64
	lastPollMono float64
	nowMono      func() float64
	nowWall      func() float64
}

func NewRuntime(cfg obj, mono, wall func() float64) *Runtime {
	if mono == nil {
		mono = func() float64 { return float64(time.Now().UnixNano()) / 1e9 }
	}
	if wall == nil {
		wall = func() float64 { return float64(time.Now().UnixNano()) / 1e9 }
	}
	r := &Runtime{cfg: cfg, snapshot: obj{}, events: arr{}, commands: arr{},
		nowMono: mono, nowWall: wall}
	r.lastPollMono = mono()
	return r
}

func (r *Runtime) MarkAlive() {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.lastPollMono = r.nowMono()
}

func (r *Runtime) CollectorAgeMs() int64 {
	r.mu.Lock()
	defer r.mu.Unlock()
	return int64((r.nowMono() - r.lastPollMono) * 1000)
}

func (r *Runtime) Update(snap obj) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.snapshot = snap
}

func (r *Runtime) Get() obj {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := obj{}
	for k, v := range r.snapshot {
		out[k] = v
	}
	return out
}

func (r *Runtime) AddEvent(ev obj) {
	ev["time"] = int64(r.nowWall() * 1000)
	r.mu.Lock()
	defer r.mu.Unlock()
	r.events = append(arr{ev}, r.events...) // appendleft
	if len(r.events) > 20 {
		r.events = r.events[:20]
	}
}

func (r *Runtime) RecordCommand(rec obj) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.commands = append(arr{rec}, r.commands...)
	if len(r.commands) > 50 {
		r.commands = r.commands[:50]
	}
}

// sortedSamples 按 addr 键排序返回快照样本（map 迭代确定化，对齐对拍）。
func (r *Runtime) sortedSamples() []obj {
	keys := make([]string, 0, len(r.snapshot))
	for k := range r.snapshot {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make([]obj, 0, len(keys))
	for _, k := range keys {
		out = append(out, asObj(r.snapshot[k]))
	}
	return out
}

func clockSyncNow() string {
	if time.Now().UTC().Year() >= 2020 {
		return "synced"
	}
	return "unsynced"
}

func (r *Runtime) Telemetry() obj {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.seq++
	devices := arr{}
	for _, s := range r.sortedSamples() {
		devices = append(devices, obj{"addr": s["addr"], "name": s["name"],
			"type": getOr(s, "type", ""), "ok": s["ok"], "points": s["points"]})
	}
	return obj{
		"device_id":  getOr(r.cfg, "device_id", "rk3506-gw-01"),
		"ts":         int64(r.nowWall() * 1000),
		"clock_sync": clockSyncNow(),
		"seq":        r.seq,
		"devices":    devices,
	}
}

func (r *Runtime) View() obj {
	r.mu.Lock()
	defer r.mu.Unlock()
	devices := arr{}
	for _, s := range r.sortedSamples() {
		devices = append(devices, s)
	}
	cmds := r.commands
	if len(cmds) > 10 {
		cmds = cmds[:10]
	}
	return obj{
		"device_id": r.cfg["device_id"],
		"ts":        int64(r.nowWall() * 1000),
		"devices":   devices,
		"events":    append(arr{}, r.events...),
		"commands":  append(arr{}, cmds...),
	}
}
