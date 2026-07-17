#!/usr/bin/env python3
"""Retired compatibility entry point for the former Python-to-Go font generator."""

import sys


def main() -> int:
    print(
        "已退役:Go HMI 字形不再从 cjk_font.py 生成。"
        "请直接维护 hmi-go/internal/font 的 Go 字形表，并运行字形覆盖测试。",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
