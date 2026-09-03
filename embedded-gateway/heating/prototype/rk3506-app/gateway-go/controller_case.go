package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
)

// runControllerCase 用脚本化依赖驱动真实 Go Controller，输出可与 app.py 对拍的观察结果。
func runControllerCase(args []string) {
	if len(args) != 1 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc controllercase <scenario.json>")
		os.Exit(2)
	}
	raw, err := os.ReadFile(args[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "读取场景失败: %v\n", err)
		os.Exit(2)
	}
	var scenario obj
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if err := decoder.Decode(&scenario); err != nil {
		fmt.Fprintf(os.Stderr, "解析场景失败: %v\n", err)
		os.Exit(2)
	}

	now := float64(0)
	currentSnapshot := obj{"devices": arr{}}
	feedbackSnapshots := arr{}
	feedbackIndex := 0
	writeOK := true
	records := []ControlRecord{}
	alarms := []ControlAlarm{}
	writes := []ControlWrite{}
	results := arr{}

	controller := NewController(ControllerDeps{
		Snapshot: func() obj { return currentSnapshot },
		Write: func(pointID string, value float64) bool {
			writes = append(writes, ControlWrite{PointID: pointID, Value: value})
			return writeOK
		},
		Clock: func() float64 { return now },
		Sleep: func(seconds float64) {
			now += seconds
			if feedbackIndex < len(feedbackSnapshots) {
				currentSnapshot = asObj(feedbackSnapshots[feedbackIndex])
				feedbackIndex++
			}
		},
		Record: func(rec ControlRecord) { records = append(records, rec) },
		Alarm:  func(alarm ControlAlarm) { alarms = append(alarms, alarm) },
		Policy: asObj(scenario["policy"]),
	})

	for _, rawCommand := range asArr(scenario["commands"]) {
		command := asObj(rawCommand)
		now = toF(command["at"])
		if snapshot := asObj(command["snapshot"]); snapshot != nil {
			currentSnapshot = snapshot
		}
		feedbackSnapshots = asArr(command["feedback_snapshots"])
		feedbackIndex = 0
		writeOK = true
		if value, exists := command["write_ok"]; exists {
			writeOK, _ = value.(bool)
		}
		ok, reason := controller.Apply(
			asStr(command["point_id"]), command["value"],
			asStr(command["command_id"]), asStr(command["origin"]),
		)
		controller.WaitConfirmations()
		results = append(results, obj{"ok": ok, "reason": reason})
	}

	out := obj{"results": results, "writes": writes, "records": records, "alarms": alarms}
	encoded, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(encoded))
}

// runSimControlCase 把真实 Go Controller 接到真实 Go SimSource，验证完整仿真闭环。
func runSimControlCase(args []string) {
	if len(args) != 1 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc simcontrolcase <scenario.json>")
		os.Exit(2)
	}
	raw, err := os.ReadFile(args[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "读取场景失败: %v\n", err)
		os.Exit(2)
	}
	var scenario obj
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if err := decoder.Decode(&scenario); err != nil {
		fmt.Fprintf(os.Stderr, "解析场景失败: %v\n", err)
		os.Exit(2)
	}

	now := toF(scenario["at"])
	source := NewSimSource(asArr(scenario["devices"]), func() float64 { return now })
	snapshot := SamplesView(source.Poll())
	records := []ControlRecord{}
	alarms := []ControlAlarm{}
	controller := NewController(ControllerDeps{
		Snapshot: func() obj { return snapshot },
		Write:    source.WriteSetpoint,
		Clock:    func() float64 { return now },
		Sleep: func(seconds float64) {
			now += seconds
			snapshot = SamplesView(source.Poll())
		},
		Record: func(rec ControlRecord) { records = append(records, rec) },
		Alarm:  func(alarm ControlAlarm) { alarms = append(alarms, alarm) },
		Policy: asObj(scenario["policy"]),
	})
	command := asObj(scenario["command"])
	ok, reason := controller.Apply(
		asStr(command["point_id"]), command["value"],
		asStr(command["command_id"]), asStr(command["origin"]),
	)
	controller.WaitConfirmations()
	out := obj{
		"result": obj{"ok": ok, "reason": reason}, "records": records,
		"alarms": alarms, "snapshot": snapshot,
	}
	encoded, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(encoded))
}
