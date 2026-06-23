// 适配层 —— 编译产物 → app.py 内核可消费的运行配置（Go 移植自 loader.py）。
// 与 compiler.go 同包，复用其中的 obj/arr/asObj/get/getOr 等辅助。
package main

import (
	"encoding/json"
	"os"
	"path/filepath"
)

var templateCN = map[string]string{
	"rs485_8ai_modbus": "采集模块", "rs485_8di_modbus": "安全IO",
	"rs485_8do_modbus": "输出模块", "rs485_ao_modbus": "输出模块",
	"modbus_tcp_generic": "采集模块", "heat_meter_modbus": "热表",
	"energy_meter_modbus": "电表", "vfd_modbus": "循环泵", "private_mcu": "私有控制器",
}

func templateCNOr(t string) string {
	if v, ok := templateCN[t]; ok {
		return v
	}
	return "采集模块"
}

func readJSON(dir, name string) (obj, error) {
	b, err := os.ReadFile(filepath.Join(dir, name))
	if err != nil {
		return nil, err
	}
	var m obj
	if err := json.Unmarshal(b, &m); err != nil {
		return nil, err
	}
	return m, nil
}

// LoadRuntimeCfg: build_dir 下的 poll_plan/point_registry/safety_policy → app.py 扁平 cfg。
func LoadRuntimeCfg(buildDir, deviceID, source string) (obj, error) {
	poll, err := readJSON(buildDir, "poll_plan.json")
	if err != nil {
		return nil, err
	}
	reg, err := readJSON(buildDir, "point_registry.json")
	if err != nil {
		return nil, err
	}
	safety, err := readJSON(buildDir, "safety_policy.json")
	if err != nil {
		return nil, err
	}
	points := asObj(reg["points"])

	// 每个 task 即一个被采集设备 → 还原 app.py 的 devices[]。
	// 设备类型按 hardware_template 映射（物理能力），不能用 business_template。
	devices := arr{}
	for _, busi := range asArr(poll["buses"]) {
		bus := asObj(busi)
		for _, ti := range asArr(bus["tasks"]) {
			t := asObj(ti)
			did := asStr(t["device_id"])
			devPoints := arr{}
			for _, pti := range asArr(t["points"]) {
				pt := asObj(pti)
				pinfo := asObj(points[asStr(pt["point_id"])])
				devPoints = append(devPoints, obj{
					"id": pt["point_id"], "reg": pt["register"],
					"scale": getOr(pt, "scale", float64(1)),
					"unit":  getOr(pinfo, "unit", ""),
				})
			}
			dev := obj{
				"addr": t["slave"], "name": did,
				"type":  templateCNOr(asStr(getOr(t, "hardware_template", ""))),
				"start": t["start"], "count": t["count"], "fault": "none",
				"points": devPoints,
			}
			// 桥接：把每设备可靠性参数透传给 app.py
			for _, k := range []string{"timeout_ms", "retries"} {
				if v := get(t, k); v != nil {
					dev[k] = v
				}
			}
			devices = append(devices, dev)
		}
	}

	// safety_policy.commands → control_map（写设定值用）
	controlMap := obj{}
	for pid := range asObj(safety["commands"]) {
		src := asObj(get(asObj(points[pid]), "source"))
		if get(src, "slave") != nil && get(src, "register") != nil {
			controlMap[pid] = obj{"addr": src["slave"], "reg": src["register"],
				"scale": getOr(src, "scale", float64(1))}
		}
	}

	return obj{
		"device_id": deviceID, "source": source,
		"poll_interval_s": float64(2), "telemetry_interval_s": float64(10),
		"heartbeat_interval_s": float64(30), "html_dir": "html",
		"devices": devices, "control_map": controlMap,
		"safety_policy":   getOr(safety, "commands", obj{}),
		"_generated_from": "compiler products", "config_version": poll["config_version"],
	}, nil
}
