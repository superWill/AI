// Package app:HMI 状态机与帧缓存,对标 drm_hmi_v4.py 的 main() 闭包,
// 无硬件依赖,可在开发机单测。
// 设备配置表单状态机已随 LCD 配置页退役(设备接入走 Web /config 页)。
package app

import (
	"math"
	"sync"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

// Deps 注入 OnTap 的外部依赖,便于单测 mock。
type Deps struct {
	Blit    func(frame []byte)
	PostCmd func(pointID string, value int)
	Cache   *FrameCache
	Dirty   func()
	Logf    func(format string, args ...any)
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
	settingsDirty bool
}

func NewState() *State {
	return &State{
		Page:     "overview",
		View:     &render.View{},
		Targets:  map[string]int{},
		Settings: render.LocalSettings{Brightness: 80, Theme: "light"},
	}
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
func (s *State) RenderInputs() (view *render.View, page string, targets map[string]int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	targets = make(map[string]int, len(s.Targets))
	for k, v := range s.Targets {
		targets[k] = v
	}
	return s.View, s.Page, targets
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
