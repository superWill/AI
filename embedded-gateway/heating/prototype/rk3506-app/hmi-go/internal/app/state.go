// Package app:HMI 状态机与帧缓存,对标 drm_hmi_v4.py 的 main() 闭包,
// 无硬件依赖,可在开发机单测。
package app

import (
	"encoding/json"
	"fmt"
	"math"
	"path"
	"strconv"
	"strings"
	"sync"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

// 选项表,对标 drm_hmi_v4.py 模块级常量(顺序决定环切与标签查找)。
var deviceTypes = []struct{ Value, Label string }{
	{"other", "设备"}, {"pump_vfd", "水泵"},
	{"temp_humidity_sensor", "温度传感器"},
	{"pressure_sensor", "压力传感器"}, {"heat_meter", "热量表"},
	{"energy_meter", "电能表"}, {"io_module", "IO 模块"},
}

var (
	serialPorts   = []any{"/dev/ttyS1", "/dev/ttyS2", "/dev/ttyS3", "/dev/ttyS4"}
	bauds         = []any{1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200}
	parities      = []any{"none", "even", "odd"}
	pollIntervals = []any{250, 500, 1000, 2000, 5000, 10000}
)

// NewDeviceForm 对标 drm_hmi_v4.new_device_form()。
func NewDeviceForm() map[string]any {
	return map[string]any{
		"deviceType": "other", "deviceTypeLabel": "设备",
		"serialPort": "/dev/ttyS1", "baudRate": 9600, "dataBits": 8,
		"stopBits": 1, "parity": "none", "slaveId": 1, "pollInterval": 1000,
	}
}

func typeLabel(value string) string {
	for _, t := range deviceTypes {
		if t.Value == value {
			return t.Label
		}
	}
	return "设备"
}

// floorMod 对标 Python `%`(地板取模;Go 原生 % 对负数结果不同)。
func floorMod(a, n int) int {
	m := a % n
	if m < 0 {
		m += n
	}
	return m
}

// anyInt 对标 Python int(v)(浮点向零截断),失败用默认值。
func anyInt(v any, def int) int {
	switch x := v.(type) {
	case int:
		return x
	case json.Number:
		if i, err := strconv.Atoi(string(x)); err == nil {
			return i
		}
		if f, err := x.Float64(); err == nil {
			return int(f)
		}
	case string:
		if i, err := strconv.Atoi(strings.TrimSpace(x)); err == nil {
			return i
		}
	case float64:
		return int(x)
	}
	return def
}

// Deps 注入 OnTap 的外部依赖,便于单测 mock。
type Deps struct {
	Blit        func(frame []byte)
	PostCmd     func(pointID string, value int)
	FetchConfig func() ([]map[string]any, error)
	// SaveConfig 返回 (ok, 服务端回写的 nodes, 是否携带 nodes)
	SaveConfig func(nodes []map[string]any) (bool, []map[string]any, bool)
	Cache      *FrameCache
	Dirty      func()
	Logf       func(format string, args ...any)
}

// State 对标 drm_hmi_v4.main 的 state dict + targets。
// Python 靠 GIL 容忍触摸线程与主循环并发,Go 用互斥锁。
type State struct {
	mu              sync.Mutex
	Page            string
	Buttons         []render.Button
	View            *render.View
	ConfiguredNodes []map[string]any
	ConfigSlot      int
	DeviceForm      map[string]any
	ConfigMessage   string
	Targets         map[string]int
}

func NewState() *State {
	return &State{
		Page:       "overview",
		View:       &render.View{},
		DeviceForm: NewDeviceForm(),
		Targets:    map[string]int{},
	}
}

// SetView 注入快照并挂上草稿(对标主循环 L317-320)。
func (s *State) SetView(v *render.View) {
	s.mu.Lock()
	defer s.mu.Unlock()
	v.ConfiguredNodes = s.ConfiguredNodes
	s.View = v
}

func (s *State) SetConfiguredNodes(nodes []map[string]any) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.ConfiguredNodes = nodes
}

// RenderInputs 返回渲染输入的一致快照(map/slice 浅拷贝,防触摸线程并发写)。
func (s *State) RenderInputs() (view *render.View, page string, form map[string]any,
	slot int, msg string, targets map[string]int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	form = make(map[string]any, len(s.DeviceForm))
	for k, v := range s.DeviceForm {
		form[k] = v
	}
	targets = make(map[string]int, len(s.Targets))
	for k, v := range s.Targets {
		targets[k] = v
	}
	return s.View, s.Page, form, s.ConfigSlot, s.ConfigMessage, targets
}

// CommitIfCurrent 对标主循环 L331-333:渲染期间未被切页才提交按钮并上屏。
func (s *State) CommitIfCurrent(page string, buttons []render.Button, blit func()) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.Page == page {
		s.Buttons = buttons
		blit()
	}
}

// OnTap 对标 drm_hmi_v4.on_tap,±8px 容差,首个命中即处理。
func (s *State) OnTap(x, y int, d Deps) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, b := range s.Buttons {
		if !b.Hit(x, y) {
			continue
		}
		switch {
		case b.Nav != "":
			s.Page = b.Nav
			d.Logf("[nav] → %s", b.Nav)
			if frame, btns, ok := d.Cache.Get(b.Nav); ok {
				s.Buttons = btns
				d.Blit(frame)
			}
			d.Dirty()
		case b.Action == "open_device_add" || b.Action == "open_device_config":
			nodes, err := d.FetchConfig()
			if err != nil {
				nodes = nil
			}
			s.ConfiguredNodes = nodes
			s.ConfigMessage = ""
			slot := 0
			if b.Action == "open_device_config" && len(s.ConfiguredNodes) > 0 {
				slot = 1
			}
			s.loadConfigSlot(slot)
			s.Page = "device_config"
			d.Dirty()
		case b.Action == "config_back":
			s.Page = "nodes"
			d.Dirty()
		case b.Action == "config_change":
			s.configChange(b.Field, b.Delta)
			s.ConfigMessage = ""
			d.Dirty()
		case b.Action == "config_save":
			s.configSave(d)
			d.Dirty()
		default: // 控制键:{fb,sp,delta,lo,hi}
			base, has := s.Targets[b.FBID]
			if !has {
				base = b.Lo
				if f, ok := render.Pick(s.View, b.FBID).Float(); ok {
					base = int(math.RoundToEven(f)) // Python round() 银行家舍入
				}
			}
			nv := max(b.Lo, min(b.Hi, base+b.Delta))
			s.Targets[b.FBID] = nv
			d.Logf("[ctl] tap → %s = %d", b.SP, nv)
			d.PostCmd(b.SP, nv)
			d.Dirty()
		}
		return
	}
}

// loadConfigSlot:slot 0=新建,1..n=编辑第 slot-1 个,地板模环绕。
func (s *State) loadConfigSlot(slot int) {
	n := len(s.ConfiguredNodes)
	s.ConfigSlot = floorMod(slot, n+1)
	if s.ConfigSlot == 0 {
		s.DeviceForm = NewDeviceForm()
		return
	}
	node := make(map[string]any)
	for k, v := range s.ConfiguredNodes[s.ConfigSlot-1] {
		node[k] = v
	}
	node["deviceTypeLabel"] = typeLabel(render.AnyStr(node["deviceType"]))
	s.DeviceForm = node
}

// cycleValue:候选表环切;当前值不在表中时从 index 0 起步。
// 比较经 AnyStr 规范化(表单值可能是 json.Number,候选表是 Go 原生 int/string)。
func (s *State) cycleValue(field string, values []any, delta int) {
	cur := render.AnyStr(s.DeviceForm[field])
	index := 0
	for i, v := range values {
		if render.AnyStr(v) == cur {
			index = i
			break
		}
	}
	s.DeviceForm[field] = values[floorMod(index+delta, len(values))]
}

func (s *State) configChange(field string, delta int) {
	switch field {
	case "record":
		s.loadConfigSlot(s.ConfigSlot + delta)
	case "deviceType":
		vals := make([]any, len(deviceTypes))
		for i, t := range deviceTypes {
			vals[i] = t.Value
		}
		s.cycleValue(field, vals, delta)
		s.DeviceForm["deviceTypeLabel"] = typeLabel(render.AnyStr(s.DeviceForm["deviceType"]))
	case "serialPort":
		s.cycleValue(field, serialPorts, delta)
	case "baudRate":
		s.cycleValue(field, bauds, delta)
	case "parity":
		s.cycleValue(field, parities, delta)
	case "pollInterval":
		s.cycleValue(field, pollIntervals, delta)
	case "slaveId":
		s.DeviceForm["slaveId"] = floorMod(anyInt(s.DeviceForm["slaveId"], 1)-1+delta, 247) + 1
	}
}

// configSave 对标 drm_hmi_v4 L277-300。
// 与 Python 的两处刻意差异(Python 在异常路径会 StopIteration 崩溃,Go 走安全默认):
// deviceType 不在表中时 name 用 "设备";保存后 id 未找到时 slot 保持不变。
func (s *State) configSave(d Deps) {
	adding := s.ConfigSlot == 0
	form := make(map[string]any, len(s.DeviceForm)+6)
	for k, v := range s.DeviceForm {
		form[k] = v
	}
	delete(form, "deviceTypeLabel")
	form["type"] = "Southbound"
	form["driver"] = "Modbus RTU"
	form["transport"] = "RTU"
	form["endpoint"] = form["serialPort"]
	form["byteOrder"] = "ABCD"
	form["name"] = fmt.Sprintf("%s %s",
		typeLabel(render.AnyStr(form["deviceType"])), render.AnyStr(form["slaveId"]))
	nodes := make([]map[string]any, len(s.ConfiguredNodes))
	copy(nodes, s.ConfiguredNodes)
	if s.ConfigSlot != 0 {
		form["id"] = nodes[s.ConfigSlot-1]["id"]
		nodes[s.ConfigSlot-1] = form
	} else {
		form["id"] = fmt.Sprintf("local-%s-%s",
			path.Base(render.AnyStr(form["serialPort"])), render.AnyStr(form["slaveId"]))
		nodes = append(nodes, form)
	}
	ok, saved, hasSaved := d.SaveConfig(nodes)
	if !ok {
		s.ConfigMessage = "配置异常"
		return
	}
	if hasSaved {
		s.ConfiguredNodes = saved
	} else {
		s.ConfiguredNodes = nodes
	}
	for i, n := range s.ConfiguredNodes {
		if render.AnyStr(n["id"]) == render.AnyStr(form["id"]) {
			s.ConfigSlot = i + 1
			break
		}
	}
	if adding {
		s.ConfigMessage = "设备已接入"
	} else {
		s.ConfigMessage = "配置正常"
	}
	d.Cache.Invalidate("nodes", "device_config")
}
