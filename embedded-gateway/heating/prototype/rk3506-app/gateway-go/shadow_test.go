package main

import "testing"

// 不变量:影子执行器只累加意图计数,结构上不持有任何总线/串口句柄——写不出去。
// 返回 true 仅为模拟"写成功"以对齐生产决策状态路径,不代表发生了真实总线写。
func TestShadowExecutorNoBusHandle(t *testing.T) {
	exec := &shadowExecutor{}
	for i := 0; i < 5; i++ {
		_ = exec.Write("sec_supply_temp", float64(40+i))
	}
	if exec.intents != 5 {
		t.Fatalf("意图计数 = %d,期望 5", exec.intents)
	}
	// shadowExecutor 仅有一个计数器字段;此测试与编译期共同保证它无 SerialPort/source 引用。
}

// 不变量:封死执行器接进 Controller 后,决策能正常走完(可对比生产),
// 且每次"写"都只落到意图计数器,不存在到总线的副作用。
func TestShadowControllerDecisionReachesSealedExecutor(t *testing.T) {
	exec := &shadowExecutor{}
	var lastStatus string
	ctrl := NewController(ControllerDeps{
		Snapshot: func() obj {
			return obj{"devices": arr{obj{"addr": float64(1), "name": "站",
				"points": obj{"sec_supply_temp": obj{"v": float64(40), "q": "good", "u": "degC"}}}}}
		},
		Write:  exec.Write,
		Record: func(r ControlRecord) { lastStatus = r.Status },
		// 放行的 policy(无 feedback):决策通过安全校验后走到"写",状态应为 accepted。
		Policy: obj{"sec_supply_temp": obj{"lo": float64(0), "hi": float64(100)}},
	})
	ctrl.Apply("sec_supply_temp", float64(45), "t1", "platform-shadow")
	if exec.intents == 0 {
		t.Fatalf("决策应到达写执行器(记录意图),实际意图计数为 0;status=%q", lastStatus)
	}
	if lastStatus != "accepted" {
		t.Fatalf("放行点位经封死执行器应得 accepted(模拟写成功),得到 status=%q", lastStatus)
	}
}
