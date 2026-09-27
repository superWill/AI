package render

import "fmt"

func pageMonitor(f *FB, v *View, targets map[string]int, buttons *[]Button) {
	if len(displayCards) > 0 {
		pageMonitorCards(f, v)
		return
	}
	pts := AllPoints(v)
	panel(f, 16, 66, 768, 364, 14, true)
	f.Text(fmt.Sprintf("采集点表 · 共 %d 点", len(pts)), 34, 82, 1, Muted)
	colW := 356
	per := 11
	n := min(len(pts), per*2)
	for idx := 0; idx < n; idx++ {
		p := pts[idx]
		col, row := idx/per, idx%per
		x := 34 + col*(colW+22)
		ry := 110 + row*27
		f.Rect(x, ry+5, 7, 7, qColor(p.Q))
		f.Text(truncRunes(p.PID, 16), x+14, ry, 1, Ink)
		vc := Muted
		if p.Q == "good" || p.Q == "" {
			vc = Ink
		}
		f.TextRight(fmt.Sprintf("%s %s", Fnum(p.V, 1), p.U), x+colW-6, ry, 1, vc)
		f.HLine(x, x+colW-6, ry+22, Line)
	}
}

// pageMonitorCards:display_model 驱动,2 列流式,超高卡片截断(跳过)。
func pageMonitorCards(f *FB, v *View) {
	colW := 378
	colx := [2]int{16, 406}
	coly := [2]int{66, 66}
	for _, c := range displayCards {
		fields := c.Fields
		if len(fields) > 6 {
			fields = fields[:6]
		}
		ch := 30 + len(fields)*22 + 8
		ci := 1
		if coly[0] <= coly[1] {
			ci = 0
		}
		x, y := colx[ci], coly[ci]
		if y+ch > 430 {
			continue
		}
		panel(f, x, y, colW, ch, 12, true)
		f.Text(truncRunes(c.Title, 14), x+14, y+8, 1, Muted)
		ry := y + 30
		for _, fd := range fields {
			var pt Point // point_of 未命中 → 空 dict 语义(q="",v=None,u="")
			if p := PointOf(v, fd.PID); p != nil {
				pt = *p
			}
			f.Rect(x+14, ry+5, 7, 7, qColor(pt.Q))
			f.Text(truncRunes(fd.Label, 10), x+24, ry, 1, Ink)
			vc := Muted
			if pt.Q == "good" || pt.Q == "" {
				vc = Ink
			}
			f.TextRight(fmt.Sprintf("%s %s", Fnum(pt.V, 1), pt.U), x+colW-14, ry, 1, vc)
			ry += 22
		}
		coly[ci] = y + ch + 12
	}
}
