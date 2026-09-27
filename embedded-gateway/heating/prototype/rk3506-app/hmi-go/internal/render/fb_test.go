package render

import (
	"bytes"
	"testing"
)

func countColor(f *FB, c RGB) int {
	n := 0
	for i := 0; i < len(f.Buf); i += 3 {
		if f.Buf[i] == c.R && f.Buf[i+1] == c.G && f.Buf[i+2] == c.B {
			n++
		}
	}
	return n
}

func TestRectClipping(t *testing.T) {
	cases := []struct {
		name       string
		x, y, w, h int
		want       int // 期望着色像素数
	}{
		{"完全在内", 10, 10, 5, 4, 20},
		{"负坐标裁剪", -3, -2, 10, 10, 7 * 8},
		{"右下溢出", W - 4, H - 3, 100, 100, 4 * 3},
		{"完全在外", W + 10, 0, 5, 5, 0},
		{"零宽", 10, 10, 0, 5, 0},
		{"负高", 10, 10, 5, -1, 0},
	}
	red := RGB{255, 0, 0}
	for _, c := range cases {
		f := NewFB()
		f.Rect(c.x, c.y, c.w, c.h, red)
		if got := countColor(f, red); got != c.want {
			t.Errorf("%s: %d 像素 != %d", c.name, got, c.want)
		}
	}
}

func TestClearFillsAll(t *testing.T) {
	f := NewFB()
	f.Clear(BG)
	if got := countColor(f, BG); got != W*H {
		t.Fatalf("Clear 覆盖 %d != %d", got, W*H)
	}
}

func TestCharMissingGlyphAdvance(t *testing.T) {
	f := NewFB()
	before := bytes.Clone(f.Buf)
	if adv := f.Char('߿', 10, 10, 2, Ink); adv != 16 {
		t.Fatalf("缺字形前进 %d != 8*scale", adv)
	}
	if !bytes.Equal(before, f.Buf) {
		t.Fatal("缺字形不应绘制任何像素")
	}
}

func TestTextSpacing(t *testing.T) {
	f := NewFB()
	// 'E'(8 宽):scale=1 → 8+1;scale=2 → 16+2
	if end := f.Text("E", 0, 100, 1, Ink); end != 9 {
		t.Fatalf("scale1 结束 x=%d != 9", end)
	}
	if end := f.Text("E", 0, 200, 2, Ink); end != 18 {
		t.Fatalf("scale2 结束 x=%d != 18", end)
	}
	if w := f.TextW("总览", 1); w != (16+1)*2 {
		t.Fatalf("TextW=%d != 34", w)
	}
}
