package render

// 颜色与布局常量,逐值对标 dashboard.py L19-53。
type RGB struct{ R, G, B byte }

const (
	W = 800
	H = 480
)

var (
	BG        = RGB{244, 248, 255}
	Sidebar   = RGB{255, 255, 255}
	Card      = RGB{255, 255, 255}
	Card2     = RGB{247, 250, 255}
	Line      = RGB{221, 230, 242}
	Ink       = RGB{22, 34, 56}
	Muted     = RGB{112, 130, 157}
	Blue      = RGB{47, 128, 237}
	Blue2     = RGB{37, 99, 235}
	Green     = RGB{34, 197, 94}
	Amber     = RGB{245, 158, 11}
	Red       = RGB{239, 68, 68}
	Track     = RGB{229, 236, 247}
	PaleBlue  = RGB{235, 244, 255}
	PaleGreen = RGB{232, 249, 241}
	PaleAmber = RGB{255, 246, 230}
	Shadow    = RGB{232, 238, 248}
	White     = RGB{255, 255, 255}
	PaleRed   = RGB{255, 238, 238} // page_nodes 离线徽标底色(Python 里内联元组)
)

type palette struct {
	BG, Sidebar, Card, Card2, Line, Ink, Muted    RGB
	Track, PaleBlue, PaleGreen, PaleAmber, Shadow RGB
}

var palettes = map[string]palette{
	"light": {
		RGB{244, 248, 255}, RGB{255, 255, 255}, RGB{255, 255, 255},
		RGB{247, 250, 255}, RGB{221, 230, 242}, RGB{22, 34, 56},
		RGB{112, 130, 157}, RGB{229, 236, 247}, RGB{235, 244, 255},
		RGB{232, 249, 241}, RGB{255, 246, 230}, RGB{232, 238, 248},
	},
	"dark": {
		RGB{15, 23, 42}, RGB{17, 24, 39}, RGB{30, 41, 59},
		RGB{37, 50, 70}, RGB{55, 65, 81}, RGB{241, 245, 249},
		RGB{156, 163, 175}, RGB{55, 65, 81}, RGB{30, 58, 95},
		RGB{26, 67, 55}, RGB{78, 55, 25}, RGB{12, 18, 32},
	},
}

func ApplyTheme(name string) string {
	p, ok := palettes[name]
	if !ok {
		name, p = "light", palettes["light"]
	}
	BG, Sidebar, Card, Card2 = p.BG, p.Sidebar, p.Card, p.Card2
	Line, Ink, Muted, Track = p.Line, p.Ink, p.Muted, p.Track
	PaleBlue, PaleGreen, PaleAmber, Shadow = p.PaleBlue, p.PaleGreen, p.PaleAmber, p.Shadow
	return name
}

type NavItem struct{ ID, Label string }

var Nav = []NavItem{
	{"overview", "总览"}, {"monitor", "监控"}, {"nodes", "设备"},
	{"control", "控制"}, {"settings", "设置"},
}

var PageTitle = map[string]string{
	"overview": "总览", "monitor": "数据监控", "nodes": "设备管理",
	"control": "就地控制", "settings": "系统设置",
	"device_config": "离线设备配置",
}

type Control struct {
	Label  string
	FB, SP string
	Lo, Hi int
	Step   int
	Unit   string
	Col    RGB
}

var Controls = []Control{
	{"二次供温", "sec_supply_temp", "sec_supply_temp_sp", 20, 75, 2, "℃", Blue},
	{"阀位开度", "valve_open", "valve_open_sp", 0, 100, 5, "%", Green},
	{"循环泵频率", "pump_freq", "pump_freq_sp", 0, 50, 2, "Hz", Amber},
}

var DeviceTypeLabels = map[string]string{
	"other": "设备", "pump_vfd": "水泵", "temp_humidity_sensor": "温度传感器",
	"pressure_sensor": "压力传感器", "heat_meter": "热量表",
	"energy_meter": "电能表", "io_module": "IO 模块",
}
