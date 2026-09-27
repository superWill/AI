package app

import (
	"sync"

	"embedded-gateway/heating/rk3506-app/hmi-go/internal/render"
)

// FrameCache 对标 drm_hmi_v4.FrameCache:按页缓存已转换的 DRM 帧和按钮。
// Put 拷贝按钮切片,复刻 Python tuple(buttons) 防外部改写的语义。
type FrameCache struct {
	mu    sync.Mutex
	pages map[string]cacheEntry
}

type cacheEntry struct {
	frame   []byte
	buttons []render.Button
}

func NewFrameCache() *FrameCache {
	return &FrameCache{pages: map[string]cacheEntry{}}
}

func (c *FrameCache) Put(page string, frame []byte, buttons []render.Button) {
	cp := make([]render.Button, len(buttons))
	copy(cp, buttons)
	c.mu.Lock()
	c.pages[page] = cacheEntry{frame, cp}
	c.mu.Unlock()
}

func (c *FrameCache) Get(page string) ([]byte, []render.Button, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	e, ok := c.pages[page]
	return e.frame, e.buttons, ok
}

func (c *FrameCache) Invalidate(pages ...string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	for _, p := range pages {
		delete(c.pages, p)
	}
}
