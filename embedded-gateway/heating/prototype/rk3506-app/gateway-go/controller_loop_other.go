//go:build !linux

package main

import (
	"fmt"
	"os"
)

func runControllerLoop(args []string) {
	fmt.Fprintln(os.Stderr, "controllerloop 仅 Linux 支持（在 RK3506 上运行）")
	os.Exit(2)
}
