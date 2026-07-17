package templates

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"testing"
)

func TestExpandAllTemplates(t *testing.T) {
	items, err := Load("../../../device_templates.json")
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 3 {
		t.Fatalf("模板数=%d want=3", len(items))
	}
	for _, tpl := range items {
		for _, tc := range []struct {
			bus   string
			slave int
		}{{"rs485_1", 9}, {"rs485_2", 247}} {
			t.Run(tpl.ID+"/"+tc.bus, func(t *testing.T) {
				devID, payload := Expand(tpl, tc.bus, tc.slave)
				want := fmt.Sprintf("%s_%d", tpl.ID, tc.slave)
				if devID != want {
					t.Errorf("device_id=%q want=%q", devID, want)
				}
				hardware, ok := payload["hardware"].(map[string]any)
				if !ok || hardware["device_id"] != devID || hardware["bus_id"] != tc.bus || hardware["slave"] != tc.slave {
					t.Errorf("hardware 未正确展开: %#v", hardware)
				}
				raw, err := json.Marshal(payload)
				if err != nil {
					t.Fatal(err)
				}
				if strings.Contains(string(raw), "$ID") || strings.Contains(string(raw), "$BUS") || strings.Contains(string(raw), "$SLAVE") {
					t.Errorf("展开后仍有占位符: %s", raw)
				}
			})
		}
	}
}

func TestLoadRejectsMissingProvenance(t *testing.T) {
	path := t.TempDir() + "/templates.json"
	raw := []byte(`{"templates":[{"id":"x","label":"X","source":"","hardware":{},"business_devices":[]}]}`)
	if err := os.WriteFile(path, raw, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := Load(path); err == nil {
		t.Fatal("缺少 source 的模板应被拒绝")
	}
}
