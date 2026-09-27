package render

import "fmt"

var parityDisplay = map[string]string{"none": "N", "even": "E", "odd": "O"}

func pageDeviceConfig(f *FB, form map[string]any, slot, count int, message string, buttons *[]Button) {
	back := [4]int{16, 68, 86, 30}
	f.RoundRect(back[0], back[1], back[2], back[3], Card2, 8, &Line)
	*buttons = append(*buttons, Button{Rect: back, Action: "config_back"})
	f.TextCenter("返回", back[0]+back[2]/2, back[1]+7, 1, Ink)
	title := "设备配置"
	if slot == 0 {
		title = "设备接入"
	}
	f.Text(title+" · 离线配置", 120, 76, 1, Blue)
	rec := "+ 设备"
	if slot != 0 {
		rec = fmt.Sprintf("设备 %d/%d", slot, count)
	}
	par, ok := parityDisplay[nodeGet(form, "parity", "")]
	if !ok {
		par = "N"
	}
	rows := []struct{ label, value, field string }{
		{"设备", rec, "record"},
		{"设备类型", nodeGet(form, "deviceTypeLabel", "设备"), "deviceType"},
		{"串口", nodeGet(form, "serialPort", "/dev/ttyS1"), "serialPort"},
		{"速率", nodeGet(form, "baudRate", "9600"), "baudRate"},
		{"校验", "8" + par + "1", "parity"},
		{"地址", nodeGet(form, "slaveId", "1"), "slaveId"},
		{"采集", nodeGet(form, "pollInterval", "1000") + " ms", "pollInterval"},
	}
	for i, r := range rows {
		y := 108 + i*42
		panel(f, 16, y-4, 768, 38, 8, true)
		f.Text(r.label, 34, y+8, 1, Muted)
		f.TextCenter(r.value, 430, y+8, 1, Ink)
		minus := [4]int{650, y, 48, 30}
		plus := [4]int{718, y, 48, 30}
		f.RoundRect(minus[0], minus[1], minus[2], minus[3], Card2, 7, &Line)
		f.TextCenter("-", 674, y+4, 2, Muted)
		f.RoundRect(plus[0], plus[1], plus[2], plus[3], Card2, 7, &Blue)
		f.TextCenter("+", 742, y+4, 2, Blue)
		*buttons = append(*buttons,
			Button{Rect: minus, Action: "config_change", Field: r.field, Delta: -1},
			Button{Rect: plus, Action: "config_change", Field: r.field, Delta: 1})
	}
	save := [4]int{616, 406, 168, 30}
	f.RoundRect(save[0], save[1], save[2], save[3], Blue, 9, nil)
	lbl := "本机配置"
	if slot == 0 {
		lbl = "设备接入"
	}
	f.TextCenter(lbl, 700, 413, 1, White)
	*buttons = append(*buttons, Button{Rect: save, Action: "config_save"})
	if message != "" {
		col := Red
		if message == "配置正常" || message == "设备已接入" {
			col = Green
		}
		f.Text(truncRunes(message, 28), 24, 413, 1, col)
	}
}
