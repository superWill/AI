//go:build !linux

// 非 Linux（如 Mac 开发机）无串口实现，modbusread 给出明确提示。
package main

import (
	"fmt"
	"os"
)

func runModbusRead(args []string) {
	fmt.Fprintln(os.Stderr, "modbusread 仅 Linux 支持（在 RK3506 上运行）")
	os.Exit(2)
}
