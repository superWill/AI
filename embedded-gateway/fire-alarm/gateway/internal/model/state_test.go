package model

import (
	"testing"
	"time"

	"github.com/superwill/fire-alarm/gateway/internal/crtlink"
)

func frame(t uint8, r crtlink.Report) crtlink.Frame {
	return crtlink.Frame{Src: crtlink.AddrHost, Dst: crtlink.AddrCRT, Type: t,
		Data: crtlink.EncodeReport(r)}
}

// 复位只清锁存态：火警走，屏蔽留。GB 4717 5.4.4.7 明写屏蔽不受复位影响。
func TestResetClearsAlarmButKeepsShield(t *testing.T) {
	s := NewState()
	s.Apply(frame(crtlink.TypeAlarm, crtlink.Report{Loop: 1, Addr: 5, Zone: 1, Code: crtlink.AlarmFromDetector}))
	s.Apply(frame(crtlink.TypeShield, crtlink.Report{Loop: 1, Addr: 9, Code: 1}))

	if c := s.Snapshot(0).Counters; c.Alarm != 1 || c.Shielded != 1 {
		t.Fatalf("复位前计数 = %+v", c)
	}
	s.Apply(crtlink.Frame{Type: crtlink.TypeReset})
	c := s.Snapshot(0).Counters
	if c.Alarm != 0 {
		t.Errorf("复位后仍有 %d 个火警，锁存态未清", c.Alarm)
	}
	if c.Shielded != 1 {
		t.Errorf("复位把屏蔽清掉了（违反 5.4.4.7），屏蔽数 = %d", c.Shielded)
	}
}

// 故障是跟随型：源排除即消失，不需要复位。
func TestFaultFollowsSourceWithoutReset(t *testing.T) {
	s := NewState()
	s.Apply(frame(crtlink.TypeFault, crtlink.Report{Loop: 1, Addr: 3, Code: crtlink.FaultOpen}))
	if s.Snapshot(0).Counters.Fault != 1 {
		t.Fatal("断路故障未记入")
	}
	s.Apply(frame(crtlink.TypeFault, crtlink.Report{Loop: 1, Addr: 3, Code: 0}))
	if n := s.Snapshot(0).Counters.Fault; n != 0 {
		t.Errorf("故障排除后仍显示 %d 条", n)
	}
}

// 首火警在复位前不被后续火警顶掉（5.4.1.7）。
func TestFirstAlarmHeldUntilReset(t *testing.T) {
	s := NewState()
	s.Apply(frame(crtlink.TypeAlarm, crtlink.Report{Loop: 1, Addr: 7, Zone: 2,
		Code: crtlink.AlarmFromDetector | crtlink.AlarmFirst, At: time.Unix(1756600000, 0)}))
	s.Apply(frame(crtlink.TypeAlarm, crtlink.Report{Loop: 1, Addr: 8, Zone: 2,
		Code: crtlink.AlarmFromDetector, At: time.Unix(1756600030, 0)}))

	snap := s.Snapshot(0)
	if snap.First == nil {
		t.Fatal("首火警丢失")
	}
	if snap.First.Addr != 7 {
		t.Errorf("首火警被后续火警顶掉，现为地址 %d", snap.First.Addr)
	}
	if snap.Counters.Alarm != 2 {
		t.Errorf("火警总数 = %d，期望 2", snap.Counters.Alarm)
	}
	s.Apply(crtlink.Frame{Type: crtlink.TypeReset})
	if s.Snapshot(0).First != nil {
		t.Error("复位后首火警未清")
	}
}

// 手报必须与探测器可区分（5.4.1.4）。
func TestManualCallPointIsDistinguishable(t *testing.T) {
	s := NewState()
	s.Apply(frame(crtlink.TypeAlarm, crtlink.Report{Loop: 1, Addr: 20, Code: crtlink.AlarmFromManual}))
	d := s.Snapshot(0).Devices[0]
	if !d.Manual {
		t.Error("手报未标记为手动触发，面板无法区分类型")
	}
}

// 一个点可以同时报火警和被屏蔽，状态位不能互相压扁。
func TestAlarmAndShieldCoexistOnSameDevice(t *testing.T) {
	s := NewState()
	s.Apply(frame(crtlink.TypeShield, crtlink.Report{Loop: 1, Addr: 4, Code: 1}))
	s.Apply(frame(crtlink.TypeAlarm, crtlink.Report{Loop: 1, Addr: 4, Code: crtlink.AlarmFromDetector}))
	d := s.Snapshot(0).Devices[0]
	if !d.Alarm || !d.Shielded {
		t.Fatalf("状态位互相覆盖: alarm=%v shielded=%v", d.Alarm, d.Shielded)
	}
}

// 反馈跟随受控设备：设备回位后反馈撤销（5.4.2.9「保持至联动设备恢复」）。
func TestFeedbackWithdrawnWhenDeviceReturns(t *testing.T) {
	s := NewState()
	s.Apply(frame(crtlink.TypeAction, crtlink.Report{Loop: 1, Addr: 30, Code: 1}))
	s.Apply(frame(crtlink.TypeFeedback, crtlink.Report{Loop: 1, Addr: 30, Code: 1}))
	if c := s.Snapshot(0).Counters; c.Action != 1 || c.Feedback != 1 {
		t.Fatalf("启动/反馈计数 = %+v", c)
	}
	s.Apply(frame(crtlink.TypeFeedback, crtlink.Report{Loop: 1, Addr: 30, Code: 0}))
	c := s.Snapshot(0).Counters
	if c.Feedback != 0 {
		t.Error("设备恢复后反馈未撤销")
	}
	if c.Action != 1 {
		t.Error("启动是锁存态，不应随反馈撤销而消失")
	}
}

// 心跳停了就要报链路断，不能让页面显示陈旧数据当正常。
func TestLinkGoesDownWithoutHeartbeat(t *testing.T) {
	s := NewState()
	s.Apply(crtlink.Frame{Type: crtlink.TypeHeartbeat,
		Data: crtlink.EncodeHeartbeat(crtlink.Heartbeat{At: time.Now(), MainOK: true, BatteryOK: true})})
	if !s.Snapshot(0).LinkUp {
		t.Fatal("收到心跳后链路仍判为断开")
	}
	s.mu.Lock()
	s.lastBeat = time.Now().Add(-LinkTimeout - time.Second)
	s.mu.Unlock()
	if s.Snapshot(0).LinkUp {
		t.Error("心跳超时后链路仍判为在线")
	}
}

// 事件流按时间倒序给页面，最新在最上面。
func TestEventsNewestFirst(t *testing.T) {
	s := NewState()
	for i := uint8(1); i <= 3; i++ {
		s.Apply(frame(crtlink.TypeFault, crtlink.Report{Loop: 1, Addr: i, Code: crtlink.FaultOpen}))
	}
	ev := s.Snapshot(10).Events
	if len(ev) != 3 || ev[0].Addr != 3 {
		t.Fatalf("事件顺序错误: %+v", ev)
	}
}
