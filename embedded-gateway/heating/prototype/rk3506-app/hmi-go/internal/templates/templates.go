// Package templates:LCD 设备接入模板库的加载与占位符展开。
// 展开规则由本包单测锁定:
// 字符串做 $ID/$BUS 子串替换;值恰为 "$SLAVE" 的替换为整数。
package templates

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

type Template struct {
	ID              string `json:"id"`
	Label           string `json:"label"`
	Source          string `json:"source"`
	Hardware        any    `json:"hardware"`
	BusinessDevices any    `json:"business_devices"`
}

// Load 读取模板库并强制溯源红线(source 必填且带合法前缀)。
func Load(path string) ([]Template, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var data struct {
		Templates []Template `json:"templates"`
	}
	if err := dec.Decode(&data); err != nil {
		return nil, err
	}
	for _, t := range data.Templates {
		if t.ID == "" || t.Label == "" || t.Hardware == nil || t.BusinessDevices == nil {
			return nil, fmt.Errorf("模板 %q 缺必填字段", t.ID)
		}
		if !strings.HasPrefix(t.Source, "sim:") &&
			!strings.HasPrefix(t.Source, "datasheet:") &&
			!strings.HasPrefix(t.Source, "capture:") {
			return nil, fmt.Errorf("模板 %s 的 source 必须以 sim:/datasheet:/capture: 开头(可溯源红线)", t.ID)
		}
	}
	return data.Templates, nil
}

func expand(node any, devID, busID string, slave int) any {
	switch x := node.(type) {
	case map[string]any:
		out := make(map[string]any, len(x))
		for k, v := range x {
			out[k] = expand(v, devID, busID, slave)
		}
		return out
	case []any:
		out := make([]any, len(x))
		for i, v := range x {
			out[i] = expand(v, devID, busID, slave)
		}
		return out
	case string:
		if x == "$SLAVE" {
			return slave
		}
		return strings.ReplaceAll(strings.ReplaceAll(x, "$ID", devID), "$BUS", busID)
	}
	return node
}

// Expand 展开为 /api/config/devices 的 payload。device_id = <模板id>_<slave>。
func Expand(t Template, busID string, slave int) (string, map[string]any) {
	devID := fmt.Sprintf("%s_%d", t.ID, slave)
	return devID, map[string]any{
		"hardware":         expand(t.Hardware, devID, busID, slave),
		"business_devices": expand(t.BusinessDevices, devID, busID, slave),
	}
}
