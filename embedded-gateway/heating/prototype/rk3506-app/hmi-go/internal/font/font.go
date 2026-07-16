// Package font 提供 GNU Unifont 子集字形的游程(run)解码。
// 语义对标 dashboard.py 的 _GLYPH_RUNS:每字形固定 16 行,
// hex 串长 64 → 16px 宽(CJK),32 → 8px 宽(ASCII/半角),位序 MSB 在最左像素。
package font

import "strconv"

type Run struct{ Start, End int }

type Glyph struct {
	W    int
	Rows [16][]Run
}

var glyphs map[rune]Glyph

func init() {
	glyphs = make(map[rune]Glyph, len(glyphHex))
	for ch, bm := range glyphHex {
		glyphs[ch] = decode(bm)
	}
}

func decode(bm string) Glyph {
	gw := 8
	if len(bm) == 64 {
		gw = 16
	}
	bpr := gw / 8
	g := Glyph{W: gw}
	for ry := 0; ry < 16; ry++ {
		val, err := strconv.ParseUint(bm[ry*bpr*2:(ry+1)*bpr*2], 16, 32)
		if err != nil {
			continue // 与 Python 不同处仅在于非法 hex;生成器已断言合法
		}
		var runs []Run
		rx := 0
		for rx < gw {
			if val&(1<<uint(gw-1-rx)) == 0 {
				rx++
				continue
			}
			start := rx
			for rx < gw && val&(1<<uint(gw-1-rx)) != 0 {
				rx++
			}
			runs = append(runs, Run{start, rx})
		}
		g.Rows[ry] = runs
	}
	return g
}

// Get 返回字形;缺字形 ok=false(调用方按 8*scale 占位前进,同 Python)。
func Get(ch rune) (Glyph, bool) {
	g, ok := glyphs[ch]
	return g, ok
}

// Width 返回 text_w 语义的字宽:缺字形按 8 计。
func Width(ch rune) int {
	if g, ok := glyphs[ch]; ok {
		return g.W
	}
	return 8
}
