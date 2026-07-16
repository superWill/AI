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

type NavItem struct{ ID, Label string }

var Nav = []NavItem{
	{"overview", "总览"}, {"monitor", "监控"}, {"nodes", "设备"},
	{"control", "控制"}, {"settings", "设置"},
}

var PageTitle = map[string]string{
	"overview": "总览", "monitor": "数据监控", "nodes": "设备管理",
	"control": "就地控制", "settings": "系统设置",
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
