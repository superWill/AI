// Package app:HMI 状态机与帧缓存,对标 drm_hmi_v4.py 的 main() 闭包,
// 无硬件依赖,可在开发机单测。
// 设备配置表单状态机已随 LCD 配置页退役(设备接入走 Web /config 页)。
package app

import (
	"math"
	"sync"
	"time"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/api"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/templates"
)

type ConfigAPI interface {
	Login() error
	AddDevice(payload map[string]any) (bool, []string)
	GetDraft() (map[string]any, bool, error)
	Compile(draft map[string]any) (bool, []string)
	Activate() (bool, string, []string)
	ActivateStatus() (api.ActivateStatus, error)
}

// Deps 注入 OnTap 的外部依赖,便于单测 mock。
type Deps struct {
	Blit    func(frame []byte)
	PostCmd func(pointID string, value int)
	Cache   *FrameCache
	Dirty   func()
	Logf    func(format string, args ...any)
	Config  ConfigAPI
}

type AddForm struct {
	TplIdx int
	BusIdx int
	Slave  int
}

// State 对标 drm_hmi_v4.main 的 state dict + targets。
// Python 靠 GIL 容忍触摸线程与主循环并发,Go 用互斥锁。
type State struct {
	mu            sync.Mutex
	Page          string
	Buttons       []render.Button
	View          *render.View
	Targets       map[string]int
	Settings      render.LocalSettings
	Templates     []templates.Template
	Buses         []string
	AddForm       AddForm
	AddMessage    string
	AddBusy       bool
	settingsDirty bool
}

func NewState() *State {
	return &State{
		Page:     "overview",
		View:     &render.View{},
		Targets:  map[string]int{},
		Settings: render.LocalSettings{Brightness: 80, Theme: "light"},
		AddForm:  AddForm{Slave: 1},
	}
}

func (s *State) SetTemplates(items []templates.Template) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Templates = append([]templates.Template(nil), items...)
}

func (s *State) SetView(v *render.View) {
	s.mu.Lock()
	defer s.mu.Unlock()
	v.LocalSettings = s.Settings
	s.View = v
}

func normalizeSettings(settings render.LocalSettings) render.LocalSettings {
	settings.Brightness = max(10, min(100, settings.Brightness))
	if settings.Theme != "dark" {
		settings.Theme = "light"
	}
	return settings
}

func (s *State) SetSettings(settings render.LocalSettings) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Settings = normalizeSettings(settings)
	if s.View != nil {
		s.View.LocalSettings = s.Settings
	}
}

func (s *State) ConsumeSettings() (render.LocalSettings, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	settings, dirty := s.Settings, s.settingsDirty
	s.settingsDirty = false
	return settings, dirty
}

// RenderInputs 返回渲染输入的一致快照(targets 浅拷贝,防触摸线程并发写)。
func (s *State) RenderInputs() (view *render.View, page string, targets map[string]int,
	addForm *render.AddForm, addMessage string, addBusy bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	targets = make(map[string]int, len(s.Targets))
	for k, v := range s.Targets {
		targets[k] = v
	}
	if len(s.Templates) > 0 && len(s.Buses) > 0 {
		tpl := s.Templates[floorMod(s.AddForm.TplIdx, len(s.Templates))]
		bus := s.Buses[floorMod(s.AddForm.BusIdx, len(s.Buses))]
		addForm = &render.AddForm{Template: tpl.Label, Bus: bus, Slave: s.AddForm.Slave}
	} else {
		addForm = &render.AddForm{Slave: s.AddForm.Slave}
	}
	return s.View, s.Page, targets, addForm, s.AddMessage, s.AddBusy
}

// CommitIfCurrent 对标主循环:渲染期间未被切页才提交按钮并上屏。
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
		case b.Action == "brightness_change":
			s.Settings.Brightness = max(10, min(100, s.Settings.Brightness+b.Delta))
			s.settingsDirty = true
			d.Dirty()
		case b.Action == "theme_set":
			s.Settings.Theme = b.Theme
			s.Settings = normalizeSettings(s.Settings)
			s.settingsDirty = true
			d.Dirty()
		case b.Action == "open_device_add":
			s.Page = "device_add"
			s.AddForm = AddForm{Slave: 1}
			s.AddBusy = false
			if len(s.Templates) == 0 {
				s.AddMessage = "模板库缺失"
			} else if d.Config == nil {
				s.AddMessage = "配置服务不可用"
			} else {
				s.AddMessage = "读取总线…"
				go s.loadBuses(d)
			}
			d.Dirty()
		case b.Action == "config_back":
			s.Page = "nodes"
			s.AddMessage = ""
			d.Cache.Invalidate("nodes", "device_add")
			d.Dirty()
		case b.Action == "devadd_change":
			if s.AddBusy {
				return
			}
			s.changeAddForm(b.Field, b.Delta)
			d.Cache.Invalidate("device_add")
			d.Dirty()
		case b.Action == "devadd_save":
			if s.AddBusy {
				return
			}
			if len(s.Templates) == 0 {
				s.AddMessage = "模板库缺失"
				d.Dirty()
				return
			}
			if len(s.Buses) == 0 {
				s.AddMessage = "无可用总线"
				d.Dirty()
				return
			}
			if d.Config == nil {
				s.AddMessage = "配置服务不可用"
				d.Dirty()
				return
			}
			tpl := s.Templates[floorMod(s.AddForm.TplIdx, len(s.Templates))]
			bus := s.Buses[floorMod(s.AddForm.BusIdx, len(s.Buses))]
			slave := s.AddForm.Slave
			s.AddBusy, s.AddMessage = true, ""
			d.Cache.Invalidate("device_add")
			d.Dirty()
			go s.publishDevice(d, tpl, bus, slave)
		case b.Action == "" && b.SP != "": // 控制键:{fb,sp,delta,lo,hi}
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

func floorMod(v, n int) int {
	if n <= 0 {
		return 0
	}
	r := v % n
	if r < 0 {
		r += n
	}
	return r
}

func (s *State) changeAddForm(field string, delta int) {
	switch field {
	case "template":
		s.AddForm.TplIdx = floorMod(s.AddForm.TplIdx+delta, len(s.Templates))
	case "bus":
		s.AddForm.BusIdx = floorMod(s.AddForm.BusIdx+delta, len(s.Buses))
	case "slave":
		s.AddForm.Slave = 1 + floorMod(s.AddForm.Slave-1+delta, 247)
	}
}

func draftBuses(draft map[string]any) []string {
	items, _ := draft["buses"].([]any)
	var out []string
	for _, item := range items {
		bus, _ := item.(map[string]any)
		id, _ := bus["bus_id"].(string)
		if id != "" {
			out = append(out, id)
		}
	}
	return out
}

func draftHasDevice(draft map[string]any, deviceID string) bool {
	items, _ := draft["hardware_devices"].([]any)
	for _, item := range items {
		dev, _ := item.(map[string]any)
		if id, _ := dev["device_id"].(string); id == deviceID {
			return true
		}
	}
	return false
}

func (s *State) loadBuses(d Deps) {
	err := d.Config.Login()
	var draft map[string]any
	var has bool
	if err == nil {
		draft, has, err = d.Config.GetDraft()
	}
	s.mu.Lock()
	if err != nil {
		s.AddMessage = truncRunes(err.Error(), 28)
	} else if !has {
		s.AddMessage = "无配置草稿"
	} else {
		s.Buses = draftBuses(draft)
		if len(s.Buses) == 0 {
			s.AddMessage = "无可用总线"
		} else {
			s.AddForm.BusIdx = floorMod(s.AddForm.BusIdx, len(s.Buses))
			s.AddMessage = ""
		}
	}
	s.mu.Unlock()
	d.Cache.Invalidate("device_add")
	d.Dirty()
}

func firstError(errs []string, fallback string) string {
	if len(errs) > 0 && errs[0] != "" {
		return truncRunes(errs[0], 28)
	}
	return fallback
}

func (s *State) publishDevice(d Deps, tpl templates.Template, bus string, slave int) {
	fail := func(message string) {
		s.mu.Lock()
		s.AddBusy = false
		s.AddMessage = truncRunes(message, 28)
		s.mu.Unlock()
		d.Cache.Invalidate("device_add")
		d.Dirty()
	}
	if err := d.Config.Login(); err != nil {
		fail(err.Error())
		return
	}
	draft, has, err := d.Config.GetDraft()
	if err != nil {
		fail(err.Error())
		return
	}
	if !has {
		fail("无配置草稿")
		return
	}
	deviceID, payload := templates.Expand(tpl, bus, slave)
	if draftHasDevice(draft, deviceID) {
		fail("device_id 重复: " + deviceID)
		return
	}
	if ok, errs := d.Config.AddDevice(payload); !ok {
		fail(firstError(errs, "添加设备失败"))
		return
	}
	draft, has, err = d.Config.GetDraft()
	if err != nil {
		fail(err.Error())
		return
	}
	if !has {
		fail("设备写入后草稿丢失")
		return
	}
	if ok, errs := d.Config.Compile(draft); !ok {
		fail(firstError(errs, "编译失败"))
		return
	}
	if ok, _, errs := d.Config.Activate(); !ok {
		fail(firstError(errs, "激活失败"))
		return
	}
	var lastErr error
	for i := 0; i < 20; i++ {
		status, statusErr := d.Config.ActivateStatus()
		if statusErr == nil && status.ActivationState() == "active" {
			s.mu.Lock()
			s.AddBusy = false
			s.AddMessage = "已发布"
			s.Page = "nodes"
			s.mu.Unlock()
			d.Cache.Invalidate("overview", "monitor", "nodes", "control", "settings", "device_add")
			d.Logf("[devadd] %s published", deviceID)
			d.Dirty()
			return
		}
		if statusErr != nil {
			lastErr = statusErr
		} else if len(status.ActivationErrors()) > 0 {
			fail(firstError(status.ActivationErrors(), "激活失败"))
			return
		}
		time.Sleep(250 * time.Millisecond)
	}
	if lastErr != nil {
		fail(lastErr.Error())
	} else {
		fail("激活状态确认超时")
	}
}

func truncRunes(value string, n int) string {
	runes := []rune(value)
	if len(runes) > n {
		return string(runes[:n])
	}
	return value
}
