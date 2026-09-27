//go:build linux

// Package touch:Goodix 触摸读线程,对标 drm_hmi_v4.Touch。
// 32 位 ARM input_event 固定 16 字节("<IIHHi"),坐标与 800x480 1:1 无变换,
// BTN_TOUCH 松手(value=0)即一次 tap。
package touch

import (
	"encoding/binary"
	"fmt"
	"os"
)

const (
	evKey    = 1
	evAbs    = 3
	btnTouch = 0x14A
)

// Start 启动读线程;设备打不开只打日志退出(同 Python)。
func Start(dev string, onTap func(x, y int)) {
	go func() {
		f, err := os.Open(dev)
		if err != nil {
			fmt.Printf("[touch] 打不开 %s: %v\n", dev, err)
			return
		}
		defer f.Close()
		le := binary.LittleEndian
		buf := make([]byte, 16)
		x, y := 0, 0
		for {
			n, err := f.Read(buf)
			if err != nil {
				fmt.Printf("[touch] 读失败: %v\n", err)
				return
			}
			if n < 16 {
				continue
			}
			typ := le.Uint16(buf[8:])
			code := le.Uint16(buf[10:])
			val := int32(le.Uint32(buf[12:]))
			switch {
			case typ == evAbs && (code == 0x00 || code == 0x35): // ABS_X / ABS_MT_POSITION_X
				x = int(val)
			case typ == evAbs && (code == 0x01 || code == 0x36):
				y = int(val)
			case typ == evKey && code == btnTouch && val == 0:
				func() {
					defer func() {
						if r := recover(); r != nil {
							fmt.Printf("[touch] on_tap err: %v\n", r)
						}
					}()
					onTap(x, y)
				}()
			}
		}
	}()
}
