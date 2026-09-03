package main

import (
	"encoding/hex"
	"testing"
)

func TestModbusCRC(t *testing.T) {
	// 向量经 Python app.ModbusSource._crc 校验
	for in, want := range map[string]string{
		"010300000004": "4409", "11030064000a": "8682", "deadbeef": "9bc1",
	} {
		b, _ := hex.DecodeString(in)
		if got := hex.EncodeToString(ModbusCRC(b)); got != want {
			t.Errorf("CRC(%s)=%s 期望 %s", in, got, want)
		}
	}
}

func TestBuildFrames(t *testing.T) {
	if got := hex.EncodeToString(BuildReadHolding(1, 0, 6)); got != "010300000006c5c8" {
		t.Errorf("read req=%s", got)
	}
	if got := hex.EncodeToString(BuildWriteRegister(1, 0, 50)); got != "010600000032081f" {
		t.Errorf("write req=%s", got)
	}
}

func TestParseReadHolding(t *testing.T) {
	b, _ := hex.DecodeString("0103040136002a9a1e")
	regs, e := ParseReadHolding(b)
	if e != "" || len(regs) != 2 || regs[0] != 310 || regs[1] != 42 {
		t.Errorf("regs=%v e=%q", regs, e)
	}
	bad, _ := hex.DecodeString("01030401360000")
	if _, e := ParseReadHolding(bad); e != "crc_error" {
		t.Errorf("应 crc_error, 得 %q", e)
	}
	if _, e := ParseReadHolding(nil); e != "timeout" {
		t.Errorf("空应 timeout, 得 %q", e)
	}
}

func TestModbusSetpointWriterMapsAndRoundsLikePython(t *testing.T) {
	var addr, reg, value int
	writer := NewModbusSetpointWriter(
		obj{"valve_open_sp": obj{"addr": 3, "reg": 120, "scale": 0.1}},
		func(a, r, v int) bool {
			addr, reg, value = a, r, v
			return true
		},
	)

	if !writer.WriteSetpoint("valve_open_sp", 12.25) {
		t.Fatal("write should succeed")
	}
	if addr != 3 || reg != 120 || value != 122 {
		t.Fatalf("write=(addr=%d reg=%d value=%d), want (3,120,122)", addr, reg, value)
	}
}

func TestModbusSetpointWriterRejectsUnknownPoint(t *testing.T) {
	called := false
	writer := NewModbusSetpointWriter(obj{}, func(a, r, v int) bool {
		called = true
		return true
	})
	if writer.WriteSetpoint("unknown", 1) || called {
		t.Fatal("unknown point must not reach register writer")
	}
}
