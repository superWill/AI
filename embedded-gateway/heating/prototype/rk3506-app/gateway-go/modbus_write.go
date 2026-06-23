package main

// ModbusSetpointWriter 把 point_id/value 映射成 FC06 写单寄存器调用。
// 换算严格对齐 app.py: int(round(value / scale))。
type ModbusSetpointWriter struct {
	controlMap obj
	writeReg   func(addr, reg, value int) bool
}

func NewModbusSetpointWriter(controlMap obj, writeReg func(int, int, int) bool) *ModbusSetpointWriter {
	return &ModbusSetpointWriter{controlMap: controlMap, writeReg: writeReg}
}

func (w *ModbusSetpointWriter) WriteSetpoint(pointID string, value float64) bool {
	mapping := asObj(w.controlMap[pointID])
	if mapping == nil || w.writeReg == nil {
		return false
	}
	scale := toF(getOr(mapping, "scale", float64(1)))
	if scale == 0 {
		return false
	}
	registerValue := int(pyRound(value/scale, 0))
	return w.writeReg(
		int(toF(mapping["addr"])),
		int(toF(mapping["reg"])),
		registerValue,
	)
}
