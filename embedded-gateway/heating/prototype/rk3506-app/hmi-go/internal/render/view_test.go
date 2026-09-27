package render

import "testing"

// points 保序:像素输出依赖 JSON 对象键序,Go map 会打乱,Points 必须保持。
func TestPointsOrderPreserved(t *testing.T) {
	blob := []byte(`{"devices":[{"name":"d","ok":true,"points":{
		"zzz":{"v":1,"u":"a","q":"good"},
		"aaa":{"v":2,"u":"b","q":"good"},
		"mmm":{"v":null,"u":"c","q":"stale"},
		"bbb":{"v":"3.5","u":"d","q":""}}}]}`)
	v, err := DecodeView(blob)
	if err != nil {
		t.Fatal(err)
	}
	got := []string{}
	for _, np := range v.Devices[0].Points {
		got = append(got, np.ID)
	}
	want := []string{"zzz", "aaa", "mmm", "bbb"}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("键序 %v != %v", got, want)
		}
	}
	// pick 语义:首个非 null → zzz 的 1
	if p := Pick(v, "mmm"); !p.IsNull() {
		t.Fatal("null 点值应视为缺失")
	}
	if p := Pick(v, "bbb"); p.PyStr() != "3.5" {
		t.Fatalf("字符串点值 %q", p.PyStr())
	}
}

func TestFnumSemantics(t *testing.T) {
	cases := []struct {
		json string
		d    int
		want string
	}{
		{"null", 1, "--"},
		{"52.3", 1, "52.3"},
		{"68", 0, "68"},
		{"68", 1, "68.0"},
		{"0.315", 2, "0.32"}, // %.2f 十进制舍入
		{`"52.3"`, 1, "52.3"},
		{`"abc"`, 1, "abc"}, // float() 失败 → str(v)
		{`""`, 1, ""},
		{"true", 1, "1.0"}, // float(True) == 1.0
	}
	for _, c := range cases {
		var v Value
		if err := v.UnmarshalJSON([]byte(c.json)); err != nil {
			t.Fatal(err)
		}
		if got := Fnum(v, c.d); got != c.want {
			t.Errorf("fnum(%s, %d) = %q != %q", c.json, c.d, got, c.want)
		}
	}
}

func TestTruncRunes(t *testing.T) {
	if got := truncRunes("一号换热机组ABC", 4); got != "一号换热" {
		t.Fatalf("按字符截断: %q", got)
	}
	if got := truncRunes("ab", 9); got != "ab" {
		t.Fatalf("不足不截: %q", got)
	}
}
