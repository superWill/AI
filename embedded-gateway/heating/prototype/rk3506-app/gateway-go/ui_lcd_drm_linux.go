//go:build linux

// RK3506 本地第一屏(LCD)—— DRM dumb buffer 直写 + Goodix 触摸 + 主循环。
// Go 移植自 drm_hmi_v4.py。仅板上(linux):DRM/evdev ioctl 与屏幕 1:1。
// 渲染逻辑见 ui_lcd_fb.go / ui_lcd_pages.go(已逐像素对拍 dashboard.py)。
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"runtime"
	"sync"
	"syscall"
	"time"
	"unsafe"

	"golang.org/x/sys/unix"
)

// DRM ioctl 号(板上 ioctl 实测,对照 drm_hmi_v4.py)。drmConn/drmCRTC 见 ui_lcd_drm_pack.go。
const (
	drmSetMaster  = 0x641E
	drmCreateDumb = 0xC02064B2
	drmMapDumb    = 0xC01064B3
	drmAddFB      = 0xC01C64AE
	drmSetCRTC    = 0xC06864A2
	touchDev      = "/dev/input/event0"
)

func drmIoctl(fd int, req uintptr, arg unsafe.Pointer) error {
	_, _, errno := syscall.Syscall(syscall.SYS_IOCTL, uintptr(fd), req, uintptr(arg))
	if errno != 0 {
		return errno
	}
	return nil
}

type screen struct {
	fd      int
	pitch   int
	size    uint64
	mm      []byte
	scratch []byte // W*H*4 BGRX 暂存
}

func openScreen() (*screen, error) {
	fd, err := unix.Open("/dev/dri/card0", unix.O_RDWR, 0)
	if err != nil {
		return nil, fmt.Errorf("打开 /dev/dri/card0 失败: %w", err)
	}
	_ = drmIoctl(fd, drmSetMaster, unsafe.Pointer(nil)) // 失败可忽略(对照 py except OSError)

	le := binary.LittleEndian
	cd := packCreateDumb() // <IIIIIIQ> height,width,bpp,flags,handle,pitch,size
	if err := drmIoctl(fd, drmCreateDumb, unsafe.Pointer(&cd[0])); err != nil {
		unix.Close(fd)
		return nil, fmt.Errorf("CREATE_DUMB: %w", err)
	}
	handle := le.Uint32(cd[16:])
	pitch := le.Uint32(cd[20:])
	size := le.Uint64(cd[24:])

	af := packAddFB(pitch, handle) // <IIIIIII> fb_id,width,height,pitch,bpp,depth,handle
	if err := drmIoctl(fd, drmAddFB, unsafe.Pointer(&af[0])); err != nil {
		unix.Close(fd)
		return nil, fmt.Errorf("ADDFB: %w", err)
	}
	fbID := le.Uint32(af[0:])

	md := packMapDumb(handle) // <IIQ> handle,pad,offset
	if err := drmIoctl(fd, drmMapDumb, unsafe.Pointer(&md[0])); err != nil {
		unix.Close(fd)
		return nil, fmt.Errorf("MAP_DUMB: %w", err)
	}
	offset := le.Uint64(md[8:])

	mm, err := unix.Mmap(fd, int64(offset), int(size),
		unix.PROT_READ|unix.PROT_WRITE, unix.MAP_SHARED)
	if err != nil {
		unix.Close(fd)
		return nil, fmt.Errorf("mmap: %w", err)
	}

	// SETCRTC: <QIIIIIII> set_connectors_ptr,count,crtc_id,fb_id,x,y,gamma,mode_valid + modeinfo
	conn := []uint32{drmConn}
	crtc := packSetCRTC(uint64(uintptr(unsafe.Pointer(&conn[0]))), fbID)
	err = drmIoctl(fd, drmSetCRTC, unsafe.Pointer(&crtc[0]))
	runtime.KeepAlive(conn)
	if err != nil {
		unix.Close(fd)
		return nil, fmt.Errorf("SETCRTC: %w", err)
	}
	return &screen{fd: fd, pitch: int(pitch), size: size, mm: mm,
		scratch: make([]byte, lcdW*lcdH*4)}, nil
}

// blit: RGB(W*H*3) → BGRX(W*H*4) 写入 mmap(对照 py blit_rgb)。
func (s *screen) blit(rgbBuf []byte) {
	n := lcdW * lcdH
	out := s.scratch
	for i := 0; i < n; i++ {
		out[i*4] = rgbBuf[i*3+2]   // B
		out[i*4+1] = rgbBuf[i*3+1] // G
		out[i*4+2] = rgbBuf[i*3]   // R
		out[i*4+3] = 0             // X
	}
	if s.pitch == lcdW*4 {
		copy(s.mm[:n*4], out)
		return
	}
	for y := 0; y < lcdH; y++ {
		copy(s.mm[y*s.pitch:y*s.pitch+lcdW*4], out[y*lcdW*4:(y+1)*lcdW*4])
	}
}

// touchLoop: 读 Goodix 触摸,松手即一次 tap → onTap(x,y)(对照 py Touch 线程)。
func touchLoop(onTap func(x, y int)) {
	fd, err := unix.Open(touchDev, unix.O_RDONLY, 0)
	if err != nil {
		fmt.Printf("[touch] 打不开 %s: %v\n", touchDev, err)
		return
	}
	const evKey, evAbs, btnTouch = 1, 3, 0x14A
	buf := make([]byte, 16)
	x, y := 0, 0
	le := binary.LittleEndian
	for {
		nr, err := unix.Read(fd, buf)
		if err != nil || nr < 16 {
			continue
		}
		typ := le.Uint16(buf[8:])
		code := le.Uint16(buf[10:])
		val := int32(le.Uint32(buf[12:]))
		switch {
		case typ == evAbs && (code == 0x00 || code == 0x35):
			x = int(val)
		case typ == evAbs && (code == 0x01 || code == 0x36):
			y = int(val)
		case typ == evKey && code == btnTouch && val == 0:
			onTap(x, y)
		}
	}
}

// runLCDMain: gatewayc lcd —— 接管屏幕,1Hz 拉 /api/snapshot 渲染 + 触摸控制下发。
//
//	gatewayc lcd [--port 8092] [--products build] [--control-token TOK]
func runLCDMain(args []string) {
	fs := flag.NewFlagSet("lcd", flag.ExitOnError)
	port := fs.Int("port", 8092, "后端 UI 端口")
	products := fs.String("products", "", "编译产物目录(监控页 display_model 分组)")
	tokFlag := fs.String("control-token", "", "控制 token(缺省取环境变量)")
	fs.Parse(args)

	base := fmt.Sprintf("http://127.0.0.1:%d", *port)
	token := *tokFlag
	if token == "" {
		token = os.Getenv("GATEWAYC_CONTROL_TOKEN")
	}
	if *products != "" {
		if raw, err := os.ReadFile(*products + "/display_model.json"); err == nil {
			var dm obj
			if json.Unmarshal(raw, &dm) == nil {
				configureDisplayUI(dm)
				fmt.Printf("[显示] 监控页按 %s/display_model.json 分组(%d 卡片)\n", *products, len(displayCards))
			}
		}
	}

	scr, err := openScreen()
	if err != nil {
		fmt.Fprintf(os.Stderr, "[LCD] 接管屏幕失败: %v\n", err)
		os.Exit(1)
	}

	client := &http.Client{Timeout: 3 * time.Second}
	var mu sync.Mutex
	targets := obj{}
	page := "overview"
	var buttons []obj
	var view obj
	dirty := make(chan struct{}, 1)
	wake := func() {
		select {
		case dirty <- struct{}{}:
		default:
		}
	}

	postCmd := func(pointID string, value float64) {
		body, _ := json.Marshal(obj{"point_id": pointID, "value": value})
		req, _ := http.NewRequest("POST", base+"/api/command", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		if token != "" {
			req.Header.Set("X-Control-Token", token)
		}
		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("[ctl] post err: %v\n", err)
			return
		}
		resp.Body.Close()
	}

	onTap := func(x, y int) {
		mu.Lock()
		defer mu.Unlock()
		for _, b := range buttons {
			r := asArr(b["rect"])
			if len(r) < 4 {
				continue
			}
			bx, by, bw, bh := int(toF(r[0])), int(toF(r[1])), int(toF(r[2])), int(toF(r[3]))
			if x < bx-8 || x > bx+bw+8 || y < by-8 || y > by+bh+8 {
				continue
			}
			if nav := asStr(b["nav"]); nav != "" {
				page = nav
				fmt.Printf("[nav] → %s\n", nav)
				wake()
				return
			}
			fbid := asStr(b["fb"])
			var basev float64
			if t, ok := targets[fbid]; ok && t != nil {
				basev = toF(t)
			} else if cur := lcdPick(view, fbid); cur != nil {
				cv, _ := pythonFloat(cur)
				basev = pyRound(cv, 0)
			} else {
				basev = toF(b["lo"])
			}
			lo, hi := toF(b["lo"]), toF(b["hi"])
			newv := basev + toF(b["delta"])
			if newv < lo {
				newv = lo
			} else if newv > hi {
				newv = hi
			}
			targets[fbid] = newv
			sp := asStr(b["sp"])
			fmt.Printf("[ctl] tap → %s = %v\n", sp, newv)
			postCmd(sp, newv)
			wake()
			return
		}
	}

	go touchLoop(onTap)
	fmt.Printf("LCD(Go 触摸仪表盘)接管屏幕,读 %s/api/snapshot。\n", base)

	for {
		var snap obj
		resp, err := client.Get(base + "/api/snapshot")
		if err == nil {
			json.NewDecoder(resp.Body).Decode(&snap)
			resp.Body.Close()
		}
		if snap == nil {
			snap = obj{"devices": arr{}, "events": arr{obj{"detail": "正在连接后端…"}}}
		}
		clock := "--:--:--"
		now := time.Now()
		if now.Year() >= 2020 {
			clock = now.Format("15:04:05")
		}
		mu.Lock()
		view = snap
		f, btns := lcdRender(view, clock, targets, page)
		buttons = btns
		mu.Unlock()
		scr.blit(f.buf)
		select {
		case <-dirty:
		case <-time.After(time.Second):
		}
	}
}
