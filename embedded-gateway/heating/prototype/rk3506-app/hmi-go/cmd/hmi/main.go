//go:build linux

// hmic:RK3506 本地 LCD 触摸仪表盘,drm_hmi_v4.py 的 Go 移植。
// 用法(与 Python 版参数兼容,新增 --config-base 消除硬编码):
//
//	hmic [port] [--products <dir>] [--config-base <url>] [--touch <dev>]
//
// port 为 gatewayc core 端口(部署态 8091,默认 8092 同 Python)。
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/api"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/app"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/drm"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/localsettings"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/templates"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/touch"
)

// parseArgs 对标 drm_hmi_v4 的手工解析:位置参数 + --flag value,顺序无关。
func parseArgs(argv []string) (pos []string, opt map[string]string) {
	opt = map[string]string{}
	for i := 0; i < len(argv); i++ {
		a := argv[i]
		if len(a) > 2 && a[:2] == "--" {
			if i+1 < len(argv) {
				opt[a[2:]] = argv[i+1]
				i++
			}
			continue
		}
		pos = append(pos, a)
	}
	return pos, opt
}

func optOr(opt map[string]string, key, def string) string {
	if v, ok := opt[key]; ok {
		return v
	}
	return def
}

func resolveProductsDir(root string) string {
	if _, err := os.Stat(filepath.Join(root, "display_model.json")); err == nil {
		return root
	}
	raw, err := os.ReadFile(filepath.Join(root, "active"))
	if err != nil {
		return root
	}
	version := strings.TrimSpace(string(raw))
	if version == "" {
		return root
	}
	return filepath.Join(root, "versions", version)
}

func main() {
	pos, opt := parseArgs(os.Args[1:])
	port := 8092
	if len(pos) > 0 {
		if p, err := strconv.Atoi(pos[0]); err == nil {
			port = p
		}
	}
	base := fmt.Sprintf("http://127.0.0.1:%d", port)
	touchDev := optOr(opt, "touch", "/dev/input/event0")
	settingsPath := optOr(opt, "settings", "/userdata/rk3506-app/data/hmi-settings.json")
	backlightPath := optOr(opt, "backlight", "/sys/class/backlight/backlight")
	templatesPath := optOr(opt, "templates", "/userdata/rk3506-app/device_templates.json")
	configBase := "http://127.0.0.1:8092"

	if products := opt["products"]; products != "" {
		products = resolveProductsDir(products)
		dmPath := products + "/display_model.json"
		if raw, err := os.ReadFile(dmPath); err == nil {
			var dm map[string]any
			dec := json.NewDecoder(bytes.NewReader(raw))
			dec.UseNumber()
			if dec.Decode(&dm) == nil {
				render.ConfigureDisplay(dm)
			}
		}
	}

	settings := localsettings.Load(settingsPath)
	appliedTheme := render.ApplyTheme(settings.Theme)
	if _, err := localsettings.ApplyBrightness(backlightPath, settings.Brightness); err != nil {
		fmt.Printf("[settings] brightness err: %v\n", err)
	}

	scr, err := drm.NewScreen()
	if err != nil {
		fmt.Printf("[drm] 初始化失败: %v\n", err)
		os.Exit(1)
	}
	client := api.NewWithConfig(base, configBase)
	st := app.NewState()
	st.SetSettings(settings)
	if tpls, err := templates.Load(templatesPath); err != nil {
		fmt.Printf("[devadd] template load err: %v\n", err)
	} else {
		st.SetTemplates(tpls)
	}
	cache := app.NewFrameCache()
	dirty := make(chan struct{}, 1)
	deps := app.Deps{
		Blit:    scr.BlitFrame,
		PostCmd: client.PostCmd,
		Cache:   cache,
		Dirty: func() {
			select {
			case dirty <- struct{}{}:
			default:
			}
		},
		Logf: func(format string, args ...any) {
			fmt.Printf(format+"\n", args...)
		},
		Config: client,
	}
	touch.Start(touchDev, func(x, y int) { st.OnTap(x, y, deps) })
	fmt.Printf("LCD go(触摸仪表盘)接管屏幕,读 %s/api/snapshot。\n", base)

	warm := []string{}
	for _, nv := range render.Nav {
		if nv.ID != "overview" {
			warm = append(warm, nv.ID)
		}
	}
	resetWarm := func(exclude string) {
		warm = warm[:0]
		for _, nv := range render.Nav {
			if nv.ID != exclude {
				warm = append(warm, nv.ID)
			}
		}
	}
	for {
		if next, changed := st.ConsumeSettings(); changed {
			themeChanged := next.Theme != appliedTheme
			if themeChanged {
				appliedTheme = render.ApplyTheme(next.Theme)
				pages := []string{}
				for _, nv := range render.Nav {
					pages = append(pages, nv.ID)
				}
				cache.Invalidate(pages...)
				_, page, _, _, _, _ := st.RenderInputs()
				resetWarm(page)
			} else {
				cache.Invalidate("settings")
			}
			if _, err := localsettings.ApplyBrightness(backlightPath, next.Brightness); err != nil {
				fmt.Printf("[settings] brightness err: %v\n", err)
			}
			if err := localsettings.Save(settingsPath, next); err != nil {
				fmt.Printf("[settings] save err: %v\n", err)
			}
		}
		view, err := client.FetchSnapshot()
		if err != nil {
			view = &render.View{Events: []render.Event{{Detail: "正在连接后端…"}}}
		}
		st.SetView(view)
		clock := "--:--:--"
		if time.Now().UTC().Year() >= 2020 {
			clock = time.Now().Format("15:04:05")
		}
		vw, renderPage, targets, addForm, addMessage, addBusy := st.RenderInputs()
		fb, buttons := render.Render(vw, clock, targets, renderPage,
			addForm, addMessage, addBusy)
		frame := drm.PrepareRGB(fb.Buf)
		cache.Put(renderPage, frame, buttons)
		// 渲染期间可能被 tap 切页:旧帧绝不覆盖新选中的页(对标 L329-333)
		st.CommitIfCurrent(renderPage, buttons, func() { scr.BlitFrame(frame) })

		// 后端有数据后每轮预热一页,尽快铺满 5 页缓存(对标 L335-350)
		if len(warm) > 0 && len(vw.Devices) > 0 {
			wp := warm[0]
			warm = warm[1:]
			wfb, wbtns := render.Render(vw, clock, targets, wp, nil, "", false)
			wframe := drm.PrepareRGB(wfb.Buf)
			cache.Put(wp, wframe, wbtns)
			st.CommitIfCurrent(wp, wbtns, func() { scr.BlitFrame(wframe) })
			continue
		}
		select { // 1Hz 刷新,触摸即时重绘
		case <-dirty:
		case <-time.After(time.Second):
		}
	}
}
