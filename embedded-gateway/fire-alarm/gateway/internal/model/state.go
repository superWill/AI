// Package model 维护 CRT 侧看到的控制器运行态。
//
// 状态保持语义直接对应 GB 4717-2024，三种保持方式互不相同，实现时最容易搞混：
//
//	火警 / 启动 / 监管 —— 锁存，保持至手动复位（5.4.1.1 / 5.4.2.9 / 5.4.5.2）
//	故障 / 反馈       —— 跟随，源消失即消失（5.4.3.2 光保持"至故障排除"）
//	屏蔽             —— 独立于复位，只能手动解除（5.4.4.7）
//
// 复位（0x16）只清锁存态，不清屏蔽，也不清仍然存在的故障——故障会在复位后由
// 主机重新上报（5.4.3.8：≤100 s 重新显示）。
package model

import (
	"sort"
	"sync"
	"time"

	"github.com/superwill/fire-alarm/gateway/internal/crtlink"
)

// Key 是点位在系统中的唯一标识：回路号 + 回路内地址。
type Key struct {
	Loop uint8 `json:"loop"`
	Addr uint8 `json:"addr"`
}

// Device 是一个回路点位的运行态。各状态位可以并存——一只探测器可以既报火警
// 又被屏蔽，面板要同时反映，不能用单一枚举压扁。
type Device struct {
	Key
	Zone        uint16    `json:"zone"`
	Name        string    `json:"name"`
	Type        string    `json:"type"`
	Alarm       bool      `json:"alarm"`
	FirstAlarm  bool      `json:"first_alarm"`
	Manual      bool      `json:"manual"` // 火警来自手报/消火栓按钮（5.4.1.4 须可区分）
	Action      bool      `json:"action"`
	Feedback    bool      `json:"feedback"`
	Supervisory bool      `json:"supervisory"`
	Shielded    bool      `json:"shielded"`
	FaultFlags  uint8     `json:"fault_flags"`
	LastSeen    time.Time `json:"last_seen"`
}

func (d *Device) Faulted() bool { return d.FaultFlags != 0 }

// FaultText 把故障标志位翻成中文，供页面直接显示。
func (d *Device) FaultText() string {
	if d.FaultFlags == 0 {
		return ""
	}
	var s []string
	if d.FaultFlags&crtlink.FaultOpen != 0 {
		s = append(s, "断路")
	}
	if d.FaultFlags&crtlink.FaultShort != 0 {
		s = append(s, "短路")
	}
	if d.FaultFlags&crtlink.FaultTimeout != 0 {
		s = append(s, "失联")
	}
	if d.FaultFlags&crtlink.FaultInvalid != 0 {
		s = append(s, "响应非法")
	}
	out := s[0]
	for _, x := range s[1:] {
		out += "/" + x
	}
	return out
}

// Event 是一条落账的事件，对应黑匣子里的一行（附录 B B.1.1）。
type Event struct {
	Seq     uint64    `json:"seq"`
	Kind    string    `json:"kind"`
	EventID uint32    `json:"event_id"`
	Loop    uint8     `json:"loop"`
	Addr    uint8     `json:"addr"`
	Zone    uint16    `json:"zone"`
	Detail  string    `json:"detail"`
	At      time.Time `json:"at"`
}

const maxEvents = 5000

// State 是 CRT 侧的全量运行态，并发安全。
type State struct {
	mu       sync.RWMutex
	devices  map[Key]*Device
	points   map[Key]Point
	events   []Event
	nextSeq  uint64
	first    *Event // 首火警，复位前不被后续火警顶掉（5.4.1.7）
	linkUp   bool
	lastBeat time.Time
	mainOK   bool
	battOK   bool
	rev      uint64 // 每次变更自增，页面据此判断是否需要重绘
}

func NewState() *State {
	return &State{devices: map[Key]*Device{}, points: map[Key]Point{}, mainOK: true, battOK: true}
}

// Point 是工程点表里的一条：名称与类型只在 CRT 侧维护，不占用总线带宽。
type Point struct {
	Loop uint8  `json:"loop"`
	Addr uint8  `json:"addr"`
	Name string `json:"name"`
	Type string `json:"type"`
	Zone uint16 `json:"zone"`
}

// LoadPoints 装载工程点表。已在线的点会就地补上名称。
func (s *State) LoadPoints(points []Point) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.points == nil {
		s.points = map[Key]Point{}
	}
	for _, p := range points {
		k := Key{p.Loop, p.Addr}
		s.points[k] = p
		if d, ok := s.devices[k]; ok {
			d.Name, d.Type = p.Name, p.Type
			if p.Zone != 0 {
				d.Zone = p.Zone
			}
		}
	}
	s.rev++
}

func (s *State) dev(loop, addr uint8) *Device {
	k := Key{loop, addr}
	d, ok := s.devices[k]
	if !ok {
		d = &Device{Key: k}
		if p, ok := s.points[k]; ok {
			d.Name, d.Type, d.Zone = p.Name, p.Type, p.Zone
		}
		s.devices[k] = d
	}
	return d
}

func (s *State) log(kind string, r crtlink.Report, detail string) {
	at := r.At
	if at.IsZero() {
		at = time.Now()
	}
	s.nextSeq++
	e := Event{Seq: s.nextSeq, Kind: kind, EventID: r.EventID, Loop: r.Loop,
		Addr: r.Addr, Zone: r.Zone, Detail: detail, At: at}
	s.events = append(s.events, e)
	if len(s.events) > maxEvents {
		s.events = s.events[len(s.events)-maxEvents:]
	}
	if kind == "火警" && s.first == nil {
		c := e
		s.first = &c
	}
}

// Apply 把一帧上行报文并入状态。返回是否产生了变更。
func (s *State) Apply(f crtlink.Frame) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	switch f.Type {
	case crtlink.TypeHeartbeat:
		hb, err := crtlink.DecodeHeartbeat(f.Data)
		if err != nil {
			return false
		}
		s.linkUp, s.lastBeat, s.mainOK, s.battOK = true, time.Now(), hb.MainOK, hb.BatteryOK
		s.rev++
		return true

	case crtlink.TypeReset:
		// 复位只清锁存态：火警/启动/监管/首火警。屏蔽与故障不动——
		// 屏蔽按 5.4.4.7 不受复位影响，故障由主机在 100 s 内重新上报。
		for _, d := range s.devices {
			d.Alarm, d.FirstAlarm, d.Manual, d.Action, d.Supervisory = false, false, false, false, false
			d.Feedback = false
		}
		s.first = nil
		s.nextSeq++
		s.events = append(s.events, Event{Seq: s.nextSeq, Kind: "复位",
			Detail: "控制器复位，锁存状态清除（屏蔽保持）", At: time.Now()})
		s.rev++
		return true

	case crtlink.TypePowerEvent:
		r, err := crtlink.DecodeReport(f.Data)
		if err != nil {
			return false
		}
		switch r.Code {
		case 1:
			s.mainOK = false
		case 2:
			s.battOK = false
		case 3:
			s.mainOK, s.battOK = true, true
		}
		s.log("电源", r, powerText(r.Code))
		s.rev++
		return true
	}

	r, err := crtlink.DecodeReport(f.Data)
	if err != nil {
		return false
	}
	d := s.dev(r.Loop, r.Addr)
	if r.Zone != 0 {
		d.Zone = r.Zone
	}
	d.LastSeen = time.Now()

	switch f.Type {
	case crtlink.TypeAlarm:
		d.Alarm = true
		d.Manual = r.Code&0x7F == crtlink.AlarmFromManual || r.Code&0x7F == crtlink.AlarmFromHydrant
		src := "探测器"
		if d.Manual {
			src = "手报"
		}
		if r.Code&crtlink.AlarmFirst != 0 && s.first == nil {
			d.FirstAlarm = true
			src = "首火警·" + src
		}
		s.log("火警", r, src)

	case crtlink.TypeAction:
		d.Action = true
		s.log("启动", r, "联动控制输出已启动")

	case crtlink.TypeFeedback:
		// 反馈跟随受控设备：Code=0 表示设备恢复原位，反馈随之撤销。
		d.Feedback = r.Code != 0
		if d.Feedback {
			s.log("反馈", r, "收到受控设备动作反馈")
		} else {
			s.log("反馈", r, "受控设备恢复，反馈撤销")
		}

	case crtlink.TypeFault:
		d.FaultFlags = r.Code
		if r.Code == 0 {
			s.log("故障", r, "故障排除")
		} else {
			s.log("故障", r, d.FaultText())
		}

	case crtlink.TypeShield:
		d.Shielded = r.Code != 0
		if d.Shielded {
			s.log("屏蔽", r, "已屏蔽")
		} else {
			s.log("屏蔽", r, "已解除屏蔽")
		}

	case crtlink.TypeSupervisor:
		d.Supervisory = r.Code != 0
		s.log("监管", r, "监管信号输入")

	default:
		return false
	}
	s.rev++
	return true
}

func powerText(code uint8) string {
	switch code {
	case 1:
		return "主电故障，已转备电"
	case 2:
		return "备电欠压/故障"
	case 3:
		return "电源恢复正常"
	}
	return "电源状态变化"
}

// Counters 是面板上那六个计数，页面顶部照面板顺序显示。
type Counters struct {
	Alarm       int `json:"alarm"`
	Supervisory int `json:"supervisory"`
	Action      int `json:"action"`
	Feedback    int `json:"feedback"`
	Fault       int `json:"fault"`
	Shielded    int `json:"shielded"`
}

// Snapshot 是页面消费的完整视图。
type Snapshot struct {
	Rev       uint64    `json:"rev"`
	LinkUp    bool      `json:"link_up"`
	LastBeat  time.Time `json:"last_beat"`
	MainOK    bool      `json:"main_ok"`
	BatteryOK bool      `json:"battery_ok"`
	Counters  Counters  `json:"counters"`
	First     *Event    `json:"first_alarm"`
	Devices   []Device  `json:"devices"`
	Events    []Event   `json:"events"`
	Now       time.Time `json:"now"`
}

// LinkTimeout 是判定链路断开的阈值：心跳周期 5 s 的 3 倍（见 default-parameters.json）。
const LinkTimeout = 15 * time.Second

// Snapshot 生成当前视图。events 参数限制返回的最近事件条数。
func (s *State) Snapshot(events int) Snapshot {
	s.mu.RLock()
	defer s.mu.RUnlock()

	snap := Snapshot{Rev: s.rev, MainOK: s.mainOK, BatteryOK: s.battOK,
		LastBeat: s.lastBeat, First: s.first, Now: time.Now()}
	snap.LinkUp = s.linkUp && time.Since(s.lastBeat) < LinkTimeout

	for _, d := range s.devices {
		c := *d
		snap.Devices = append(snap.Devices, c)
		if c.Alarm {
			snap.Counters.Alarm++
		}
		if c.Supervisory {
			snap.Counters.Supervisory++
		}
		if c.Action {
			snap.Counters.Action++
		}
		if c.Feedback {
			snap.Counters.Feedback++
		}
		if c.Faulted() {
			snap.Counters.Fault++
		}
		if c.Shielded {
			snap.Counters.Shielded++
		}
	}
	sort.Slice(snap.Devices, func(i, j int) bool {
		a, b := snap.Devices[i], snap.Devices[j]
		if a.Loop != b.Loop {
			return a.Loop < b.Loop
		}
		return a.Addr < b.Addr
	})

	if events > 0 && events < len(s.events) {
		snap.Events = append(snap.Events, s.events[len(s.events)-events:]...)
	} else {
		snap.Events = append(snap.Events, s.events...)
	}
	// 页面按时间倒序看，最新在上。
	for i, j := 0, len(snap.Events)-1; i < j; i, j = i+1, j-1 {
		snap.Events[i], snap.Events[j] = snap.Events[j], snap.Events[i]
	}
	return snap
}

// MarkLinkDown 在连接断开时调用，页面立刻显示链路故障而不必等心跳超时。
func (s *State) MarkLinkDown() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.linkUp = false
	s.rev++
}
