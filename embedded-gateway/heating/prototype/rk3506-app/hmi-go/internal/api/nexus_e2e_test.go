package api_test

import (
	"bytes"
	"encoding/json"
	"os"
	"testing"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/api"
	"embedded-gateway/heating/rk3506-app/hmi-go/internal/templates"
)

func readObject(t *testing.T, path string) map[string]any {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var value map[string]any
	if err := dec.Decode(&value); err != nil {
		t.Fatal(err)
	}
	return value
}

// TestNexusWorkflow 对拍 nexus_server 配置契约。默认跳过；本地验收通过
// NEXUS_E2E_URL/NEXUS_E2E_DRAFT/NEXUS_E2E_TEMPLATES 显式启用。
func TestNexusWorkflow(t *testing.T) {
	base := os.Getenv("NEXUS_E2E_URL")
	if base == "" {
		t.Skip("未设置 NEXUS_E2E_URL")
	}
	draftPath := os.Getenv("NEXUS_E2E_DRAFT")
	templatePath := os.Getenv("NEXUS_E2E_TEMPLATES")
	if draftPath == "" || templatePath == "" {
		t.Fatal("必须设置 NEXUS_E2E_DRAFT 和 NEXUS_E2E_TEMPLATES")
	}
	c := api.New(base)
	if err := c.Login(); err != nil {
		t.Fatal(err)
	}
	if ok, errs := c.Compile(readObject(t, draftPath)); !ok {
		t.Fatalf("基线 compile: %v", errs)
	}
	items, err := templates.Load(templatePath)
	if err != nil {
		t.Fatal(err)
	}
	var pump templates.Template
	for _, item := range items {
		if item.ID == "pumpvfd" {
			pump = item
		}
	}
	if pump.ID == "" {
		t.Fatal("模板库缺少 pumpvfd")
	}
	_, payload := templates.Expand(pump, "rs485_1", 9)
	if ok, errs := c.AddDevice(payload); !ok {
		t.Fatalf("devices: %v", errs)
	}
	draft, has, err := c.GetDraft()
	if err != nil || !has {
		t.Fatalf("draft has=%v err=%v", has, err)
	}
	if ok, errs := c.Compile(draft); !ok {
		t.Fatalf("compile: %v", errs)
	}
	if ok, state, errs := c.Activate(); !ok || state != "active" {
		t.Fatalf("activate state=%s errs=%v", state, errs)
	}
	status, err := c.ActivateStatus()
	if err != nil || status.ActivationState() != "active" {
		t.Fatalf("status=%+v err=%v", status, err)
	}
	if ok, errs := c.AddDevice(payload); ok || len(errs) == 0 {
		t.Fatalf("重复设备应失败: ok=%v errs=%v", ok, errs)
	}
}
