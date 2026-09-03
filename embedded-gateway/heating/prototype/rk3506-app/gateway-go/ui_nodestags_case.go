package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// nodestags: 读快照 view(+可选产物目录)→ 输出 edge-os nodes/tags(对拍 Python build_nodes_tags 用)。
//
//	gatewayc nodestags <snapshot.json> [products_dir] [endpoint]
func runNodesTags(args []string) {
	if len(args) < 1 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc nodestags <snapshot.json> [products_dir] [endpoint]")
		os.Exit(2)
	}
	raw, err := os.ReadFile(args[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "读取快照失败: %v\n", err)
		os.Exit(2)
	}
	var view obj
	if err := json.Unmarshal(raw, &view); err != nil {
		fmt.Fprintf(os.Stderr, "解析快照失败: %v\n", err)
		os.Exit(2)
	}
	var pr, dm obj
	if len(args) >= 2 && args[1] != "" {
		pr = readJSONObj(filepath.Join(args[1], "point_registry.json"))
		dm = readJSONObj(filepath.Join(args[1], "display_model.json"))
	}
	endpoint := "sim"
	if len(args) >= 3 {
		endpoint = args[2]
	}
	m := configureMapsUI(pr, dm)
	nodes, tags := buildNodesTagsUI(view, endpoint, m)
	b, _ := json.MarshalIndent(obj{"nodes": nodes, "tags": tags}, "", "  ")
	fmt.Println(string(b))
}

func readJSONObj(path string) obj {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	var o obj
	if json.Unmarshal(raw, &o) != nil {
		return nil
	}
	return o
}
