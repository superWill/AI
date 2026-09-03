package crtlink

import (
	"bytes"
	"testing"
	"time"
)

func TestCRC16ModbusKnownVector(t *testing.T) {
	// MODBUS 标准测试向量："123456789" -> 0x4B37
	if got := CRC([]byte("123456789")); got != 0x4B37 {
		t.Fatalf("CRC-16/MODBUS = 0x%04X, 期望 0x4B37", got)
	}
}

func TestEncodeDecodeRoundTrip(t *testing.T) {
	in := Frame{Seq: 0x1234, Src: AddrHost, Dst: AddrCRT, Type: TypeAlarm,
		Data: EncodeReport(Report{EventID: 7, Loop: 1, Addr: 12, Zone: 3,
			Code: AlarmFromDetector | AlarmFirst, At: time.Unix(1756600000, 0)})}
	wire, err := Encode(in)
	if err != nil {
		t.Fatal(err)
	}
	out, err := NewDecoder(bytes.NewReader(wire)).Next()
	if err != nil {
		t.Fatal(err)
	}
	if out.Seq != in.Seq || out.Src != in.Src || out.Dst != in.Dst || out.Type != in.Type {
		t.Fatalf("帧头不一致: %+v vs %+v", out, in)
	}
	r, err := DecodeReport(out.Data)
	if err != nil {
		t.Fatal(err)
	}
	if r.EventID != 7 || r.Loop != 1 || r.Addr != 12 || r.Zone != 3 {
		t.Fatalf("帧体不一致: %+v", r)
	}
	if r.Code&AlarmFirst == 0 {
		t.Fatal("首火警标志丢失")
	}
}

// 转义必须覆盖帧头与 CRC，否则 SEQ=0x007E 这类帧会把接收端带偏。
func TestEscapeCoversHeaderNotOnlyData(t *testing.T) {
	in := Frame{Seq: 0x007E, Src: AddrHost, Dst: AddrCRT, Type: TypeFault,
		Data: []byte{0x7E, 0x7D, 0x00, 0x7E}}
	wire, err := Encode(in)
	if err != nil {
		t.Fatal(err)
	}
	if n := bytes.Count(wire, []byte{SOF}); n != 1 {
		t.Fatalf("流中出现 %d 个 0x7E，SOF 必须唯一", n)
	}
	out, err := NewDecoder(bytes.NewReader(wire)).Next()
	if err != nil {
		t.Fatal(err)
	}
	if out.Seq != 0x007E || !bytes.Equal(out.Data, in.Data) {
		t.Fatalf("解码不一致: seq=0x%04X data=%v", out.Seq, out.Data)
	}
}

func TestDecoderSkipsNoiseAndResyncs(t *testing.T) {
	good, _ := Encode(Frame{Seq: 1, Src: AddrHost, Dst: AddrCRT, Type: TypeHeartbeat,
		Data: EncodeHeartbeat(Heartbeat{At: time.Unix(1756600000, 0), MainOK: true, BatteryOK: true})})
	stream := append([]byte{0x00, 0xFF, 0xAA}, good...) // 前置噪声
	f, err := NewDecoder(bytes.NewReader(stream)).Next()
	if err != nil {
		t.Fatal(err)
	}
	if f.Type != TypeHeartbeat {
		t.Fatalf("类型 = 0x%02X", f.Type)
	}
	hb, err := DecodeHeartbeat(f.Data)
	if err != nil || !hb.MainOK || !hb.BatteryOK {
		t.Fatalf("心跳解析失败: %+v err=%v", hb, err)
	}
}

func TestCRCErrorIsReportedNotSilentlyAccepted(t *testing.T) {
	wire, _ := Encode(Frame{Seq: 5, Src: AddrHost, Dst: AddrCRT, Type: TypeFault, Data: []byte{1, 2, 3}})
	wire[len(wire)-1] ^= 0xFF // 破坏 CRC
	if _, err := NewDecoder(bytes.NewReader(wire)).Next(); err != ErrCRC {
		t.Fatalf("期望 ErrCRC，得到 %v", err)
	}
}

func TestTruncatedFrameThenGoodFrame(t *testing.T) {
	full, _ := Encode(Frame{Seq: 9, Src: AddrHost, Dst: AddrCRT, Type: TypeAction, Data: []byte{9, 9}})
	stream := append(append([]byte{}, full[:5]...), full...) // 半截帧 + 完整帧
	f, err := NewDecoder(bytes.NewReader(stream)).Next()
	if err != nil {
		t.Fatal(err)
	}
	if f.Seq != 9 || f.Type != TypeAction {
		t.Fatalf("重同步后取到错误帧: %+v", f)
	}
}

func TestDataLengthLimit(t *testing.T) {
	if _, err := Encode(Frame{Data: make([]byte, MaxDataLen+1)}); err != ErrTooLong {
		t.Fatalf("期望 ErrTooLong，得到 %v", err)
	}
}
