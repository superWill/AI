// Command golden renders a review candidate for one Go HMI snapshot case.
// It never changes committed baselines unless both --accept and --reviewed are set.
package main

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

type input struct {
	View         json.RawMessage `json:"view"`
	Clock        string          `json:"clock"`
	Targets      map[string]int  `json:"targets"`
	Page         string          `json:"page"`
	DisplayModel map[string]any  `json:"display_model"`
	AddForm      *render.AddForm `json:"add_form"`
	AddMessage   string          `json:"add_message"`
	AddBusy      bool            `json:"add_busy"`
}

func main() {
	caseName := flag.String("case", "", "snapshot case name, e.g. devadd_new")
	goldenDir := flag.String("golden-dir", "../tests/golden", "input/baseline directory")
	outDir := flag.String("out", "/tmp/hmi-golden-candidate", "review candidate directory")
	accept := flag.Bool("accept", false, "replace committed RGB/buttons baseline")
	reviewed := flag.Bool("reviewed", false, "confirm candidate PNG was visually reviewed")
	flag.Parse()
	if *caseName == "" {
		fatalf("--case is required")
	}
	if *accept && !*reviewed {
		fatalf("--accept requires --reviewed; inspect the candidate PNG first")
	}

	in := loadInput(filepath.Join(*goldenDir, *caseName+".input.json"))
	view, err := render.DecodeView(in.View)
	if err != nil {
		fatalf("decode view: %v", err)
	}
	render.ConfigureDisplay(in.DisplayModel)
	render.ApplyTheme(view.LocalSettings.Theme)
	defer func() {
		render.ConfigureDisplay(nil)
		render.ApplyTheme("light")
	}()
	fb, buttons := render.Render(view, in.Clock, in.Targets, in.Page,
		in.AddForm, in.AddMessage, in.AddBusy)

	if err := os.MkdirAll(*outDir, 0o755); err != nil {
		fatalf("mkdir candidate: %v", err)
	}
	pngPath := filepath.Join(*outDir, *caseName+".png")
	writePNG(pngPath, fb.Buf)
	writeGzip(filepath.Join(*outDir, *caseName+".rgb.gz"), fb.Buf)
	writeButtons(filepath.Join(*outDir, *caseName+".buttons.json"), buttons)
	fmt.Printf("candidate: %s\n", pngPath)

	if *accept {
		writeGzip(filepath.Join(*goldenDir, *caseName+".rgb.gz"), fb.Buf)
		writeButtons(filepath.Join(*goldenDir, *caseName+".buttons.json"), buttons)
		fmt.Printf("accepted reviewed snapshot: %s\n", *caseName)
	}
}

func loadInput(path string) input {
	raw, err := os.ReadFile(path)
	if err != nil {
		fatalf("read input: %v", err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var in input
	if err := dec.Decode(&in); err != nil {
		fatalf("decode input: %v", err)
	}
	return in
}

func writeGzip(path string, data []byte) {
	f, err := os.Create(path)
	if err != nil {
		fatalf("create gzip: %v", err)
	}
	zw := gzip.NewWriter(f)
	if _, err := zw.Write(data); err != nil {
		fatalf("write gzip: %v", err)
	}
	if err := zw.Close(); err != nil {
		fatalf("close gzip: %v", err)
	}
	if err := f.Close(); err != nil {
		fatalf("close file: %v", err)
	}
}

func writeButtons(path string, buttons []render.Button) {
	raw, err := json.MarshalIndent(buttons, "", " ")
	if err != nil {
		fatalf("marshal buttons: %v", err)
	}
	raw = append(raw, '\n')
	if err := os.WriteFile(path, raw, 0o644); err != nil {
		fatalf("write buttons: %v", err)
	}
}

func writePNG(path string, rgb []byte) {
	img := image.NewRGBA(image.Rect(0, 0, render.W, render.H))
	for y := 0; y < render.H; y++ {
		for x := 0; x < render.W; x++ {
			i := (y*render.W + x) * 3
			img.Set(x, y, color.RGBA{R: rgb[i], G: rgb[i+1], B: rgb[i+2], A: 255})
		}
	}
	f, err := os.Create(path)
	if err != nil {
		fatalf("create png: %v", err)
	}
	if err := png.Encode(f, img); err != nil {
		fatalf("encode png: %v", err)
	}
	if err := f.Close(); err != nil {
		fatalf("close png: %v", err)
	}
}

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
	os.Exit(1)
}
