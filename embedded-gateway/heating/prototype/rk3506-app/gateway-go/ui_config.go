// gatewayc ui 的配置管理(对照 nexus_server.py:版本化/状态/编译/加设备/激活)。
// 编译/校验用 gatewayc 进程内 Compile/Validate/LoadRuntimeCfg(不 shell);激活=翻 active
// 指针 + 重启核心 gatewayc(持其 pidfile)+ 启动健康门 + 回退。
package main

import (
	_ "embed"
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"syscall"
	"time"
)

//go:embed config_page.html
var configPageHTML string

type uiConfig struct {
	build, draftPath, deviceID, coreURL, gwPidfile string
	client                                         *http.Client
	lastActivate                                   obj
}

func (c *uiConfig) versionsDir() string     { return filepath.Join(c.build, "versions") }
func (c *uiConfig) activeFile() string      { return filepath.Join(c.build, "active") }
func (c *uiConfig) versionDir(n int) string { return filepath.Join(c.versionsDir(), strconv.Itoa(n)) }

func (c *uiConfig) listVersions() []int {
	ents, err := os.ReadDir(c.versionsDir())
	if err != nil {
		return nil
	}
	var vs []int
	for _, e := range ents {
		if e.IsDir() {
			if n, err := strconv.Atoi(e.Name()); err == nil {
				vs = append(vs, n)
			}
		}
	}
	sort.Ints(vs)
	return vs
}

func (c *uiConfig) nextVersion() int {
	vs := c.listVersions()
	if len(vs) == 0 {
		return 1
	}
	return vs[len(vs)-1] + 1
}

func (c *uiConfig) latestVersion() int {
	vs := c.listVersions()
	if len(vs) == 0 {
		return -1
	}
	return vs[len(vs)-1]
}

func (c *uiConfig) readActive() int {
	b, err := os.ReadFile(c.activeFile())
	if err != nil {
		return -1
	}
	n, err := strconv.Atoi(string(trimSpace(b)))
	if err != nil {
		return -1
	}
	return n
}

func (c *uiConfig) writeActive(n int) error {
	os.MkdirAll(c.build, 0o755)
	tmp := c.activeFile() + ".tmp"
	if err := os.WriteFile(tmp, []byte(strconv.Itoa(n)), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, c.activeFile())
}

func trimSpace(b []byte) []byte {
	for len(b) > 0 && (b[0] == ' ' || b[0] == '\n' || b[0] == '\r' || b[0] == '\t') {
		b = b[1:]
	}
	for len(b) > 0 {
		e := b[len(b)-1]
		if e == ' ' || e == '\n' || e == '\r' || e == '\t' {
			b = b[:len(b)-1]
		} else {
			break
		}
	}
	return b
}

// versionSummary:某版本产物摘要(对照 nexus version_summary);读不到返回 nil。
func (c *uiConfig) versionSummary(n int) obj {
	if n < 0 {
		return nil
	}
	vd := c.versionDir(n)
	pr := readJSONObj(filepath.Join(vd, "point_registry.json"))
	if pr == nil {
		return nil
	}
	pp := readJSONObj(filepath.Join(vd, "poll_plan.json"))
	dm := readJSONObj(filepath.Join(vd, "display_model.json"))
	sp := readJSONObj(filepath.Join(vd, "safety_policy.json"))
	devs := map[string]bool{}
	for _, bi := range asArr(pp["buses"]) {
		for _, ti := range asArr(asObj(bi)["tasks"]) {
			devs[asStr(asObj(ti)["device_id"])] = true
		}
	}
	cards := 0
	for _, pgi := range asArr(dm["pages"]) {
		cards += len(asArr(asObj(pgi)["cards"]))
	}
	return obj{"version": n, "config_version": getOr(pr, "config_version", nil),
		"devices": len(devs), "points": len(asObj(pr["points"])),
		"display_cards": cards, "safety_commands": len(asObj(sp["commands"]))}
}

func (c *uiConfig) status() obj {
	n := c.readActive()
	active := c.versionSummary(n)
	draft := readJSONObj(c.draftPath)
	var errCount interface{}
	if draft != nil {
		errCount = len(Validate(draft))
	}
	av := interface{}(nil)
	if n >= 0 {
		av = n
	}
	lv := interface{}(nil)
	if c.latestVersion() >= 0 {
		lv = c.latestVersion()
	}
	return obj{"active_version": av,
		"config_version": getOr(orEmpty(active), "config_version", nil),
		"devices":        getOr(orEmpty(active), "devices", 0),
		"points":         getOr(orEmpty(active), "points", 0),
		"errors":         errCount, "has_draft": draft != nil,
		"latest_version": lv, "latest_compiled": c.versionSummary(c.latestVersion())}
}

func orEmpty(o obj) obj {
	if o == nil {
		return obj{}
	}
	return o
}

// compileDraft:Validate → Compile(进程内)→ 写 versions/N/*.json + app_config.generated.json
// + 存 draft。不设 active、不热切。返回 (ok, errors, status)。
func (c *uiConfig) compileDraft(draft obj) (bool, []string, obj) {
	errs := Validate(draft)
	if len(errs) > 0 {
		return false, errs, nil
	}
	n := c.nextVersion()
	vd := c.versionDir(n)
	os.MkdirAll(vd, 0o755)
	products := Compile(draft)
	for name, p := range products {
		b, _ := json.MarshalIndent(p, "", "  ")
		os.WriteFile(filepath.Join(vd, name), append(b, '\n'), 0o644)
	}
	cfg, err := LoadRuntimeCfg(vd, c.deviceID, "sim")
	if err != nil {
		return false, []string{"loader 失败: " + err.Error()}, nil
	}
	b, _ := json.MarshalIndent(cfg, "", "  ")
	os.WriteFile(filepath.Join(vd, "app_config.generated.json"), append(b, '\n'), 0o644)
	db, _ := json.MarshalIndent(draft, "", "  ")
	os.WriteFile(c.draftPath, append(db, '\n'), 0o644)
	return true, nil, c.status()
}

// addDeviceToDraft:把 payload 的一台 hardware + 一组 business 追加到 draft 副本,校验(对照同名函数)。
func addDeviceToDraftUI(draft, payload obj) (bool, []string, obj) {
	hw := asObj(payload["hardware"])
	bizs := asArr(payload["business_devices"])
	if hw == nil {
		return false, []string{"payload.hardware 缺失或非对象"}, nil
	}
	if len(bizs) == 0 {
		return false, []string{"payload.business_devices 缺失或为空"}, nil
	}
	nd := deepCopyObj(draft)
	hwArr := asArr(nd["hardware_devices"])
	nd["hardware_devices"] = append(hwArr, hw)
	bizArr := asArr(nd["business_devices"])
	nd["business_devices"] = append(bizArr, bizs...)
	if errs := Validate(nd); len(errs) > 0 {
		return false, errs, nil
	}
	return true, nil, nd
}

func deepCopyObj(o obj) obj {
	b, _ := json.Marshal(o)
	var c obj
	json.Unmarshal(b, &c)
	return c
}

// activate:翻 active 指针 + 重启核心 + 启动健康门 + 回退(对照 remote_activate)。
func (c *uiConfig) activate(version int) (bool, []string, string) {
	if version < 0 {
		return false, []string{"无可激活版本(先 compile)"}, "failed"
	}
	prev := c.readActive()
	c.writeActive(version)
	if !c.restartCore() {
		if prev >= 0 {
			c.writeActive(prev)
		}
		return false, []string{"无法重启核心(pidfile 不可用,supervisor 在跑吗?)"}, "failed"
	}
	if c.waitCoreHealthy(30 * time.Second) {
		return true, nil, "active"
	}
	if prev >= 0 {
		c.writeActive(prev)
	} else {
		os.Remove(c.activeFile())
	}
	c.restartCore()
	c.waitCoreHealthy(30 * time.Second)
	return false, []string{"新版本健康门失败,已回退到 " + strconv.Itoa(prev)}, "rolled_back"
}

func (c *uiConfig) restartCore() bool {
	b, err := os.ReadFile(c.gwPidfile)
	if err != nil {
		return false
	}
	pid, err := strconv.Atoi(string(trimSpace(b)))
	if err != nil {
		return false
	}
	p, err := os.FindProcess(pid)
	if err != nil {
		return false
	}
	return p.Signal(syscall.SIGTERM) == nil
}

func (c *uiConfig) waitCoreHealthy(timeout time.Duration) bool {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if ok, _ := healthOnce(c.client, c.coreURL, 6000, -1); ok {
			return true
		}
		time.Sleep(time.Second)
	}
	return false
}

// registerConfigEndpoints:把 /api/config/* + /config 注册到 mux(对照 nexus 同端点)。
func registerConfigEndpoints(mux *http.ServeMux, c *uiConfig,
	authed func(*http.Request) bool, writeJSON func(http.ResponseWriter, interface{}, int)) {

	mux.HandleFunc("/config", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Write([]byte(configPageHTML))
	})
	mux.HandleFunc("/api/config/status", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, c.status(), 200)
	})
	mux.HandleFunc("/api/config/products", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, c.versionSummary(c.readActive()), 200) // active 版本摘要(无则 null)
	})
	mux.HandleFunc("/api/config/draft", func(w http.ResponseWriter, r *http.Request) {
		d := readJSONObj(c.draftPath)
		writeJSON(w, obj{"has_draft": d != nil, "draft": d}, 200)
	})
	mux.HandleFunc("/api/config/activate/status", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, c.lastActivate, 200)
	})
	mux.HandleFunc("/api/config/validate", func(w http.ResponseWriter, r *http.Request) {
		if !authed(r) {
			writeJSON(w, obj{"error": "Unauthorized"}, 401)
			return
		}
		var body obj
		json.NewDecoder(r.Body).Decode(&body)
		errs := Validate(body)
		writeJSON(w, obj{"ok": len(errs) == 0, "errors": strArr(errs)}, 200)
	})
	mux.HandleFunc("/api/config/compile", func(w http.ResponseWriter, r *http.Request) {
		if !authed(r) {
			writeJSON(w, obj{"error": "Unauthorized"}, 401)
			return
		}
		var body obj
		json.NewDecoder(r.Body).Decode(&body)
		ok, errs, st := c.compileDraft(body)
		writeJSON(w, obj{"ok": ok, "errors": strArr(errs), "status": st}, 200)
	})
	mux.HandleFunc("/api/config/devices", func(w http.ResponseWriter, r *http.Request) {
		if !authed(r) {
			writeJSON(w, obj{"error": "Unauthorized"}, 401)
			return
		}
		var body obj
		json.NewDecoder(r.Body).Decode(&body)
		base := readJSONObj(c.draftPath)
		if base == nil {
			writeJSON(w, obj{"ok": false,
				"errors": arr{"无 current_draft;请先 /api/config/compile 生成基础草稿"},
				"status": c.status()}, 400)
			return
		}
		ok, errs, nd := addDeviceToDraftUI(base, body)
		if ok {
			db, _ := json.MarshalIndent(nd, "", "  ")
			os.WriteFile(c.draftPath, append(db, '\n'), 0o644)
		}
		writeJSON(w, obj{"ok": ok, "errors": strArr(errs), "status": c.status()}, 200)
	})
	mux.HandleFunc("/api/config/activate", func(w http.ResponseWriter, r *http.Request) {
		if !authed(r) {
			writeJSON(w, obj{"error": "Unauthorized"}, 401)
			return
		}
		var body obj
		json.NewDecoder(r.Body).Decode(&body)
		version := c.latestVersion()
		if v, ok := body["version"]; ok {
			version = int(toF(v))
		}
		prev := c.readActive()
		ok, errs, state := c.activate(version)
		c.lastActivate = obj{"version": version, "state": state, "errors": strArr(errs),
			"previous_active": prev}
		writeJSON(w, obj{"ok": ok, "version": version, "state": state,
			"errors": strArr(errs), "status": c.status()}, 200)
	})
	mux.HandleFunc("/api/config/rollback", func(w http.ResponseWriter, r *http.Request) {
		if !authed(r) {
			writeJSON(w, obj{"error": "Unauthorized"}, 401)
			return
		}
		prev, _ := c.lastActivate["previous_active"].(int)
		pv, hasPrev := c.lastActivate["previous_active"]
		if !hasPrev || pv == nil {
			writeJSON(w, obj{"ok": false, "errors": arr{"无可回滚的上一版本"}}, 400)
			return
		}
		prev = int(toF(pv))
		cur := c.readActive()
		ok, errs, state := c.activate(prev)
		if ok {
			c.lastActivate = obj{"version": prev, "state": state, "errors": arr{}, "previous_active": cur}
		}
		writeJSON(w, obj{"ok": ok, "version": prev, "state": state,
			"errors": strArr(errs), "status": c.status()}, 200)
	})
}

func strArr(s []string) arr {
	a := arr{}
	for _, x := range s {
		a = append(a, x)
	}
	return a
}
