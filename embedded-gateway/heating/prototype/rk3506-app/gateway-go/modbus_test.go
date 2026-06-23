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
