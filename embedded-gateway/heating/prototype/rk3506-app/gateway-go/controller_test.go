package main

import (
	"sync"
	"testing"
)

func TestSafetyCheckMatchesPythonBranches(t *testing.T) {
	tests := []struct {
		name   string
		pid    string
		value  interface{}
		policy obj
		ok     bool
		reason string
	}{
		{"fallback accepts", "pump_freq_sp", 50, nil, true, ""},
		{"fallback unknown", "unknown", 1, nil, false, "未知或不可远程设定的点位 unknown"},
		{"strict unknown", "valve_open_sp", 50, obj{"other": obj{"lo": 0, "hi": 1}}, false, "未知或不可远程设定的点位 valve_open_sp"},
		{"missing limit", "x", 1, obj{"x": obj{"lo": 0}}, false, "x 缺少安全限值"},
		{"invalid value", "x", "bad", obj{"x": obj{"lo": 0, "hi": 10}}, false, "x 值非法 'bad'"},
		{"below range", "x", -1, obj{"x": obj{"lo": 0, "hi": 10}}, false, "x=-1.0 超出安全限值 [0,10]"},
		{"above range", "x", 11, obj{"x": obj{"lo": 0.0, "hi": 10.0}}, false, "x=11.0 超出安全限值 [0.0,10.0]"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			ok, reason, _ := SafetyCheck(tc.pid, tc.value, tc.policy)
			if ok != tc.ok || reason != tc.reason {
				t.Fatalf("SafetyCheck()=(%v,%q), want (%v,%q)", ok, reason, tc.ok, tc.reason)
			}
		})
	}
}

func TestControllerAcceptsSafeCommandAndWrites(t *testing.T) {
	var writes []ControlWrite
	var records []ControlRecord
	c := NewController(ControllerDeps{
		Snapshot: func() obj { return obj{"devices": arr{}} },
		Write: func(pointID string, value float64) bool {
			writes = append(writes, ControlWrite{PointID: pointID, Value: value})
			return true
		},
		Clock:  func() float64 { return 100 },
		Record: func(rec ControlRecord) { records = append(records, rec) },
	})

	ok, reason := c.Apply("valve_open_sp", 80, "cmd-1", "hmi")

	if !ok || reason != "" {
		t.Fatalf("Apply()=(%v,%q), want (true, empty)", ok, reason)
	}
	if len(writes) != 1 || writes[0] != (ControlWrite{PointID: "valve_open_sp", Value: 80}) {
		t.Fatalf("writes=%v", writes)
	}
	if len(records) != 1 || records[0].Status != "accepted" {
		t.Fatalf("records=%v", records)
	}
}

func TestControllerAppliesRateLimitBeforeWrite(t *testing.T) {
	now := 100.0
	writes := 0
	var records []ControlRecord
	c := NewController(ControllerDeps{
		Snapshot: func() obj { return obj{"devices": arr{}} },
		Write: func(string, float64) bool {
			writes++
			return true
		},
		Clock:  func() float64 { return now },
		Record: func(rec ControlRecord) { records = append(records, rec) },
		Policy: obj{"valve_open_sp": obj{"lo": 0, "hi": 100, "rate_per_s": 1}},
	})

	if ok, _ := c.Apply("valve_open_sp", 80, "first", "platform"); !ok {
		t.Fatal("first command should pass")
	}
	now = 101
	ok, reason := c.Apply("valve_open_sp", 82, "second", "platform")

	if ok || reason != "valve_open_sp 变化速率超限(>1/s)" {
		t.Fatalf("Apply()=(%v,%q)", ok, reason)
	}
	if writes != 1 {
		t.Fatalf("writes=%d, rejected command must not write", writes)
	}
	if records[len(records)-1].Status != "blocked_by_safety" {
		t.Fatalf("last record=%+v", records[len(records)-1])
	}
}

func TestControllerRejectsUnsafeInterlockBeforeWrite(t *testing.T) {
	writes := 0
	var records []ControlRecord
	c := NewController(ControllerDeps{
		Snapshot: func() obj {
			return obj{"devices": arr{obj{"points": obj{
				"emergency_stop": obj{"v": 1, "q": "good"},
			}}}}
		},
		Write:  func(string, float64) bool { writes++; return true },
		Clock:  func() float64 { return 100 },
		Record: func(rec ControlRecord) { records = append(records, rec) },
		Policy: obj{"pump_freq_sp": obj{
			"lo": 0, "hi": 50,
			"interlocks": arr{obj{"point": "emergency_stop", "equals": 0}},
		}},
	})

	ok, reason := c.Apply("pump_freq_sp", 30, "cmd-2", "platform")

	if ok || reason != "联锁未满足:emergency_stop=1.0 需=0" {
		t.Fatalf("Apply()=(%v,%q)", ok, reason)
	}
	if writes != 0 {
		t.Fatalf("writes=%d", writes)
	}
	if len(records) != 1 || records[0].Status != "blocked_by_interlock" {
		t.Fatalf("records=%v", records)
	}
}

func TestControllerConfirmsFeedbackAfterAccepted(t *testing.T) {
	now := 100.0
	var mu sync.Mutex
	var records []ControlRecord
	c := NewController(ControllerDeps{
		Snapshot: func() obj {
			value := 40.0
			if now >= 101 {
				value = 50
			}
			return obj{"devices": arr{obj{"points": obj{
				"sec_supply_temp": obj{"v": value, "q": "good"},
			}}}}
		},
		Write: func(string, float64) bool { return true },
		Clock: func() float64 { return now },
		Sleep: func(seconds float64) { now += seconds },
		Record: func(rec ControlRecord) {
			mu.Lock()
			records = append(records, rec)
			mu.Unlock()
		},
		Policy: obj{"sec_supply_temp_sp": obj{
			"lo": 20, "hi": 75, "feedback": "sec_supply_temp",
			"confirm_timeout_s": 5, "confirm_tolerance": 1,
		}},
	})

	if ok, _ := c.Apply("sec_supply_temp_sp", 50, "cmd-3", "platform"); !ok {
		t.Fatal("command should be accepted before confirmation")
	}
	c.WaitConfirmations()

	mu.Lock()
	defer mu.Unlock()
	if len(records) != 2 || records[0].Status != "accepted" || records[1].Status != "confirmed" {
		t.Fatalf("records=%v", records)
	}
	if records[1].Reason != "反馈 sec_supply_temp=50.0 已收敛" {
		t.Fatalf("confirm reason=%q", records[1].Reason)
	}
}

func TestControllerReportsFeedbackTimeoutAndAlarm(t *testing.T) {
	now := 100.0
	var records []ControlRecord
	var alarms []ControlAlarm
	c := NewController(ControllerDeps{
		Snapshot: func() obj {
			return obj{"devices": arr{obj{"points": obj{
				"sec_supply_temp": obj{"v": 40.0, "q": "good"},
			}}}}
		},
		Write:  func(string, float64) bool { return true },
		Clock:  func() float64 { return now },
		Sleep:  func(seconds float64) { now += seconds },
		Record: func(rec ControlRecord) { records = append(records, rec) },
		Alarm:  func(alarm ControlAlarm) { alarms = append(alarms, alarm) },
		Policy: obj{"sec_supply_temp_sp": obj{
			"lo": 20, "hi": 75, "feedback": "sec_supply_temp",
			"confirm_timeout_s": 1, "confirm_tolerance": 0.1,
		}},
	})

	c.Apply("sec_supply_temp_sp", 50, "cmd-4", "platform")
	c.WaitConfirmations()

	if len(records) != 2 || records[1].Status != "feedback_timeout" {
		t.Fatalf("records=%v", records)
	}
	wantReason := "反馈 sec_supply_temp=40.0 1s 内未收敛到 50.0±0.1"
	if records[1].Reason != wantReason {
		t.Fatalf("reason=%q, want %q", records[1].Reason, wantReason)
	}
	if len(alarms) != 1 || alarms[0].Detail != "sec_supply_temp_sp←50 回读确认失败(feedback=sec_supply_temp)" {
		t.Fatalf("alarms=%v", alarms)
	}
}

func TestControllerInterlockFailureBranches(t *testing.T) {
	tests := []struct {
		name      string
		point     obj
		interlock obj
		reason    string
	}{
		{"missing", nil, obj{"point": "guard", "equals": 0}, "联锁点 guard 不在快照中"},
		{"bad quality", obj{"v": 0, "q": "bad"}, obj{"point": "guard", "equals": 0}, "联锁点 guard 质量码非 GOOD(bad)"},
		{"invalid value", obj{"v": "bad", "q": "good"}, obj{"point": "guard", "equals": 0}, "联锁点 guard 值非法 'bad'"},
		{"above max", obj{"v": 11, "q": "good"}, obj{"point": "guard", "max": 10}, "联锁未满足:guard=11.0 需≤10"},
		{"below min", obj{"v": -1, "q": "good"}, obj{"point": "guard", "min": 0}, "联锁未满足:guard=-1.0 需≥0"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			points := obj{}
			if tc.point != nil {
				points["guard"] = tc.point
			}
			c := NewController(ControllerDeps{
				Snapshot: func() obj { return obj{"devices": arr{obj{"points": points}}} },
				Write:    func(string, float64) bool { t.Fatal("unsafe command wrote"); return false },
				Clock:    func() float64 { return 100 },
				Policy: obj{"pump_freq_sp": obj{
					"lo": 0, "hi": 50, "interlocks": arr{tc.interlock},
				}},
			})
			ok, reason := c.Apply("pump_freq_sp", 30, "", "hmi")
			if ok || reason != tc.reason {
				t.Fatalf("Apply()=(%v,%q), want false,%q", ok, reason, tc.reason)
			}
		})
	}
}

func TestControllerRecordsWriteFailure(t *testing.T) {
	var records []ControlRecord
	c := NewController(ControllerDeps{
		Write:  func(string, float64) bool { return false },
		Clock:  func() float64 { return 100 },
		Record: func(rec ControlRecord) { records = append(records, rec) },
	})
	ok, reason := c.Apply("pump_freq_sp", 30, "cmd-5", "hmi")
	if ok || reason != "" {
		t.Fatalf("Apply()=(%v,%q)", ok, reason)
	}
	if len(records) != 1 || records[0].Status != "write_failed" || records[0].Reason != "源写入失败" {
		t.Fatalf("records=%v", records)
	}
}

func TestControllerAndSimSourceCloseTheFeedbackLoop(t *testing.T) {
	now := 100.0
	devices := arr{obj{
		"addr": 1, "name": "二次供温", "type": "仿真",
		"points": arr{obj{"id": "sec_supply_temp", "unit": "degC"}},
	}}
	source := NewSimSource(devices, func() float64 { return now })
	snapshot := obj{"devices": arr{}}
	var records []ControlRecord
	poll := func() {
		samples := source.Poll()
		snapshot = SamplesView(samples)
	}
	poll()
	controller := NewController(ControllerDeps{
		Snapshot: func() obj { return snapshot },
		Write:    source.WriteSetpoint,
		Clock:    func() float64 { return now },
		Sleep: func(seconds float64) {
			now += seconds
			poll()
		},
		Record: func(rec ControlRecord) { records = append(records, rec) },
		Policy: obj{"sec_supply_temp_sp": obj{
			"lo": 20, "hi": 75, "feedback": "sec_supply_temp",
			"confirm_timeout_s": 8, "confirm_tolerance": 1,
		}},
	})

	ok, reason := controller.Apply("sec_supply_temp_sp", 60, "sim-1", "hmi")
	controller.WaitConfirmations()

	if !ok || reason != "" {
		t.Fatalf("Apply()=(%v,%q)", ok, reason)
	}
	if len(records) != 2 || records[0].Status != "accepted" || records[1].Status != "confirmed" {
		t.Fatalf("records=%v", records)
	}
	point := asObj(asObj(asArr(snapshot["devices"])[0])["points"])["sec_supply_temp"]
	if value := toF(asObj(point)["v"]); value < 59 || value > 61 {
		t.Fatalf("feedback=%v, want target±1", value)
	}
}
