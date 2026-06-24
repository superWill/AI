// LCD 多页渲染(对照 dashboard.py 的页面函数 + 颜色/导航/控制常量)。增量B。
package main

import (
	"fmt"
	"sort"
	"strconv"
)

// 颜色(对照 dashboard.py;BG/SIDEBAR 为紫色 Go 标记)。trackColor 在 ui_lcd_fb.go。
var (
	cBG      = rgb{38, 20, 58}
	cSIDEBAR = rgb{124, 58, 237}
	cCARD    = rgb{30, 41, 59}
	cCARD2   = rgb{23, 33, 52}
	cLINE    = rgb{51, 65, 85}
	cINK     = rgb{226, 232, 240}
	cMUTED   = rgb{148, 163, 184}
	cBLUE    = rgb{56, 189, 248}
	cBLUE2   = rgb{37, 99, 235}
	cGREEN   = rgb{34, 197, 94}
	cAMBER   = rgb{245, 158, 11}
	cRED     = rgb{239, 68, 68}
)

var lcdNav = [][2]string{{"overview", "总览"}, {"monitor", "监控"}, {"nodes", "设备"}, {"control", "控制"}, {"settings", "设置"}}
var lcdPageTitle = map[string]string{"overview": "总览", "monitor": "数据监控", "nodes": "设备管理", "control": "就地控制", "settings": "系统设置"}

type ctlDef struct {
	label, fbid, spid string
	lo, hi, step      float64
	unit              string
	col               rgb
}

var lcdControls = []ctlDef{
	{"二次供温", "sec_supply_temp", "sec_supply_temp_sp", 20, 75, 2, "℃", cBLUE},
	{"阀位开度", "valve_open", "valve_open_sp", 0, 100, 5, "%", cGREEN},
	{"循环泵频率", "pump_freq", "pump_freq_sp", 0, 50, 2, "Hz", cAMBER},
}

type dispCard struct {
	title  string
	fields [][2]string // (point_id, label)
}

var displayCards []dispCard

func configureDisplayUI(displayModel obj) {
	displayCards = nil
	if displayModel == nil {
		return
	}
	type item struct {
		pi, prio int
		title    string
		fields   [][2]string
	}
	var items []item
	for pi, pgi := range asArr(displayModel["pages"]) {
		pg := asObj(pgi)
		for _, ci := range asArr(pg["cards"]) {
			card := asObj(ci)
			title := asStr(card["label"])
			if title == "" {
				title = asStr(card["card"])
			}
			var fields [][2]string
			for _, fi := range asArr(card["fields"]) {
				fld := asObj(fi)
				pid := asStr(fld["point_id"])
				if pid == "" {
					continue
				}
				lbl := asStr(fld["label"])
				if lbl == "" {
					lbl = pid
				}
				fields = append(fields, [2]string{pid, lbl})
			}
			items = append(items, item{pi, int(toF(getOr(card, "priority", float64(50)))), title, fields})
		}
	}
	// 稳定排序 by (pi, prio)
	for i := 1; i < len(items); i++ {
		for j := i; j > 0 && (items[j].pi < items[j-1].pi || (items[j].pi == items[j-1].pi && items[j].prio < items[j-1].prio)); j-- {
			items[j], items[j-1] = items[j-1], items[j]
		}
	}
	for _, it := range items {
		displayCards = append(displayCards, dispCard{it.title, it.fields})
	}
}

func fnum(v interface{}, d int) string {
	if v == nil {
		return "--"
	}
	if f, ok := pythonFloat(v); ok {
		return strconv.FormatFloat(f, 'f', d, 64)
	}
	return fmt.Sprint(v)
}

func lcdPick(view obj, pid string) interface{} {
	for _, di := range asArr(view["devices"]) {
		p := asObj(asObj(asObj(di)["points"])[pid])
		if p != nil && p["v"] != nil {
			return p["v"]
		}
	}
	return nil
}

func lcdPointOf(view obj, pid string) obj {
	for _, di := range asArr(view["devices"]) {
		if p := asObj(asObj(di)["points"])[pid]; p != nil {
			return asObj(p)
		}
	}
	return nil
}

// pointOrder: 点位遍历顺序。Python dict 按插入序;Go map 随机,故对拍时
// 由 harness 注入 _porder(= Python 插入序);运行时缺省退化为按 key 排序(确定性)。
func pointOrder(d obj) []string {
	pts := asObj(d["points"])
	if ord := asArr(d["_porder"]); len(ord) > 0 {
		out := make([]string, 0, len(ord))
		for _, k := range ord {
			if ks := asStr(k); pts[ks] != nil {
				out = append(out, ks)
			}
		}
		return out
	}
	keys := make([]string, 0, len(pts))
	for k := range pts {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

func qcolor(q string) rgb {
	switch q {
	case "good", "":
		return cGREEN
	case "stale", "est":
		return cAMBER
	}
	return cRED
}

func runeClip(s string, n int) string {
	r := []rune(s)
	if len(r) > n {
		return string(r[:n])
	}
	return s
}

func drawSidebar(f *fb, page string, buttons *[]obj) {
	f.rect(0, 0, 76, lcdH, cSIDEBAR)
	f.roundRect(20, 12, 36, 32, cBLUE2, 8, nil)
	f.textCenter("N", 38, 18, 2, rgb{255, 255, 255})
	for i, nv := range lcdNav {
		pid, label := nv[0], nv[1]
		y := 66 + i*78
		active := pid == page
		bg := cSIDEBAR
		var bd *rgb
		if active {
			bg = rgb{19, 35, 58}
			bd = &cBLUE
		}
		f.roundRect(8, y, 60, 68, bg, 10, bd)
		ic := cCARD2
		var icbd *rgb
		if active {
			ic = cBLUE2
		} else {
			icbd = &cLINE
		}
		f.roundRect(26, y+8, 24, 24, ic, 6, icbd)
		lc := cMUTED
		if active {
			lc = rgb{255, 255, 255}
		}
		f.rect(32, y+14, 12, 3, lc)
		f.rect(32, y+19, 12, 3, lc)
		tc := cMUTED
		if active {
			tc = cINK
		}
		f.textCenter(label, 38, y+40, 1, tc)
		*buttons = append(*buttons, obj{"rect": arr{4, y, 68, 72}, "nav": pid})
	}
}

func drawHeader(f *fb, view obj, clock, title string) {
	f.rect(76, 0, lcdW-76, 52, cCARD2)
	f.hline(76, lcdW, 52, cLINE)
	f.text(title, 92, 16, 2, cINK)
	devs := asArr(view["devices"])
	online := 0
	for _, di := range devs {
		if b, _ := asObj(di)["ok"].(bool); b {
			online++
		}
	}
	total := len(devs)
	clkW := f.textW(clock, 1)
	f.text(clock, lcdW-clkW-14, 18, 1, cMUTED)
	pc := cAMBER
	if online == total && total > 0 {
		pc = cGREEN
	}
	pl := fmt.Sprintf("在线 %d/%d", online, total)
	pw := f.textW(pl, 1) + 34
	px := lcdW - clkW - 14 - pw - 14
	chip := rgb{50, 38, 16}
	if pc == cGREEN {
		chip = rgb{20, 45, 30}
	}
	f.roundRect(px, 14, pw, 24, chip, 12, nil)
	f.rect(px+12, 23, 7, 7, pc)
	f.text(pl, px+24, 17, 1, pc)
}

func countPoints(view obj) int {
	n := 0
	for _, di := range asArr(view["devices"]) {
		n += len(asObj(asObj(di)["points"]))
	}
	return n
}

func kpiRow(f *fb, view obj) {
	devs := asArr(view["devices"])
	online := 0
	for _, di := range devs {
		if b, _ := asObj(di)["ok"].(bool); b {
			online++
		}
	}
	total := len(devs)
	pts := countPoints(view)
	cx0, cy0, cw, ch, gap := 88, 64, 168, 76, 12
	onCol := cAMBER
	if online == total {
		onCol = cGREEN
	}
	kpis := []struct {
		label, val, unit string
		col              rgb
	}{
		{"接入设备", strconv.Itoa(total), "台", cBLUE},
		{"在线", fmt.Sprintf("%d/%d", online, total), "", onCol},
		{"采集点位", strconv.Itoa(pts), "点", cBLUE},
		{"上行 MQTT", "在线", "", cGREEN},
	}
	for i, k := range kpis {
		x := cx0 + i*(cw+gap)
		f.roundRect(x, cy0, cw, ch, cCARD, 10, &cLINE)
		f.text(k.label, x+14, cy0+10, 1, cMUTED)
		vx := f.text(k.val, x+14, cy0+32, 3, k.col)
		if k.unit != "" {
			f.text(k.unit, vx+6, cy0+46, 1, cMUTED)
		}
	}
}

func deviceList(f *fb, view obj, x, y, w, h int) {
	devs := asArr(view["devices"])
	online := 0
	for _, di := range devs {
		if b, _ := asObj(di)["ok"].(bool); b {
			online++
		}
	}
	f.roundRect(x, y, w, h, cCARD, 10, &cLINE)
	f.text("接入设备", x+14, y+12, 1, cMUTED)
	f.textRight(fmt.Sprintf("%d/%d 在线", online, len(devs)), x+w-14, y+12, 1, cMUTED)
	ry := y + 36
	limit := (h - 40) / 28
	for idx, di := range devs {
		if idx >= limit {
			break
		}
		d := asObj(di)
		ok, _ := d["ok"].(bool)
		dot := cRED
		if ok {
			dot = cGREEN
		}
		f.rect(x+16, ry+7, 8, 8, dot)
		f.text(runeClip(asStr(d["name"]), 9), x+32, ry+2, 1, cINK)
		first := "--"
		pts := asObj(d["points"])
		for _, pid := range pointOrder(d) {
			p := asObj(pts[pid])
			if p["v"] != nil {
				first = fmt.Sprintf("%s %s", fnum(p["v"], 1), asStr(p["u"]))
				break
			}
		}
		tc := cMUTED
		if ok {
			tc = cINK
		}
		f.textRight(first, x+w-14, ry+2, 1, tc)
		f.hline(x+14, x+w-14, ry+26, rgb{37, 47, 66})
		ry += 28
	}
}

func statusBar(f *fb, view obj) {
	by := 424
	events := asArr(view["events"])
	if len(events) > 0 {
		msg := asStr(asObj(events[0])["detail"])
		f.roundRect(88, by, lcdW-88-12, 44, cCARD2, 10, nil)
		f.rect(104, by+17, 8, 8, cAMBER)
		f.text(runeClip("事件 "+msg, 42), 124, by+13, 1, cINK)
		return
	}
	f.roundRect(88, by, lcdW-88-12, 44, cCARD2, 10, nil)
	f.rect(104, by+17, 8, 8, cGREEN)
	f.text("系统正常 · 采集与上行运行中", 124, by+13, 1, cGREEN)
}

func pageOverview(f *fb, view, targets obj, buttons *[]obj) {
	kpiRow(f, view)
	gx0, gy := 88, 152
	f.roundRect(gx0, gy, 332, 252, cCARD, 10, &cLINE)
	f.text("关键运行参数", gx0+16, gy+12, 1, cMUTED)
	type g struct {
		label    string
		val      interface{}
		lo, hi   float64
		unit     string
		col      rgb
	}
	gauges := []g{
		{"二次供温", lcdPick(view, "sec_supply_temp"), 0, 80, "℃", cBLUE},
		{"阀位开度", lcdPick(view, "valve_open"), 0, 100, "%", cGREEN},
		{"泵频率", lcdPick(view, "pump_freq"), 0, 50, "Hz", cAMBER},
	}
	cxs := []int{gx0 + 70, gx0 + 166, gx0 + 262}
	for i, ga := range gauges {
		cxp := cxs[i]
		frac := 0.0
		if ga.val != nil {
			fv, _ := pythonFloat(ga.val)
			frac = (fv - ga.lo) / (ga.hi - ga.lo)
		}
		f.ring(cxp, gy+120, 44, 33, frac, ga.col, 270, 135)
		dd := 1
		if ga.unit == "%" {
			dd = 0
		}
		f.textCenter(fnum(ga.val, dd), cxp, gy+108, 2, cINK)
		f.textCenter(ga.unit, cxp, gy+128, 1, cMUTED)
		f.textCenter(ga.label, cxp, gy+178, 1, cMUTED)
	}
	deviceList(f, view, 432, gy, lcdW-432-12, 252)
	statusBar(f, view)
}

func pageMonitor(f *fb, view, targets obj, buttons *[]obj) {
	if len(displayCards) > 0 {
		pageMonitorCards(f, view)
		return
	}
	var pts [][5]interface{}
	for _, di := range asArr(view["devices"]) {
		d := asObj(di)
		dpts := asObj(d["points"])
		for _, pid := range pointOrder(d) {
			p := asObj(dpts[pid])
			pts = append(pts, [5]interface{}{asStr(d["name"]), pid, p["v"], asStr(p["u"]), asStr(p["q"])})
		}
	}
	f.roundRect(88, 64, lcdW-88-12, 400, cCARD, 10, &cLINE)
	f.text(fmt.Sprintf("采集点表 · 共 %d 点", len(pts)), 104, 76, 1, cMUTED)
	colW := (lcdW - 88 - 12 - 24) / 2
	per := 13
	for idx := 0; idx < len(pts) && idx < per*2; idx++ {
		col := idx / per
		row := idx % per
		x := 104 + col*(colW+8)
		ry := 102 + row*27
		pid, _ := pts[idx][1].(string)
		q, _ := pts[idx][4].(string)
		f.rect(x, ry+5, 7, 7, qcolor(q))
		f.text(runeClip(pid, 16), x+14, ry, 1, cINK)
		tc := cMUTED
		if q == "good" || q == "" {
			tc = cINK
		}
		f.textRight(fmt.Sprintf("%s %s", fnum(pts[idx][2], 1), pts[idx][3]), x+colW-6, ry, 1, tc)
		f.hline(x, x+colW-6, ry+22, rgb{34, 44, 62})
	}
}

func pageMonitorCards(f *fb, view obj) {
	colW := (lcdW - 88 - 12 - 12) / 2
	colx := []int{88, 88 + colW + 12}
	coly := []int{64, 64}
	for _, c := range displayCards {
		fields := c.fields
		if len(fields) > 6 {
			fields = fields[:6]
		}
		ch := 30 + len(fields)*22 + 8
		ci := 0
		if coly[0] > coly[1] {
			ci = 1
		}
		x, y := colx[ci], coly[ci]
		if y+ch > 466 {
			continue
		}
		f.roundRect(x, y, colW, ch, cCARD, 10, &cLINE)
		f.text(runeClip(c.title, 14), x+14, y+8, 1, cMUTED)
		ry := y + 30
		for _, fld := range fields {
			p := lcdPointOf(view, fld[0])
			q := asStr(p["q"])
			f.rect(x+14, ry+5, 7, 7, qcolor(q))
			f.text(runeClip(fld[1], 10), x+24, ry, 1, cINK)
			tc := cMUTED
			if q == "good" || q == "" {
				tc = cINK
			}
			var pv interface{}
			var pu string
			if p != nil {
				pv, pu = p["v"], asStr(p["u"])
			}
			f.textRight(fmt.Sprintf("%s %s", fnum(pv, 1), pu), x+colW-14, ry, 1, tc)
			ry += 22
		}
		coly[ci] = y + ch + 12
	}
}

func pageNodes(f *fb, view, targets obj, buttons *[]obj) {
	devs := asArr(view["devices"])
	cw, chh, gap := (lcdW-88-12-12)/2, 92, 12
	for i, di := range devs {
		if i >= 8 {
			break
		}
		d := asObj(di)
		col, row := i%2, i/2
		x := 88 + col*(cw+gap)
		y := 64 + row*(chh+gap)
		ok, _ := d["ok"].(bool)
		f.roundRect(x, y, cw, chh, cCARD, 10, &cLINE)
		dot := cRED
		if ok {
			dot = cGREEN
		}
		f.rect(x+16, y+18, 10, 10, dot)
		f.text(runeClip(asStr(d["name"]), 12), x+32, y+12, 1, cINK)
		sc, st, chip := cRED, "离线", rgb{50, 24, 24}
		if ok {
			sc, st, chip = cGREEN, "在线", rgb{20, 45, 30}
		}
		f.roundRect(x+cw-64, y+12, 50, 22, chip, 11, nil)
		f.textCenter(st, x+cw-39, y+15, 1, sc)
		f.text("类型 "+asStr(getOr(d, "type", "-")), x+16, y+40, 1, cMUTED)
		f.text(fmt.Sprintf("地址 %s · 点位 %d", numStr(getOr(d, "addr", "-")), len(asObj(d["points"]))), x+16, y+62, 1, cMUTED)
	}
}

func pageControl(f *fb, view, targets obj, buttons *[]obj) {
	f.roundRect(88, 64, lcdW-88-12, 400, cCARD, 10, &cLINE)
	f.text("就地控制 · 点 −/+ 下发设定值(安全校验)", 104, 78, 1, cMUTED)
	for i, c := range lcdControls {
		ry := 116 + i*106
		cur := lcdPick(view, c.fbid)
		var tgt float64
		if t, ok := targets[c.fbid]; ok && t != nil {
			tgt = toF(t)
		} else if cur != nil {
			cv, _ := pythonFloat(cur)
			tgt = pyRound(cv, 0)
		} else {
			tgt = c.lo
		}
		f.text(c.label, 116, ry, 2, cINK)
		frac := 0.0
		if cur != nil {
			cv, _ := pythonFloat(cur)
			frac = (cv - c.lo) / (c.hi - c.lo)
			if frac < 0 {
				frac = 0
			} else if frac > 1 {
				frac = 1
			}
		}
		f.rect(116, ry+40, 300, 12, trackColor)
		f.rect(116, ry+40, int(300*frac), 12, c.col)
		dd := 1
		if c.unit == "%" {
			dd = 0
		}
		f.text(fmt.Sprintf("当前 %s%s", fnum(cur, dd), c.unit), 116, ry+60, 1, cMUTED)
		f.roundRect(470, ry, 70, 70, cCARD2, 12, &cLINE)
		f.textCenter("-", 470+35, ry+12, 3, cMUTED)
		pbg := cCARD2
		if c.col == cGREEN {
			pbg = rgb{18, 38, 26}
		}
		f.roundRect(650, ry, 70, 70, pbg, 12, &c.col)
		f.textCenter("+", 650+35, ry+12, 3, c.col)
		f.textCenter(fnum(tgt, 0), 595, ry+10, 3, cINK)
		f.textCenter("设定 "+c.unit, 595, ry+58, 1, cMUTED)
		*buttons = append(*buttons,
			obj{"rect": arr{470, ry, 70, 70}, "fb": c.fbid, "sp": c.spid, "delta": -c.step, "lo": c.lo, "hi": c.hi},
			obj{"rect": arr{650, ry, 70, 70}, "fb": c.fbid, "sp": c.spid, "delta": c.step, "lo": c.lo, "hi": c.hi})
	}
}

func pageSettings(f *fb, view, targets obj, buttons *[]obj) {
	devs := asArr(view["devices"])
	online := 0
	for _, di := range devs {
		if b, _ := asObj(di)["ok"].(bool); b {
			online++
		}
	}
	pts := countPoints(view)
	f.roundRect(88, 64, lcdW-88-12, 400, cCARD, 10, &cLINE)
	f.text("系统信息", 104, 78, 1, cMUTED)
	rows := [][2]string{
		{"设备 ID", asStr(getOr(view, "device_id", "rk3506-gw-01"))},
		{"接入设备", fmt.Sprintf("%d 台(在线 %d)", len(devs), online)},
		{"采集点位", fmt.Sprintf("%d 点", pts)},
		{"上行链路", "MQTT 在线"},
		{"本机地址", "192.168.1.10 : 8092"},
		{"应用版本", "nexus-edge gateway v1"},
		{"运行平台", "RK3506 · Buildroot · DRM"},
	}
	for i, kv := range rows {
		ry := 112 + i*44
		f.text(kv[0], 116, ry, 1, cMUTED)
		f.text(kv[1], 320, ry, 1, cINK)
		f.hline(104, lcdW-24, ry+28, rgb{34, 44, 62})
	}
}

var lcdPages = map[string]func(*fb, obj, obj, *[]obj){
	"overview": pageOverview, "monitor": pageMonitor, "nodes": pageNodes,
	"control": pageControl, "settings": pageSettings,
}

// lcdRender:对照 dashboard.render —— clear + sidebar + header + 页面;返回帧 + 按钮。
func lcdRender(view obj, clock string, targets obj, page string) (*fb, []obj) {
	if targets == nil {
		targets = obj{}
	}
	buttons := []obj{}
	f := newFB(lcdW, lcdH)
	f.clear(cBG)
	if _, ok := lcdPages[page]; !ok {
		page = "overview"
	}
	drawSidebar(f, page, &buttons)
	drawHeader(f, view, clock, lcdPageTitle[page])
	lcdPages[page](f, view, targets, &buttons)
	return f, buttons
}
