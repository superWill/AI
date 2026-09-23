//go:build !linux

package main

import "errors"

func newModbusRuntime(cfg obj) (pollSource, func(string, float64) bool, error) {
	return nil, nil, errors.New("modbus 源仅 Linux 支持(在 RK3506 上运行)")
}
