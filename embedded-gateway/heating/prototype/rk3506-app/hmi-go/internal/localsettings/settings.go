package localsettings

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

func Normalize(settings render.LocalSettings) render.LocalSettings {
	if settings.Brightness < 10 {
		settings.Brightness = 10
	}
	if settings.Brightness > 100 {
		settings.Brightness = 100
	}
	if settings.Theme != "dark" {
		settings.Theme = "light"
	}
	return settings
}

func Load(path string) render.LocalSettings {
	settings := render.LocalSettings{Brightness: 80, Theme: "light"}
	raw, err := os.ReadFile(path)
	if err == nil {
		_ = json.Unmarshal(raw, &settings)
	}
	return Normalize(settings)
}

func Save(path string, settings render.LocalSettings) error {
	settings = Normalize(settings)
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(settings, "", "  ")
	if err != nil {
		return err
	}
	tmp := path + ".tmp"
	file, err := os.OpenFile(tmp, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	if _, err = file.Write(append(raw, '\n')); err == nil {
		err = file.Sync()
	}
	closeErr := file.Close()
	if err != nil {
		_ = os.Remove(tmp)
		return err
	}
	if closeErr != nil {
		_ = os.Remove(tmp)
		return closeErr
	}
	return os.Rename(tmp, path)
}

func ApplyBrightness(backlightPath string, percent int) (int, error) {
	settings := Normalize(render.LocalSettings{Brightness: percent, Theme: "light"})
	raw, err := os.ReadFile(filepath.Join(backlightPath, "max_brightness"))
	if err != nil {
		return 0, err
	}
	maximum, err := strconv.Atoi(strings.TrimSpace(string(raw)))
	if err != nil || maximum < 1 {
		return 0, fmt.Errorf("invalid max_brightness %q", strings.TrimSpace(string(raw)))
	}
	value := (maximum*settings.Brightness + 50) / 100
	if value < 1 {
		value = 1
	}
	if value > maximum {
		value = maximum
	}
	err = os.WriteFile(filepath.Join(backlightPath, "brightness"),
		[]byte(strconv.Itoa(value)), 0o644)
	return value, err
}
