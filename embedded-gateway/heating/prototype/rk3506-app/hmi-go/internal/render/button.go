package render

import "encoding/json"

// Button 对标 dashboard buttons 元素(dict)。四类字段集:
// 导航 {rect,nav} / 动作 {rect,action} / 表单 {rect,action,field,delta} /
// 控制 {rect,fb,sp,delta,lo,hi}。序列化输出与 Python json.dumps(sort_keys) 同构。
type Button struct {
	Rect   [4]int
	Nav    string
	Action string
	Field  string
	Theme  string
	Delta  int
	FBID   string
	SP     string
	Lo, Hi int
}

func (b Button) MarshalJSON() ([]byte, error) {
	m := map[string]any{"rect": b.Rect}
	switch {
	case b.Nav != "":
		m["nav"] = b.Nav
	case b.Action == "config_change":
		m["action"] = b.Action
		m["field"] = b.Field
		m["delta"] = b.Delta
	case b.Action == "brightness_change":
		m["action"] = b.Action
		m["delta"] = b.Delta
	case b.Action == "theme_set":
		m["action"] = b.Action
		m["theme"] = b.Theme
	case b.Action != "":
		m["action"] = b.Action
	default:
		m["fb"] = b.FBID
		m["sp"] = b.SP
		m["delta"] = b.Delta
		m["lo"] = b.Lo
		m["hi"] = b.Hi
	}
	return json.Marshal(m)
}

// Hit 对标 drm_hmi_v4.on_tap 的 ±8px 容差命中判定。
func (b Button) Hit(x, y int) bool {
	bx, by, bw, bh := b.Rect[0], b.Rect[1], b.Rect[2], b.Rect[3]
	return bx-8 <= x && x <= bx+bw+8 && by-8 <= y && y <= by+bh+8
}
