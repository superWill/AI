// DRM ioctl 缓冲区打包(纯字节,无 syscall),与平台无关,便于在主机上逐字节
// 对拍 Python drm_hmi_v4.py 的 struct.pack。screen 直写见 ui_lcd_drm_linux.go。
package main

import (
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"os"
)

// 屏幕固定参数(对照 drm_hmi_v4.py CONN/CRTC)。
const (
	drmConn = 75
	drmCRTC = 72
)

// modeInfo: drm_mode_modeinfo,对照 MODE = struct.pack("<IHHHHHHHHHHIII32s", ...)。68 字节。
func modeInfo() []byte {
	b := make([]byte, 68)
	le := binary.LittleEndian
	le.PutUint32(b[0:], 30000) // clock
	for i, v := range []uint16{800, 806, 811, 816, 0, 480, 485, 493, 503, 0} {
		le.PutUint16(b[4+i*2:], v) // hdisplay..vscan
	}
	le.PutUint32(b[24:], 73)   // vrefresh
	le.PutUint32(b[28:], 0x0A) // flags
	le.PutUint32(b[32:], 0x48) // type
	copy(b[36:], []byte("800x480"))
	return b
}

// packCreateDumb: drm_mode_create_dumb 输入,对照 struct.pack("<IIIIIIQ", H, W, 32, 0,0,0,0)。
func packCreateDumb() []byte {
	b := make([]byte, 32)
	le := binary.LittleEndian
	le.PutUint32(b[0:], lcdH)
	le.PutUint32(b[4:], lcdW)
	le.PutUint32(b[8:], 32)
	return b
}

// packAddFB: drm_mode_fb_cmd,对照 struct.pack("<IIIIIII", 0, W, H, pitch, 32, 24, handle)。
func packAddFB(pitch, handle uint32) []byte {
	b := make([]byte, 28)
	le := binary.LittleEndian
	le.PutUint32(b[4:], lcdW)
	le.PutUint32(b[8:], lcdH)
	le.PutUint32(b[12:], pitch)
	le.PutUint32(b[16:], 32)
	le.PutUint32(b[20:], 24)
	le.PutUint32(b[24:], handle)
	return b
}

// packMapDumb: drm_mode_map_dumb,对照 struct.pack("<IIQ", handle, 0, 0)。
func packMapDumb(handle uint32) []byte {
	b := make([]byte, 16)
	binary.LittleEndian.PutUint32(b[0:], handle)
	return b
}

// packSetCRTC: drm_mode_crtc + modeinfo,对照
// struct.pack("<QIIIIIII", connPtr, 1, CRTC, fb_id, 0,0,0,1) + MODE。
func packSetCRTC(connPtr uint64, fbID uint32) []byte {
	b := make([]byte, 36)
	le := binary.LittleEndian
	le.PutUint64(b[0:], connPtr)
	le.PutUint32(b[8:], 1) // count_connectors
	le.PutUint32(b[12:], drmCRTC)
	le.PutUint32(b[16:], fbID)
	le.PutUint32(b[32:], 1) // mode_valid
	return append(b, modeInfo()...)
}

// runLCDDRMPack: 用固定占位输入 dump 四个 DRM ioctl 缓冲 hex,供 Python struct.pack 逐字节对拍。
//
//	gatewayc lcddrmpack
func runLCDDRMPack(args []string) {
	out := obj{
		"mode":        hex.EncodeToString(modeInfo()),
		"create_dumb": hex.EncodeToString(packCreateDumb()),
		"addfb":       hex.EncodeToString(packAddFB(3200, 7)),
		"map_dumb":    hex.EncodeToString(packMapDumb(7)),
		"setcrtc":     hex.EncodeToString(packSetCRTC(0, 42)),
	}
	for _, k := range []string{"mode", "create_dumb", "addfb", "map_dumb", "setcrtc"} {
		fmt.Fprintf(os.Stdout, "%s\t%s\n", k, out[k])
	}
}
