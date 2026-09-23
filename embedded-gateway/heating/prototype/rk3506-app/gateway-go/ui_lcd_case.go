package main

import (
	"fmt"
	"os"
)

// lcdtest: 渲染一个固定测试场景(对拍 Python dashboard.FB 用),导出原始 RGB 缓冲 + PNG。
//
//	gatewayc lcdtest <out_raw> [out_png]
// 场景必须与 ui_lcd_harness.py 里逐一对应(同序同参),逐像素比 buf。
func runLCDTest(args []string) {
	if len(args) < 1 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc lcdtest <out_raw.rgb> [out.png]")
		os.Exit(2)
	}
	f := newFB(lcdW, lcdH)
	border := rgb{56, 189, 248}
	f.clear(rgb{15, 23, 42})
	f.roundRect(10, 10, 120, 70, rgb{30, 41, 59}, 8, &border)
	f.text("温度 52.3℃ ABC", 20, 90, 2, rgb{226, 232, 240})
	f.ring(200, 200, 40, 28, 0.6, rgb{34, 197, 94}, 270, 135)
	f.text("二次供水温度 急停 缺水 反馈", 20, 140, 1, rgb{148, 163, 184})
	f.textRight("7/8 在线", 790, 20, 1, rgb{245, 158, 11})
	if err := os.WriteFile(args[0], f.buf, 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "写 raw 失败: %v\n", err)
		os.Exit(2)
	}
	if len(args) >= 2 {
		f.toPNG(args[1])
	}
	fmt.Printf("[lcdtest] 渲染完成 %dx%d → %s (%d 字节)\n", f.w, f.h, args[0], len(f.buf))
}
