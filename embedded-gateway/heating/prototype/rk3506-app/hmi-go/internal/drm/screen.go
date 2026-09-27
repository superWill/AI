//go:build linux

// Package drm:DRM dumb buffer 直写屏幕,逐 ioctl 对标 drm_hmi_v4.Screen。
// 封送策略:不用 Go struct 直映内核结构,全部像 Python struct.pack 一样
// 显式小端打包进定长 []byte,绕开 32 位 ARM 上 uint64 对齐的不确定性。
package drm

import (
	"encoding/binary"
	"fmt"
	"runtime"
	"sync"
	"unsafe"

	"golang.org/x/sys/unix"
)

const (
	drmSetMaster  = 0x641E
	drmCreateDumb = 0xC02064B2 // size 0x20=32
	drmMapDumb    = 0xC01064B3 // size 0x10=16
	drmAddFB      = 0xC01C64AE // size 0x1C=28
	drmSetCRTC    = 0xC06864A2 // size 0x68=104

	W, H = 800, 480
	// 板级实测 connector/crtc id(drm_hmi_v4.py L43),换屏/换板需重测
	conn = 75
	crtc = 72
)

var le = binary.LittleEndian

// mode 对标 MODE = struct.pack("<IHHHHHHHHHHIII32s", ...):
// 30000kHz, h 800/806/811/816/skew0, v 480/485/493/503/scan0,
// vrefresh 73, flags 0x0A, type 0x48, name "800x480"。
func modeBytes() []byte {
	b := make([]byte, 68)
	le.PutUint32(b[0:], 30000)
	for i, v := range []uint16{800, 806, 811, 816, 0, 480, 485, 493, 503, 0} {
		le.PutUint16(b[4+i*2:], v)
	}
	le.PutUint32(b[24:], 73)
	le.PutUint32(b[28:], 0x0A)
	le.PutUint32(b[32:], 0x48)
	copy(b[36:], "800x480")
	return b
}

func ioctl(fd int, req uint, arg unsafe.Pointer) error {
	_, _, errno := unix.Syscall(unix.SYS_IOCTL, uintptr(fd), uintptr(req), uintptr(arg))
	if errno != 0 {
		return errno
	}
	return nil
}

// 编译期长度断言:pack 缓冲长度必须等于 ioctl 编码中的 size 位。
func ioctlSize(req uint) int { return int((req >> 16) & 0x3FFF) }

type Screen struct {
	mu      sync.Mutex
	fd      int
	handle  uint32
	pitch   uint32
	size    uint64
	fbID    uint32
	mm      []byte
	connBuf *[4]byte // SETCRTC 里被内核经指针读取,必须终身持有
}

func NewScreen() (*Screen, error) {
	fd, err := unix.Open("/dev/dri/card0", unix.O_RDWR, 0)
	if err != nil {
		return nil, fmt.Errorf("open /dev/dri/card0: %w", err)
	}
	s := &Screen{fd: fd}

	// SET_MASTER(失败吞掉,同 Python try/except)
	_ = ioctl(fd, drmSetMaster, nil)

	// CREATE_DUMB "<IIIIIIQ": height,width,bpp,flags,handle,pitch,size(u64)
	cd := make([]byte, ioctlSize(drmCreateDumb)) // 32
	le.PutUint32(cd[0:], H)
	le.PutUint32(cd[4:], W)
	le.PutUint32(cd[8:], 32)
	if err := ioctl(fd, drmCreateDumb, unsafe.Pointer(&cd[0])); err != nil {
		return nil, fmt.Errorf("CREATE_DUMB: %w", err)
	}
	s.handle = le.Uint32(cd[16:])
	s.pitch = le.Uint32(cd[20:])
	s.size = le.Uint64(cd[24:])

	// ADDFB "<IIIIIII": fb_id,width,height,pitch,bpp=32,depth=24,handle
	fb := make([]byte, ioctlSize(drmAddFB)) // 28
	le.PutUint32(fb[4:], W)
	le.PutUint32(fb[8:], H)
	le.PutUint32(fb[12:], s.pitch)
	le.PutUint32(fb[16:], 32)
	le.PutUint32(fb[20:], 24)
	le.PutUint32(fb[24:], s.handle)
	if err := ioctl(fd, drmAddFB, unsafe.Pointer(&fb[0])); err != nil {
		return nil, fmt.Errorf("ADDFB: %w", err)
	}
	s.fbID = le.Uint32(fb[0:])

	// MAP_DUMB "<IIQ": handle,pad,offset(u64)
	md := make([]byte, ioctlSize(drmMapDumb)) // 16
	le.PutUint32(md[0:], s.handle)
	if err := ioctl(fd, drmMapDumb, unsafe.Pointer(&md[0])); err != nil {
		return nil, fmt.Errorf("MAP_DUMB: %w", err)
	}
	offset := le.Uint64(md[8:])

	s.mm, err = unix.Mmap(fd, int64(offset), int(s.size),
		unix.PROT_READ|unix.PROT_WRITE, unix.MAP_SHARED)
	if err != nil {
		return nil, fmt.Errorf("mmap: %w", err)
	}

	// SETCRTC "<QIIIIIII"+MODE: set_connectors_ptr 指向 4 字节 connector id 缓冲,
	// 内核经该用户态指针读取 → connBuf 存进 Screen 终身持有 + KeepAlive 双保险。
	s.connBuf = new([4]byte)
	le.PutUint32(s.connBuf[:], conn)
	sc := make([]byte, ioctlSize(drmSetCRTC)) // 104
	le.PutUint64(sc[0:], uint64(uintptr(unsafe.Pointer(s.connBuf))))
	le.PutUint32(sc[8:], 1) // count_connectors
	le.PutUint32(sc[12:], crtc)
	le.PutUint32(sc[16:], s.fbID)
	// x=0 y=0 gamma_size=0
	le.PutUint32(sc[32:], 1) // mode_valid
	copy(sc[36:], modeBytes())
	if err := ioctl(fd, drmSetCRTC, unsafe.Pointer(&sc[0])); err != nil {
		return nil, fmt.Errorf("SETCRTC: %w", err)
	}
	runtime.KeepAlive(s.connBuf)
	return s, nil
}

// PrepareRGB 对标 Screen.prepare_rgb:RGB888 → BGRX8888,缓存页一次 mmap 拷贝可显示。
func PrepareRGB(rgb []byte) []byte {
	out := make([]byte, W*H*4)
	for i, j := 0, 0; i < len(rgb); i, j = i+3, j+4 {
		out[j] = rgb[i+2]
		out[j+1] = rgb[i+1]
		out[j+2] = rgb[i]
	}
	return out
}

// BlitFrame 对标 Screen.blit_frame:pitch 匹配则整块拷贝,否则逐行。
func (s *Screen) BlitFrame(frame []byte) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.pitch == W*4 {
		copy(s.mm[:W*H*4], frame)
		return
	}
	for y := 0; y < H; y++ {
		copy(s.mm[y*int(s.pitch):y*int(s.pitch)+W*4], frame[y*W*4:(y+1)*W*4])
	}
}
