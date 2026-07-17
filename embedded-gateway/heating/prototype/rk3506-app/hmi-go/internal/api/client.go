// Package api:与 gatewayc core 的 HTTP 客户端,
// 超时对标 drm_hmi_v4.py(snapshot 读 2s,command 写 3s)。
package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"sync"
	"time"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

type Client struct {
	Base       string // gatewayc core,如 http://127.0.0.1:8091
	ConfigBase string // gatewayc ui 配置 API,部署态 http://127.0.0.1:8092
	// gatewayc core /api/command 的控制鉴权 token(S99 start() export,
	// 进程继承)。Python 版没带 → 在 Go 核心拓扑下控制一直 401,此处为
	// 对 Python 的刻意修复,见 hmi-go/README.md 差异清单。
	controlToken string
	mu           sync.Mutex
	token        string
	read         *http.Client
	write        *http.Client
	configRead   *http.Client
	compile      *http.Client
	activate     *http.Client
}

func New(base string) *Client {
	return NewWithConfig(base, base)
}

func NewWithConfig(base, configBase string) *Client {
	return &Client{
		Base:         base,
		ConfigBase:   configBase,
		controlToken: os.Getenv("GATEWAYC_CONTROL_TOKEN"),
		read:         &http.Client{Timeout: 2 * time.Second},
		write:        &http.Client{Timeout: 3 * time.Second},
		configRead:   &http.Client{Timeout: 5 * time.Second},
		compile:      &http.Client{Timeout: 30 * time.Second},
		activate:     &http.Client{Timeout: 60 * time.Second},
	}
}

func body(resp *http.Response, err error) ([]byte, error) {
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("HTTP %d: %.120s", resp.StatusCode, b)
	}
	return b, nil
}

// FetchSnapshot 对标 drm_hmi_v4.fetch()。
func (c *Client) FetchSnapshot() (*render.View, error) {
	b, err := body(c.read.Get(c.Base + "/api/snapshot"))
	if err != nil {
		return nil, err
	}
	return render.DecodeView(b)
}

// PostCmd 对标 post_cmd:失败只打日志(调用方无返回值依赖)。
func (c *Client) PostCmd(pointID string, value int) {
	payload, _ := json.Marshal(map[string]any{"point_id": pointID, "value": value})
	req, err := http.NewRequest(http.MethodPost, c.Base+"/api/command",
		bytes.NewReader(payload))
	if err != nil {
		fmt.Printf("[ctl] post err: %v\n", err)
		return
	}
	req.Header.Set("Content-Type", "application/json")
	if c.controlToken != "" {
		req.Header.Set("X-Control-Token", c.controlToken)
	}
	if _, err := body(c.write.Do(req)); err != nil {
		fmt.Printf("[ctl] post err: %v\n", err)
	}
}

type result struct {
	OK     bool     `json:"ok"`
	Errors []string `json:"errors"`
	State  string   `json:"state"`
}

type ActivateStatus struct {
	State             string      `json:"state"`
	Errors            []string    `json:"errors"`
	Active            json.Number `json:"active"`
	Latest            json.Number `json:"latest"`
	LiveActiveVersion json.Number `json:"live_active_version"`
	LastActivate      struct {
		State  string   `json:"state"`
		Errors []string `json:"errors"`
	} `json:"last_activate"`
}

func (s ActivateStatus) ActivationState() string {
	if s.State != "" {
		return s.State
	}
	return s.LastActivate.State
}

func (s ActivateStatus) ActivationErrors() []string {
	if len(s.Errors) > 0 {
		return s.Errors
	}
	return s.LastActivate.Errors
}

func decodeUseNumber(raw []byte, dst any) error {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	return dec.Decode(dst)
}

func (c *Client) configRequest(client *http.Client, method, path string, payload any, dst any) (int, error) {
	var reader io.Reader
	if payload != nil {
		raw, err := json.Marshal(payload)
		if err != nil {
			return 0, err
		}
		reader = bytes.NewReader(raw)
	}
	req, err := http.NewRequest(method, c.ConfigBase+path, reader)
	if err != nil {
		return 0, err
	}
	if payload != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	c.mu.Lock()
	token := c.token
	c.mu.Unlock()
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := client.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return resp.StatusCode, err
	}
	if dst != nil && len(raw) > 0 {
		if err := decodeUseNumber(raw, dst); err != nil {
			return resp.StatusCode, fmt.Errorf("解码 %s: %w", path, err)
		}
	}
	return resp.StatusCode, nil
}

// Login 获取并缓存 LCD 配置 API 的 Bearer token。
func (c *Client) Login() error {
	var response struct {
		Token string `json:"token"`
	}
	status, err := c.configRequest(c.configRead, http.MethodPost, "/api/login",
		map[string]string{"username": "lcd", "password": "x"}, &response)
	if err != nil {
		return err
	}
	if status >= 400 || response.Token == "" {
		return fmt.Errorf("登录失败: HTTP %d", status)
	}
	c.mu.Lock()
	c.token = response.Token
	c.mu.Unlock()
	return nil
}

func responseErrors(status int, errs []string) []string {
	if len(errs) > 0 {
		return errs
	}
	return []string{fmt.Sprintf("HTTP %d", status)}
}

func (c *Client) AddDevice(payload map[string]any) (bool, []string) {
	var response result
	status, err := c.configRequest(c.configRead, http.MethodPost, "/api/config/devices", payload, &response)
	if err != nil {
		return false, []string{err.Error()}
	}
	if status >= 400 || !response.OK {
		return false, responseErrors(status, response.Errors)
	}
	return true, nil
}

func (c *Client) GetDraft() (map[string]any, bool, error) {
	var response struct {
		HasDraft bool           `json:"has_draft"`
		Draft    map[string]any `json:"draft"`
	}
	status, err := c.configRequest(c.configRead, http.MethodGet, "/api/config/draft", nil, &response)
	if err != nil {
		return nil, false, err
	}
	if status >= 400 {
		return nil, false, fmt.Errorf("读取草稿失败: HTTP %d", status)
	}
	return response.Draft, response.HasDraft, nil
}

func (c *Client) Compile(draft map[string]any) (bool, []string) {
	var response result
	status, err := c.configRequest(c.compile, http.MethodPost, "/api/config/compile", draft, &response)
	if err != nil {
		return false, []string{err.Error()}
	}
	if status >= 400 || !response.OK {
		return false, responseErrors(status, response.Errors)
	}
	return true, nil
}

func (c *Client) Activate() (bool, string, []string) {
	var response result
	status, err := c.configRequest(c.activate, http.MethodPost, "/api/config/activate", map[string]any{}, &response)
	if err != nil {
		return false, "", []string{err.Error()}
	}
	if status >= 400 || !response.OK {
		return false, response.State, responseErrors(status, response.Errors)
	}
	return true, response.State, nil
}

func (c *Client) ActivateStatus() (ActivateStatus, error) {
	var response ActivateStatus
	status, err := c.configRequest(c.configRead, http.MethodGet, "/api/config/activate/status", nil, &response)
	if err != nil {
		return response, err
	}
	if status >= 400 {
		return response, fmt.Errorf("读取激活状态失败: HTTP %d", status)
	}
	return response, nil
}
