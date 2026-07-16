package render

// 视图模型:对标 dashboard.py 消费的 /api/snapshot dict 结构。
// 关键约束:points 必须保持 JSON 对象键序(Python dict 保序,像素输出依赖它);
// 所有解码必须 UseNumber,数值原文经 json.Number 保真。

import (
	"bytes"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
)

// Value 对标 Python 点值的动态类型(数字/字符串/布尔/None 或字段缺失)。
type Value struct {
	Kind byte // 0=null/缺失 'n'=数字 's'=字符串 'b'=布尔
	Num  json.Number
	Str  string
	Bool bool
}

func (v *Value) UnmarshalJSON(b []byte) error {
	s := strings.TrimSpace(string(b))
	switch {
	case s == "null":
		v.Kind = 0
	case s[0] == '"':
		v.Kind = 's'
		return json.Unmarshal(b, &v.Str)
	case s == "true", s == "false":
		v.Kind = 'b'
		v.Bool = s == "true"
	default:
		v.Kind = 'n'
		v.Num = json.Number(s)
	}
	return nil
}

func (v Value) IsNull() bool { return v.Kind == 0 }

// Float 对标 Python float(v):数字/数字字符串/布尔可转,失败 ok=false。
func (v Value) Float() (float64, bool) {
	switch v.Kind {
	case 'n':
		f, err := v.Num.Float64()
		return f, err == nil
	case 's':
		f, err := strconv.ParseFloat(strings.TrimSpace(v.Str), 64)
		return f, err == nil
	case 'b':
		if v.Bool {
			return 1, true
		}
		return 0, true
	}
	return 0, false
}

// PyStr 对标 "%s" % v。
func (v Value) PyStr() string {
	switch v.Kind {
	case 'n':
		return string(v.Num)
	case 's':
		return v.Str
	case 'b':
		if v.Bool {
			return "True"
		}
		return "False"
	}
	return "None"
}

// StrOr 对标 view.get(key, def):字段缺失/null 时用默认值。
func (v Value) StrOr(def string) string {
	if v.Kind == 0 {
		return def
	}
	return v.PyStr()
}

// Fnum 对标 dashboard.fnum(v, d)。
func Fnum(v Value, d int) string {
	if v.Kind == 0 {
		return "--"
	}
	if f, ok := v.Float(); ok {
		return fmt.Sprintf("%.*f", d, f)
	}
	return v.PyStr()
}

type Point struct {
	V Value  `json:"v"`
	U string `json:"u"`
	Q string `json:"q"`
}

type NamedPoint struct {
	ID string
	P  Point
}

// Points 保序解码 JSON 对象(等价 Python 有序 dict)。
type Points []NamedPoint

func (p *Points) UnmarshalJSON(b []byte) error {
	*p = nil
	dec := json.NewDecoder(bytes.NewReader(b))
	dec.UseNumber()
	tok, err := dec.Token()
	if err != nil {
		return err
	}
	if tok == nil { // JSON null
		return nil
	}
	if d, ok := tok.(json.Delim); !ok || d != '{' {
		return fmt.Errorf("points: 期望 JSON 对象,得到 %v", tok)
	}
	for dec.More() {
		keyTok, err := dec.Token()
		if err != nil {
			return err
		}
		key, _ := keyTok.(string)
		var pt Point
		if err := dec.Decode(&pt); err != nil {
			return err
		}
		*p = append(*p, NamedPoint{key, pt})
	}
	_, err = dec.Token() // 收掉 '}'
	return err
}

type Device struct {
	Name   string `json:"name"`
	Type   Value  `json:"type"`
	Addr   Value  `json:"addr"`
	OK     bool   `json:"ok"`
	Points Points `json:"points"`
}

type Event struct {
	Detail string `json:"detail"`
}

type View struct {
	DeviceID Value    `json:"device_id"`
	Devices  []Device `json:"devices"`
	Events   []Event  `json:"events"`
}

// DecodeView 从 JSON 解码;必须走这里保证 UseNumber + points 保序。
func DecodeView(b []byte) (*View, error) {
	dec := json.NewDecoder(bytes.NewReader(b))
	dec.UseNumber()
	var v View
	if err := dec.Decode(&v); err != nil {
		return nil, err
	}
	return &v, nil
}

func onlineCount(v *View) (online, total int) {
	for _, d := range v.Devices {
		if d.OK {
			online++
		}
	}
	return online, len(v.Devices)
}

// Pick 对标 dashboard.pick:首个 v 非 None 的点值。
func Pick(v *View, pid string) Value {
	for _, d := range v.Devices {
		for _, np := range d.Points {
			if np.ID == pid && !np.P.V.IsNull() {
				return np.P.V
			}
		}
	}
	return Value{}
}

type FlatPoint struct {
	DN, PID string
	V       Value
	U, Q    string
}

// AllPoints 对标 dashboard.all_points(顺序=设备序×点位插入序)。
func AllPoints(v *View) []FlatPoint {
	var out []FlatPoint
	for _, d := range v.Devices {
		for _, np := range d.Points {
			out = append(out, FlatPoint{d.Name, np.ID, np.P.V, np.P.U, np.P.Q})
		}
	}
	return out
}

// PointOf 对标 dashboard.point_of:首个含该 pid 的点(v 可为 None);无则 nil。
func PointOf(v *View, pid string) *Point {
	for _, d := range v.Devices {
		for _, np := range d.Points {
			if np.ID == pid {
				p := np.P
				return &p
			}
		}
	}
	return nil
}

// ---- map[string]any(草稿节点/表单)取值助手,对标 dict.get 语义 ----

// AnyStr 对标 "%s" % value(值来自 UseNumber 解码的 JSON)。
func AnyStr(v any) string {
	switch x := v.(type) {
	case nil:
		return "None"
	case string:
		return x
	case json.Number:
		return string(x)
	case bool:
		if x {
			return "True"
		}
		return "False"
	}
	return fmt.Sprintf("%v", v)
}

// nodeGet 对标 d.get(key, def):键缺失返回 def,存在则 "%s" 化。
func nodeGet(m map[string]any, key, def string) string {
	if v, ok := m[key]; ok {
		return AnyStr(v)
	}
	return def
}

// truncRunes 对标 Python 字符串切片 s[:n](按字符而非字节)。
func truncRunes(s string, n int) string {
	r := []rune(s)
	if len(r) > n {
		return string(r[:n])
	}
	return s
}
