package render

import "fmt"

func pageSettings(f *FB, v *View, targets map[string]int, buttons *[]Button) {
	online, total := onlineCount(v)
	pts := 0
	for _, d := range v.Devices {
		pts += len(d.Points)
	}
	panel(f, 16, 66, 768, 364, 14, true)
	f.Text("系统信息", 34, 82, 1, Muted)
	rows := [][2]string{
		{"设备 ID", v.DeviceID.StrOr("rk3506-gw-01")},
		{"接入设备", fmt.Sprintf("%d 台(在线 %d)", total, online)},
		{"采集点位", fmt.Sprintf("%d 点", pts)},
		{"本机监控", "离线运行"},
		{"本机地址", "192.168.1.10 : 8092"},
		{"应用版本", "nexus-edge gateway v1"},
		{"运行平台", "RK3506 · Buildroot · DRM"},
	}
	for i, r := range rows {
		ry := 116 + i*42
		f.Text(r[0], 44, ry, 1, Muted)
		f.Text(r[1], 294, ry, 1, Ink)
		f.HLine(34, W-34, ry+27, Line)
	}
}
