package render

import "fmt"

func pageSettings(f *FB, v *View, targets map[string]int, buttons *[]Button) {
	online, total := onlineCount(v)
	pts := 0
	for _, d := range v.Devices {
		pts += len(d.Points)
	}
	brightness := max(10, min(100, v.LocalSettings.Brightness))
	if brightness == 10 && v.LocalSettings.Brightness == 0 {
		brightness = 80
	}
	theme := v.LocalSettings.Theme
	if theme != "dark" {
		theme = "light"
	}
	panel(f, 16, 66, 768, 364, 14, true)
	f.Text("画面调节", 34, 82, 1, Muted)

	f.RoundRect(34, 108, 716, 76, Card2, 12, &Line)
	f.Text("明度", 52, 126, 2, Ink)
	f.Text("10% - 100%", 52, 154, 1, Muted)
	minus := [4]int{466, 120, 68, 48}
	plus := [4]int{664, 120, 68, 48}
	f.RoundRect(minus[0], minus[1], minus[2], minus[3], Card, 10, &Line)
	f.TextCenter("-", minus[0]+minus[2]/2, 128, 2, Muted)
	f.TextCenter(fmt.Sprintf("%d%%", brightness), 599, 128, 2, Ink)
	f.RoundRect(plus[0], plus[1], plus[2], plus[3], PaleBlue, 10, &Blue)
	f.TextCenter("+", plus[0]+plus[2]/2, 128, 2, Blue)
	*buttons = append(*buttons,
		Button{Rect: minus, Action: "brightness_change", Delta: -10},
		Button{Rect: plus, Action: "brightness_change", Delta: 10})

	f.RoundRect(34, 198, 716, 76, Card2, 12, &Line)
	f.Text("风格", 52, 218, 2, Ink)
	f.Text("LIGHT / DARK", 52, 248, 1, Muted)
	choices := []struct {
		rect  [4]int
		value string
		label string
	}{
		{[4]int{466, 212, 120, 48}, "light", "LIGHT"},
		{[4]int{612, 212, 120, 48}, "dark", "DARK"},
	}
	for _, choice := range choices {
		fill, border, text := Card, Line, Muted
		if theme == choice.value {
			fill, border, text = PaleBlue, Blue, Blue
		}
		r := choice.rect
		f.RoundRect(r[0], r[1], r[2], r[3], fill, 10, &border)
		f.TextCenter(choice.label, r[0]+r[2]/2, 228, 1, text)
		*buttons = append(*buttons,
			Button{Rect: r, Action: "theme_set", Theme: choice.value})
	}

	f.Text("系统信息", 34, 294, 1, Muted)
	rows := [][2]string{
		{"设备", fmt.Sprintf("%d 台 · 在线 %d", total, online)},
		{"点位", fmt.Sprintf("%d 点", pts)},
		{"平台", "RK3506 · Buildroot · DRM"},
	}
	for i, r := range rows {
		ry := 320 + i*32
		f.Text(r[0], 52, ry, 1, Muted)
		f.Text(r[1], 220, ry, 1, Ink)
		if i < len(rows)-1 {
			f.HLine(44, W-44, ry+22, Line)
		}
	}
}
