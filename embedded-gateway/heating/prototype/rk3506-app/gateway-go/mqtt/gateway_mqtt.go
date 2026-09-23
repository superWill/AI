// RK3506 云↔网关 MQTT 客户端（Go 移植自 cloud-gateway-mqtt/gateway_mqtt.py）。
//
// 实现数据契约的 topic：
//   上行 station/{id}/telemetry|heartbeat|alarm|command_reply
//   下行 station/{id}/property/set
// 特性与 Python 版一致：seq 单调；断网本地缓存、恢复后按 seq 补传(replay:true,保留原始 ts)；
// 下发设定值经本地安全校验 stub，冲突回 blocked_by_safety；read_points 为 stub。
package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

// --------------------------------------------------------------------------- //
// 数据源 —— 唯一要接真实采集的地方（UART/firebus → 点表）。现为 stub。
// --------------------------------------------------------------------------- //
func readPoints() map[string]interface{} {
	pt := func(v float64) map[string]interface{} { return map[string]interface{}{"v": v, "q": "good"} }
	return map[string]interface{}{
		"pri_supply_temp":    pt(78.4),
		"pri_return_temp":     pt(45.1),
		"pri_flow":            pt(32.7),
		"pri_valve_feedback":  pt(61.0),
		"sec_supply_temp":     pt(52.3),
		"sec_return_temp":     pt(41.8),
		"outdoor_temp":        pt(-3.2),
	}
}

func clockSyncState() string { return "synced" } // TODO: 接 chrony/ntp

// 安全校验 stub —— 平台只能给设定值，绝不越过本地安全分层（契约 §8）。
func safetyCheck(commandType string, payload map[string]interface{}) (bool, string) {
	if t, ok := payload["sec_supply_temp_target"]; ok && t != nil {
		if f, ok := t.(float64); ok && !(f >= 20.0 && f <= 75.0) {
			return false, fmt.Sprintf("sec_supply_temp_target %v out of safe range [20,75]", t)
		}
	}
	return true, ""
}

// --------------------------------------------------------------------------- //
type Config struct {
	DeviceID          string `json:"device_id"`
	ClientID          string `json:"client_id"`
	BrokerHost        string `json:"broker_host"`
	BrokerPort        int    `json:"broker_port"`
	Keepalive         int    `json:"keepalive"`
	Username          string `json:"username"`
	Password          string `json:"password"`
	TLS               bool   `json:"tls"`
	CACerts           string `json:"ca_certs"`
	CertFile          string `json:"certfile"`
	KeyFile           string `json:"keyfile"`
	TelemetryInterval int    `json:"telemetry_interval"`
	HeartbeatInterval int    `json:"heartbeat_interval"`
	BufferMax         int    `json:"buffer_max"`
}

func (c *Config) defaults() {
	if c.BrokerPort == 0 {
		c.BrokerPort = 1883
	}
	if c.Keepalive == 0 {
		c.Keepalive = 30
	}
	if c.TelemetryInterval == 0 {
		c.TelemetryInterval = 30
	}
	if c.HeartbeatInterval == 0 {
		c.HeartbeatInterval = 60
	}
	if c.BufferMax == 0 {
		c.BufferMax = 5000
	}
}

type frame = map[string]interface{}

// Gateway 网关 MQTT 客户端
type Gateway struct {
	cfg      Config
	deviceID string
	base     string
	seq      int64
	buf      []frame // 断网缓存（环形，满了丢最旧）
	bufMu    sync.Mutex
	client   mqtt.Client
	verbose  bool
}

func NewGateway(cfg Config, verbose bool) *Gateway {
	cfg.defaults()
	g := &Gateway{cfg: cfg, deviceID: cfg.DeviceID, base: "station/" + cfg.DeviceID, verbose: verbose}

	scheme := "tcp"
	if cfg.TLS {
		scheme = "ssl"
	}
	opts := mqtt.NewClientOptions().
		AddBroker(fmt.Sprintf("%s://%s:%d", scheme, cfg.BrokerHost, cfg.BrokerPort)).
		SetClientID(cfg.ClientID).
		SetKeepAlive(time.Duration(cfg.Keepalive) * time.Second).
		SetAutoReconnect(true).            // 自动重连
		SetConnectRetry(true).             // 首连失败也重试
		SetConnectRetryInterval(1 * time.Second).
		SetMaxReconnectInterval(30 * time.Second).
		SetOnConnectHandler(g.onConnect)
	if cfg.Username != "" {
		opts.SetUsername(cfg.Username).SetPassword(cfg.Password)
	}
	if cfg.TLS {
		opts.SetTLSConfig(buildTLS(cfg))
	}
	// 遗嘱：掉线时 broker 替它发离线心跳
	will, _ := json.Marshal(frame{"device_id": cfg.DeviceID, "online": false})
	opts.SetBinaryWill(g.base+"/heartbeat", will, 1, false)

	g.client = mqtt.NewClient(opts)
	return g
}

func buildTLS(cfg Config) *tls.Config {
	t := &tls.Config{}
	if cfg.CACerts != "" {
		if ca, err := os.ReadFile(cfg.CACerts); err == nil {
			pool := x509.NewCertPool()
			pool.AppendCertsFromPEM(ca)
			t.RootCAs = pool
		}
	}
	if cfg.CertFile != "" && cfg.KeyFile != "" {
		if cert, err := tls.LoadX509KeyPair(cfg.CertFile, cfg.KeyFile); err == nil {
			t.Certificates = []tls.Certificate{cert}
		}
	}
	return t
}

func (g *Gateway) nextSeq() int64 { return atomic.AddInt64(&g.seq, 1) }

func (g *Gateway) debugf(f string, a ...interface{}) {
	if g.verbose {
		log.Printf(f, a...)
	}
}

func nowMs() int64 { return time.Now().UnixMilli() }

// -- 回调 --------------------------------------------------------------------
func (g *Gateway) onConnect(c mqtt.Client) {
	log.Printf("connected to broker, subscribing %s/property/set", g.base)
	c.Subscribe(g.base+"/property/set", 1, g.onMessage)
}

func (g *Gateway) onMessage(c mqtt.Client, msg mqtt.Message) {
	log.Printf("downlink %s: %.200s", msg.Topic(), msg.Payload())
	var cmd frame
	if err := json.Unmarshal(msg.Payload(), &cmd); err != nil {
		log.Printf("bad command json: %v", err)
		return
	}
	g.handleSetpoint(cmd)
}

// -- 下发设定值处理 + 回传 ---------------------------------------------------
func (g *Gateway) handleSetpoint(cmd frame) {
	commandID, _ := cmd["command_id"].(string)
	ctype, _ := cmd["command_type"].(string)
	if ctype == "" {
		ctype = "set_point"
	}
	payload, _ := cmd["payload"].(map[string]interface{})
	if payload == nil {
		payload = map[string]interface{}{}
	}
	if ok, reason := safetyCheck(ctype, payload); !ok {
		g.reply(commandID, "blocked_by_safety", frame{}, reason)
		log.Printf("setpoint blocked: %s", reason)
		return
	}
	// TODO: 目标值交本地气候补偿+PID 执行；先回 accepted
	g.reply(commandID, "accepted", frame{}, "")
	log.Printf("setpoint accepted: %v", payload)
}

func (g *Gateway) reply(commandID, status string, achieved frame, reason string) {
	f := frame{"command_id": commandID, "ts": nowMs(), "status": status,
		"achieved": achieved, "reason": reason}
	g.pub(g.base+"/command_reply", f, 1)
}

// -- 上行 --------------------------------------------------------------------
func (g *Gateway) buildTelemetry(replay bool, ts int64) frame {
	if ts == 0 {
		ts = nowMs()
	}
	f := frame{"device_id": g.deviceID, "ts": ts, "clock_sync": clockSyncState(),
		"seq": g.nextSeq(), "points": readPoints()}
	if replay {
		f["replay"] = true
	}
	return f
}

func (g *Gateway) publishTelemetry() {
	f := g.buildTelemetry(false, 0)
	if g.client.IsConnectionOpen() {
		g.flushBuffer()
		g.pub(g.base+"/telemetry", f, 1)
	} else {
		g.bufMu.Lock()
		g.buf = append(g.buf, f)
		if len(g.buf) > g.cfg.BufferMax {
			g.buf = g.buf[len(g.buf)-g.cfg.BufferMax:] // 丢最旧
		}
		n := len(g.buf)
		g.bufMu.Unlock()
		g.debugf("offline, buffered seq=%v (buffer=%d)", f["seq"], n)
	}
}

// flushBuffer 重连后按 seq 顺序补传，标 replay:true、保留原始 ts。
func (g *Gateway) flushBuffer() {
	for {
		g.bufMu.Lock()
		if len(g.buf) == 0 || !g.client.IsConnectionOpen() {
			done := len(g.buf) == 0
			g.bufMu.Unlock()
			if done {
				log.Printf("backfill complete")
			}
			return
		}
		f := g.buf[0]
		g.buf = g.buf[1:]
		g.bufMu.Unlock()
		f["replay"] = true
		g.pub(g.base+"/telemetry", f, 1)
	}
}

func (g *Gateway) publishHeartbeat() {
	if g.client.IsConnectionOpen() {
		g.bufMu.Lock()
		n := len(g.buf)
		g.bufMu.Unlock()
		g.pub(g.base+"/heartbeat", frame{"device_id": g.deviceID, "online": true,
			"ts": nowMs(), "buffer": n}, 0)
	}
}

func (g *Gateway) PublishAlarm(alarmID, message string) {
	g.pub(g.base+"/alarm", frame{"device_id": g.deviceID, "ts": nowMs(),
		"alarm_id": alarmID, "message": message}, 1)
}

func (g *Gateway) pub(topic string, f frame, qos byte) {
	b, _ := json.Marshal(f)
	g.client.Publish(topic, qos, false, b)
}

// -- 主循环 ------------------------------------------------------------------
func (g *Gateway) Run(stop <-chan struct{}) {
	log.Printf("connecting %s:%d as %s", g.cfg.BrokerHost, g.cfg.BrokerPort, g.deviceID)
	g.client.Connect() // ConnectRetry=true：后台重试，不阻塞

	g.publishTelemetry() // 启动即发一帧（对齐 Python：首循环立即上送）
	g.publishHeartbeat()
	teleTick := time.NewTicker(time.Duration(g.cfg.TelemetryInterval) * time.Second)
	hbTick := time.NewTicker(time.Duration(g.cfg.HeartbeatInterval) * time.Second)
	defer teleTick.Stop()
	defer hbTick.Stop()

	for {
		select {
		case <-stop:
			g.client.Disconnect(250)
			g.bufMu.Lock()
			n := len(g.buf)
			g.bufMu.Unlock()
			log.Printf("stopped, %d frames left in buffer", n)
			return
		case <-teleTick.C:
			g.publishTelemetry()
		case <-hbTick.C:
			g.publishHeartbeat()
		}
	}
}

func main() {
	cfgPath := flag.String("config", "config.json", "配置文件")
	verbose := flag.Bool("v", false, "调试日志")
	flag.Parse()

	raw, err := os.ReadFile(*cfgPath)
	if err != nil {
		log.Fatalf("读取配置失败: %v", err)
	}
	var cfg Config
	if err := json.Unmarshal(raw, &cfg); err != nil {
		log.Fatalf("解析配置失败: %v", err)
	}

	gw := NewGateway(cfg, *verbose)
	stop := make(chan struct{})
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	go func() { <-sig; close(stop) }()
	gw.Run(stop)
}
