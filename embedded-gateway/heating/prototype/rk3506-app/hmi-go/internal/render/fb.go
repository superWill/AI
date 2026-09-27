package render

// FB:800x480 RGB888 软件帧缓冲,绘图原语逐行对标 dashboard.py FB 类。
// 一切取整/边界语义必须与 Python 逐位一致,否则金帧比对失败。

import (
	"math"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/font"
)

const radToDeg = 180 / math.Pi // 与 CPython math.degrees 的编译期常量一致

type FB struct {
	W, H int
	Buf  []byte
}

func NewFB() *FB {
	return &FB{W: W, H: H, Buf: make([]byte, W*H*3)}
}

func (f *FB) Clear(c RGB) {
	f.Rect(0, 0, f.W, f.H, c)
}

func (f *FB) Rect(x, y, w, h int, c RGB) {
	x0, y0 := max(0, x), max(0, y)
	x1, y1 := min(f.W, x+w), min(f.H, y+h)
	if x1 <= x0 || y1 <= y0 {
		return
	}
	i0 := (y0*f.W + x0) * 3
	rowLen := (x1 - x0) * 3
	for i := i0; i < i0+rowLen; i += 3 {
		f.Buf[i], f.Buf[i+1], f.Buf[i+2] = c.R, c.G, c.B
	}
	for yy := y0 + 1; yy < y1; yy++ {
		j := (yy*f.W + x0) * 3
		copy(f.Buf[j:j+rowLen], f.Buf[i0:i0+rowLen])
	}
}

func (f *FB) Px(x, y int, c RGB) {
	if x >= 0 && x < f.W && y >= 0 && y < f.H {
		i := (y*f.W + x) * 3
		f.Buf[i], f.Buf[i+1], f.Buf[i+2] = c.R, c.G, c.B
	}
}

func (f *FB) RoundRect(x, y, w, h int, c RGB, r int, border *RGB) {
	r = max(0, min(r, min(w/2, h/2)))
	if r == 0 {
		f.Rect(x, y, w, h, c)
		return
	}
	f.Rect(x, y+r, w, h-2*r, c)
	rr := r * r
	for dy := 0; dy < r; dy++ {
		cy := r - dy
		inset := r - int(math.Sqrt(math.Max(0, float64(rr-cy*cy))))
		span := w - inset*2
		f.Rect(x+inset, y+dy, span, 1, c)
		f.Rect(x+inset, y+h-1-dy, span, 1, c)
	}
	if border != nil {
		f.HLine(x+r, x+w-r, y, *border)
		f.HLine(x+r, x+w-r, y+h-1, *border)
		f.VLine(y+r, y+h-r, x, *border)
		f.VLine(y+r, y+h-r, x+w-1, *border)
	}
}

func (f *FB) HLine(x0, x1, y int, c RGB) {
	f.Rect(x0, y, x1-x0, 1, c)
}

func (f *FB) VLine(y0, y1, x int, c RGB) {
	f.Rect(x, y0, 1, y1-y0, c)
}

func (f *FB) Ring(cx, cy, rOut, rIn int, frac float64, vc RGB, sweep, start float64) {
	frac = math.Max(0.0, math.Min(1.0, frac))
	ro2, ri2 := rOut*rOut, rIn*rIn
	for y := cy - rOut; y <= cy+rOut; y++ {
		for x := cx - rOut; x <= cx+rOut; x++ {
			dx, dy := x-cx, y-cy
			d2 := dx*dx + dy*dy
			if d2 < ri2 || d2 > ro2 {
				continue
			}
			ang := math.Mod(math.Atan2(float64(dy), float64(dx))*radToDeg+360, 360)
			rel := math.Mod(ang-start+360, 360)
			if rel <= sweep {
				col := Track
				if rel <= sweep*frac {
					col = vc
				}
				f.Px(x, y, col)
			}
		}
	}
}

func (f *FB) Char(ch rune, x, y, scale int, c RGB) int {
	g, ok := font.Get(ch)
	if !ok {
		return 8 * scale
	}
	for ry := range g.Rows {
		for _, r := range g.Rows[ry] {
			f.Rect(x+r.Start*scale, y+ry*scale, (r.End-r.Start)*scale, scale, c)
		}
	}
	return g.W * scale
}

func spacing(scale int) int {
	if scale <= 1 {
		return 1
	}
	return scale
}

func (f *FB) Text(s string, x, y, scale int, c RGB) int {
	for _, ch := range s {
		x += f.Char(ch, x, y, scale, c) + spacing(scale)
	}
	return x
}

func (f *FB) TextW(s string, scale int) int {
	w := 0
	for _, ch := range s {
		w += font.Width(ch)*scale + spacing(scale)
	}
	return w
}

func (f *FB) TextCenter(s string, cx, y, scale int, c RGB) {
	f.Text(s, cx-f.TextW(s, scale)/2, y, scale, c)
}

func (f *FB) TextRight(s string, rx, y, scale int, c RGB) {
	f.Text(s, rx-f.TextW(s, scale), y, scale, c)
}
