// 网关 daemon 的 MQTT 发布/订阅(paho)。telemetry 带断网缓存 + 重连补传(replay:true),
// 语义对齐已验证的 mqtt/gateway_mqtt.go(用 IsConnectionOpen 判活,断网不静默丢数据)。
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

type MqttPub struct {
	client    mqtt.Client
	buf       []obj // 断网缓存(telemetry 原始帧)
	bufMu     sync.Mutex
	bufferMax int
	subs      map[string]func([]byte) // 已注册订阅(topic→handler),重连后据此恢复
	subMu     sync.Mutex
}

func NewMqttPub(host string, port int, clientID, user, pass string, keepalive, bufferMax int) *MqttPub {
	if keepalive <= 0 {
		keepalive = 30
	}
	if bufferMax <= 0 {
		bufferMax = 5000
	}
	p := &MqttPub{bufferMax: bufferMax, subs: map[string]func([]byte){}}
	opts := mqtt.NewClientOptions().
		AddBroker(fmt.Sprintf("tcp://%s:%d", host, port)).
		SetClientID(clientID).
		SetKeepAlive(time.Duration(keepalive) * time.Second).
		SetAutoReconnect(true).
		SetConnectRetry(true).
		SetConnectRetryInterval(time.Second).
		SetMaxReconnectInterval(30 * time.Second).
		// 关键:paho ResumeSubs 默认 false,且首连/重连前 Subscribe 会静默失败。
		// 按官方范式把(重)订阅放进 OnConnect,每次连上都恢复全部订阅。
		SetOnConnectHandler(func(_ mqtt.Client) { p.resubscribe() })
	if user != "" {
		opts.SetUsername(user).SetPassword(pass)
	}
	p.client = mqtt.NewClient(opts)
	p.client.Connect()
	return p
}

// resubscribe 把已注册的全部订阅重新下发,检查 SUBACK(失败打日志,不静默)。
func (p *MqttPub) resubscribe() {
	p.subMu.Lock()
	items := make(map[string]func([]byte), len(p.subs))
	for t, h := range p.subs {
		items[t] = h
	}
	p.subMu.Unlock()
	for topic, h := range items {
		hh := h
		tok := p.client.Subscribe(topic, 1, func(_ mqtt.Client, m mqtt.Message) { hh(m.Payload()) })
		if !tok.WaitTimeout(5*time.Second) || tok.Error() != nil {
			fmt.Fprintf(os.Stderr, "[MQTT] 订阅失败 %s: %v\n", topic, tok.Error())
		}
	}
}

// connected 反映真实 socket 状态（AutoReconnect 下 IsConnected 断网仍 true，必须用 IsConnectionOpen）。
func (p *MqttPub) connected() bool { return p.client.IsConnectionOpen() }

// tryPublish 发布并等 PUBACK(QoS1);超时/出错视为未送达(断网瞬间 socket 已死)。
func (p *MqttPub) tryPublish(topic string, payload obj) bool {
	b, _ := json.Marshal(payload)
	t := p.client.Publish(topic, 1, false, b)
	return t.WaitTimeout(2*time.Second) && t.Error() == nil
}

func (p *MqttPub) bufAppend(frame obj) {
	p.bufMu.Lock()
	p.buf = append(p.buf, frame)
	if len(p.buf) > p.bufferMax {
		p.buf = p.buf[len(p.buf)-p.bufferMax:] // 环形,满丢最旧
	}
	p.bufMu.Unlock()
}

// Publish 普通发布(heartbeat/command_reply):连上才发,断网即弃(瞬时量无补传意义)。
func (p *MqttPub) Publish(topic string, payload obj) {
	if p.connected() {
		p.tryPublish(topic, payload)
	}
}

// PublishTelemetry 周期遥测:连上→先补传缓存再发当前帧;断网或发布未送达→入缓存。
// 用 PUBACK 结果而非仅 IsConnectionOpen 判定,断网瞬间那一帧也不丢。
func (p *MqttPub) PublishTelemetry(topic string, frame obj) {
	if !p.connected() {
		p.bufAppend(frame)
		return
	}
	p.flush(topic)
	if !p.tryPublish(topic, frame) { // 实时帧未确认 → 收进缓存待补传
		p.bufAppend(frame)
	}
}

// flush 重连后按顺序补传,标 replay:true、保留原始 ts/seq;发布失败即停(留缓存下轮再试)。
func (p *MqttPub) flush(topic string) {
	for {
		p.bufMu.Lock()
		if len(p.buf) == 0 || !p.connected() {
			p.bufMu.Unlock()
			return
		}
		f := p.buf[0]
		p.bufMu.Unlock()
		f["replay"] = true
		if !p.tryPublish(topic, f) {
			return // 仍未送达,保留在缓存
		}
		p.bufMu.Lock()
		p.buf = p.buf[1:] // 确认送达才出队
		p.bufMu.Unlock()
	}
}

// Subscribe 登记订阅并立即(若已连)下发;断连/重连由 OnConnect→resubscribe 兜底恢复。
func (p *MqttPub) Subscribe(topic string, handler func(payload []byte)) {
	p.subMu.Lock()
	p.subs[topic] = handler
	p.subMu.Unlock()
	if p.connected() {
		p.resubscribe()
	}
	// 未连则不在此下发(必失败),等首个 OnConnect 触发恢复。
}

func (p *MqttPub) Disconnect() { p.client.Disconnect(250) }
