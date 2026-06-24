// gatewayc ui 的 edge-os 模型层(对照 nexus_server.py 的 configure_maps + build_nodes_tags)。
// 把网关快照 view 译成 edge-os 前端要的 nodes/tags。增量1:纯逻辑 + 子命令对拍 Python。
package main

import (
	"fmt"
	"sort"
	"strconv"
	"time"
)

// numStr:把 JSON 数字(float64)按整数渲成 "1"(非 "1.0"),对齐 Python "%s" % int。
func numStr(v interface{}) string {
	switch n := v.(type) {
	case float64:
		if n == float64(int64(n)) {
			return strconv.FormatInt(int64(n), 10)
		}
		return strconv.FormatFloat(n, 'g', -1, 64)
	case int:
		return strconv.Itoa(n)
	case int64:
		return strconv.FormatInt(n, 10)
	case string:
		return n
	default:
		return fmt.Sprint(v)
	}
}

// 默认(无编译产物时回退)映射 —— 对照 nexus_server.py 同名常量。
var controllableDefault = map[string]bool{"valve_open": true, "pump_freq": true, "sec_supply_temp": true}

var devTypeDefault = map[string]string{
	"换热机组": "boiler", "循环泵": "pump_vfd", "电动调节阀": "valve_actuator",
	"压力传感器": "pressure_sensor", "安全IO": "io_module", "热表": "heat_meter",
	"电表": "energy_meter", "温度传感器": "temp_humidity_sensor", "采集模块": "other",
}

var template2edgeos = map[string]string{
	"circulation_pump": "pump_vfd", "makeup_pump": "pump_vfd", "vfd": "pump_vfd",
	"control_valve": "valve_actuator", "pressure_point": "pressure_sensor",
	"temperature_point": "temp_humidity_sensor", "heat_meter": "heat_meter",
	"energy_meter": "energy_meter", "safety_io": "io_module",
}

var data2tagtype = map[string]string{
	"bool": "BOOLEAN", "uint16": "UINT16", "int16": "INT16",
	"uint32": "FLOAT32", "int32": "FLOAT32", "float32": "FLOAT32",
}

// uiMaps 持有展示层映射(产物驱动或默认),取代 nexus 的可变全局。
type uiMaps struct {
	controllable    map[string]bool   // pid 是否可控(可写)
	devTypeByDevice map[string]string // device name -> edge-os type
	pointTagType    map[string]string // pid -> Tag.type
	pointLabel      map[string]string // pid -> 人类可读名
	displayRank     map[string][3]int // pid -> (page, priority, field)
	displayGroup    map[string]string // pid -> "page/card"
	hasProducts     bool
}

// configureMapsUI:有 point_registry 则产物驱动,否则用默认(对照 configure_maps)。
func configureMapsUI(pointRegistry, displayModel obj) *uiMaps {
	m := &uiMaps{
		controllable: map[string]bool{}, devTypeByDevice: map[string]string{},
		pointTagType: map[string]string{}, pointLabel: map[string]string{},
		displayRank: map[string][3]int{}, displayGroup: map[string]string{},
	}
	if pointRegistry == nil {
		for k := range controllableDefault { // 回退:默认可控点
			m.controllable[k] = true
		}
		return m
	}
	m.hasProducts = true
	pts := asObj(pointRegistry["points"])
	for pid, ei := range pts {
		e := asObj(ei)
		if b, _ := e["writable"].(bool); b {
			m.controllable[pid] = true // 可写点自映射为可控点
		}
		src := asObj(e["source"])
		if did := asStr(src["device_id"]); did != "" {
			if tmpl := asStr(e["business_template"]); tmpl != "" {
				if t, ok := template2edgeos[tmpl]; ok {
					m.devTypeByDevice[did] = t
				} else {
					m.devTypeByDevice[did] = "other"
				}
			}
		}
		if dt := asStr(src["data_type"]); dt != "" {
			if t, ok := data2tagtype[dt]; ok {
				m.pointTagType[pid] = t
			} else {
				m.pointTagType[pid] = "FLOAT32"
			}
		}
		if nm := asStr(e["name"]); nm != "" {
			m.pointLabel[pid] = nm
		}
	}
	for pi, pgi := range asArr(displayModel["pages"]) {
		pg := asObj(pgi)
		for _, ci := range asArr(pg["cards"]) {
			card := asObj(ci)
			prio := int(toF(getOr(card, "priority", float64(50))))
			for fi, fdi := range asArr(card["fields"]) {
				pid := asStr(asObj(fdi)["point_id"])
				if pid == "" {
					continue
				}
				m.displayRank[pid] = [3]int{pi, prio, fi}
				m.displayGroup[pid] = asStr(pg["page"]) + "/" + asStr(card["card"])
			}
		}
	}
	return m
}

// buildNodesTagsUI:view → edge-os nodes/tags(对照 build_nodes_tags)。
func buildNodesTagsUI(view obj, endpoint string, m *uiMaps) (arr, arr) {
	nodes, tags := arr{}, arr{}
	nowMs := time.Now().UnixMilli()
	for _, di := range asArr(view["devices"]) {
		d := asObj(di)
		addr := d["addr"]
		nid := "node-" + numStr(addr)
		name := asStr(d["name"])
		ok, _ := d["ok"].(bool)
		devType := m.devTypeByDevice[name]
		if devType == "" {
			if t, has := devTypeDefault[asStr(d["type"])]; has {
				devType = t
			} else {
				devType = "other"
			}
		}
		status := "Error"
		errs := 1
		if ok {
			status, errs = "Running", 0
		}
		nodes = append(nodes, obj{
			"id": nid, "name": name, "type": getOr(d, "type", ""), "deviceType": devType,
			"driver": "Modbus RTU", "endpoint": endpoint, "slaveId": addr, "status": status,
			"metrics": obj{"tx": 0, "rx": 0, "errors": errs}, "uptime": "-",
		})
		ts := getOr(d, "ts", nowMs)
		for pid, pi := range asObj(d["points"]) {
			p := asObj(pi)
			ctrl := m.controllable[pid]
			access := "R"
			if ctrl {
				access = "RW"
			}
			label := pid
			if l, has := m.pointLabel[pid]; has {
				label = l
			}
			ttype := "FLOAT32"
			if t, has := m.pointTagType[pid]; has {
				ttype = t
			}
			var val interface{} = p["v"]
			if val == nil {
				val = 0
			}
			tag := obj{
				"id": "tag-" + numStr(addr) + "-" + pid, "nodeId": nid, "name": label,
				"address": pid, "type": ttype, "access": access, "value": val,
				"timestamp": ts, "unit": getOr(p, "u", ""),
			}
			if g, has := m.displayGroup[pid]; has {
				tag["group"] = g
			}
			tags = append(tags, tag)
		}
	}
	if len(m.displayRank) > 0 { // display_model 有则按 (node, 展示优先级, address) 排序
		big := [3]int{9999, 9999, 9999}
		sort.SliceStable(tags, func(i, j int) bool {
			a, b := asObj(tags[i]), asObj(tags[j])
			if asStr(a["nodeId"]) != asStr(b["nodeId"]) {
				return asStr(a["nodeId"]) < asStr(b["nodeId"])
			}
			ra, rb := big, big
			if r, has := m.displayRank[asStr(a["address"])]; has {
				ra = r
			}
			if r, has := m.displayRank[asStr(b["address"])]; has {
				rb = r
			}
			if ra != rb {
				return rankLess(ra, rb)
			}
			return asStr(a["address"]) < asStr(b["address"])
		})
	}
	return nodes, tags
}

func rankLess(a, b [3]int) bool {
	for i := 0; i < 3; i++ {
		if a[i] != b[i] {
			return a[i] < b[i]
		}
	}
	return false
}
