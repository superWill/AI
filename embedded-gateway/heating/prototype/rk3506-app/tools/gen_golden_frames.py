#!/usr/bin/env python3
"""Retired: Python is no longer the rendering oracle for the Go-only LCD HMI."""

raise SystemExit(
    "已退役:不要用 Python 覆盖 Go HMI 回归快照。"
    "请在 hmi-go/ 运行 `go run ./cmd/golden --case <name>` 生成候选 PNG，"
    "人工审核后再用 `--accept --reviewed` 显式接受。"
)
