package render

import "fmt"

// pageNodes:设备页只读展示运行设备。配置入口已退役(设备接入走 Web /config 页)。
func pageNodes(f *FB, v *View, targets map[string]int, buttons *[]Button) {
	devs := v.Devices
	f.Text(fmt.Sprintf("运行 %d 台", len(devs)), 24, 76, 1, Muted)
	cw, chh, gap := 376, 72, 8
	for i := 0; i < min(len(devs), 8); i++ {
		d := &devs[i]
		col, row := i%2, i/2
		x := 16 + col*(cw+16)
		y := 108 + row*(chh+gap)
		panel(f, x, y, cw, chh, 12, true)
		dot, sc, st, badge := Red, Red, "离线", PaleRed
		if d.OK {
			dot, sc, st, badge = Green, Green, "在线", PaleGreen
		}
		f.Rect(x+16, y+18, 10, 10, dot)
		f.Text(truncRunes(d.Name, 12), x+32, y+12, 1, Ink)
		f.RoundRect(x+cw-64, y+12, 50, 22, badge, 11, nil)
		f.TextCenter(st, x+cw-39, y+15, 1, sc)
		f.Text(fmt.Sprintf("类型 %s", d.Type.StrOr("-")), x+16, y+36, 1, Muted)
		f.Text(fmt.Sprintf("地址 %s · 点位 %d", d.Addr.StrOr("-"), len(d.Points)),
			x+16, y+56, 1, Muted)
	}
}
