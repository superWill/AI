package app

import (
	"reflect"
	"sync"
	"testing"
	"time"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/api"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/templates"
)

func noopDeps(cache *FrameCache) Deps {
	if cache == nil {
		cache = NewFrameCache()
	}
	return Deps{
		Blit:    func([]byte) {},
		PostCmd: func(string, int) {},
		Cache:   cache,
		Dirty:   func() {},
		Logf:    func(string, ...any) {},
	}
}

func viewFromJSON(t *testing.T, blob string) *render.View {
	v, err := render.DecodeView([]byte(blob))
	if err != nil {
		t.Fatal(err)
	}
	return v
}

// 控制键:无 target 时 base=round(cur) 银行家舍入;clamp 到 [lo,hi];POST 下发。
func TestOnTapControl(t *testing.T) {
	s := NewState()
	s.View = viewFromJSON(t, `{"devices":[{"name":"d","ok":true,
		"points":{"pump_freq":{"v":38.5,"u":"Hz","q":"good"}}}]}`)
	s.Buttons = []render.Button{
		{Rect: [4]int{690, 312, 64, 64}, FBID: "pump_freq", SP: "pump_freq_sp",
			Delta: 2, Lo: 0, Hi: 50},
	}
	var gotSP string
	var gotVal int
	d := noopDeps(nil)
	d.PostCmd = func(sp string, v int) { gotSP, gotVal = sp, v }
	s.OnTap(700, 320, d)
	// round(38.5) 银行家舍入 → 38,+2 → 40
	if gotSP != "pump_freq_sp" || gotVal != 40 {
		t.Fatalf("下发 %s=%d != pump_freq_sp=40", gotSP, gotVal)
	}
	if s.Targets["pump_freq"] != 40 {
		t.Fatalf("target %d", s.Targets["pump_freq"])
	}
	// 已有 target 后按 clamp 累加到 hi
	for i := 0; i < 10; i++ {
		s.OnTap(700, 320, d)
	}
	if s.Targets["pump_freq"] != 50 {
		t.Fatalf("clamp 到 hi 失败: %d", s.Targets["pump_freq"])
	}
}

// ±8px 容差:边界外 9px 不命中,8px 命中。
func TestOnTapTolerance(t *testing.T) {
	s := NewState()
	s.Buttons = []render.Button{{Rect: [4]int{100, 100, 50, 30}, Nav: "monitor"}}
	d := noopDeps(nil)
	s.OnTap(91, 100, d) // x=100-9 → 不命中
	if s.Page == "monitor" {
		t.Fatal("容差外不应命中")
	}
	s.OnTap(92, 100, d) // x=100-8 → 命中
	if s.Page != "monitor" {
		t.Fatal("容差内应命中")
	}
}

func TestOnTapDisplaySettings(t *testing.T) {
	s := NewState()
	dirty := 0
	d := noopDeps(nil)
	d.Dirty = func() { dirty++ }
	s.Buttons = []render.Button{
		{Rect: [4]int{466, 120, 68, 48}, Action: "brightness_change", Delta: -10},
	}
	s.OnTap(480, 130, d)
	settings, changed := s.ConsumeSettings()
	if !changed || settings.Brightness != 70 || dirty != 1 {
		t.Fatalf("brightness=%d changed=%v dirty=%d", settings.Brightness, changed, dirty)
	}
	s.Buttons = []render.Button{
		{Rect: [4]int{612, 212, 120, 48}, Action: "theme_set", Theme: "dark"},
	}
	s.OnTap(620, 220, d)
	settings, changed = s.ConsumeSettings()
	if !changed || settings.Theme != "dark" || dirty != 2 {
		t.Fatalf("theme=%s changed=%v dirty=%d", settings.Theme, changed, dirty)
	}
}

// nav 命中缓存页 → 直接用缓存按钮 + blit。
func TestOnTapNavUsesCache(t *testing.T) {
	s := NewState()
	cache := NewFrameCache()
	cachedBtns := []render.Button{{Rect: [4]int{1, 2, 3, 4}, Nav: "x"}}
	cache.Put("monitor", []byte{1, 2, 3}, cachedBtns)
	s.Buttons = []render.Button{{Rect: [4]int{0, 442, 104, 38}, Nav: "monitor"}}
	blitted := false
	d := noopDeps(cache)
	d.Blit = func(f []byte) { blitted = len(f) == 3 }
	s.OnTap(10, 450, d)
	if s.Page != "monitor" || !blitted || len(s.Buttons) != 1 || s.Buttons[0].Nav != "x" {
		t.Fatalf("nav 缓存直出失败: page=%s blit=%v", s.Page, blitted)
	}
}

// open_device_config:有草稿 → slot 1;fetch 失败 → 空列表 slot 0。

type mockConfig struct {
	mu        sync.Mutex
	calls     []string
	draft     map[string]any
	hasDraft  bool
	addErrors []string
}

func (m *mockConfig) call(name string) {
	m.mu.Lock()
	m.calls = append(m.calls, name)
	m.mu.Unlock()
}

func (m *mockConfig) Login() error { m.call("login"); return nil }
func (m *mockConfig) GetDraft() (map[string]any, bool, error) {
	m.call("draft")
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.draft, m.hasDraft, nil
}
func (m *mockConfig) AddDevice(payload map[string]any) (bool, []string) {
	m.call("devices")
	if len(m.addErrors) > 0 {
		return false, m.addErrors
	}
	hardware, _ := payload["hardware"].(map[string]any)
	m.mu.Lock()
	items, _ := m.draft["hardware_devices"].([]any)
	m.draft["hardware_devices"] = append(items, hardware)
	m.mu.Unlock()
	return true, nil
}
func (m *mockConfig) Compile(map[string]any) (bool, []string) {
	m.call("compile")
	return true, nil
}
func (m *mockConfig) Activate() (bool, string, []string) {
	m.call("activate")
	return true, "active", nil
}
func (m *mockConfig) ActivateStatus() (api.ActivateStatus, error) {
	m.call("status")
	var status api.ActivateStatus
	status.LastActivate.State = "active"
	return status, nil
}

func simTemplate() templates.Template {
	return templates.Template{
		ID: "pumpvfd", Label: "循环泵变频器", Source: "sim:test",
		Hardware:        map[string]any{"device_id": "$ID", "bus_id": "$BUS", "slave": "$SLAVE"},
		BusinessDevices: []any{},
	}
}

func waitFor(t *testing.T, check func() bool) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if check() {
			return
		}
		time.Sleep(5 * time.Millisecond)
	}
	t.Fatal("异步状态等待超时")
}

func TestDeviceAddOpenLoadsBusesAndWrapsFields(t *testing.T) {
	s := NewState()
	s.SetTemplates([]templates.Template{simTemplate(), {ID: "safeio", Label: "安全IO", Source: "sim:test", Hardware: map[string]any{}, BusinessDevices: []any{}}})
	m := &mockConfig{hasDraft: true, draft: map[string]any{
		"buses":            []any{map[string]any{"bus_id": "rs485_1"}, map[string]any{"bus_id": "rs485_2"}},
		"hardware_devices": []any{},
	}}
	d := noopDeps(nil)
	d.Config = m
	s.Buttons = []render.Button{{Rect: [4]int{646, 66, 138, 34}, Action: "open_device_add"}}
	s.OnTap(700, 80, d)
	waitFor(t, func() bool {
		s.mu.Lock()
		defer s.mu.Unlock()
		return len(s.Buses) == 2 && s.AddMessage == ""
	})
	s.mu.Lock()
	s.changeAddForm("template", -1)
	s.changeAddForm("bus", -1)
	s.AddForm.Slave = 1
	s.changeAddForm("slave", -1)
	if s.AddForm.TplIdx != 1 || s.AddForm.BusIdx != 1 || s.AddForm.Slave != 247 {
		t.Fatalf("地板模环绕失败: %+v", s.AddForm)
	}
	s.mu.Unlock()
}

func TestDeviceAddSavePublishesAndReturnsToNodes(t *testing.T) {
	s := NewState()
	s.SetTemplates([]templates.Template{simTemplate()})
	s.Page = "device_add"
	s.Buses = []string{"rs485_1"}
	s.AddForm = AddForm{Slave: 9}
	s.Buttons = []render.Button{{Rect: [4]int{616, 406, 168, 30}, Action: "devadd_save"}}
	m := &mockConfig{hasDraft: true, draft: map[string]any{
		"buses": []any{map[string]any{"bus_id": "rs485_1"}}, "hardware_devices": []any{},
	}}
	d := noopDeps(nil)
	d.Config = m
	s.OnTap(700, 420, d)
	waitFor(t, func() bool {
		s.mu.Lock()
		defer s.mu.Unlock()
		return !s.AddBusy && s.Page == "nodes"
	})
	m.mu.Lock()
	got := append([]string(nil), m.calls...)
	m.mu.Unlock()
	want := []string{"login", "draft", "devices", "draft", "compile", "activate", "status"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("编排顺序=%v want=%v", got, want)
	}
}

func TestDeviceAddDuplicateFailsBeforePost(t *testing.T) {
	s := NewState()
	s.SetTemplates([]templates.Template{simTemplate()})
	s.Page = "device_add"
	s.Buses = []string{"rs485_1"}
	s.AddForm = AddForm{Slave: 9}
	s.Buttons = []render.Button{{Rect: [4]int{616, 406, 168, 30}, Action: "devadd_save"}}
	m := &mockConfig{hasDraft: true, draft: map[string]any{
		"buses":            []any{map[string]any{"bus_id": "rs485_1"}},
		"hardware_devices": []any{map[string]any{"device_id": "pumpvfd_9"}},
	}}
	d := noopDeps(nil)
	d.Config = m
	s.OnTap(700, 420, d)
	waitFor(t, func() bool {
		s.mu.Lock()
		defer s.mu.Unlock()
		return !s.AddBusy && s.AddMessage != ""
	})
	s.mu.Lock()
	message, page := s.AddMessage, s.Page
	s.mu.Unlock()
	if message != "device_id 重复: pumpvfd_9" || page != "device_add" {
		t.Fatalf("message=%q page=%s", message, page)
	}
	m.mu.Lock()
	calls := append([]string(nil), m.calls...)
	m.mu.Unlock()
	if !reflect.DeepEqual(calls, []string{"login", "draft"}) {
		t.Fatalf("重复预检后不应 POST: %v", calls)
	}
}
