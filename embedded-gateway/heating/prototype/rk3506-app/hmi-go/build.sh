#!/bin/sh
# 交叉编译 hmic → ../hmic(RK3506: 32 位 ARMv7 静态二进制)。
set -eu
cd "$(dirname "$0")"
CGO_ENABLED=0 GOOS=linux GOARCH=arm GOARM=7 \
	go build -trimpath -ldflags "-s -w" -o ../hmic ./cmd/hmi
ls -lh ../hmic
file ../hmic 2>/dev/null || true
