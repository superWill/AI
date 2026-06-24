// gatewayc ui —— edge-os 前端适配(Go,替 nexus_server.py)。消费 gatewayc 核心(取快照、
// 转发控制),服务 edge-os REST + 登录 + 静态。socket.io 见增量3,配置 UI 见增量4。
package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

func runUI(args []string) {
	fs := flag.NewFlagSet("ui", flag.ExitOnError)
	coreURL := fs.String("core-url", "http://127.0.0.1:8091", "gatewayc 核心基址")
	port := fs.Int("port", 8092, "edge-os UI 端口")
	productsDir := fs.String("products", "", "编译产物目录(派生 tag 名/类型/分组)")
	distDir := fs.String("dist", "nexus-dist", "edge-os 前端 dist 目录")
	endpoint := fs.String("endpoint", "sim", "node.endpoint 标签")
	controlToken := fs.String("control-token", "", "转发控制到核心的 X-Control-Token(默认 env GATEWAYC_CONTROL_TOKEN)")
	fs.Parse(args)
	if *controlToken == "" {
		*controlToken = os.Getenv("GATEWAYC_CONTROL_TOKEN")
	}

	var pr, dm obj
	if *productsDir != "" {
		pr = readJSONObj(filepath.Join(*productsDir, "point_registry.json"))
		dm = readJSONObj(filepath.Join(*productsDir, "display_model.json"))
	}
	maps := configureMapsUI(pr, dm)
	core := strings.TrimRight(*coreURL, "/")
	client := &http.Client{Timeout: 3 * time.Second}
	var tokens sync.Map

	coreView := func() (obj, error) {
		resp, err := client.Get(core + "/api/snapshot")
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()
		var v obj
		if err := json.NewDecoder(resp.Body).Decode(&v); err != nil {
			return nil, err
		}
		return v, nil
	}
	// 转发控制到核心 /api/command(带 token),返回核心的 {ok,reason} 原文。
	coreCommand := func(pointID string, value interface{}) (obj, error) {
		b, _ := json.Marshal(obj{"point_id": pointID, "value": value})
		req, _ := http.NewRequest("POST", core+"/api/command", strings.NewReader(string(b)))
		req.Header.Set("Content-Type", "application/json")
		if *controlToken != "" {
			req.Header.Set("X-Control-Token", *controlToken)
		}
		resp, err := client.Do(req)
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()
		var o obj
		json.NewDecoder(resp.Body).Decode(&o)
		return o, nil
	}

	mux := http.NewServeMux()
	writeJSON := func(w http.ResponseWriter, v interface{}, code int) {
		b, _ := json.Marshal(v)
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(code)
		w.Write(b)
	}
	authed := func(r *http.Request) bool {
		a := r.Header.Get("Authorization")
		return strings.HasPrefix(a, "Bearer ") && len(a) > 8
	}

	mux.HandleFunc("/api/me", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, obj{"username": "admin", "role": "admin"}, 200)
	})
	mux.HandleFunc("/api/login", func(w http.ResponseWriter, r *http.Request) {
		var body obj
		json.NewDecoder(r.Body).Decode(&body)
		buf := make([]byte, 16)
		rand.Read(buf)
		tok := hex.EncodeToString(buf)
		tokens.Store(tok, true)
		writeJSON(w, obj{"token": tok, "user": obj{"username": asStrOr(body["username"], "admin")}}, 200)
	})
	mux.HandleFunc("/api/init", func(w http.ResponseWriter, r *http.Request) {
		if !authed(r) {
			writeJSON(w, obj{"error": "Unauthorized"}, 401)
			return
		}
		v, err := coreView()
		if err != nil {
			writeJSON(w, obj{"error": "core unavailable"}, 502)
			return
		}
		nodes, tags := buildNodesTagsUI(v, *endpoint, maps)
		writeJSON(w, obj{"nodes": nodes, "tags": tags, "apps": arr{}, "rules": arr{}}, 200)
	})
	mux.HandleFunc("/api/snapshot", func(w http.ResponseWriter, r *http.Request) { // 给本地 LCD
		resp, err := client.Get(core + "/api/snapshot")
		if err != nil {
			writeJSON(w, obj{"error": "core unavailable"}, 502)
			return
		}
		defer resp.Body.Close()
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		io.Copy(w, resp.Body)
	})
	mux.HandleFunc("/api/command", func(w http.ResponseWriter, r *http.Request) { // 本地触摸屏
		var body obj
		json.NewDecoder(r.Body).Decode(&body)
		o, err := coreCommand(asStr(body["point_id"]), body["value"])
		if err != nil {
			writeJSON(w, obj{"ok": false, "reason": "core unavailable"}, 200)
			return
		}
		writeJSON(w, o, 200)
	})
	mux.HandleFunc("/api/tags/write", func(w http.ResponseWriter, r *http.Request) {
		var body obj
		json.NewDecoder(r.Body).Decode(&body)
		ok, errMsg := writeTagUI(asStr(body["tagId"]), body["value"], maps, coreCommand)
		if !ok {
			writeJSON(w, obj{"ok": false, "error": errMsg}, 200)
			return
		}
		writeJSON(w, obj{"ok": true}, 200)
	})
	mux.HandleFunc("/api/scada", func(w http.ResponseWriter, r *http.Request) { writeJSON(w, arr{}, 200) })
	mux.HandleFunc("/api/history", func(w http.ResponseWriter, r *http.Request) { writeJSON(w, arr{}, 200) })

	// 静态 edge-os dist(SPA:未命中文件回退 index.html)。socket.io/config/api-config 见后续增量。
	dist, _ := filepath.Abs(filepath.Clean(*distDir))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		rel := strings.TrimPrefix(r.URL.Path, "/")
		if rel == "" {
			rel = "index.html"
		}
		full := filepath.Clean(filepath.Join(dist, rel))
		if !strings.HasPrefix(full, dist) {
			http.Error(w, "", 404)
			return
		}
		if _, err := os.Stat(full); err != nil {
			full = filepath.Join(dist, "index.html") // SPA 回退
		}
		http.ServeFile(w, r, full)
	})

	fmt.Printf("[ui] edge-os UI 在 :%d,核心 %s,产物 %s\n", *port, core, map[bool]string{true: *productsDir, false: "默认映射"}[*productsDir != ""])
	if err := http.ListenAndServe(fmt.Sprintf("0.0.0.0:%d", *port), mux); err != nil {
		fmt.Fprintf(os.Stderr, "[ui] %v\n", err)
		os.Exit(1)
	}
}

// writeTagUI: tag-<addr>-<pid> → pid → 设定值点 → 转发核心 /api/command(对照 _write_tag)。
func writeTagUI(tagID string, value interface{}, m *uiMaps, coreCommand func(string, interface{}) (obj, error)) (bool, string) {
	parts := strings.SplitN(tagID, "-", 3)
	if len(parts) != 3 {
		return false, "bad tagId"
	}
	pid := parts[2]
	sp, ok := m.controllable[pid]
	if !ok {
		return false, "该点位不可写"
	}
	o, err := coreCommand(sp, value)
	if err != nil {
		return false, "core unavailable"
	}
	if b, _ := o["ok"].(bool); !b {
		return false, asStr(o["reason"])
	}
	return true, ""
}

func asStrOr(v interface{}, def string) string {
	if s, ok := v.(string); ok && s != "" {
		return s
	}
	return def
}
