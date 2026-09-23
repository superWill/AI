// Modbus RTU 协议核心（Go 移植自 app.py ModbusSource 的 _crc/read_holding/write_register
// 的帧构造与解析部分）。纯字节运算，与 Python 逐字节对拍。串口传输与退避状态机另迁。
package main

import (
	"encoding/binary"
)

// ModbusCRC 标准 Modbus CRC16（多项式 0xA001），返回小端 2 字节（对齐 struct.pack("<H")）。
func ModbusCRC(data []byte) []byte {
	crc := uint16(0xFFFF)
	for _, b := range data {
		crc ^= uint16(b)
		for i := 0; i < 8; i++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0xA001
			} else {
				crc >>= 1
			}
		}
	}
	out := make([]byte, 2)
	binary.LittleEndian.PutUint16(out, crc)
	return out
}

// BuildReadHolding 构造读保持寄存器请求(FC 0x03)：struct.pack(">BBHH",addr,3,start,count)+CRC。
func BuildReadHolding(addr, start, count int) []byte {
	body := []byte{byte(addr), 0x03,
		byte(start >> 8), byte(start & 0xFF),
		byte(count >> 8), byte(count & 0xFF)}
	return append(body, ModbusCRC(body)...)
}

// BuildWriteRegister 构造写单寄存器请求(FC 0x06)。
func BuildWriteRegister(addr, reg, value int) []byte {
	v := value & 0xFFFF
	body := []byte{byte(addr), 0x06,
		byte(reg >> 8), byte(reg & 0xFF),
		byte(v >> 8), byte(v & 0xFF)}
	return append(body, ModbusCRC(body)...)
}

// ParseReadHolding 解析读保持寄存器应答（对应 read_holding 单次应答的判定）：
// 返回 (寄存器值大端 uint16 列表, 错误码)。错误码: ""=成功 / timeout / crc_error / exception。
func ParseReadHolding(resp []byte) ([]uint16, string) {
	if len(resp) == 0 {
		return nil, "timeout"
	}
	body := resp[:len(resp)-2]
	crc := resp[len(resp)-2:]
	got := ModbusCRC(body)
	if got[0] != crc[0] || got[1] != crc[1] {
		return nil, "crc_error"
	}
	if resp[1]&0x80 != 0 {
		return nil, "exception"
	}
	n := int(resp[2]) // 字节数
	regs := make([]uint16, 0, n/2)
	for i := 0; i < n; i += 2 {
		regs = append(regs, uint16(resp[3+i])<<8|uint16(resp[4+i])) // 大端
	}
	return regs, ""
}
