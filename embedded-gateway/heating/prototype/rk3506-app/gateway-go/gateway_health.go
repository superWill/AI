// gatewayc health —— 启动健康门(供 supervisor 与激活重启复用)。
// 轮询 gatewayc 自己的 /api/health,直到「采集新鲜 + 离线设备不超阈」才算就绪(exit 0);
// 超时仍不就绪 exit 1。零外部依赖(net/http),不需要板上有 curl/python。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"time"
)

func runHealth(args []string) {
	fs := flag.NewFlagSet("health", flag.ExitOnError)
	url := fs.String("url", "http://127.0.0.1:8091", "gatewayc 基址")
	timeout := fs.Int("timeout", 20, "等待就绪的最长秒数")
	staleMs := fs.Int("stale-ms", 6000, "采集年龄上限(ms);超过视为采集未起来")
	maxOffline := fs.Int("max-offline", -1, "允许离线设备数上限(-1=不检查)")
	fs.Parse(args)

	client := &http.Client{Timeout: 3 * time.Second}
	deadline := time.Now().Add(time.Duration(*timeout) * time.Second)
	var last string
	for {
		ok, detail := healthOnce(client, *url, *staleMs, *maxOffline)
		last = detail
		if ok {
			fmt.Printf("[health] 就绪:%s\n", detail)
			os.Exit(0)
		}
		if !time.Now().Before(deadline) {
			break
		}
		time.Sleep(time.Second)
	}
	fmt.Fprintf(os.Stderr, "[health] %ds 内未就绪:%s\n", *timeout, last)
	os.Exit(1)
}

func healthOnce(client *http.Client, base string, staleMs, maxOffline int) (bool, string) {
	resp, err := client.Get(base + "/api/health")
	if err != nil {
		return false, fmt.Sprintf("HTTP 不通: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return false, fmt.Sprintf("HTTP %d", resp.StatusCode)
	}
	var h struct {
		OK             bool  `json:"ok"`
		CollectorAgeMs int64 `json:"collector_age_ms"`
		DevicesTotal   int   `json:"devices_total"`
		DevicesOffline int   `json:"devices_offline"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&h); err != nil {
		return false, fmt.Sprintf("解析失败: %v", err)
	}
	if h.CollectorAgeMs < 0 || h.CollectorAgeMs > int64(staleMs) {
		return false, fmt.Sprintf("采集年龄 %dms > %dms(采集未就绪)", h.CollectorAgeMs, staleMs)
	}
	if maxOffline >= 0 && h.DevicesOffline > maxOffline {
		return false, fmt.Sprintf("离线设备 %d > %d", h.DevicesOffline, maxOffline)
	}
	return true, fmt.Sprintf("采集年龄 %dms,设备 %d 在线/%d 离线",
		h.CollectorAgeMs, h.DevicesTotal-h.DevicesOffline, h.DevicesOffline)
}
