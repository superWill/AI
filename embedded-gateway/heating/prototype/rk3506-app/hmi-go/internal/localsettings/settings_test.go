package localsettings

import (
	"os"
	"path/filepath"
	"testing"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

func TestRoundTripAndClamp(t *testing.T) {
	path := filepath.Join(t.TempDir(), "hmi-settings.json")
	if err := Save(path, render.LocalSettings{Brightness: 0, Theme: "dark"}); err != nil {
		t.Fatal(err)
	}
	got := Load(path)
	if got.Brightness != 10 || got.Theme != "dark" {
		t.Fatalf("got %+v", got)
	}
}

func TestApplyBrightness(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "max_brightness"), []byte("255"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "brightness"), []byte("200"), 0o644); err != nil {
		t.Fatal(err)
	}
	value, err := ApplyBrightness(dir, 50)
	if err != nil {
		t.Fatal(err)
	}
	if value != 128 {
		t.Fatalf("value=%d", value)
	}
	raw, _ := os.ReadFile(filepath.Join(dir, "brightness"))
	if string(raw) != "128" {
		t.Fatalf("brightness=%q", raw)
	}
}
