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
	"time"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

type Client struct {
	Base string // gatewayc core,如 http://127.0.0.1:8091
	// gatewayc core /api/command 的控制鉴权 token(S99 start() export,
	// 进程继承)。Python 版没带 → 在 Go 核心拓扑下控制一直 401,此处为
	// 对 Python 的刻意修复,见 hmi-go/README.md 差异清单。
	controlToken string
	read         *http.Client
	write        *http.Client
}

func New(base string) *Client {
	return &Client{
		Base:         base,
		controlToken: os.Getenv("GATEWAYC_CONTROL_TOKEN"),
		read:         &http.Client{Timeout: 2 * time.Second},
		write:        &http.Client{Timeout: 3 * time.Second},
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
