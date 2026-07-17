package render

import "strconv"

func pageDeviceAdd(f *FB, form *AddForm, message string, busy bool, buttons *[]Button) {
	if form == nil {
		form = &AddForm{Template: "选择", Bus: "选择", Slave: 1}
	}
	back := [4]int{16, 68, 86, 30}
	f.RoundRect(back[0], back[1], back[2], back[3], Card2, 8, &Line)
	f.TextCenter("返回", back[0]+back[2]/2, back[1]+7, 1, Ink)
	*buttons = append(*buttons, Button{Rect: back, Action: "config_back"})
	f.Text("选择模板并挂到现有总线", 120, 76, 1, Blue)

	rows := []struct {
		label, value, field string
	}{
		{"型号", valueOr(form.Template, "选择"), "template"},
		{"总线", valueOr(form.Bus, "选择"), "bus"},
		{"从站地址", strconv.Itoa(form.Slave), "slave"},
	}
	for i, row := range rows {
		y := 108 + i*42
		panel(f, 16, y-4, 768, 38, 8, true)
		f.Text(row.label, 34, y+8, 1, Muted)
		f.TextCenter(row.value, 430, y+8, 1, Ink)
		minus, plus := [4]int{650, y, 48, 30}, [4]int{718, y, 48, 30}
		f.RoundRect(minus[0], minus[1], minus[2], minus[3], Card2, 7, &Line)
		f.TextCenter("-", 674, y+4, 2, Muted)
		f.RoundRect(plus[0], plus[1], plus[2], plus[3], Card2, 7, &Blue)
		f.TextCenter("+", 742, y+4, 2, Blue)
		*buttons = append(*buttons,
			Button{Rect: minus, Action: "devadd_change", Field: row.field, Delta: -1},
			Button{Rect: plus, Action: "devadd_change", Field: row.field, Delta: 1})
	}

	save := [4]int{616, 406, 168, 30}
	fill := Blue
	if busy {
		fill = Muted
	}
	f.RoundRect(save[0], save[1], save[2], save[3], fill, 9, nil)
	f.TextCenter("保存并发布", 700, 413, 1, White)
	if !busy {
		*buttons = append(*buttons, Button{Rect: save, Action: "devadd_save"})
	}
	if busy {
		f.Text("发布中…", 24, 413, 1, Amber)
	} else if message != "" {
		col := Red
		if message == "已发布" {
			col = Green
		}
		f.Text(truncRunes(message, 28), 24, 413, 1, col)
	}
}

func valueOr(value, fallback string) string {
	if value == "" {
		return fallback
	}
	return value
}
