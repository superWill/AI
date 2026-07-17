package render

import "fmt"

// pageNodes:设备页展示运行设备，并开放模板化设备接入入口。
func pageNodes(f *FB, v *View, targets map[string]int, buttons *[]Button) {
	devs := v.Devices
	f.Text(fmt.Sprintf("运行 %d 台", len(devs)), 24, 76, 1, Muted)
	add := [4]int{646, 66, 138, 34}
	f.RoundRect(add[0], add[1], add[2], add[3], Blue, 8, nil)
	f.TextCenter("接入设备", add[0]+add[2]/2, add[1]+9, 1, White)
	*buttons = append(*buttons, Button{Rect: add, Action: "open_device_add"})
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
