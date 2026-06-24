// gatewayc ui 的自实现 socket.io(Engine.IO v4 + Socket.IO v5,仅 polling)——对照 nexus_server.py。
// EIO: 0=open 2=ping 3=pong;SIO: 40=connect 42=event;RS=\x1e 分隔多包。
package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

const sioRS = "\x1e"

func randHex(n int) string {
	b := make([]byte, n)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func eioOpen(sid string) string {
	b, _ := json.Marshal(obj{"sid": sid, "upgrades": arr{},
		"pingInterval": 25000, "pingTimeout": 20000, "maxPayload": 1000000})
	return "0" + string(b)
}

func sioEvent(event string, data interface{}) string {
	b, _ := json.Marshal(arr{event, data})
	return "42" + string(b)
}

type sioSession struct {
	mu  sync.Mutex
	q   []string
	sig chan struct{}
}

type socketHub struct {
	mu       sync.Mutex
	sessions map[string]*sioSession
}

func newSocketHub() *socketHub { return &socketHub{sessions: map[string]*sioSession{}} }

func (h *socketHub) newSession() string {
	sid := randHex(8) // 16 hex,对照 "%016x"
	h.mu.Lock()
	h.sessions[sid] = &sioSession{sig: make(chan struct{}, 1)}
	h.mu.Unlock()
	return sid
}

func (h *socketHub) get(sid string) *sioSession {
	h.mu.Lock()
	defer h.mu.Unlock()
	return h.sessions[sid]
}

func (h *socketHub) push(sid, pkt string) {
	s := h.get(sid)
	if s == nil {
		return
	}
	s.mu.Lock()
	s.q = append(s.q, pkt)
	s.mu.Unlock()
	select {
	case s.sig <- struct{}{}:
	default:
	}
}

func (h *socketHub) broadcast(pkt string) {
	h.mu.Lock()
	sids := make([]string, 0, len(h.sessions))
	for sid := range h.sessions {
		sids = append(sids, sid)
	}
	h.mu.Unlock()
	for _, sid := range sids {
		h.push(sid, pkt)
	}
}

// poll:等 timeout 内有包就返回 RS 连接;无包返回 "2"(EIO ping 维持长轮询);未知 sid 重握手。
func (h *socketHub) poll(sid string, timeout time.Duration) string {
	s := h.get(sid)
	if s == nil {
		b, _ := json.Marshal(obj{"sid": h.newSession()})
		return "0" + string(b)
	}
	select {
	case <-s.sig:
	case <-time.After(timeout):
	}
	s.mu.Lock()
	pkts := s.q
	s.q = nil
	s.mu.Unlock()
	select {
	case <-s.sig:
	default:
	}
	if len(pkts) == 0 {
		return "2"
	}
	return strings.Join(pkts, sioRS)
}

func (h *socketHub) handlePost(sid, body string) {
	if h.get(sid) == nil {
		return
	}
	for _, pkt := range strings.Split(body, sioRS) {
		if strings.HasPrefix(pkt, "40") { // SIO CONNECT → 回 connect ack
			b, _ := json.Marshal(obj{"sid": randHex(8)})
			h.push(sid, "40"+string(b))
		} else if pkt == "2" { // EIO ping → pong
			h.push(sid, "3")
		}
	}
}

// sysMetricsUI:对照 nexus sys_metrics——/proc/loadavg + /proc/meminfo;读不到给占位。
func sysMetricsUI() obj {
	cpu, mem := 5.0, 30.0
	if b, err := os.ReadFile("/proc/loadavg"); err == nil {
		if f := strings.Fields(string(b)); len(f) > 0 {
			if la, e := strconv.ParseFloat(f[0], 64); e == nil {
				cpu = la * 25
				if cpu > 100 {
					cpu = 100
				}
			}
		}
	}
	if b, err := os.ReadFile("/proc/meminfo"); err == nil {
		var mt, ma float64
		for _, ln := range strings.Split(string(b), "\n") {
			f := strings.Fields(ln)
			if len(f) >= 2 {
				if f[0] == "MemTotal:" {
					mt, _ = strconv.ParseFloat(f[1], 64)
				} else if f[0] == "MemAvailable:" {
					ma, _ = strconv.ParseFloat(f[1], 64)
				}
			}
		}
		if mt > 0 {
			mem = round1((mt - ma) * 100.0 / mt)
		}
	}
	return obj{"cpu": round1(cpu), "memory": mem, "throughput": 0,
		"rx": 0, "tx": 0, "nbRx": 0, "nbTx": 0, "network": arr{}}
}

func round1(f float64) float64 {
	return float64(int64(f*10+0.5)) / 10
}
