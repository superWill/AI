package render

// 公共绘制件:panel/顶栏/底部导航/KPI 行/设备列表/状态栏,
// 逐行对标 dashboard.py L245-347。

import "fmt"

// panel 对标 dashboard.panel:白卡 + 一像素克制阴影。
func panel(f *FB, x, y, w, h, r int, border bool) {
	f.RoundRect(x+2, y+3, w, h, Shadow, r, nil)
	var b *RGB
	if border {
		b = &Line
	}
	f.RoundRect(x, y, w, h, Card, r, b)
}

func paleFor(col RGB) RGB {
	if col == Green {
		return PaleGreen
	}
	if col == Amber {
		return PaleAmber
	}
	return PaleBlue
}

func drawNav(f *FB, page string, buttons *[]Button) {
	y := 442
	f.Rect(0, y, W, H-y, Card)
	f.HLine(0, W, y, Line)
	cell := 104
	x0 := (W - cell*len(Nav)) / 2
	for i, nv := range Nav {
		x := x0 + i*cell
		active := nv.ID == page || (page == "device_add" && nv.ID == "nodes")
		off, col := 0, Muted
		if active {
			f.RoundRect(x+7, y+5, cell-14, 28, PaleBlue, 14, nil)
			f.Rect(x+17, y+16, 6, 6, Blue)
			off, col = 5, Blue
		}
		f.TextCenter(nv.Label, x+cell/2+off, y+10, 1, col)
		*buttons = append(*buttons, Button{Rect: [4]int{x, y, cell, H - y}, Nav: nv.ID})
	}
}

func drawHeader(f *FB, v *View, clock, title string) {
	f.Rect(0, 0, W, 54, Card)
	f.HLine(0, W, 53, Line)
	f.RoundRect(16, 11, 32, 32, Blue2, 8, nil)
	f.TextCenter("E", 32, 17, 2, White)
	f.Text("EdgeAgent", 58, 12, 1, Ink)
	f.Text("ONE", 58, 29, 1, Blue)
	f.VLine(12, 42, 142, Line)
	f.Text(title, 158, 18, 1, Ink)
	online, total := onlineCount(v)
	clkW := f.TextW(clock, 1)
	f.Text(clock, W-clkW-18, 19, 1, Muted)
	pc := Amber
	if online == total && total > 0 {
		pc = Green
	}
	pl := fmt.Sprintf("设备 %d/%d", online, total)
	if pc == Green {
		pl = "系统正常"
	}
	pw := f.TextW(pl, 1) + 34
	px := W - clkW - 18 - pw - 20
	f.RoundRect(px, 14, pw, 25, paleFor(pc), 12, nil)
	f.Rect(px+12, 23, 7, 7, pc)
	f.Text(pl, px+24, 17, 1, pc)
}

func kpiRow(f *FB, v *View) {
	online, total := onlineCount(v)
	cx0, cy0, cw, ch, gap := 16, 132, 132, 104, 8
	okCol := Amber
	if online == total {
		okCol = Green
	}
	kpis := []struct {
		label, val, unit string
		col              RGB
	}{
		{"二次供温", Fnum(Pick(v, "sec_supply_temp"), 1), "℃", Blue},
		{"供水压力", Fnum(Pick(v, "sec_supply_pressure"), 2), "MPa", Blue},
		{"循环泵频率", Fnum(Pick(v, "pump_freq"), 1), "Hz", Green},
		{"在线设备", fmt.Sprintf("%d/%d", online, total), "", okCol},
	}
	bars := [12]int{5, 9, 7, 13, 8, 16, 11, 18, 13, 20, 14, 17}
	for i, k := range kpis {
		x := cx0 + i*(cw+gap)
		panel(f, x, cy0, cw, ch, 12, true)
		f.RoundRect(x+12, cy0+10, 24, 24, paleFor(k.col), 8, nil)
		f.Rect(x+20, cy0+18, 8, 8, k.col)
		f.Text(k.label, x+44, cy0+14, 1, Muted)
		vx := f.Text(k.val, x+14, cy0+43, 2, Ink)
		if k.unit != "" {
			f.Text(k.unit, vx+5, cy0+52, 1, Muted)
		}
		for bi, bh := range bars {
			f.RoundRect(x+14+bi*8, cy0+91-bh, 4, bh, k.col, 2, nil)
		}
	}
}

func deviceList(f *FB, v *View, x, y, w, h int) {
	online, total := onlineCount(v)
	panel(f, x, y, w, h, 12, true)
	f.Text("接入设备", x+14, y+12, 1, Muted)
	f.TextRight(fmt.Sprintf("%d/%d 在线", online, total), x+w-14, y+12, 1, Muted)
	ry := y + 36
	limit := (h - 40) / 28
	for i, d := range v.Devices {
		if i >= limit {
			break
		}
		dot, tcol := Red, Muted
		if d.OK {
			dot, tcol = Green, Ink
		}
		f.Rect(x+16, ry+7, 8, 8, dot)
		f.Text(truncRunes(d.Name, 9), x+32, ry+2, 1, Ink)
		first := "--"
		for _, np := range d.Points {
			if !np.P.V.IsNull() {
				first = fmt.Sprintf("%s %s", Fnum(np.P.V, 1), np.P.U)
				break
			}
		}
		f.TextRight(first, x+w-14, ry+2, 1, tcol)
		f.HLine(x+14, x+w-14, ry+26, Line)
		ry += 28
	}
}

func statusBar(f *FB, v *View) {
	by := 394
	msg := ""
	if len(v.Events) > 0 {
		msg = v.Events[0].Detail
	}
	if msg != "" {
		f.RoundRect(16, by, 552, 36, Card, 10, &Line)
		f.Rect(28, by+14, 8, 8, Amber)
		f.Text(truncRunes("事件 "+msg, 38), 40, by+10, 1, Ink)
	} else {
		f.RoundRect(16, by, 552, 36, Card, 10, &Line)
		f.Rect(28, by+14, 8, 8, Green)
		f.Text("系统正常 · 本机采集与设备监控运行中", 46, by+9, 1, Green)
	}
}

func qColor(q string) RGB {
	if q == "good" || q == "" {
		return Green
	}
	if q == "stale" || q == "est" {
		return Amber
	}
	return Red
}
