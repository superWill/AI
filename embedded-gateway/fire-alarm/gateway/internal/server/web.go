package server

import (
	"io/fs"
)

// fsSub 把嵌入的 web 目录提升为根，使 "/" 直接映射到 index.html。
func fsSub() (fs.FS, error) { return fs.Sub(webFS, "web") }
