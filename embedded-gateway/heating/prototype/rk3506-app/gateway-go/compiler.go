// 配置编译器 —— config_draft.json → 运行产物（Go 移植自 compiler.py，逐函数对照）。
//
// 设计原则与 Python 版一致：纯函数 Validate / Compile；零外部依赖（仅标准库）。
// 校验错误信息与 Python 版逐字一致，便于对拍。
package main

import (
	"fmt"
	"sort"
	"strings"
)

// 与 schema 对齐的枚举（只列编译器真正依赖的）
var protoTemplates = set("rs485_8ai_modbus", "rs485_8di_modbus", "rs485_8do_modbus",
	"rs485_ao_modbus", "modbus_tcp_generic", "heat_meter_modbus", "energy_meter_modbus",
	"vfd_modbus", "private_mcu")
var businessTemplates = set("temperature_point", "pressure_point", "circulation_pump",
	"makeup_pump", "control_valve", "heat_meter", "energy_meter", "vfd", "safety_io")
var roles = set("measurement", "feedback", "command", "setpoint", "fault", "derived")
var writableRoles = set("command", "setpoint")
var dataWidth = map[string]float64{"bool": 1, "uint16": 1, "int16": 1, "uint32": 2, "int32": 2, "float32": 2}
var pages = set("overview", "primary_loop", "secondary_loop", "pumps", "makeup",
	"devices", "alarms", "system")

// --------------------------------------------------------------------------- //
// 类型别名 + 取值助手（对齐 Python dict/list 语义；JSON 数字统一 float64）
// --------------------------------------------------------------------------- //
type obj = map[string]interface{}
type arr = []interface{}

func set(xs ...string) map[string]bool {
	m := map[string]bool{}
	for _, x := range xs {
		m[x] = true
	}
	return m
}
func asObj(v interface{}) obj   { m, _ := v.(obj); return m }
func asArr(v interface{}) arr   { s, _ := v.(arr); return s }
func asStr(v interface{}) string { s, _ := v.(string); return s }
func has(m obj, k string) bool   { _, ok := m[k]; return ok }

// get 取键，缺失返回 nil
func get(m obj, k string) interface{} {
	if m == nil {
		return nil
	}
	return m[k]
}

// getOr 取键，缺失/为 nil 时返回 def
func getOr(m obj, k string, def interface{}) interface{} {
	if v, ok := m[k]; ok && v != nil {
		return v
	}
	return def
}

// reprStr 模拟 Python 的 {x!r}：字符串加单引号，nil 为 None
func reprStr(v interface{}) string {
	if v == nil {
		return "None"
	}
	if s, ok := v.(string); ok {
		return "'" + s + "'"
	}
	return fmt.Sprintf("%v", v)
}

// ===========================================================================
// 校验（结构必填 + x-compiler-constraints）—— 错误串与 compiler.py 逐字一致
// ===========================================================================
func Validate(draft obj) []string {
	errs := []string{}
	if draft == nil {
		return []string{"顶层必须是对象"}
	}
	for _, k := range []string{"config_version", "industry", "buses", "hardware_devices", "business_devices"} {
		if !has(draft, k) {
			errs = append(errs, "缺少必填字段 "+k)
		}
	}
	if len(errs) > 0 {
		return errs
	}

	industry := asStr(draft["industry"])
	buses := asArr(get(draft, "buses"))
	hws := asArr(get(draft, "hardware_devices"))
	bizs := asArr(get(draft, "business_devices"))

	// --- 总线 ---
	busIDs := map[string]bool{}
	for _, bi := range buses {
		b := asObj(bi)
		bid := asStr(get(b, "bus_id"))
		if bid == "" {
			errs = append(errs, "bus 缺少 bus_id")
			continue
		}
		if busIDs[bid] {
			errs = append(errs, "bus_id 重复: "+bid)
		}
		busIDs[bid] = true
		if asStr(get(b, "type")) == "rs485" {
			for _, f := range []string{"baud", "parity", "data_bits", "stop_bits"} {
				if !has(b, f) {
					errs = append(errs, fmt.Sprintf("rs485 总线 %s 缺少 %s", bid, f))
				}
			}
		}
	}

	// --- 硬件设备 + 通道 ---
	devChannels := map[string]map[string]obj{} // device_id -> {channel: chan}
	devIDs := map[string]bool{}
	busSlaves := map[string]map[string]bool{} // bus_id -> {slave}
	for _, di := range hws {
		d := asObj(di)
		did := asStr(get(d, "device_id"))
		if did == "" {
			errs = append(errs, "hardware_device 缺少 device_id")
			continue
		}
		if devIDs[did] {
			errs = append(errs, "device_id 重复: "+did)
		}
		devIDs[did] = true
		if !protoTemplates[asStr(get(d, "hardware_template"))] {
			errs = append(errs, fmt.Sprintf("%s: 未知 hardware_template %s", did, reprStr(get(d, "hardware_template"))))
		}
		if !busIDs[asStr(get(d, "bus_id"))] {
			errs = append(errs, fmt.Sprintf("%s: bus_id %s 未声明", did, reprStr(get(d, "bus_id"))))
		}
		if slave := get(d, "slave"); slave != nil {
			busID := asStr(get(d, "bus_id"))
			bag := busSlaves[busID]
			if bag == nil {
				bag = map[string]bool{}
				busSlaves[busID] = bag
			}
			sk := fmt.Sprintf("%v", slave)
			if bag[sk] {
				errs = append(errs, fmt.Sprintf("总线 %s 从站地址重复: %v", busID, slave))
			}
			bag[sk] = true
		}
		chans := map[string]obj{}
		for _, ci := range asArr(get(d, "channels")) {
			c := asObj(ci)
			ch := asStr(get(c, "channel"))
			if ch == "" {
				errs = append(errs, did+": 通道缺少 channel")
				continue
			}
			if _, dup := chans[ch]; dup {
				errs = append(errs, fmt.Sprintf("%s: 通道 %s 重复", did, ch))
			}
			chans[ch] = c
			if _, ok := dataWidth[asStr(get(c, "data_type"))]; !ok {
				errs = append(errs, fmt.Sprintf("%s.%s: 未知 data_type %s", did, ch, reprStr(get(c, "data_type"))))
			}
			if len(ch) >= 2 && (ch[:2] == "AI" || ch[:2] == "AO") {
				if !has(c, "raw_range") || !has(c, "eng_range") {
					errs = append(errs, fmt.Sprintf("%s.%s: AI/AO 必须配置 raw_range 与 eng_range", did, ch))
				}
			}
		}
		devChannels[did] = chans
	}

	// --- 业务设备 + 绑定 ---
	// 先收齐全部 point_id：interlock 可引用后面声明的点位。
	allPointIDs := map[string]bool{}
	for _, bzi := range bizs {
		biz := asObj(bzi)
		for _, bdi := range asObj(get(biz, "bindings")) {
			bd := asObj(bdi)
			if pid := asStr(get(bd, "point_id")); pid != "" {
				allPointIDs[pid] = true
			}
		}
	}

	pointIDs := map[string]bool{}
	bizIDs := map[string]bool{}
	for _, bzi := range bizs {
		biz := asObj(bzi)
		bzid := "?"
		if v := asStr(get(biz, "business_id")); v != "" {
			bzid = v
		}
		if asStr(get(biz, "business_id")) == "" {
			errs = append(errs, "business_device 缺少 business_id")
		} else if bizIDs[bzid] {
			errs = append(errs, "business_id 重复: "+bzid)
		}
		bizIDs[bzid] = true
		if !businessTemplates[asStr(get(biz, "business_template"))] {
			errs = append(errs, fmt.Sprintf("%s: 未知 business_template %s", bzid, reprStr(get(biz, "business_template"))))
		}
		bizInd := industry
		if v := get(biz, "industry"); v != nil {
			bizInd = asStr(v)
		}
		if bizInd != industry {
			errs = append(errs, fmt.Sprintf("%s: industry %s 与顶层 %s 不一致", bzid, reprStr(bizInd), reprStr(industry)))
		}
		bindings := asObj(get(biz, "bindings"))
		if len(bindings) == 0 {
			errs = append(errs, bzid+": 至少需要一个 binding")
		}
		for role, bdi := range bindings {
			bd := asObj(bdi)
			if !roles[role] {
				errs = append(errs, fmt.Sprintf("%s: 未知绑定角色 %s", bzid, reprStr(role)))
			}
			pid := asStr(get(bd, "point_id"))
			if pid == "" {
				errs = append(errs, fmt.Sprintf("%s.%s: 缺少 point_id", bzid, role))
				continue
			}
			if pointIDs[pid] {
				errs = append(errs, "point_id 全局重复: "+pid)
			}
			pointIDs[pid] = true
			frm := asStr(get(bd, "from"))
			if role == "derived" {
				if asStr(get(bd, "expr")) == "" {
					errs = append(errs, fmt.Sprintf("%s.%s: derived 点必须有 expr", bzid, pid))
				}
			} else if frm != "" {
				dd := frm
				cc := ""
				if i := strings.Index(frm, "."); i >= 0 {
					dd, cc = frm[:i], frm[i+1:]
				}
				if _, ok := devChannels[dd]; !ok {
					errs = append(errs, fmt.Sprintf("%s.%s: from 引用未知设备 %s", bzid, pid, dd))
				} else if _, ok := devChannels[dd][cc]; !ok {
					errs = append(errs, fmt.Sprintf("%s.%s: from 引用未知通道 %s.%s", bzid, pid, dd, cc))
				}
			} else {
				errs = append(errs, fmt.Sprintf("%s.%s: 非 derived 点必须有 from", bzid, pid))
			}
			if writableRoles[role] {
				if !has(bd, "limit_lo") || !has(bd, "limit_hi") {
					errs = append(errs, fmt.Sprintf("%s.%s: %s 必须配置 limit_lo/limit_hi(安全限值)", bzid, pid, role))
				}
				if _, ok := bindings["feedback"]; !ok {
					errs = append(errs, fmt.Sprintf("%s: 含 %s 的控制对象应绑定 feedback(反馈点)", bzid, role))
				}
				for _, ili := range asArr(get(bd, "interlocks")) {
					il := asObj(ili)
					ilp := asStr(get(il, "point"))
					if ilp == "" {
						errs = append(errs, fmt.Sprintf("%s.%s: interlock 缺少 point", bzid, pid))
					} else if !allPointIDs[ilp] {
						errs = append(errs, fmt.Sprintf("%s.%s: interlock 引用未知点位 %s", bzid, pid, ilp))
					}
					if !has(il, "equals") && !has(il, "max") && !has(il, "min") {
						errs = append(errs, fmt.Sprintf("%s.%s: interlock %s 缺少条件(equals/max/min)", bzid, pid, ilp))
					}
				}
				if cts := get(bd, "confirm_timeout_s"); cts != nil {
					if _, ok := cts.(float64); !ok {
						errs = append(errs, fmt.Sprintf("%s.%s: confirm_timeout_s 必须是数值", bzid, pid))
					}
				}
			}
		}
		disp := asObj(get(biz, "display"))
		if get(biz, "display") == nil && getOr(biz, "backend_only", false) == false {
			errs = append(errs, bzid+": 必须有 display 或标记 backend_only")
		} else if disp != nil && !pages[asStr(get(disp, "page"))] {
			errs = append(errs, fmt.Sprintf("%s: 未知显示页面 %s", bzid, reprStr(get(disp, "page"))))
		}
	}
	return errs
}

// ===========================================================================
// 编译（假设已 Validate 通过）
// ===========================================================================
// channelsIndex: "device_id.channel" -> (device, channel)
func channelsIndex(draft obj) map[string][2]obj {
	idx := map[string][2]obj{}
	for _, di := range asArr(get(draft, "hardware_devices")) {
		d := asObj(di)
		for _, ci := range asArr(get(d, "channels")) {
			c := asObj(ci)
			idx[asStr(d["device_id"])+"."+asStr(c["channel"])] = [2]obj{d, c}
		}
	}
	return idx
}

func buildPointRegistry(draft obj) obj {
	idx := channelsIndex(draft)
	points := obj{}
	for _, bzi := range asArr(get(draft, "business_devices")) {
		biz := asObj(bzi)
		for role, bdi := range asObj(get(biz, "bindings")) {
			bd := asObj(bdi)
			pid := asStr(bd["point_id"])
			entry := obj{
				"point_id":        pid,
				"name":            firstNonEmpty(asStr(get(bd, "label")), pid),
				"role":            role,
				"business_id":     biz["business_id"],
				"business_template": biz["business_template"],
				"writable":        writableRoles[role],
				"quality_rules":   obj{"non_good_on_timeout": true, "stale_after_polls": float64(2)},
			}
			if role == "derived" {
				entry["source"] = obj{"kind": "derived", "expr": get(bd, "expr")}
			} else {
				dc := idx[asStr(bd["from"])]
				d, c := dc[0], dc[1]
				entry["unit"] = getOr(c, "unit", "")
				entry["source"] = obj{
					"kind":      "modbus",
					"device_id": d["device_id"], "bus_id": d["bus_id"],
					"slave": get(d, "slave"), "register": get(c, "register"),
					"function":  getOr(c, "function", float64(3)),
					"data_type": c["data_type"], "scale": getOr(c, "scale", float64(1)),
				}
			}
			if writableRoles[role] {
				entry["safety"] = obj{"lo": get(bd, "limit_lo"), "hi": get(bd, "limit_hi"),
					"rate_per_s": get(bd, "rate_limit_per_s")}
			}
			points[pid] = entry
		}
	}
	return obj{"config_version": draft["config_version"], "points": points}
}

func buildPollPlan(draft obj) obj {
	// point_id 反查（device -> [(point_id, from)]）
	regPoints := map[string][][2]string{}
	for _, bzi := range asArr(get(draft, "business_devices")) {
		biz := asObj(bzi)
		for role, bdi := range asObj(get(biz, "bindings")) {
			if role == "derived" {
				continue
			}
			bd := asObj(bdi)
			frm := asStr(bd["from"])
			dID := frm
			if i := strings.Index(frm, "."); i >= 0 {
				dID = frm[:i]
			}
			regPoints[dID] = append(regPoints[dID], [2]string{asStr(bd["point_id"]), frm})
		}
	}

	idx := channelsIndex(draft)
	type busAgg struct {
		bus   obj
		tasks arr
	}
	busOrder := []string{}
	busMap := map[string]*busAgg{}
	for _, bi := range asArr(get(draft, "buses")) {
		b := asObj(bi)
		bid := asStr(b["bus_id"])
		busOrder = append(busOrder, bid)
		busMap[bid] = &busAgg{bus: obj{"bus_id": bid, "type": b["type"], "tasks": arr{}}}
	}

	for _, di := range asArr(get(draft, "hardware_devices")) {
		d := asObj(di)
		var chans []obj
		for _, ci := range asArr(get(d, "channels")) {
			c := asObj(ci)
			if get(c, "register") != nil {
				chans = append(chans, c)
			}
		}
		if len(chans) == 0 {
			continue
		}
		// 按功能码分组（首见顺序）
		fnOrder := []float64{}
		byFn := map[float64][]obj{}
		for _, c := range chans {
			fn := toF(getOr(c, "function", float64(3)))
			if _, ok := byFn[fn]; !ok {
				fnOrder = append(fnOrder, fn)
			}
			byFn[fn] = append(byFn[fn], c)
		}
		for _, fn := range fnOrder {
			cs := byFn[fn]
			start := toF(get(cs[0], "register"))
			end := 0.0
			first := true
			for _, c := range cs {
				r := toF(get(c, "register"))
				w := dataWidth[asStr(c["data_type"])]
				if first || r < start {
					start = r
				}
				if first || r+w > end {
					end = r + w
				}
				first = false
			}
			pts := arr{}
			for _, pf := range regPoints[asStr(d["device_id"])] {
				dc := idx[pf[1]]
				c := dc[1]
				if toF(getOr(c, "function", float64(3))) == fn && get(c, "register") != nil {
					pts = append(pts, obj{"point_id": pf[0], "register": c["register"],
						"data_type": c["data_type"], "scale": getOr(c, "scale", float64(1))})
				}
			}
			ba := busMap[asStr(d["bus_id"])]
			ba.tasks = append(ba.tasks, obj{
				"task_id":           fmt.Sprintf("read_%s_fn%g", asStr(d["device_id"]), fn),
				"device_id":         d["device_id"],
				"hardware_template": d["hardware_template"], "slave": get(d, "slave"),
				"function": fn, "start": start, "count": end - start,
				"period_ms": float64(2000), "timeout_ms": getOr(d, "timeout_ms", float64(250)),
				"retries":                getOr(d, "retries", float64(1)),
				"backoff_after_failures": float64(3), "backoff_period_ms": float64(30000),
				"points": pts,
			})
		}
	}

	outBuses := arr{}
	for _, bid := range busOrder {
		ba := busMap[bid]
		if len(ba.tasks) > 0 {
			ba.bus["tasks"] = ba.tasks
			outBuses = append(outBuses, ba.bus)
		}
	}
	return obj{"config_version": draft["config_version"], "buses": outBuses}
}

func buildDisplayModel(draft obj) obj {
	type pageAgg struct {
		page  obj
		cards map[string]obj
		order []string
	}
	pageOrder := []string{}
	pageMap := map[string]*pageAgg{}
	for _, bzi := range asArr(get(draft, "business_devices")) {
		biz := asObj(bzi)
		disp := asObj(get(biz, "display"))
		if disp == nil {
			continue
		}
		pg := asStr(disp["page"])
		pa := pageMap[pg]
		if pa == nil {
			pa = &pageAgg{page: obj{"page": pg}, cards: map[string]obj{}}
			pageMap[pg] = pa
			pageOrder = append(pageOrder, pg)
		}
		cardName := asStr(getOr(disp, "card", biz["business_id"]))
		card := pa.cards[cardName]
		if card == nil {
			card = obj{"card": cardName, "label": getOr(disp, "label", cardName),
				"priority": getOr(disp, "priority", float64(50)), "fields": arr{}}
			pa.cards[cardName] = card
			pa.order = append(pa.order, cardName)
		}
		for role, bdi := range asObj(get(biz, "bindings")) {
			bd := asObj(bdi)
			card["fields"] = append(asArr(card["fields"]), obj{"point_id": bd["point_id"],
				"label": firstNonEmpty(asStr(get(bd, "label")), asStr(bd["point_id"])), "role": role})
		}
	}
	out := arr{}
	for _, pg := range pageOrder {
		pa := pageMap[pg]
		cards := []obj{}
		for _, cn := range pa.order {
			cards = append(cards, pa.cards[cn])
		}
		sort.SliceStable(cards, func(i, j int) bool {
			return toF(cards[i]["priority"]) < toF(cards[j]["priority"])
		})
		cardsArr := arr{}
		for _, c := range cards {
			cardsArr = append(cardsArr, c)
		}
		pa.page["cards"] = cardsArr
		out = append(out, pa.page)
	}
	return obj{"config_version": draft["config_version"], "pages": out}
}

func buildSafetyPolicy(draft obj) obj {
	cmds := obj{}
	for _, bzi := range asArr(get(draft, "business_devices")) {
		biz := asObj(bzi)
		bindings := asObj(get(biz, "bindings"))
		for role, bdi := range bindings {
			if !writableRoles[role] {
				continue
			}
			bd := asObj(bdi)
			var fb interface{}
			if fbBind := asObj(bindings["feedback"]); fbBind != nil {
				fb = get(fbBind, "point_id")
			}
			cmds[asStr(bd["point_id"])] = obj{
				"lo": get(bd, "limit_lo"), "hi": get(bd, "limit_hi"),
				"rate_per_s":        get(bd, "rate_limit_per_s"),
				"business_id":       biz["business_id"],
				"feedback":          fb,
				"interlocks":        getOr(bd, "interlocks", arr{}),
				"confirm_timeout_s": get(bd, "confirm_timeout_s"),
				"confirm_tolerance": get(bd, "confirm_tolerance"),
			}
		}
	}
	return obj{"config_version": draft["config_version"], "commands": cmds}
}

func Compile(draft obj) obj {
	return obj{
		"point_registry.json": buildPointRegistry(draft),
		"poll_plan.json":      buildPollPlan(draft),
		"display_model.json":  buildDisplayModel(draft),
		"safety_policy.json":  buildSafetyPolicy(draft),
	}
}

// --------------------------------------------------------------------------- //
func firstNonEmpty(a, b string) string {
	if a != "" {
		return a
	}
	return b
}
func toF(v interface{}) float64 {
	if f, ok := v.(float64); ok {
		return f
	}
	return 0
}
