package render

// 金帧测试:消费 tests/golden/(由 tools/gen_golden_frames.py 生成),
// 走真实 JSON 解码路径渲染,与 Python 基准逐字节比对。

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

const goldenDir = "../../../tests/golden"

type goldenInput struct {
	View         json.RawMessage `json:"view"`
	Clock        string          `json:"clock"`
	Targets      map[string]int  `json:"targets"`
	Page         string          `json:"page"`
	DisplayModel map[string]any  `json:"display_model"`
}

func TestGolden(t *testing.T) {
	matches, _ := filepath.Glob(filepath.Join(goldenDir, "*.input.json"))
	if len(matches) == 0 {
		t.Fatal("找不到金帧用例,先跑 python3 tools/gen_golden_frames.py")
	}
	for _, m := range matches {
		name := strings.TrimSuffix(filepath.Base(m), ".input.json")
		t.Run(name, func(t *testing.T) { runGolden(t, name) })
	}
}

func runGolden(t *testing.T, name string) {
	raw, err := os.ReadFile(filepath.Join(goldenDir, name+".input.json"))
	if err != nil {
		t.Fatal(err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var in goldenInput
	if err := dec.Decode(&in); err != nil {
		t.Fatalf("解码 input.json: %v", err)
	}
	view, err := DecodeView(in.View)
	if err != nil {
		t.Fatalf("解码 view: %v", err)
	}
	ConfigureDisplay(in.DisplayModel)
	ApplyTheme(view.LocalSettings.Theme)
	defer func() {
		ConfigureDisplay(nil)
		ApplyTheme("light")
	}()

	fb, buttons := Render(view, in.Clock, in.Targets, in.Page)

	want := readGz(t, filepath.Join(goldenDir, name+".rgb.gz"))
	if !bytes.Equal(fb.Buf, want) {
		reportFrameDiff(t, name, fb, want)
	}

	gotJSON, err := json.Marshal(buttons)
	if err != nil {
		t.Fatal(err)
	}
	wantJSON, err := os.ReadFile(filepath.Join(goldenDir, name+".buttons.json"))
	if err != nil {
		t.Fatal(err)
	}
	var g, w any
	if err := json.Unmarshal(gotJSON, &g); err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(wantJSON, &w); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(g, w) {
		t.Errorf("按钮不一致:\n got: %s\nwant: %s", gotJSON, bytes.TrimSpace(wantJSON))
	}
}

func readGz(t *testing.T, path string) []byte {
	f, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	zr, err := gzip.NewReader(f)
	if err != nil {
		t.Fatal(err)
	}
	data, err := io.ReadAll(zr)
	if err != nil {
		t.Fatal(err)
	}
	return data
}

// reportFrameDiff:统计 diff 像素、列出前 20 个坐标,并把 got/diff 掩码
// PNG 写到持久临时目录供人工看图。
func reportFrameDiff(t *testing.T, name string, fb *FB, want []byte) {
	if len(fb.Buf) != len(want) {
		t.Fatalf("帧长度 %d != %d", len(fb.Buf), len(want))
	}
	type pt struct{ x, y int }
	var diffs []pt
	for y := 0; y < fb.H; y++ {
		for x := 0; x < fb.W; x++ {
			i := (y*fb.W + x) * 3
			if fb.Buf[i] != want[i] || fb.Buf[i+1] != want[i+1] || fb.Buf[i+2] != want[i+2] {
				diffs = append(diffs, pt{x, y})
			}
		}
	}
	head := diffs
	if len(head) > 20 {
		head = head[:20]
	}
	var sb strings.Builder
	for _, d := range head {
		i := (d.y*fb.W + d.x) * 3
		fmt.Fprintf(&sb, "  (%d,%d) got=%v want=%v\n", d.x, d.y,
			fb.Buf[i:i+3], want[i:i+3])
	}
	dir, err := os.MkdirTemp("", "golden-"+name+"-")
	if err == nil {
		writePNG(filepath.Join(dir, "got.png"), fb.Buf, fb.W, fb.H)
		writePNG(filepath.Join(dir, "want.png"), want, fb.W, fb.H)
		mask := make([]byte, len(fb.Buf))
		for _, d := range diffs {
			i := (d.y*fb.W + d.x) * 3
			mask[i] = 255
		}
		writePNG(filepath.Join(dir, "diff.png"), mask, fb.W, fb.H)
	}
	t.Errorf("帧不一致: %d 个 diff 像素,前 20:\n%s调试图: %s", len(diffs), sb.String(), dir)
}

func writePNG(path string, rgb []byte, w, h int) {
	img := image.NewRGBA(image.Rect(0, 0, w, h))
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			i := (y*w + x) * 3
			img.Set(x, y, color.RGBA{rgb[i], rgb[i+1], rgb[i+2], 255})
		}
	}
	f, err := os.Create(path)
	if err != nil {
		return
	}
	defer f.Close()
	png.Encode(f, img)
}
