// Package server 提供 CRT 侧的两个面：对下是控制器链路（TCP/串口字节流），
// 对上是给页面用的 HTTP + SSE。
package server

import (
	"embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/superwill/fire-alarm/gateway/internal/crtlink"
	"github.com/superwill/fire-alarm/gateway/internal/model"
)

//go:embed all:web
var webFS embed.FS

// FrameLog 保存最近的原始帧，供协议一致性核对（用例 CM-04 / CM-10 / CM-14）。
// 页面上能直接看到十六进制原文和解析结果，不必另接抓包工具。
type FrameLog struct {
	mu    sync.RWMutex
	items []FrameRecord
	max   int
}

type FrameRecord struct {
	At   time.Time `json:"at"`
	Dir  string    `json:"dir"` // "上行"（控制器→CRT）/"下行"（CRT→控制器）
	Type string    `json:"type"`
	Seq  uint16    `json:"seq"`
	Hex  string    `json:"hex"`
	Err  string    `json:"err,omitempty"`
}

func NewFrameLog(max int) *FrameLog { return &FrameLog{max: max} }

func (l *FrameLog) Add(rec FrameRecord) {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.items = append(l.items, rec)
	if len(l.items) > l.max {
		l.items = l.items[len(l.items)-l.max:]
	}
}

func (l *FrameLog) Recent(n int) []FrameRecord {
	l.mu.RLock()
	defer l.mu.RUnlock()
	src := l.items
	if n > 0 && n < len(src) {
		src = src[len(src)-n:]
	}
	out := make([]FrameRecord, len(src))
	for i, r := range src { // 倒序，最新在前
		out[len(src)-1-i] = r
	}
	return out
}

// Server 把链路、状态、页面串起来。
type Server struct {
	State  *model.State
	Frames *FrameLog

	mu      sync.Mutex
	conn    net.Conn // 当前控制器连接，用于下行命令
	seq     uint16
	subs    map[chan struct{}]struct{}
	subsMu  sync.Mutex
	autoAck bool
}

func New() *Server {
	return &Server{State: model.NewState(), Frames: NewFrameLog(500),
		subs: map[chan struct{}]struct{}{}, autoAck: true}
}

// notify 唤醒所有 SSE 订阅者。非阻塞：慢客户端不拖住链路。
func (s *Server) notify() {
	s.subsMu.Lock()
	defer s.subsMu.Unlock()
	for ch := range s.subs {
		select {
		case ch <- struct{}{}:
		default:
		}
	}
}

// ServeLink 在 addr 上监听控制器连接。同一时刻只服务一条链路（现场就是
// 一台控制器对一台图形显示装置），新连接会顶掉旧连接。
func (s *Server) ServeLink(addr string) error {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}
	log.Printf("链路监听 %s，等待控制器接入", addr)
	for {
		c, err := ln.Accept()
		if err != nil {
			return err
		}
		s.mu.Lock()
		if s.conn != nil {
			s.conn.Close()
		}
		s.conn = c
		s.mu.Unlock()
		log.Printf("控制器已接入：%s", c.RemoteAddr())
		go s.handleConn(c)
	}
}

func (s *Server) handleConn(c net.Conn) {
	defer func() {
		c.Close()
		s.mu.Lock()
		if s.conn == c {
			s.conn = nil
		}
		s.mu.Unlock()
		s.State.MarkLinkDown()
		s.notify()
		log.Printf("控制器断开：%s", c.RemoteAddr())
	}()

	dec := crtlink.NewDecoder(c)
	for {
		f, err := dec.Next()
		if err != nil {
			if err == io.EOF {
				return
			}
			if err == crtlink.ErrCRC {
				// CRC 错不断链：回 ACK(status=1) 让主机重发，链路自行重同步。
				s.Frames.Add(FrameRecord{At: time.Now(), Dir: "上行", Type: "CRC 错", Err: err.Error()})
				s.sendACK(0, crtlink.ACKCRCError)
				s.notify()
				continue
			}
			var ne net.Error
			if ok := func() bool { ne, _ = err.(net.Error); return ne != nil }(); ok && ne.Timeout() {
				continue
			}
			log.Printf("链路解码错误：%v", err)
			return
		}
		raw, _ := crtlink.Encode(f)
		s.Frames.Add(FrameRecord{At: time.Now(), Dir: "上行", Type: crtlink.TypeName(f.Type),
			Seq: f.Seq, Hex: hex.EncodeToString(raw)})

		if s.State.Apply(f) {
			s.notify()
		}
		if s.autoAck && f.Type != crtlink.TypeACK {
			s.sendACK(f.Seq, crtlink.ACKOK)
		}
	}
}

// Send 下发一帧到控制器。
func (s *Server) Send(typ uint8, data []byte) error {
	s.mu.Lock()
	c := s.conn
	s.seq++
	seq := s.seq
	s.mu.Unlock()
	if c == nil {
		return fmt.Errorf("控制器未接入")
	}
	f := crtlink.Frame{Seq: seq, Src: crtlink.AddrCRT, Dst: crtlink.AddrHost, Type: typ, Data: data}
	raw, err := crtlink.Encode(f)
	if err != nil {
		return err
	}
	if _, err := c.Write(raw); err != nil {
		return err
	}
	s.Frames.Add(FrameRecord{At: time.Now(), Dir: "下行", Type: crtlink.TypeName(typ),
		Seq: seq, Hex: hex.EncodeToString(raw)})
	s.notify()
	return nil
}

func (s *Server) sendACK(seq uint16, status uint8) {
	_ = s.Send(crtlink.TypeACK, crtlink.EncodeACK(seq, status))
}

// Routes 返回 HTTP 处理器。
func (s *Server) Routes() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("/api/snapshot", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, s.State.Snapshot(200))
	})

	mux.HandleFunc("/api/frames", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, s.Frames.Recent(200))
	})

	// SSE：状态一变就推，页面不必轮询。
	mux.HandleFunc("/api/stream", func(w http.ResponseWriter, r *http.Request) {
		fl, ok := w.(http.Flusher)
		if !ok {
			http.Error(w, "不支持流式响应", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")

		ch := make(chan struct{}, 1)
		s.subsMu.Lock()
		s.subs[ch] = struct{}{}
		s.subsMu.Unlock()
		defer func() {
			s.subsMu.Lock()
			delete(s.subs, ch)
			s.subsMu.Unlock()
		}()

		tick := time.NewTicker(3 * time.Second) // 兜底心跳，同时驱动链路超时判定
		defer tick.Stop()
		send := func() bool {
			b, err := json.Marshal(s.State.Snapshot(200))
			if err != nil {
				return false
			}
			fmt.Fprintf(w, "data: %s\n\n", b)
			fl.Flush()
			return true
		}
		if !send() {
			return
		}
		for {
			select {
			case <-r.Context().Done():
				return
			case <-ch:
				if !send() {
					return
				}
			case <-tick.C:
				if !send() {
					return
				}
			}
		}
	})

	// 下行命令：授时、复位、屏蔽、手动启停。密码/钥匙类命令由控制器侧鉴权，
	// CRT 只负责把请求发下去（GB 4717 表 1 的权限判定在主机，不在这里）。
	mux.HandleFunc("/api/cmd/timesync", func(w http.ResponseWriter, r *http.Request) {
		respond(w, s.Send(crtlink.TypeTimeSync, crtlink.EncodeTimeSync(time.Now())))
	})
	mux.HandleFunc("/api/cmd/reset", func(w http.ResponseWriter, r *http.Request) {
		respond(w, s.Send(crtlink.TypeCmdReset, []byte{0}))
	})
	mux.HandleFunc("/api/cmd/selftest", func(w http.ResponseWriter, r *http.Request) {
		respond(w, s.Send(crtlink.TypeSelfTest, []byte{0}))
	})

	sub, err := fsSub()
	if err != nil {
		log.Printf("页面资源加载失败：%v", err)
	} else {
		mux.Handle("/", http.FileServer(http.FS(sub)))
	}
	return mux
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_ = json.NewEncoder(w).Encode(v)
}

func respond(w http.ResponseWriter, err error) {
	if err != nil {
		w.WriteHeader(http.StatusServiceUnavailable)
		writeJSON(w, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, map[string]bool{"ok": true})
}
