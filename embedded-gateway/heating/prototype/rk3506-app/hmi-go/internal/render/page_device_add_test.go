package render

import "testing"

func TestDeviceAddButtonContract(t *testing.T) {
	view := &View{}
	form := &AddForm{Template: "循环泵变频器", Bus: "rs485_1", Slave: 9}
	_, buttons := Render(view, "14:32:07", nil, "device_add", form, "", false)

	changes := map[string]map[int]int{}
	actions := map[string]int{}
	for _, button := range buttons {
		actions[button.Action]++
		if button.Action == "devadd_change" {
			if changes[button.Field] == nil {
				changes[button.Field] = map[int]int{}
			}
			changes[button.Field][button.Delta]++
		}
		x, y, w, h := button.Rect[0], button.Rect[1], button.Rect[2], button.Rect[3]
		if x < 0 || y < 0 || w <= 0 || h <= 0 || x+w > W || y+h > H {
			t.Errorf("按钮越界: %+v", button)
		}
	}
	if actions["config_back"] != 1 || actions["devadd_save"] != 1 || actions["devadd_change"] != 6 {
		t.Fatalf("动作数量错误: %v", actions)
	}
	for _, field := range []string{"template", "bus", "slave"} {
		if changes[field][-1] != 1 || changes[field][1] != 1 {
			t.Errorf("字段 %s 缺少成对 -/+ 动作: %v", field, changes[field])
		}
	}
}

func TestDeviceAddBusyRemovesSaveAction(t *testing.T) {
	_, buttons := Render(&View{}, "14:32:07", nil, "device_add",
		&AddForm{Template: "循环泵变频器", Bus: "rs485_1", Slave: 9}, "", true)
	for _, button := range buttons {
		if button.Action == "devadd_save" {
			t.Fatal("发布中不应存在保存按钮")
		}
	}
}
