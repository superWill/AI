package main

import "sort"

// SamplesView 把数据源的 {addr: sample} 转为 Python Runtime.view() 的最小形状。
// 排序保证 map 迭代不会让设备顺序随机，便于 HMI、控制联锁和跨语言对拍。
func SamplesView(samples obj) obj {
	keys := make([]string, 0, len(samples))
	for key := range samples {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	devices := make(arr, 0, len(keys))
	for _, key := range keys {
		devices = append(devices, samples[key])
	}
	return obj{"devices": devices}
}
