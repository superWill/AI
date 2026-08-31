package crtlink

import (
	"encoding/binary"
	"errors"
	"time"
)

// Report 是各类上行事件帧（0x10~0x17）共用的帧体。
//
// 草案按帧类型分别列了字段，但它们的并集是同一组：事件号、部位（回路+地址+
// 分区）、子类型码、时间。统一成一个 14 字节定长体，编解码只有一份实现，
// 帧类型本身承载"这是哪类事件"的语义。
//
//	EventID(4) Loop(1) Addr(1) Zone(2) Code(1) Flags(1) Unix(4)
//
// Code 的含义随帧类型而定：火警＝报警类型、启动/反馈＝动作类型、故障＝故障
// 标志位、屏蔽＝是否屏蔽、监管＝监管类型、电源＝电源事件类型。
type Report struct {
	EventID uint32
	Loop    uint8
	Addr    uint8
	Zone    uint16
	Code    uint8
	Flags   uint8
	At      time.Time
}

const reportLen = 14

var ErrBadBody = errors.New("crtlink: 帧体长度不符")

// 故障标志位（对应点表 fault_flags，见 docs/point-table/initial-point-table.md）。
const (
	FaultOpen    = 1 << 0 // 断路
	FaultShort   = 1 << 1 // 短路
	FaultTimeout = 1 << 2 // 轮询超时（失联）
	FaultInvalid = 1 << 3 // 响应非法
)

// 火警子类型：区分探测器报警与手报，供 GB 4717 5.4.1.4「明确指示为手报」判定。
const (
	AlarmFromDetector = 0x01
	AlarmFromManual   = 0x02 // 手动火灾报警按钮
	AlarmFromHydrant  = 0x03 // 消火栓按钮
	AlarmFirst        = 0x80 // 与上述按位或：该条为首火警（GB 4717 5.4.1.7）
)

// EncodeReport 序列化事件帧体。
func EncodeReport(r Report) []byte {
	b := make([]byte, 0, reportLen)
	b = binary.LittleEndian.AppendUint32(b, r.EventID)
	b = append(b, r.Loop, r.Addr)
	b = binary.LittleEndian.AppendUint16(b, r.Zone)
	b = append(b, r.Code, r.Flags)
	var ts uint32
	if !r.At.IsZero() {
		ts = uint32(r.At.Unix())
	}
	return binary.LittleEndian.AppendUint32(b, ts)
}

// DecodeReport 解析事件帧体。
func DecodeReport(b []byte) (Report, error) {
	if len(b) != reportLen {
		return Report{}, ErrBadBody
	}
	return Report{
		EventID: binary.LittleEndian.Uint32(b[0:4]),
		Loop:    b[4],
		Addr:    b[5],
		Zone:    binary.LittleEndian.Uint16(b[6:8]),
		Code:    b[8],
		Flags:   b[9],
		At:      time.Unix(int64(binary.LittleEndian.Uint32(b[10:14])), 0),
	}, nil
}

// Heartbeat 是 0x01 帧体：主机时间戳 + 主备电状态。
//
// 心跳兼作 GB 4717 5.4.10.2 的在线判据：CRT 侧超过 3 个周期未收到即判链路故障。
type Heartbeat struct {
	At        time.Time
	MainOK    bool // 主电正常
	BatteryOK bool // 备电正常
}

const heartbeatLen = 5

func EncodeHeartbeat(h Heartbeat) []byte {
	b := binary.LittleEndian.AppendUint32(make([]byte, 0, heartbeatLen), uint32(h.At.Unix()))
	var flags uint8
	if h.MainOK {
		flags |= 1 << 0
	}
	if h.BatteryOK {
		flags |= 1 << 1
	}
	return append(b, flags)
}

func DecodeHeartbeat(b []byte) (Heartbeat, error) {
	if len(b) != heartbeatLen {
		return Heartbeat{}, ErrBadBody
	}
	return Heartbeat{
		At:        time.Unix(int64(binary.LittleEndian.Uint32(b[0:4])), 0),
		MainOK:    b[4]&(1<<0) != 0,
		BatteryOK: b[4]&(1<<1) != 0,
	}, nil
}

// EncodeACK / DecodeACK 对应 0x02：acked_seq + status。
func EncodeACK(seq uint16, status uint8) []byte {
	return append(binary.LittleEndian.AppendUint16(make([]byte, 0, 3), seq), status)
}

func DecodeACK(b []byte) (seq uint16, status uint8, err error) {
	if len(b) != 3 {
		return 0, 0, ErrBadBody
	}
	return binary.LittleEndian.Uint16(b[0:2]), b[2], nil
}

// EncodeTimeSync / DecodeTimeSync 对应 0x27 授时（GB 4717 5.4.10.3，用例 CM-03）。
func EncodeTimeSync(t time.Time) []byte {
	return binary.LittleEndian.AppendUint32(make([]byte, 0, 4), uint32(t.Unix()))
}

func DecodeTimeSync(b []byte) (time.Time, error) {
	if len(b) != 4 {
		return time.Time{}, ErrBadBody
	}
	return time.Unix(int64(binary.LittleEndian.Uint32(b)), 0), nil
}
