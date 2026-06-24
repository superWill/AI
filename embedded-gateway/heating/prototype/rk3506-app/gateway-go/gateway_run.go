// 网关 daemon（Go 移植自 app.py 的三个 loop + main 装配）。
// sim/modbus 源 + Runtime + Controller + 可选 MQTT + collector/watchdog/uploader + HTTP/HMI。
// modbus 源走串口(Linux,见 modbus_daemon_linux.go);可替 `python3 app.py`。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"
)

type pollSource interface{ Poll() obj }

func collectorLoop(src pollSource, rt *Runtime, interval time.Duration, stop <-chan struct{}) {
	for {
		rt.Update(src.Poll())
		rt.MarkAlive()
		select {
		case <-stop:
			return
		case <-time.After(interval):
		}
	}
}

func watchdogLoop(rt *Runtime, cfg obj, stop <-chan struct{}) {
	rel := asObj(cfg["reliability"])
	poll := toF(getOr(cfg, "poll_interval_s", float64(2)))
	staleLimit := toF(getOr(rel, "stale_limit_s", maxF(6, poll*3)))
	wd := asObj(cfg["watchdog"])
	wdDev := asStr(get(wd, "device"))
	interval := toF(getOr(wd, "interval_s", float64(5)))
	var fd *os.File
	if wdDev != "" {
		if _, err := os.Stat(wdDev); err == nil {
			fd, _ = os.OpenFile(wdDev, os.O_WRONLY, 0)
		}
	}
	warned := false
	for {
		age := float64(rt.CollectorAgeMs()) / 1000.0
		if age <= staleLimit {
			if warned {
				rt.AddEvent(obj{"kind": "watchdog", "action": "recovered",
					"detail": fmt.Sprintf("采集恢复 age=%.1fs", age)})
				warned = false
			}
			if fd != nil {
				fd.Write([]byte("w"))
			}
		} else if !warned {
			rt.AddEvent(obj{"kind": "watchdog", "action": "critical",
				"detail": fmt.Sprintf("采集停滞 %.1fs,看门狗停喂", age)})
			warned = true
		}
		select {
		case <-stop:
			if fd != nil {
				fd.Close()
			}
			return
		case <-time.After(time.Duration(interval * float64(time.Second))):
		}
	}
}

func uploaderLoop(rt *Runtime, pub *MqttPub, base string, tTele, tHb time.Duration, stop <-chan struct{}) {
	var nextT, nextH time.Time
	for {
		now := time.Now()
		if !now.Before(nextT) {
			pub.PublishTelemetry(base+"/telemetry", rt.Telemetry())
			nextT = now.Add(tTele)
		}
		if !now.Before(nextH) {
			pub.Publish(base+"/heartbeat", obj{"device_id": rt.cfg["device_id"],
				"online": true, "ts": time.Now().UnixMilli()})
			nextH = now.Add(tHb)
		}
		select {
		case <-stop:
			return
		case <-time.After(time.Second):
		}
	}
}

// cmdValid:命令带 valid_until(ms epoch)且已过期则拒绝。无该字段=不强制(向后兼容)。
// 失联安全:平台下发命令时带短有效期,网关失联/延迟导致命令过期即不执行,避免迟到指令误动作。
func cmdValid(body obj) (bool, string) {
	vu, has := body["valid_until"]
	if !has || vu == nil {
		return true, ""
	}
	f, ok := pythonFloat(vu)
	if !ok {
		return false, "valid_until 非法"
	}
	now := float64(time.Now().UnixMilli())
	if now > f {
		return false, fmt.Sprintf("命令已过期(valid_until=%d < now=%d)", int64(f), int64(now))
	}
	return true, ""
}

func runGateway(args []string) {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	cfgPath := fs.String("config", "app_config.json", "运行配置")
	srcKind := fs.String("source", "", "采集源 sim|modbus(空则用配置)")
	seconds := fs.Int("seconds", 0, ">0 则跑 N 秒后 dump view 退出(冒烟用)")
	portFlag := fs.Int("port", 0, "HTTP 端口(>0 覆盖配置 http_port;边界拓扑核心走 8091)")
	fs.Parse(args)

	raw, err := os.ReadFile(*cfgPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "读取配置失败: %v\n", err)
		os.Exit(2)
	}
	var cfg obj
	if err := json.Unmarshal(raw, &cfg); err != nil {
		fmt.Fprintf(os.Stderr, "解析配置失败: %v\n", err)
		os.Exit(2)
	}

	kind := *srcKind
	if kind == "" {
		kind = asStr(getOr(cfg, "source", "sim"))
	}
	var src pollSource
	var writeFn func(string, float64) bool
	switch kind {
	case "sim":
		s := NewSimSource(asArr(cfg["devices"]), nil)
		fmt.Println("[源] sim 内置仿真")
		src, writeFn = s, s.WriteSetpoint
	case "modbus":
		ms, w, err := newModbusRuntime(cfg)
		if err != nil {
			fmt.Fprintf(os.Stderr, "modbus 源装配失败: %v\n", err)
			os.Exit(2)
		}
		src, writeFn = ms, w
	default:
		fmt.Fprintf(os.Stderr, "未知源: %s\n", kind)
		os.Exit(2)
	}

	rt := NewRuntime(cfg, nil, nil)
	base := "station/" + asStr(getOr(cfg, "device_id", "rk3506-gw-01"))

	var pub *MqttPub
	if mcfg := asObj(cfg["mqtt"]); mcfg != nil {
		pub = NewMqttPub(asStr(mcfg["host"]), int(toF(getOr(mcfg, "port", float64(1883)))),
			asStr(getOr(cfg, "device_id", "rk3506-gw-01")), asStr(mcfg["username"]), asStr(mcfg["password"]),
			int(toF(getOr(mcfg, "keepalive", float64(30)))), int(toF(getOr(mcfg, "buffer_max", float64(5000)))))
	}

	ctrl := NewController(ControllerDeps{
		Snapshot: func() obj { return SamplesView(rt.Get()) },
		Write:    writeFn,
		Clock:    defaultClock,
		Record: func(r ControlRecord) {
			rec := obj{"command_id": r.CommandID, "point_id": r.PointID, "value": r.Value,
				"status": r.Status, "reason": r.Reason, "origin": r.Origin, "ts": r.TS}
			rt.RecordCommand(rec)
			reasonPart := ""
			if r.Reason != "" {
				reasonPart = " " + r.Reason
			}
			rt.AddEvent(obj{"kind": "command", "action": r.Status,
				"detail": fmt.Sprintf("%s ← %v (%s%s)", r.PointID, r.Value, r.Status, reasonPart)})
			if pub != nil {
				pub.Publish(base+"/command_reply", rec)
			}
		},
		Alarm: func(a ControlAlarm) {
			rt.AddEvent(obj{"kind": "alarm", "action": a.Action, "detail": a.Detail})
		},
		Policy: asObj(cfg["safety_policy"]),
	})

	if pub != nil {
		pub.Subscribe(base+"/property/set", func(payload []byte) {
			var cmd obj
			if json.Unmarshal(payload, &cmd) != nil {
				return
			}
			if ok, reason := cmdValid(cmd); !ok { // valid_until 过期即拒,不下发
				rt.AddEvent(obj{"kind": "command", "action": "rejected_expired", "detail": reason})
				return
			}
			pl := asObj(cmd["payload"])
			if pl == nil {
				pl = cmd
			}
			for pid, val := range pl {
				ctrl.Apply(pid, val, asStr(cmd["command_id"]), "platform")
			}
		})
	}

	stop := make(chan struct{})
	go collectorLoop(src, rt, time.Duration(toF(getOr(cfg, "poll_interval_s", float64(2)))*float64(time.Second)), stop)
	go watchdogLoop(rt, cfg, stop)
	if pub != nil {
		go uploaderLoop(rt, pub, base,
			time.Duration(toF(getOr(cfg, "telemetry_interval_s", float64(10)))*float64(time.Second)),
			time.Duration(toF(getOr(cfg, "heartbeat_interval_s", float64(30)))*float64(time.Second)), stop)
	}
	fmt.Println("[daemon] collector/watchdog" + map[bool]string{true: "/uploader", false: ""}[pub != nil] + " 已启动")

	htmlDir := asStr(getOr(cfg, "html_dir", "html"))
	port := int(toF(getOr(cfg, "http_port", float64(8092))))
	if *portFlag > 0 {
		port = *portFlag // 显式覆盖(边界拓扑:gatewayc 核心 8091)
	}
	controlToken := asStr(getOr(cfg, "control_token", ""))
	if env := os.Getenv("GATEWAYC_CONTROL_TOKEN"); env != "" {
		controlToken = env // env 覆盖(supervisor 注入,不落配置文件)
	}
	srv := startHTTP(rt, ctrl, htmlDir, port, controlToken)

	if *seconds > 0 { // 冒烟:跑 N 秒 dump view 退出
		time.Sleep(time.Duration(*seconds) * time.Second)
		close(stop)
		srv.Close()
		b, _ := json.MarshalIndent(rt.View(), "", "  ")
		fmt.Println(string(b))
		return
	}
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	close(stop)
	srv.Close()
	if pub != nil {
		pub.Disconnect()
	}
	fmt.Println("\n退出。")
}
