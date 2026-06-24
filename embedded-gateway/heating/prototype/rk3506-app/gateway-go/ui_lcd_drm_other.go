//go:build !linux

// LCD 直写屏幕仅板上(linux)支持;主机构建提供占位,使 lcdtest/lcdrender 对拍仍可编译。
package main

import (
	"fmt"
	"os"
)

func runLCDMain(args []string) {
	fmt.Fprintln(os.Stderr, "gatewayc lcd 仅在板上(linux/arm)运行:DRM 直写 + evdev 触摸")
	os.Exit(2)
}
