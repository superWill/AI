// 轨 B 阶段一:只读影子并行(`gatewayc shadow`)。
//
// 硬不变量(本文件强制):
//   - 影子模式**不构造任何数据源/串口写句柄**——物理上没有到总线的路径;
//   - Controller 注入 shadowExecutor:只记录"打算写什么",return false,从不触碰总线;
//   - 不订阅/写入任何生产执行通路。
//
// 数据流(全程只读):
//   订阅 station/<id>/_shadow/samples(app.py 旁路出的原始采样)→ 喂 Go Runtime;
//   订阅 station/<id>/property/set(与生产同一广播)→ 喂 Go Controller(写被封死);
//   把 Go 的 view 摘要与每条控制决策发到 station/<id>/_shadow/go 供板外比对器对账。
// 板上不落盘(省 NAND),只发 MQTT。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
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

func runShadow(args []string) {
	fs := flag.NewFlagSet("shadow", flag.ExitOnError)
	cfgPath := fs.String("config", "app_config.json", "运行配置(与生产同一份,只用 device_id/mqtt/safety_policy)")
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
	if mcfg == nil {
		fmt.Fprintln(os.Stderr, "影子模式需要 mqtt 配置(订阅旁路采样)")
		os.Exit(2)
	}
	deviceID := asStr(getOr(cfg, "device_id", "rk3506-gw-01"))
	base := "station/" + deviceID

	rt := NewRuntime(cfg, nil, nil)
	exec := &shadowExecutor{}

	// 影子专用 client id,避免与生产网关在 broker 上撞 id。
	pub := NewMqttPub(asStr(mcfg["host"]), int(toF(getOr(mcfg, "port", float64(1883)))),
		deviceID+"-shadow", asStr(mcfg["username"]), asStr(mcfg["password"]),
		int(toF(getOr(mcfg, "keepalive", float64(30)))), int(toF(getOr(mcfg, "buffer_max", float64(2000)))))

	ctrl := NewController(ControllerDeps{
		Snapshot: func() obj { return SamplesView(rt.Get()) },
		Write:    exec.Write, // 封死:只记意图
		Clock:    defaultClock,
		Record: func(r ControlRecord) {
			rt.AddEvent(obj{"kind": "command", "action": r.Status,
				"detail": fmt.Sprintf("%s ← %v (%s)", r.PointID, r.Value, r.Status)})
			pub.Publish(base+"/_shadow/go", obj{
				"kind": "decision", "ts": r.TS, "command_id": r.CommandID,
				"point_id": r.PointID, "value": r.Value, "status": r.Status,
				"reason": r.Reason, "origin": r.Origin, "shadow_simulated": true,
			})
		},
		Alarm: func(a ControlAlarm) {
			rt.AddEvent(obj{"kind": "alarm", "action": a.Action, "detail": a.Detail})
			pub.Publish(base+"/_shadow/go", obj{"kind": "alarm", "ts": time.Now().UnixMilli(),
				"action": a.Action, "detail": a.Detail})
		},
		Policy: asObj(cfg["safety_policy"]),
	})

	var lastSampleTs float64
	// 旁路采样 → 喂 Go Runtime,并把 Go 的 view 摘要发回供对账。
	pub.Subscribe(base+"/_shadow/samples", func(payload []byte) {
		var msg obj
		if json.Unmarshal(payload, &msg) != nil {
			return
		}
		samples := asObj(msg["samples"])
		if samples == nil {
			return
		}
		rt.Update(samples)
		rt.MarkAlive()
		lastSampleTs = toF(msg["ts"])
		points, offline := shadowDigest(rt.View())
		pub.Publish(base+"/_shadow/go", obj{
			"kind": "view", "ts": msg["ts"], "points": points, "offline": offline,
			"rss_kb": readRSSKb(),
		})
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

	fmt.Printf("[影子] 已启动:订阅 %s/_shadow/samples + %s/property/set,发往 %s/_shadow/go\n", base, base, base)
	fmt.Println("[影子] 写执行器已封死(shadowExecutor),不构造任何数据源/串口——物理上无总线写路径。")

	if *seconds > 0 {
		time.Sleep(time.Duration(*seconds) * time.Second)
		fmt.Printf("[影子] 冒烟结束:已处理采样 ts=%.0f,意图写次数=%d(全部未落总线)\n", lastSampleTs, exec.intents)
		pub.Disconnect()
		return
	}
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	pub.Disconnect()
	fmt.Println("\n影子退出。")
}
