// runtimecase: 脚本化驱动 Runtime（对拍用）。每个 op 可先设 mono/wall 钟。
package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func runRuntimeCase(args []string) {
	if len(args) < 1 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc runtimecase <scenario.json>")
		os.Exit(2)
	}
	raw, err := os.ReadFile(args[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "读取场景失败: %v\n", err)
		os.Exit(2)
	}
	var sc obj
	if err := json.Unmarshal(raw, &sc); err != nil {
		fmt.Fprintf(os.Stderr, "解析场景失败: %v\n", err)
		os.Exit(2)
	}
	var curMono, curWall float64
	rt := NewRuntime(asObj(sc["cfg"]),
		func() float64 { return curMono }, func() float64 { return curWall })
	results := arr{}
	for _, oi := range asArr(sc["ops"]) {
		o := asObj(oi)
		if v, ok := o["mono"]; ok {
			curMono = toF(v)
		}
		if v, ok := o["wall"]; ok {
			curWall = toF(v)
		}
		switch asStr(o["op"]) {
		case "mark_alive":
			rt.MarkAlive()
		case "update":
			rt.Update(asObj(o["snap"]))
		case "add_event":
			rt.AddEvent(asObj(o["ev"]))
		case "record_command":
			rt.RecordCommand(asObj(o["rec"]))
		case "get":
			results = append(results, obj{"op": "get", "out": rt.Get()})
		case "collector_age_ms":
			results = append(results, obj{"op": "collector_age_ms", "out": rt.CollectorAgeMs()})
		case "telemetry":
			results = append(results, obj{"op": "telemetry", "out": rt.Telemetry()})
		case "view":
			results = append(results, obj{"op": "view", "out": rt.View()})
		}
	}
	b, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(b))
}
