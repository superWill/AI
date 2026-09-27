package render

import "fmt"

func pageNodes(f *FB, v *View, targets map[string]int, buttons *[]Button) {
	devs := v.Devices
	drafts := v.ConfiguredNodes
	f.Text(fmt.Sprintf("运行 %d 台 · 接入配置 %d 台", len(devs), len(drafts)), 24, 76, 1, Muted)
	add := [4]int{500, 66, 132, 34}
	f.RoundRect(add[0], add[1], add[2], add[3], Blue, 8, nil)
	f.TextCenter("设备接入", add[0]+add[2]/2, add[1]+9, 1, White)
	*buttons = append(*buttons, Button{Rect: add, Action: "open_device_add"})
	cfg := [4]int{646, 66, 138, 34}
	f.RoundRect(cfg[0], cfg[1], cfg[2], cfg[3], Blue, 8, nil)
	f.TextCenter("设备配置", cfg[0]+cfg[2]/2, cfg[1]+9, 1, White)
	*buttons = append(*buttons, Button{Rect: cfg, Action: "open_device_config"})

	cw, chh, gap := 376, 72, 8
	draftCount := min(2, len(drafts))
	type cardT struct {
		draft bool
		dev   *Device
		node  map[string]any
	}
	var cards []cardT
	for i := 0; i < min(len(devs), 8-draftCount); i++ {
		cards = append(cards, cardT{dev: &devs[i]})
	}
	for i := 0; i < draftCount; i++ {
		cards = append(cards, cardT{draft: true, node: drafts[i]})
	}
	for i, c := range cards {
		col, row := i%2, i/2
		x := 16 + col*(cw+16)
		y := 108 + row*(chh+gap)
		ok := !c.draft && c.dev.OK
		panel(f, x, y, cw, chh, 12, true)
		dot, sc, st, badge := Red, Red, "离线", PaleRed
		if c.draft {
			dot, sc, st, badge = Blue, Blue, "配置", PaleBlue
		} else if ok {
			dot, sc, st, badge = Green, Green, "在线", PaleGreen
		}
		f.Rect(x+16, y+18, 10, 10, dot)
		name := ""
		if c.draft {
			name = nodeGet(c.node, "name", "")
		} else {
			name = c.dev.Name
		}
		f.Text(truncRunes(name, 12), x+32, y+12, 1, Ink)
		f.RoundRect(x+cw-64, y+12, 50, 22, badge, 11, nil)
		f.TextCenter(st, x+cw-39, y+15, 1, sc)
		if c.draft {
			dtype := nodeGet(c.node, "deviceType", "other")
			tl, okL := DeviceTypeLabels[dtype]
			if !okL {
				tl = "设备"
			}
			f.Text(fmt.Sprintf("类型 %s", nodeGet(c.node, "deviceTypeLabel", tl)),
				x+16, y+36, 1, Muted)
			sp := nodeGet(c.node, "serialPort", nodeGet(c.node, "endpoint", "-"))
			f.Text(fmt.Sprintf("串口 %s · 地址 %s", sp, nodeGet(c.node, "slaveId", "-")),
				x+16, y+56, 1, Muted)
		} else {
			f.Text(fmt.Sprintf("类型 %s", c.dev.Type.StrOr("-")), x+16, y+36, 1, Muted)
			f.Text(fmt.Sprintf("地址 %s · 点位 %d", c.dev.Addr.StrOr("-"), len(c.dev.Points)),
				x+16, y+56, 1, Muted)
		}
	}
}
