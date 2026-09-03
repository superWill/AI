// Package crtlink 实现主机 ↔ 消防控制室图形显示装置（CRT）之间的链路协议。
//
// 帧格式依据 fire-alarm/docs/protocols/crt-link-draft.md：
//
//	SOF(1) VER(1) SEQ(2) SRC(2) DST(2) TYPE(1) LEN(2) DATA(0..1024) CRC(2)
//
// 多字节字段一律小端（与 GB 4717 附录 C 的"CRC 低字节在前"一致）。
// CRC-16/MODBUS（多项式 0xA001 反射、初值 0xFFFF），覆盖 SOF..DATA。
//
// 转义范围与草案的差异（须与固件侧确认后回写草案）：草案原文写"0x7E 在 DATA
// 中转义"，但 SEQ/LEN/CRC 同样可能取到 0x7E——若只转义 DATA，一个 SEQ=0x007E
// 的帧会在接收端被当成新帧起始，链路直接错位。因此本实现对 SOF 之后的全部
// 字节（帧头+DATA+CRC）转义，SOF 成为流中唯一的 0x7E，重同步才有确定语义。
package crtlink

import (
	"bufio"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
)

const (
	SOF     = 0x7E // 帧起始，转义后流中唯一
	escByte = 0x7D // 转义引导字节
	escMask = 0x20 // 被转义字节与该掩码异或

	Version = 0x01 // 当前协议版本（草案 VER 字段）

	headerLen  = 10   // SOF 之后的帧头：VER SEQ SRC DST TYPE LEN
	MaxDataLen = 1024 // 草案规定 DATA 上限
)

// 地址（草案 Physical/Frame 章节）。
const (
	AddrHost = 0x0001 // 火灾报警控制器主机
	AddrCRT  = 0x0080 // 图形显示装置
)

// 帧类型。主机 → CRT 为上行，CRT → 主机为下行。
const (
	TypeHeartbeat  = 0x01 // 心跳：时间戳 + 主备电状态
	TypeACK        = 0x02 // 确认
	TypeAlarm      = 0x10 // 火警
	TypeAction     = 0x11 // 启动（联动动作）
	TypeFeedback   = 0x12 // 反馈
	TypeFault      = 0x13 // 故障
	TypeShield     = 0x14 // 屏蔽
	TypeSupervisor = 0x15 // 监管
	TypeReset      = 0x16 // 复位
	TypePowerEvent = 0x17 // 电源事件

	TypeListDevices = 0x20 // 下行：查询设备列表
	TypeReadState   = 0x21 // 下行：查询单点状态
	TypeSelfTest    = 0x22 // 下行：自检
	TypeCmdReset    = 0x23 // 下行：复位（需密码）
	TypeManualStart = 0x24 // 下行：手动启动（需密码+钥匙）
	TypeManualStop  = 0x25 // 下行：手动停止（需密码+钥匙）
	TypeCmdShield   = 0x26 // 下行：屏蔽（需密码）
	TypeTimeSync    = 0x27 // 下行：授时（GB 4717 5.4.10.3）

	TypeListDevicesResp = 0x80
	TypeReadStateResp   = 0x81
	TypeSelfTestResp    = 0x82
)

// ACK 状态码（草案 CRT → 主机 0x02）。
const (
	ACKOK          = 0
	ACKCRCError    = 1
	ACKAuthError   = 2
	ACKUnknownType = 3
)

var (
	ErrCRC       = errors.New("crtlink: CRC 校验失败")
	ErrTooLong   = errors.New("crtlink: DATA 超过 1024 字节")
	ErrTruncated = errors.New("crtlink: 帧不完整")
)

// Frame 是一个完整的应用帧。
type Frame struct {
	Ver  uint8
	Seq  uint16
	Src  uint16
	Dst  uint16
	Type uint8
	Data []byte
}

// TypeName 返回帧类型的中文名，用于日志与页面展示。
func TypeName(t uint8) string {
	switch t {
	case TypeHeartbeat:
		return "心跳"
	case TypeACK:
		return "确认"
	case TypeAlarm:
		return "火警"
	case TypeAction:
		return "启动"
	case TypeFeedback:
		return "反馈"
	case TypeFault:
		return "故障"
	case TypeShield:
		return "屏蔽"
	case TypeSupervisor:
		return "监管"
	case TypeReset:
		return "复位"
	case TypePowerEvent:
		return "电源事件"
	case TypeListDevices:
		return "查询设备列表"
	case TypeReadState:
		return "查询单点状态"
	case TypeSelfTest:
		return "自检"
	case TypeCmdReset:
		return "复位命令"
	case TypeManualStart:
		return "手动启动"
	case TypeManualStop:
		return "手动停止"
	case TypeCmdShield:
		return "屏蔽命令"
	case TypeTimeSync:
		return "授时"
	case TypeListDevicesResp:
		return "设备列表响应"
	case TypeReadStateResp:
		return "单点状态响应"
	case TypeSelfTestResp:
		return "自检响应"
	}
	return fmt.Sprintf("未知(0x%02X)", t)
}

// crc16Modbus 计算 CRC-16/MODBUS：多项式 0xA001（反射）、初值 0xFFFF。
func crc16Modbus(b []byte) uint16 {
	crc := uint16(0xFFFF)
	for _, c := range b {
		crc ^= uint16(c)
		for i := 0; i < 8; i++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0xA001
			} else {
				crc >>= 1
			}
		}
	}
	return crc
}

// CRC 导出校验函数，便于抓包比对（用例 CM-10.2）。
func CRC(b []byte) uint16 { return crc16Modbus(b) }

// Encode 把帧序列化为线上字节（含 SOF、转义与 CRC）。
func Encode(f Frame) ([]byte, error) {
	if len(f.Data) > MaxDataLen {
		return nil, ErrTooLong
	}
	ver := f.Ver
	if ver == 0 {
		ver = Version
	}
	// CRC 覆盖 SOF..DATA，故先按未转义顺序拼出这一段。
	raw := make([]byte, 0, 1+headerLen+len(f.Data)+2)
	raw = append(raw, SOF, ver)
	raw = binary.LittleEndian.AppendUint16(raw, f.Seq)
	raw = binary.LittleEndian.AppendUint16(raw, f.Src)
	raw = binary.LittleEndian.AppendUint16(raw, f.Dst)
	raw = append(raw, f.Type)
	raw = binary.LittleEndian.AppendUint16(raw, uint16(len(f.Data)))
	raw = append(raw, f.Data...)
	sum := crc16Modbus(raw)
	raw = binary.LittleEndian.AppendUint16(raw, sum)

	// SOF 原样发出，其后全部转义。
	out := make([]byte, 0, len(raw)+8)
	out = append(out, SOF)
	for _, c := range raw[1:] {
		if c == SOF || c == escByte {
			out = append(out, escByte, c^escMask)
			continue
		}
		out = append(out, c)
	}
	return out, nil
}

// Decoder 从字节流中逐帧读取，自动跳过噪声并在 SOF 处重同步。
type Decoder struct {
	r   *bufio.Reader
	buf []byte // 复用的解转义缓冲
}

func NewDecoder(r io.Reader) *Decoder {
	return &Decoder{r: bufio.NewReaderSize(r, 4096), buf: make([]byte, 0, 1+headerLen+MaxDataLen+2)}
}

// Next 读取下一帧。CRC 错误会返回 ErrCRC，调用方可据此回 ACK(status=1)
// 而不必断链——链路继续从下一个 SOF 重同步。
func (d *Decoder) Next() (Frame, error) {
	// 1) 同步到 SOF
	for {
		c, err := d.r.ReadByte()
		if err != nil {
			return Frame{}, err
		}
		if c == SOF {
			break
		}
	}
	// 2) 解转义，直到取满 headerLen 得知 LEN，再补足 DATA+CRC
	d.buf = d.buf[:0]
	d.buf = append(d.buf, SOF)
	need := 1 + headerLen // 先要够帧头
	for len(d.buf) < need {
		c, err := d.r.ReadByte()
		if err != nil {
			return Frame{}, ErrTruncated
		}
		if c == SOF {
			// 帧中途出现 SOF：上一帧被截断，就地重同步。
			d.buf = d.buf[:0]
			d.buf = append(d.buf, SOF)
			need = 1 + headerLen
			continue
		}
		if c == escByte {
			e, err := d.r.ReadByte()
			if err != nil {
				return Frame{}, ErrTruncated
			}
			c = e ^ escMask
		}
		d.buf = append(d.buf, c)
		if len(d.buf) == 1+headerLen {
			dataLen := int(binary.LittleEndian.Uint16(d.buf[9:11]))
			if dataLen > MaxDataLen {
				// 长度非法：整帧丢弃，回到同步态。
				return Frame{}, ErrTooLong
			}
			need = 1 + headerLen + dataLen + 2
		}
	}
	raw := d.buf
	n := len(raw)
	got := binary.LittleEndian.Uint16(raw[n-2:])
	if want := crc16Modbus(raw[:n-2]); want != got {
		return Frame{}, ErrCRC
	}
	data := make([]byte, n-2-(1+headerLen))
	copy(data, raw[1+headerLen:n-2])
	return Frame{
		Ver:  raw[1],
		Seq:  binary.LittleEndian.Uint16(raw[2:4]),
		Src:  binary.LittleEndian.Uint16(raw[4:6]),
		Dst:  binary.LittleEndian.Uint16(raw[6:8]),
		Type: raw[8],
		Data: data,
	}, nil
}
