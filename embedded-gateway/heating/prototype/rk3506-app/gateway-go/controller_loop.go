//go:build linux

// 双端完整闭环 L3 的 Go 端：真串口上跑 ModbusSource 轮询 + Controller.Apply + 回读确认。
// 与 Python app.py 的真实 Controller/ModbusSource 在同一从站上对拍闭环结果。
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"
)

func runControllerLoop(args []string) {
	if len(args) < 1 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc controllerloop <scenario.json>")
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

	sp, err := OpenSerial(asStr(sc["dev"]), int(toF(sc["baud"])))
	if err != nil {
		fmt.Fprintf(os.Stderr, "打开串口失败: %v\n", err)
		os.Exit(2)
	}
	defer sp.Close()

	readTimeout := toF(getOr(sc, "read_timeout_s", float64(0.5)))
	m := NewModbusSource(arr{sc["device"]}, asObj(sc["reliability"]),
		func(addr, start, count int, _ float64, retries int) ([]uint16, string) {
			return sp.ReadHolding(addr, start, count, readTimeout, retries)
		},
		defaultClock, defaultClock)

	// 后台采集线程：周期 Poll → 更新共享快照（Controller 联锁/回读读它）
	var snapMu sync.Mutex
	snap := obj{"devices": arr{}}
	stop := make(chan struct{})
	var pollWg sync.WaitGroup
	pollWg.Add(1)
	go func() {
		defer pollWg.Done()
		for {
			view := SamplesView(m.Poll())
			snapMu.Lock()
			snap = view
			snapMu.Unlock()
			select {
			case <-stop:
				return
			case <-time.After(300 * time.Millisecond):
			}
		}
	}()
	time.Sleep(400 * time.Millisecond) // 等首帧快照

	writer := NewModbusSetpointWriter(asObj(sc["control_map"]),
		func(addr, reg, value int) bool { return sp.WriteRegister(addr, reg, value, readTimeout) })

	var recMu sync.Mutex
	statuses := arr{}
	ctrl := NewController(ControllerDeps{
		Snapshot: func() obj { snapMu.Lock(); defer snapMu.Unlock(); return snap },
		Write:    func(pid string, v float64) bool { return writer.WriteSetpoint(pid, v) },
		Clock:    defaultClock,
		Record: func(r ControlRecord) {
			recMu.Lock()
			statuses = append(statuses, r.Status)
			recMu.Unlock()
		},
		Policy: asObj(sc["policy"]),
	})

	cmd := asObj(sc["command"])
	ok, reason := ctrl.Apply(asStr(cmd["point_id"]), cmd["value"], asStr(cmd["command_id"]), asStr(cmd["origin"]))
	ctrl.WaitConfirmations()
	close(stop)
	pollWg.Wait()

	// 取最终反馈值
	pol := asObj(asObj(sc["policy"])[asStr(cmd["point_id"])])
	fbName := asStr(pol["feedback"])
	var feedback interface{}
	snapMu.Lock()
	for _, di := range asArr(snap["devices"]) {
		if p, ok := asObj(asObj(di)["points"])[fbName]; ok {
			feedback = asObj(p)["v"]
		}
	}
	snapMu.Unlock()

	recMu.Lock()
	finalStatuses := append(arr{}, statuses...)
	recMu.Unlock()
	b, _ := json.Marshal(obj{"apply_ok": ok, "apply_reason": reason,
		"statuses": finalStatuses, "feedback": feedback})
	fmt.Println(string(b))
}
