//go:build linux

// daemon 的 modbus 源装配(Linux 串口):ModbusSource 轮询 + ModbusSetpointWriter 写。
package main

import "fmt"

func newModbusRuntime(cfg obj) (pollSource, func(string, float64) bool, error) {
	dev := asStr(getOr(cfg, "serial", "/dev/ttyS1"))
	baud := int(toF(getOr(cfg, "baud", float64(9600))))
	sp, err := OpenSerial(dev, baud)
	if err != nil {
		return nil, nil, err
	}
	ms := NewModbusSource(asArr(cfg["devices"]), asObj(cfg["reliability"]),
		func(addr, start, count int, t float64, retries int) ([]uint16, string) {
			return sp.ReadHolding(addr, start, count, t, retries)
		},
		defaultClock, defaultClock)
	writer := NewModbusSetpointWriter(asObj(cfg["control_map"]),
		func(addr, reg, value int) bool { return sp.WriteRegister(addr, reg, value, ms.timeout) })
	fmt.Printf("[源] modbus 真串口 %s @ %d\n", dev, baud)
	return ms, writer.WriteSetpoint, nil
}
