package app

import (
	"encoding/json"
	"testing"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

func noopDeps(cache *FrameCache) Deps {
	if cache == nil {
		cache = NewFrameCache()
	}
	return Deps{
		Blit:        func([]byte) {},
		PostCmd:     func(string, int) {},
		FetchConfig: func() ([]map[string]any, error) { return nil, nil },
		SaveConfig: func([]map[string]any) (bool, []map[string]any, bool) {
			return true, nil, false
		},
		Cache: cache,
		Dirty: func() {},
		Logf:  func(string, ...any) {},
	}
}

func TestFloorMod(t *testing.T) {
	cases := []struct{ a, n, want int }{
		{-1, 3, 2}, {0, 3, 0}, {3, 3, 0}, {-1, 247, 246}, {5, 3, 2},
	}
	for _, c := range cases {
		if got := floorMod(c.a, c.n); got != c.want {
			t.Errorf("floorMod(%d,%d)=%d != %d", c.a, c.n, got, c.want)
		}
	}
}

// slaveId=1 按 "−" 必须环绕到 247(Python 地板模语义,Go 原生 % 会得 -1)。
func TestSlaveIDWraparound(t *testing.T) {
	s := NewState()
	s.configChange("slaveId", -1)
	if got := s.DeviceForm["slaveId"]; got != 247 {
		t.Fatalf("slaveId=1 减 1 → %v != 247", got)
	}
	s.configChange("slaveId", 1)
	if got := s.DeviceForm["slaveId"]; got != 1 {
		t.Fatalf("247 加 1 → %v != 1", got)
	}
}

func TestLoadConfigSlotWraparound(t *testing.T) {
	s := NewState()
	s.ConfiguredNodes = []map[string]any{
		{"id": "a", "deviceType": "pump_vfd"},
		{"id": "b", "deviceType": "weird"},
	}
	s.loadConfigSlot(3) // 3 % (2+1) = 0 → 新建表单
	if s.ConfigSlot != 0 || s.DeviceForm["deviceType"] != "other" {
		t.Fatalf("slot 3 应环绕到 0,got slot=%d", s.ConfigSlot)
	}
	s.loadConfigSlot(-1) // -1 % 3 = 2(地板模)
	if s.ConfigSlot != 2 {
		t.Fatalf("slot -1 应环绕到 2,got %d", s.ConfigSlot)
	}
	// 未知 deviceType → label 回退 "设备"
	if s.DeviceForm["deviceTypeLabel"] != "设备" {
		t.Fatalf("未知类型 label %v", s.DeviceForm["deviceTypeLabel"])
	}
	// 编辑表单是拷贝,改动不能污染 ConfiguredNodes
	s.DeviceForm["slaveId"] = 99
	if _, ok := s.ConfiguredNodes[1]["slaveId"]; ok {
		t.Fatal("表单改动泄漏进节点列表")
	}
}

// 当前值不在候选表 → 从 index 0 起步(Python except ValueError: index=0)。
func TestCycleValueUnknownCurrent(t *testing.T) {
	s := NewState()
	s.DeviceForm["baudRate"] = json.Number("31250") // 不在 BAUDS 表中
	s.configChange("baudRate", 1)
	if got := s.DeviceForm["baudRate"]; got != 2400 { // values[(0+1)%8]
		t.Fatalf("未知当前值 +1 → %v != 2400", got)
	}
	// json.Number 与原生 int 的等值比较(9600 来自 JSON)
	s.DeviceForm["baudRate"] = json.Number("9600")
	s.configChange("baudRate", 1)
	if got := s.DeviceForm["baudRate"]; got != 19200 {
		t.Fatalf("9600 +1 → %v != 19200", got)
	}
}

func TestConfigSaveAddPayload(t *testing.T) {
	s := NewState()
	s.DeviceForm = map[string]any{
		"deviceType": "pump_vfd", "deviceTypeLabel": "水泵",
		"serialPort": "/dev/ttyS2", "baudRate": 19200, "dataBits": 8,
		"stopBits": 1, "parity": "even", "slaveId": 7, "pollInterval": 500,
	}
	var captured []map[string]any
	d := noopDeps(nil)
	d.SaveConfig = func(nodes []map[string]any) (bool, []map[string]any, bool) {
		captured = nodes
		return true, nil, false
	}
	s.configSave(d)
	if len(captured) != 1 {
		t.Fatalf("应保存 1 个节点,got %d", len(captured))
	}
	n := captured[0]
	want := map[string]any{
		"type": "Southbound", "driver": "Modbus RTU", "transport": "RTU",
		"endpoint": "/dev/ttyS2", "byteOrder": "ABCD",
		"name": "水泵 7", "id": "local-ttyS2-7",
	}
	for k, v := range want {
		if n[k] != v {
			t.Errorf("%s = %v != %v", k, n[k], v)
		}
	}
	if _, ok := n["deviceTypeLabel"]; ok {
		t.Error("deviceTypeLabel 必须从 payload 剔除")
	}
	if s.ConfigMessage != "设备已接入" {
		t.Errorf("新增消息 %q", s.ConfigMessage)
	}
	if s.ConfigSlot != 1 {
		t.Errorf("保存后 slot 应定位到 1,got %d", s.ConfigSlot)
	}
}

func TestConfigSaveEditKeepsID(t *testing.T) {
	s := NewState()
	s.ConfiguredNodes = []map[string]any{
		{"id": "local-ttyS1-5", "deviceType": "pump_vfd", "serialPort": "/dev/ttyS1", "slaveId": 5},
		{"id": "keep-me", "deviceType": "heat_meter", "serialPort": "/dev/ttyS3", "slaveId": 9},
	}
	s.loadConfigSlot(2)
	s.DeviceForm["slaveId"] = 10
	var captured []map[string]any
	d := noopDeps(nil)
	d.SaveConfig = func(nodes []map[string]any) (bool, []map[string]any, bool) {
		captured = nodes
		return true, nil, false
	}
	s.configSave(d)
	if captured[1]["id"] != "keep-me" {
		t.Fatalf("编辑必须保留原 id,got %v", captured[1]["id"])
	}
	if captured[1]["name"] != "热量表 10" {
		t.Fatalf("name %v", captured[1]["name"])
	}
	if s.ConfigMessage != "配置正常" {
		t.Errorf("编辑消息 %q", s.ConfigMessage)
	}
}

func TestConfigSaveFailure(t *testing.T) {
	s := NewState()
	d := noopDeps(nil)
	d.SaveConfig = func([]map[string]any) (bool, []map[string]any, bool) {
		return false, nil, false
	}
	s.configSave(d)
	if s.ConfigMessage != "配置异常" {
		t.Fatalf("失败消息 %q", s.ConfigMessage)
	}
	if len(s.ConfiguredNodes) != 0 {
		t.Fatal("失败不应改动 ConfiguredNodes")
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
func TestOnTapOpenDeviceConfig(t *testing.T) {
	s := NewState()
	s.Buttons = []render.Button{{Rect: [4]int{646, 66, 138, 34}, Action: "open_device_config"}}
	d := noopDeps(nil)
	d.FetchConfig = func() ([]map[string]any, error) {
		return []map[string]any{{"id": "a", "deviceType": "pump_vfd", "slaveId": 5}}, nil
	}
	s.OnTap(650, 70, d)
	if s.Page != "device_config" || s.ConfigSlot != 1 {
		t.Fatalf("page=%s slot=%d", s.Page, s.ConfigSlot)
	}
	if s.DeviceForm["deviceTypeLabel"] != "水泵" {
		t.Fatalf("编辑表单 label %v", s.DeviceForm["deviceTypeLabel"])
	}
}
