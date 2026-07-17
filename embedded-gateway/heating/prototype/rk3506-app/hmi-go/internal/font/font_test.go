package font

import (
	"strconv"
	"testing"
)

// 差分测试:用逐像素的朴素实现重新解码全部字形,与游程解码结果对比。
func TestDecodeAgainstNaive(t *testing.T) {
	if len(glyphHex) < 200 {
		t.Fatalf("字库条目过少: %d(应约 281,生成器可能没跑全)", len(glyphHex))
	}
	for ch, bm := range glyphHex {
		g, ok := Get(ch)
		if !ok {
			t.Fatalf("%q: 解码后缺失", ch)
		}
		gw := 8
		if len(bm) == 64 {
			gw = 16
		}
		if g.W != gw {
			t.Fatalf("%q: 宽度 %d != %d", ch, g.W, gw)
		}
		bpr := gw / 8
		for ry := 0; ry < 16; ry++ {
			val, err := strconv.ParseUint(bm[ry*bpr*2:(ry+1)*bpr*2], 16, 32)
			if err != nil {
				t.Fatalf("%q 行 %d: 非法 hex", ch, ry)
			}
			for rx := 0; rx < gw; rx++ {
				want := val&(1<<uint(gw-1-rx)) != 0
				got := false
				for _, r := range g.Rows[ry] {
					if rx >= r.Start && rx < r.End {
						got = true
						break
					}
				}
				if got != want {
					t.Fatalf("%q (%d,%d): 游程=%v 朴素=%v", ch, rx, ry, got, want)
				}
			}
		}
	}
}

func TestWidthSemantics(t *testing.T) {
	if w := Width('E'); w != 8 {
		t.Fatalf("'E' 宽 %d != 8", w)
	}
	if w := Width('总'); w != 16 {
		t.Fatalf("'总' 宽 %d != 16", w)
	}
	// 缺字形按 8 计(text_w 语义)
	if w := Width('߿'); w != 8 {
		t.Fatalf("缺字形宽 %d != 8", w)
	}
	if _, ok := Get('߿'); ok {
		t.Fatal("缺字形不应命中")
	}
}

func TestDeviceAddGlyphCoverage(t *testing.T) {
	for _, ch := range "从站保存并布已滚失败选择温度采集模块循环泵变频器安全IO" {
		if ch > 127 {
			if _, ok := Get(ch); !ok {
				t.Errorf("设备接入文案缺字形 %q U+%04X", ch, ch)
			}
		}
	}
}
