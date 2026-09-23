package main

import "testing"

func TestSafetyCheck(t *testing.T) {
	if ok, _ := safetyCheck("set_point", map[string]interface{}{"sec_supply_temp_target": 50.0}); !ok {
		t.Fatal("50℃ 在 [20,75] 应允许")
	}
	if ok, _ := safetyCheck("set_point", map[string]interface{}{"sec_supply_temp_target": 90.0}); ok {
		t.Fatal("90℃ 越限应拒绝")
	}
	if ok, _ := safetyCheck("set_point", map[string]interface{}{}); !ok {
		t.Fatal("无目标值应放行")
	}
}

func TestBuildTelemetry(t *testing.T) {
	g := &Gateway{deviceID: "x", base: "station/x"}
	f1 := g.buildTelemetry(false, 0)
	f2 := g.buildTelemetry(false, 0)
	if f1["seq"].(int64) != 1 || f2["seq"].(int64) != 2 {
		t.Fatalf("seq 应单调递增, 得到 %v %v", f1["seq"], f2["seq"])
	}
	if _, ok := f1["replay"]; ok {
		t.Fatal("非补传帧不应带 replay")
	}
	fr := g.buildTelemetry(true, 12345)
	if fr["replay"] != true || fr["ts"].(int64) != 12345 {
		t.Fatal("补传帧应带 replay:true 且保留原始 ts")
	}
	pts := f1["points"].(map[string]interface{})
	if _, ok := pts["pri_supply_temp"]; !ok {
		t.Fatal("点表应含 pri_supply_temp")
	}
}

func TestBufferDropOldest(t *testing.T) {
	g := &Gateway{cfg: Config{BufferMax: 3}}
	for i := 0; i < 5; i++ {
		g.buf = append(g.buf, frame{"seq": int64(i)})
		if len(g.buf) > g.cfg.BufferMax {
			g.buf = g.buf[len(g.buf)-g.cfg.BufferMax:]
		}
	}
	if len(g.buf) != 3 {
		t.Fatalf("缓存应被裁到 3, 实际 %d", len(g.buf))
	}
	if g.buf[0]["seq"].(int64) != 2 {
		t.Fatalf("应丢最旧, 队首应为 seq=2, 实际 %v", g.buf[0]["seq"])
	}
}
