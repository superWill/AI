package render

// display_model.json → 监控页卡片,对标 dashboard.configure_display。

import (
	"encoding/json"
	"sort"
)

type displayField struct{ PID, Label string }

type displayCard struct {
	Title  string
	Fields []displayField
}

var displayCards []displayCard

// truthy 对标 Python 真值语义(None/""/0/False 为假)。
func truthy(v any) bool {
	switch x := v.(type) {
	case nil:
		return false
	case string:
		return x != ""
	case bool:
		return x
	case json.Number:
		f, err := x.Float64()
		return err != nil || f != 0
	}
	return true
}

// orStr 对标 `m.get(k) or fallback` 的真值回退(区别于 get 的缺键回退)。
func orStr(m map[string]any, key, fallback string) string {
	if v := m[key]; truthy(v) {
		return AnyStr(v)
	}
	return fallback
}

// ConfigureDisplay 派生监控页卡片:按 (页序, card priority 默认 50) 稳定排序。
// dm 须来自 UseNumber 解码;nil/空 → 清空,监控页回退平铺点表。
func ConfigureDisplay(dm map[string]any) {
	displayCards = nil
	if len(dm) == 0 {
		return
	}
	type item struct {
		pi   int
		prio float64
		card displayCard
	}
	var items []item
	pages, _ := dm["pages"].([]any)
	for pi, pv := range pages {
		page, _ := pv.(map[string]any)
		cards, _ := page["cards"].([]any)
		for _, cv := range cards {
			card, _ := cv.(map[string]any)
			// 优先用人类可读 label,缺省回退 card id(真值回退,空串也回退)
			title := orStr(card, "label", nodeGet(card, "card", ""))
			var fields []displayField
			fl, _ := card["fields"].([]any)
			for _, fv := range fl {
				f, _ := fv.(map[string]any)
				if !truthy(f["point_id"]) { // 对标 `if f.get("point_id")` 过滤
					continue
				}
				pid := AnyStr(f["point_id"])
				fields = append(fields, displayField{pid, orStr(f, "label", pid)})
			}
			prio := 50.0
			if pn, ok := card["priority"].(json.Number); ok {
				if f, err := pn.Float64(); err == nil {
					prio = f
				}
			}
			items = append(items, item{pi, prio, displayCard{title, fields}})
		}
	}
	sort.SliceStable(items, func(i, j int) bool {
		if items[i].pi != items[j].pi {
			return items[i].pi < items[j].pi
		}
		return items[i].prio < items[j].prio
	})
	for _, it := range items {
		displayCards = append(displayCards, it.card)
	}
}
