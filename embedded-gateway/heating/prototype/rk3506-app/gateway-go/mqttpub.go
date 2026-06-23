// 网关 daemon 的 MQTT 发布/订阅(paho 薄封装,统一到与 mqtt/ 同一库,替 app.py 手写 MqttClient)。
package main

import (
	"encoding/json"
	"fmt"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

type MqttPub struct {
	client mqtt.Client
}

func NewMqttPub(host string, port int, clientID, user, pass string) *MqttPub {
	opts := mqtt.NewClientOptions().
		AddBroker(fmt.Sprintf("tcp://%s:%d", host, port)).
		SetClientID(clientID).
		SetAutoReconnect(true).
		SetConnectRetry(true).
		SetConnectRetryInterval(time.Second).
		SetMaxReconnectInterval(30 * time.Second)
	if user != "" {
		opts.SetUsername(user).SetPassword(pass)
	}
	p := &MqttPub{client: mqtt.NewClient(opts)}
	p.client.Connect() // ConnectRetry=true：后台重连，不阻塞
	return p
}

func (p *MqttPub) Publish(topic string, payload obj) {
	b, _ := json.Marshal(payload)
	p.client.Publish(topic, 1, false, b)
}

func (p *MqttPub) Subscribe(topic string, handler func(payload []byte)) {
	p.client.Subscribe(topic, 1, func(_ mqtt.Client, m mqtt.Message) { handler(m.Payload()) })
}

func (p *MqttPub) Disconnect() { p.client.Disconnect(250) }
