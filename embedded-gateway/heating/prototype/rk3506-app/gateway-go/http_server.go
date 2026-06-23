// 网关 daemon 的 HTTP 层（Go 移植自 app.py make_handler）：静态 HMI + REST + SSE。
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func startHTTP(rt *Runtime, ctrl *Controller, htmlDir string, port int) *http.Server {
	htmlDir, _ = filepath.Abs(filepath.Clean(htmlDir))
	mux := http.NewServeMux()

	writeJSON := func(w http.ResponseWriter, v interface{}, code int) {
		b, _ := json.Marshal(v)
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		w.WriteHeader(code)
		w.Write(b)
	}

	mux.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		view := rt.View()
		devs := asArr(view["devices"])
		offline := arr{}
		for _, di := range devs {
			d := asObj(di)
			if b, _ := d["offline"].(bool); b {
				offline = append(offline, obj{"addr": d["addr"], "name": d["name"],
					"fails": getOr(d, "fails", float64(0)), "next_retry_s": getOr(d, "next_retry_s", float64(0))})
			}
		}
		writeJSON(w, obj{"ok": true, "ts": time.Now().UnixMilli(),
			"collector_age_ms": rt.CollectorAgeMs(), "devices_total": len(devs),
			"devices_offline": len(offline), "offline": offline}, 200)
	})

	mux.HandleFunc("/api/snapshot", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, rt.View(), 200)
	})

	mux.HandleFunc("/api/stream", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("Connection", "keep-alive")
		flusher, _ := w.(http.Flusher)
		for {
			payload, _ := json.Marshal(rt.View())
			if _, err := fmt.Fprintf(w, "data: %s\n\n", payload); err != nil {
				return
			}
			if flusher != nil {
				flusher.Flush()
			}
			select {
			case <-r.Context().Done():
				return
			case <-time.After(time.Second):
			}
		}
	})

	mux.HandleFunc("/api/command", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "", 404)
			return
		}
		var body obj
		if json.NewDecoder(r.Body).Decode(&body) != nil {
			writeJSON(w, obj{"error": "bad json"}, 400)
			return
		}
		ok, reason := ctrl.Apply(asStr(body["point_id"]), body["value"], "", "hmi")
		writeJSON(w, obj{"ok": ok, "reason": reason}, 200)
	})

	mux.HandleFunc("/api/event", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "", 404)
			return
		}
		var body obj
		if json.NewDecoder(r.Body).Decode(&body) != nil {
			writeJSON(w, obj{"error": "bad json"}, 400)
			return
		}
		rt.AddEvent(body)
		writeJSON(w, obj{"ok": true}, 200)
	})

	// 静态文件（含路径逃逸防护）
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		rel := strings.TrimPrefix(r.URL.Path, "/")
		if rel == "" {
			rel = "index.html"
		}
		full := filepath.Clean(filepath.Join(htmlDir, rel))
		if !strings.HasPrefix(full, htmlDir) {
			http.Error(w, "", 404)
			return
		}
		data, err := os.ReadFile(full)
		if err != nil {
			http.Error(w, "", 404)
			return
		}
		ctype := "application/octet-stream"
		switch {
		case strings.HasSuffix(full, ".html"):
			ctype = "text/html"
		case strings.HasSuffix(full, ".json"):
			ctype = "application/json"
		case strings.HasSuffix(full, ".js"):
			ctype = "text/javascript"
		case strings.HasSuffix(full, ".css"):
			ctype = "text/css"
		}
		w.Header().Set("Content-Type", ctype+"; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		w.Write(data)
	})

	srv := &http.Server{Addr: fmt.Sprintf("0.0.0.0:%d", port), Handler: mux}
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(os.Stderr, "[HTTP] %v\n", err)
		}
	}()
	fmt.Printf("[HTTP] http://0.0.0.0:%d/  (HMI + /api/snapshot + /api/stream)\n", port)
	return srv
}
