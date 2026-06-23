//go:build linux

// Modbus RTU 串口传输（Go 移植自 app.py ModbusSource 的 termios 配置与 _txn/read_holding）。
// 仅 Linux：用 x/sys/unix 直接配 termios，对照 Python termios 一一对应。
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"sync"
	"time"

	"golang.org/x/sys/unix"
)

var baudBits = map[int]uint32{
	9600: unix.B9600, 19200: unix.B19200, 38400: unix.B38400,
	57600: unix.B57600, 115200: unix.B115200,
}

type SerialPort struct {
	fd int
	mu sync.Mutex // 采集与控制写共用串口，事务串行
}

// OpenSerial 打开并配为 8N1 raw 模式（对照 app.py __init__ 的 termios 设置）。
func OpenSerial(dev string, baud int) (*SerialPort, error) {
	bb, ok := baudBits[baud]
	if !ok {
		return nil, fmt.Errorf("不支持的波特率 %d", baud)
	}
	fd, err := unix.Open(dev, unix.O_RDWR|unix.O_NOCTTY, 0)
	if err != nil {
		return nil, err
	}
	t := &unix.Termios{}
	// app.py: iflag=oflag=lflag=0; cflag=CS8|CLOCAL|CREAD|baud; VMIN=VTIME=0
	t.Cflag = unix.CS8 | unix.CLOCAL | unix.CREAD | bb
	t.Ispeed = bb
	t.Ospeed = bb
	t.Cc[unix.VMIN] = 0
	t.Cc[unix.VTIME] = 0
	if err := unix.IoctlSetTermios(fd, unix.TCSETS, t); err != nil {
		unix.Close(fd)
		return nil, err
	}
	_ = unix.IoctlSetInt(fd, unix.TCFLSH, unix.TCIOFLUSH) // tcflush
	return &SerialPort{fd: fd}, nil
}

func (s *SerialPort) Close() { unix.Close(s.fd) }

// Txn 一次请求+应答原子化（对照 _txn）：flush → 写 body+CRC → select/超时读，
// 首次读到后等 30ms 再读一次收尾帧。
func (s *SerialPort) Txn(body []byte, timeoutSec float64) []byte {
	s.mu.Lock()
	defer s.mu.Unlock()
	_ = unix.IoctlSetInt(s.fd, unix.TCFLSH, unix.TCIOFLUSH)
	req := append(append([]byte{}, body...), ModbusCRC(body)...)
	_, _ = unix.Write(s.fd, req)

	deadline := time.Now().Add(time.Duration(timeoutSec * float64(time.Second)))
	tmp := make([]byte, 256)
	var buf []byte
	for time.Now().Before(deadline) {
		ms := int(time.Until(deadline).Milliseconds())
		if ms < 0 {
			ms = 0
		}
		n, _ := unix.Poll([]unix.PollFd{{Fd: int32(s.fd), Events: unix.POLLIN}}, ms)
		if n <= 0 {
			continue
		}
		if r, _ := unix.Read(s.fd, tmp); r > 0 {
			buf = append(buf, tmp[:r]...)
		}
		time.Sleep(30 * time.Millisecond)
		if n2, _ := unix.Poll([]unix.PollFd{{Fd: int32(s.fd), Events: unix.POLLIN}}, 0); n2 > 0 {
			if r2, _ := unix.Read(s.fd, tmp); r2 > 0 {
				buf = append(buf, tmp[:r2]...)
			}
		}
		break
	}
	return buf
}

// ReadHolding 对照 read_holding：timeout/crc 可重试；exception 是设备明确拒绝，不重试。
func (s *SerialPort) ReadHolding(addr, start, count int, timeoutSec float64, retries int) ([]uint16, string) {
	body := []byte{byte(addr), 0x03, byte(start >> 8), byte(start & 0xFF), byte(count >> 8), byte(count & 0xFF)}
	errc := "timeout"
	for i := 0; i <= retries; i++ {
		resp := s.Txn(body, timeoutSec)
		regs, e := ParseReadHolding(resp)
		if e == "" {
			return regs, ""
		}
		if e == "exception" {
			return nil, "exception"
		}
		errc = e // timeout / crc_error → 重试
	}
	return nil, errc
}

// WriteRegister 对照 app.py write_register：FC06，从站应原样回显前 6 字节才算成功。
func (s *SerialPort) WriteRegister(addr, reg, value int, timeoutSec float64) bool {
	body := []byte{byte(addr), 0x06, byte(reg >> 8), byte(reg & 0xFF),
		byte(value >> 8), byte(value & 0xFF)}
	resp := s.Txn(body, timeoutSec)
	return len(resp) >= 6 &&
		resp[0] == body[0] && resp[1] == body[1] &&
		resp[2] == body[2] && resp[3] == body[3] &&
		resp[4] == body[4] && resp[5] == body[5]
}

// runModbusRead: 打开串口读一次保持寄存器（板上对 modbus_sim 对拍用）。
//
//	gatewayc modbusread <dev> <baud> <addr> <start> <count> [timeoutSec] [retries]
func runModbusRead(args []string) {
	if len(args) < 5 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc modbusread <dev> <baud> <addr> <start> <count> [timeoutSec] [retries]")
		os.Exit(2)
	}
	atoi := func(s string) int { n, _ := strconv.Atoi(s); return n }
	timeout := 1.0
	retries := 0
	if len(args) > 5 {
		timeout, _ = strconv.ParseFloat(args[5], 64)
	}
	if len(args) > 6 {
		retries = atoi(args[6])
	}
	sp, err := OpenSerial(args[0], atoi(args[1]))
	if err != nil {
		fmt.Fprintf(os.Stderr, "打开串口失败: %v\n", err)
		os.Exit(2)
	}
	defer sp.Close()
	regs, e := sp.ReadHolding(atoi(args[2]), atoi(args[3]), atoi(args[4]), timeout, retries)
	b, _ := json.Marshal(obj{"regs": regs, "err": e})
	fmt.Println(string(b))
}

// runModbusWrite: 经 point_id → control_map → FC06 真串口写值。
// gatewayc modbuswrite <dev> <baud> <point_id> <value> <addr> <reg> <scale> [timeoutSec]
func runModbusWrite(args []string) {
	if len(args) < 7 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc modbuswrite <dev> <baud> <point_id> <value> <addr> <reg> <scale> [timeoutSec]")
		os.Exit(2)
	}
	atoi := func(s string) int { n, _ := strconv.Atoi(s); return n }
	value, _ := strconv.ParseFloat(args[3], 64)
	scale, _ := strconv.ParseFloat(args[6], 64)
	timeout := 1.0
	if len(args) > 7 {
		timeout, _ = strconv.ParseFloat(args[7], 64)
	}
	sp, err := OpenSerial(args[0], atoi(args[1]))
	if err != nil {
		fmt.Fprintf(os.Stderr, "打开串口失败: %v\n", err)
		os.Exit(2)
	}
	defer sp.Close()
	writer := NewModbusSetpointWriter(
		obj{args[2]: obj{"addr": atoi(args[4]), "reg": atoi(args[5]), "scale": scale}},
		func(addr, reg, registerValue int) bool {
			return sp.WriteRegister(addr, reg, registerValue, timeout)
		},
	)
	ok := writer.WriteSetpoint(args[2], value)
	registerValue := int(pyRound(value/scale, 0))
	b, _ := json.Marshal(obj{
		"ok": ok, "point_id": args[2], "value": value,
		"addr": atoi(args[4]), "reg": atoi(args[5]), "register_value": registerValue,
		"frame": fmt.Sprintf("%x", BuildWriteRegister(atoi(args[4]), atoi(args[5]), registerValue)),
	})
	fmt.Println(string(b))
}
