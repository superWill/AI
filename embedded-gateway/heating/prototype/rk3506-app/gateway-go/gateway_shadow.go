// 轨 B 阶段一:只读影子并行(`gatewayc shadow`)。
//
// 硬不变量(本文件强制):
//   - 影子模式**不构造任何数据源/串口写句柄**——物理上没有到总线的路径;
//   - Controller 注入 shadowExecutor:只记录"打算写什么",从不触碰总线;
//   - 不订阅/写入任何生产执行通路。
//
// 采样来源二选一(或都给):
//   - MQTT:订阅 station/<id>/_shadow/samples(有 broker 时);
//   - unix datagram:--samples-sock PATH(板上无 broker 的备用通道,app.py --shadow-sock 对接)。
// 命令对账需命令流:仅在有 MQTT 时订阅 property/set(无 broker 则 app.py 本就无云命令,
// 只做 view/资源对比)。输出:有 MQTT 发 station/<id>/_shadow/go;决策与周期摘要总打 stdout
// (无 broker 也能 tail 观测)。板上不落盘(省 NAND)。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

// shadowExecutor 是被封死的"执行器":只累加意图计数,**不持有任何总线/串口句柄**,
// 结构上不存在到总线的路径(影子模式也不构造任何数据源)。
// 返回 true = 模拟"写成功",目的是让决策状态路径与生产一致、可对比;
// 真实收敛由共享采样反映(生产真写了→真设备响应→采样里能看到),影子据此走 confirm。
type shadowExecutor struct {
	mu      sync.Mutex
	intents int64
}

func (s *shadowExecutor) Write(pointID string, value float64) bool {
	s.mu.Lock()
	s.intents++
	s.mu.Unlock()
	return true // 模拟写成功;本结构无任何总线句柄,物理上写不出去
}

// readRSSKb 读 /proc/self/status 的 VmRSS(KB);非 Linux 或不可读返回 0。
func readRSSKb() int64 {
	b, err := os.ReadFile("/proc/self/status")
	if err != nil {
		return 0
	}
	for _, line := range splitLines(string(b)) {
		if len(line) > 6 && line[:6] == "VmRSS:" {
			var kb int64
			fmt.Sscanf(line[6:], "%d", &kb)
			return kb
		}
	}
	return 0
}

func splitLines(s string) []string {
	var out []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			out = append(out, s[start:i])
			start = i + 1
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}

// shadowDigest 把 view 压成 {pid:{v,q}} 的紧凑映射 + 离线 addr 列表,供比对器逐点对账。
func shadowDigest(view obj) (points obj, offline arr) {
	points = obj{}
	offline = arr{}
	for _, di := range asArr(view["devices"]) {
		d := asObj(di)
		if b, _ := d["offline"].(bool); b {
			offline = append(offline, d["addr"])
		}
		for pid, pi := range asObj(d["points"]) {
			p := asObj(pi)
			points[pid] = obj{"v": p["v"], "q": p["q"]}
		}
	}
	return
}

func stdoutLine(o obj) {
	b, _ := json.Marshal(o)
	fmt.Println(string(b))
}

func runShadow(args []string) {
	fs := flag.NewFlagSet("shadow", flag.ExitOnError)
	cfgPath := fs.String("config", "app_config.json", "运行配置(与生产同一份,只用 device_id/mqtt/safety_policy)")
	samplesSock := fs.String("samples-sock", "", "unix datagram 路径:从这里读原始采样(板上无 broker 的备用通道)")
	seconds := fs.Int("seconds", 0, ">0 则跑 N 秒退出(冒烟用)")
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

	mcfg := asObj(cfg["mqtt"])
	if mcfg == nil && *samplesSock == "" {
		fmt.Fprintln(os.Stderr, "影子需要采样来源:mqtt 配置(_shadow/samples)或 --samples-sock 之一")
		os.Exit(2)
	}
	deviceID := asStr(getOr(cfg, "device_id", "rk3506-gw-01"))
	base := "station/" + deviceID

	rt := NewRuntime(cfg, nil, nil)
	exec := &shadowExecutor{}

	var pub *MqttPub
	if mcfg != nil {
		pub = NewMqttPub(asStr(mcfg["host"]), int(toF(getOr(mcfg, "port", float64(1883)))),
			deviceID+"-shadow", asStr(mcfg["username"]), asStr(mcfg["password"]),
			int(toF(getOr(mcfg, "keepalive", float64(30)))), int(toF(getOr(mcfg, "buffer_max", float64(2000)))))
	}

	var mu sync.Mutex
	var viewsN, decN, lastRSS int64
	emitGo := func(o obj) {
		if pub != nil {
			pub.Publish(base+"/_shadow/go", o)
		}
	}

	ctrl := NewController(ControllerDeps{
		Snapshot: func() obj { return SamplesView(rt.Get()) },
		Write:    exec.Write, // 封死:只记意图
		Clock:    defaultClock,
		Record: func(r ControlRecord) {
			rt.AddEvent(obj{"kind": "command", "action": r.Status,
				"detail": fmt.Sprintf("%s ← %v (%s)", r.PointID, r.Value, r.Status)})
			rec := obj{"kind": "decision", "ts": r.TS, "command_id": r.CommandID,
				"point_id": r.PointID, "value": r.Value, "status": r.Status,
				"reason": r.Reason, "origin": r.Origin, "shadow_simulated": true}
			emitGo(rec)
			stdoutLine(rec) // 决策稀疏,总打 stdout 便于无 broker 观测
			mu.Lock()
			decN++
			mu.Unlock()
		},
		Alarm: func(a ControlAlarm) {
			rt.AddEvent(obj{"kind": "alarm", "action": a.Action, "detail": a.Detail})
			al := obj{"kind": "alarm", "ts": time.Now().UnixMilli(), "action": a.Action, "detail": a.Detail}
			emitGo(al)
			stdoutLine(al)
		},
		Policy: asObj(cfg["safety_policy"]),
	})

	// ingest:采样 → Go Runtime,并把 Go 的 view 摘要发回(MQTT)供对账。
	ingest := func(samples obj, ts interface{}) {
		if samples == nil {
			return
		}
		rt.Update(samples)
		rt.MarkAlive()
		points, offline := shadowDigest(rt.View())
		rss := readRSSKb()
		mu.Lock()
		viewsN++
		lastRSS = rss
		mu.Unlock()
		emitGo(obj{"kind": "view", "ts": ts, "points": points, "offline": offline, "rss_kb": rss})
	}

	if pub != nil {
		pub.Subscribe(base+"/_shadow/samples", func(payload []byte) {
			var msg obj
			if json.Unmarshal(payload, &msg) == nil {
				ingest(asObj(msg["samples"]), msg["ts"])
			}
		})
		// 与生产同一条命令广播 → 喂 Go Controller(写被封死),对比决策。
		pub.Subscribe(base+"/property/set", func(payload []byte) {
			var cmd obj
			if json.Unmarshal(payload, &cmd) != nil {
				return
			}
			pl := asObj(cmd["payload"])
			if pl == nil {
				pl = cmd
			}
			for pid, val := range pl {
				ctrl.Apply(pid, val, asStr(cmd["command_id"]), "platform-shadow")
			}
		})
	}

	var sockConn net.PacketConn
	if *samplesSock != "" {
		os.Remove(*samplesSock) // 清理上次残留的 socket 文件
		l, err := net.ListenPacket("unixgram", *samplesSock)
		if err != nil {
			fmt.Fprintf(os.Stderr, "绑定 unix socket %s 失败: %v\n", *samplesSock, err)
			os.Exit(2)
		}
		sockConn = l
		go func() {
			buf := make([]byte, 1<<16)
			for {
				n, _, err := l.ReadFrom(buf)
				if err != nil {
					return // 关闭即退出
				}
				var msg obj
				if json.Unmarshal(buf[:n], &msg) == nil {
					ingest(asObj(msg["samples"]), msg["ts"])
				}
			}
		}()
	}

	// 周期摘要打 stdout:无 broker 也能 tail 看到 liveness/RSS/计数。
	stop := make(chan struct{})
	go func() {
		t := time.NewTicker(30 * time.Second)
		defer t.Stop()
		for {
			select {
			case <-stop:
				return
			case <-t.C:
				mu.Lock()
				stdoutLine(obj{"kind": "summary", "views": viewsN, "decisions": decN,
					"rss_kb": lastRSS, "intents": exec.intents})
				mu.Unlock()
			}
		}
	}()

	srcDesc := ""
	if pub != nil {
		srcDesc += "MQTT " + base + "/_shadow/samples"
	}
	if *samplesSock != "" {
		if srcDesc != "" {
			srcDesc += " + "
		}
		srcDesc += "unixgram " + *samplesSock
	}
	fmt.Printf("[影子] 已启动:采样来源 = %s;命令对账 = %s\n", srcDesc,
		map[bool]string{true: base + "/property/set", false: "无(无 broker,仅 view/资源对比)"}[pub != nil])
	fmt.Println("[影子] 写执行器已封死(shadowExecutor),不构造任何数据源/串口——物理上无总线写路径。")

	cleanup := func() {
		close(stop)
		if pub != nil {
			pub.Disconnect()
		}
		if sockConn != nil {
			sockConn.Close()
			os.Remove(*samplesSock)
		}
	}

	if *seconds > 0 {
		time.Sleep(time.Duration(*seconds) * time.Second)
		mu.Lock()
		fmt.Printf("[影子] 冒烟结束:views=%d decisions=%d intents=%d(全部未落总线)rss=%dKB\n",
			viewsN, decN, exec.intents, lastRSS)
		mu.Unlock()
		cleanup()
		return
	}
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	cleanup()
	fmt.Println("\n影子退出。")
}
