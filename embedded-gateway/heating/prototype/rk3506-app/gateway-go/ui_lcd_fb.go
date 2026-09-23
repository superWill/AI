// LCD 帧缓冲 + 中文点阵字库(对照 dashboard.py 的 FB 类 + cjk_font)。800x480 RGB。
// 增量A:纯渲染,PNG/原始缓冲对拍 Python FB。DRM 直写见增量C。
package main

import (
	"bufio"
	_ "embed"
	"image"
	"image/color"
	"image/png"
	"math"
	"os"
	"strconv"
	"strings"
)

const lcdW, lcdH = 800, 480

//go:embed cjk_font.txt
var cjkFontData string
var glyphs = map[rune]string{}

// TRACK:环形仪表底色(对照 dashboard.py 全局 TRACK)。
var trackColor = rgb{40, 52, 74}

func init() {
	sc := bufio.NewScanner(strings.NewReader(cjkFontData))
	sc.Buffer(make([]byte, 1<<16), 1<<16)
	for sc.Scan() {
		ln := sc.Text()
		i := strings.IndexByte(ln, '\t')
		if i <= 0 {
			continue
		}
		r := []rune(ln[:i])
		if len(r) == 1 {
			glyphs[r[0]] = ln[i+1:]
		}
	}
}

type rgb = [3]uint8

type fb struct {
	w, h int
	buf  []byte // w*h*3 RGB
}

func newFB(w, h int) *fb { return &fb{w, h, make([]byte, w*h*3)} }

func (f *fb) clear(c rgb) {
	for i := 0; i < len(f.buf); i += 3 {
		f.buf[i], f.buf[i+1], f.buf[i+2] = c[0], c[1], c[2]
	}
}

func (f *fb) px(x, y int, c rgb) {
	if x >= 0 && x < f.w && y >= 0 && y < f.h {
		i := (y*f.w + x) * 3
		f.buf[i], f.buf[i+1], f.buf[i+2] = c[0], c[1], c[2]
	}
}

func (f *fb) rect(x, y, w, h int, c rgb) {
	x0, y0 := max(0, x), max(0, y)
	x1, y1 := min(f.w, x+w), min(f.h, y+h)
	for yy := y0; yy < y1; yy++ {
		for xx := x0; xx < x1; xx++ {
			i := (yy*f.w + xx) * 3
			f.buf[i], f.buf[i+1], f.buf[i+2] = c[0], c[1], c[2]
		}
	}
}

func (f *fb) hline(x0, x1, y int, c rgb) { f.rect(x0, y, x1-x0, 1, c) }
func (f *fb) vline(y0, y1, x int, c rgb) { f.rect(x, y0, 1, y1-y0, c) }

func (f *fb) roundRect(x, y, w, h int, c rgb, r int, border *rgb) {
	f.rect(x+r, y, w-2*r, h, c)
	f.rect(x, y+r, w, h-2*r, c)
	corners := [4][2]int{{x + r, y + r}, {x + w - r - 1, y + r}, {x + r, y + h - r - 1}, {x + w - r - 1, y + h - r - 1}}
	for _, cc := range corners {
		for dy := -r; dy <= r; dy++ {
			for dx := -r; dx <= r; dx++ {
				if dx*dx+dy*dy <= r*r {
					f.px(cc[0]+dx, cc[1]+dy, c)
				}
			}
		}
	}
	if border != nil {
		f.hline(x+r, x+w-r, y, *border)
		f.hline(x+r, x+w-r, y+h-1, *border)
		f.vline(y+r, y+h-r, x, *border)
		f.vline(y+r, y+h-r, x+w-1, *border)
	}
}

func (f *fb) ring(cx, cy, rOut, rIn int, valueFrac float64, vcolor rgb, sweep, start float64) {
	if valueFrac < 0 {
		valueFrac = 0
	} else if valueFrac > 1 {
		valueFrac = 1
	}
	ro2, ri2 := rOut*rOut, rIn*rIn
	for y := cy - rOut; y <= cy+rOut; y++ {
		for x := cx - rOut; x <= cx+rOut; x++ {
			dx, dy := x-cx, y-cy
			d2 := dx*dx + dy*dy
			if d2 < ri2 || d2 > ro2 {
				continue
			}
			ang := math.Mod(math.Atan2(float64(dy), float64(dx))*180/math.Pi+360, 360)
			rel := math.Mod(ang-start+360, 360)
			if rel <= sweep {
				if rel <= sweep*valueFrac {
					f.px(x, y, vcolor)
				} else {
					f.px(x, y, trackColor)
				}
			}
		}
	}
}

func (f *fb) char(ch rune, x, y, scale int, c rgb) int {
	bm, ok := glyphs[ch]
	if !ok {
		return 8 * scale
	}
	gw := 8
	if len(bm) == 64 {
		gw = 16
	}
	bpr := gw / 8
	for ry := 0; ry < 16; ry++ {
		v, _ := strconv.ParseInt(bm[ry*bpr*2:(ry+1)*bpr*2], 16, 32)
		for rx := 0; rx < gw; rx++ {
			if v&(1<<(gw-1-rx)) != 0 {
				f.rect(x+rx*scale, y+ry*scale, scale, scale, c)
			}
		}
	}
	return gw * scale
}

func (f *fb) text(s string, x, y, scale int, c rgb) int {
	gap := 1
	if scale > 1 {
		gap = scale
	}
	for _, ch := range s {
		x += f.char(ch, x, y, scale, c) + gap
	}
	return x
}

func (f *fb) textW(s string, scale int) int {
	gap := 1
	if scale > 1 {
		gap = scale
	}
	w := 0
	for _, ch := range s {
		gw := 8
		if bm, ok := glyphs[ch]; ok && len(bm) == 64 {
			gw = 16
		}
		w += gw*scale + gap
	}
	return w
}

func (f *fb) textCenter(s string, cx, y, scale int, c rgb) { f.text(s, cx-f.textW(s, scale)/2, y, scale, c) }
func (f *fb) textRight(s string, rx, y, scale int, c rgb)  { f.text(s, rx-f.textW(s, scale), y, scale, c) }

func (f *fb) toPNG(path string) error {
	img := image.NewRGBA(image.Rect(0, 0, f.w, f.h))
	for y := 0; y < f.h; y++ {
		for x := 0; x < f.w; x++ {
			i := (y*f.w + x) * 3
			img.Set(x, y, color.RGBA{f.buf[i], f.buf[i+1], f.buf[i+2], 255})
		}
	}
	out, err := os.Create(path)
	if err != nil {
		return err
	}
	defer out.Close()
	return png.Encode(out, img)
}
