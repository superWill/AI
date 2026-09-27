package render

// Render 对标 dashboard.render:入口与分发。

var pages = map[string]func(*FB, *View, map[string]int, *[]Button){
	"overview": pageOverview,
	"monitor":  pageMonitor,
	"nodes":    pageNodes,
	"control":  pageControl,
	"settings": pageSettings,
}

func Render(view *View, clock string, targets map[string]int, page string,
	deviceForm map[string]any, configSlot int, configMessage string) (*FB, []Button) {
	if targets == nil {
		targets = map[string]int{}
	}
	var buttons []Button
	f := NewFB()
	f.Clear(BG)
	if _, ok := pages[page]; !ok && page != "device_config" {
		page = "overview"
	}
	drawHeader(f, view, clock, PageTitle[page])
	if page == "device_config" {
		pageDeviceConfig(f, deviceForm, configSlot, len(view.ConfiguredNodes),
			configMessage, &buttons)
	} else {
		pages[page](f, view, targets, &buttons)
	}
	drawNav(f, page, &buttons)
	return f, buttons
}
