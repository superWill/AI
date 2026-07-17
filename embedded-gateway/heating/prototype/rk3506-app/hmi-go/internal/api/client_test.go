package api

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestConfigWorkflowAndBearer(t *testing.T) {
	token := "test-token"
	draft := map[string]any{"buses": []any{map[string]any{"bus_id": "rs485_1"}}}
	var paths []string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		paths = append(paths, r.URL.Path)
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/login" {
			json.NewEncoder(w).Encode(map[string]any{"token": token})
			return
		}
		if r.Header.Get("Authorization") != "Bearer "+token {
			http.Error(w, `{"error":"Unauthorized"}`, http.StatusUnauthorized)
			return
		}
		switch r.URL.Path {
		case "/api/config/devices":
			json.NewEncoder(w).Encode(map[string]any{"ok": true, "errors": []string{}})
		case "/api/config/draft":
			json.NewEncoder(w).Encode(map[string]any{"has_draft": true, "draft": draft})
		case "/api/config/compile":
			json.NewEncoder(w).Encode(map[string]any{"ok": true, "errors": []string{}})
		case "/api/config/activate":
			json.NewEncoder(w).Encode(map[string]any{"ok": true, "state": "active", "errors": []string{}})
		case "/api/config/activate/status":
			json.NewEncoder(w).Encode(map[string]any{"active": 2, "latest": 2,
				"live_active_version": 2, "last_activate": map[string]any{"state": "active", "errors": []string{}}})
		default:
			http.NotFound(w, r)
		}
	}))
	defer srv.Close()

	c := New(srv.URL)
	if err := c.Login(); err != nil {
		t.Fatal(err)
	}
	if ok, errs := c.AddDevice(map[string]any{"hardware": map[string]any{}}); !ok || len(errs) != 0 {
		t.Fatalf("AddDevice ok=%v errs=%v", ok, errs)
	}
	gotDraft, has, err := c.GetDraft()
	if err != nil || !has || gotDraft == nil {
		t.Fatalf("GetDraft has=%v err=%v draft=%v", has, err, gotDraft)
	}
	if ok, errs := c.Compile(gotDraft); !ok || len(errs) != 0 {
		t.Fatalf("Compile ok=%v errs=%v", ok, errs)
	}
	if ok, state, errs := c.Activate(); !ok || state != "active" || len(errs) != 0 {
		t.Fatalf("Activate ok=%v state=%s errs=%v", ok, state, errs)
	}
	status, err := c.ActivateStatus()
	if err != nil || status.LastActivate.State != "active" {
		t.Fatalf("ActivateStatus=%+v err=%v", status, err)
	}
	if len(paths) != 6 {
		t.Fatalf("paths=%v", paths)
	}
}

func TestActivateStatusAcceptsBoardFlatShape(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/login" {
			json.NewEncoder(w).Encode(map[string]any{"token": "x"})
			return
		}
		json.NewEncoder(w).Encode(map[string]any{
			"version": 2, "state": "active", "errors": []string{}, "previous_active": 1,
		})
	}))
	defer srv.Close()
	c := New(srv.URL)
	if err := c.Login(); err != nil {
		t.Fatal(err)
	}
	status, err := c.ActivateStatus()
	if err != nil || status.ActivationState() != "active" || len(status.ActivationErrors()) != 0 {
		t.Fatalf("status=%+v err=%v", status, err)
	}
}

func TestAddDeviceSurfacesAPIError(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path == "/api/login" {
			json.NewEncoder(w).Encode(map[string]any{"token": "x"})
			return
		}
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]any{"ok": false, "errors": []string{"device_id 重复: pumpvfd_9"}})
	}))
	defer srv.Close()
	c := New(srv.URL)
	if err := c.Login(); err != nil {
		t.Fatal(err)
	}
	if ok, errs := c.AddDevice(map[string]any{}); ok || len(errs) != 1 || errs[0] != "device_id 重复: pumpvfd_9" {
		t.Fatalf("ok=%v errs=%v", ok, errs)
	}
}
