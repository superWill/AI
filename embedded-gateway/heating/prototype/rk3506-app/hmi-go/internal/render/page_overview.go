package render

import "fmt"

func pageOverview(f *FB, v *View, targets map[string]int, buttons *[]Button) {
	online, total := onlineCount(v)
	f.Text("换热网关", 18, 70, 2, Ink)
	f.Text("换热系统", 18, 104, 1, Muted)
	if online == total {
		f.Text("运行正常", 118, 104, 1, Green)
	} else {
		f.Text("设备异常", 118, 104, 1, Amber)
	}
	kpiRow(f, v)
	cards := []struct {
		name, detail string
		col          RGB
	}{
		{"换热机组", fmt.Sprintf("供温 %s℃", Fnum(Pick(v, "sec_supply_temp"), 1)), Blue},
		{"循环水泵", fmt.Sprintf("频率 %sHz", Fnum(Pick(v, "pump_freq"), 1)), Green},
		{"调节阀", fmt.Sprintf("开度 %s%%", Fnum(Pick(v, "valve_open"), 0)), Amber},
	}
	for i, c := range cards {
		x, y, w, h := 16+i*184, 248, 176, 134
		panel(f, x, y, w, h, 12, true)
		f.Text(c.name, x+14, y+12, 1, Ink)
		f.Rect(x+w-26, y+17, 7, 7, Green)
		f.Text("运行正常", x+14, y+37, 1, Green)
		f.RoundRect(x+14, y+62, 48, 48, paleFor(c.col), 12, nil)
		f.Ring(x+38, y+86, 15, 10, 0.72, c.col, 300, 120)
		f.Text(c.detail, x+72, y+79, 1, Muted)
	}
	x, y, w := 584, 66, 200
	panel(f, x, y, w, 364, 14, true)
	f.Text("本机监控中", x+16, y+16, 2, Ink)
	f.Text("离线可运行 · 就地监控", x+16, y+50, 1, Muted)
	f.HLine(x+14, x+w-14, y+76, Line)
	duties := []struct {
		name, desc string
		col        RGB
	}{
		{"数据采集", "读取设备点位", Green},
		{"设备运行", fmt.Sprintf("%d/%d 在线", online, total), Blue},
		{"本机控制", "安全校验下发", Blue},
		{"云端上行", "本机运行正常", Muted},
	}
	for i, d := range duties {
		ry := y + 92 + i*64
		frac := 1.0
		if d.col == Muted {
			frac = 0.35
		}
		f.Ring(x+24, ry+10, 9, 6, frac, d.col, 360, 0)
		if i < len(duties)-1 {
			f.VLine(ry+20, ry+58, x+24, Line)
		}
		nameCol := d.col
		if d.col == Muted {
			nameCol = Ink
		}
		f.Text(d.name, x+44, ry, 1, nameCol)
		f.Text(d.desc, x+44, ry+23, 1, Muted)
	}
	statusBar(f, v)
}
