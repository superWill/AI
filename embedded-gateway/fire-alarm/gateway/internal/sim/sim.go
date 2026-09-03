// Package sim 模拟一台火灾报警控制器主机，按 crt-link 协议向 CRT 侧发帧。
//
// 用途有二：一是没接真机时也能把页面跑起来；二是反过来当协议靶场——固件侧
// 实现好上行报文后，可以拿本模拟器的帧序列做对照（用例 CM-02 五类信息上报）。
package sim

import (
	"log"
	"net"
	"time"

	"github.com/superwill/fire-alarm/gateway/internal/crtlink"
)

// Step 是脚本里的一拍：等待 Wait 后发出一帧。
type Step struct {
	Wait time.Duration
	Type uint8
	Rep  crtlink.Report
	Note string
}

// Scenario 返回一个贴近实机台架的演示脚本：单回路，一只烟感、一个输入输出
// 模块、一只声光、一个紧急启停按钮，外加打印机与存储单元两个机内设备故障
// （与 2026-08 实机故障页一致）。脚本循环播放。
func Scenario() []Step {
	const (
		smoke   = 1  // 点型感烟探测器
		iomod   = 3  // 输入输出模块
		sounder = 5  // 声光警报器
		estop   = 7  // 紧急启停按钮
		printer = 16 // 打印机（机内）
		storage = 4  // 运行数据存储单元（机内）
	)
	return []Step{
		{Wait: 2 * time.Second, Type: crtlink.TypeFault, Note: "存储单元掉线",
			Rep: crtlink.Report{EventID: 1, Loop: 1, Addr: storage, Code: crtlink.FaultTimeout}},
		{Wait: 1 * time.Second, Type: crtlink.TypeFault, Note: "打印机掉线",
			Rep: crtlink.Report{EventID: 2, Loop: 1, Addr: printer, Code: crtlink.FaultTimeout}},
		{Wait: 1 * time.Second, Type: crtlink.TypeFault, Note: "输入模块断路",
			Rep: crtlink.Report{EventID: 3, Loop: 1, Addr: iomod, Code: crtlink.FaultOpen}},

		{Wait: 6 * time.Second, Type: crtlink.TypeAlarm, Note: "烟感首火警",
			Rep: crtlink.Report{EventID: 4, Loop: 1, Addr: smoke, Zone: 1,
				Code: crtlink.AlarmFromDetector | crtlink.AlarmFirst}},
		{Wait: 2 * time.Second, Type: crtlink.TypeAction, Note: "声光警报器启动",
			Rep: crtlink.Report{EventID: 5, Loop: 1, Addr: sounder, Zone: 1, Code: 1}},
		{Wait: 3 * time.Second, Type: crtlink.TypeFeedback, Note: "受控设备反馈",
			Rep: crtlink.Report{EventID: 6, Loop: 1, Addr: sounder, Zone: 1, Code: 1}},
		{Wait: 4 * time.Second, Type: crtlink.TypeAlarm, Note: "紧急启停按钮手动报警",
			Rep: crtlink.Report{EventID: 7, Loop: 1, Addr: estop, Zone: 1, Code: crtlink.AlarmFromManual}},
		{Wait: 4 * time.Second, Type: crtlink.TypeSupervisor, Note: "信号阀监管信号",
			Rep: crtlink.Report{EventID: 8, Loop: 1, Addr: iomod, Zone: 2, Code: 1}},
		{Wait: 4 * time.Second, Type: crtlink.TypeShield, Note: "屏蔽故障模块",
			Rep: crtlink.Report{EventID: 9, Loop: 1, Addr: iomod, Code: 1}},

		{Wait: 8 * time.Second, Type: crtlink.TypeReset, Note: "复位（屏蔽应保留）"},
		{Wait: 3 * time.Second, Type: crtlink.TypeShield, Note: "解除屏蔽",
			Rep: crtlink.Report{EventID: 10, Loop: 1, Addr: iomod, Code: 0}},
		{Wait: 3 * time.Second, Type: crtlink.TypeFault, Note: "输入模块故障排除",
			Rep: crtlink.Report{EventID: 11, Loop: 1, Addr: iomod, Code: 0}},
		{Wait: 6 * time.Second, Note: "——脚本循环——"},
	}
}

// Run 连接 CRT 网关并循环播放脚本，直到 ctx 取消。心跳独立于脚本按 5 s 发出。
func Run(addr string, stop <-chan struct{}) error {
	c, err := net.Dial("tcp", addr)
	if err != nil {
		return err
	}
	defer c.Close()
	log.Printf("模拟主机已连接 %s", addr)

	var seq uint16
	send := func(typ uint8, data []byte) error {
		seq++
		f := crtlink.Frame{Seq: seq, Src: crtlink.AddrHost, Dst: crtlink.AddrCRT, Type: typ, Data: data}
		raw, err := crtlink.Encode(f)
		if err != nil {
			return err
		}
		_, err = c.Write(raw)
		return err
	}

	// 心跳：5 s 一拍（default-parameters.json 的 heartbeat_interval_ms）。
	go func() {
		t := time.NewTicker(5 * time.Second)
		defer t.Stop()
		for {
			select {
			case <-stop:
				return
			case <-t.C:
				_ = send(crtlink.TypeHeartbeat, crtlink.EncodeHeartbeat(
					crtlink.Heartbeat{At: time.Now(), MainOK: true, BatteryOK: true}))
			}
		}
	}()

	// 丢弃 CRT 的下行帧（ACK/授时），模拟器不做完整应答。
	go func() { _, _ = c.Read(make([]byte, 0)) }()
	go func() {
		dec := crtlink.NewDecoder(c)
		for {
			f, err := dec.Next()
			if err != nil {
				return
			}
			if f.Type == crtlink.TypeTimeSync {
				if t, err := crtlink.DecodeTimeSync(f.Data); err == nil {
					log.Printf("模拟主机收到授时：%s", t.Format("2006-01-02 15:04:05"))
				}
			}
		}
	}()

	_ = send(crtlink.TypeHeartbeat, crtlink.EncodeHeartbeat(
		crtlink.Heartbeat{At: time.Now(), MainOK: true, BatteryOK: true}))

	steps := Scenario()
	for {
		for _, st := range steps {
			select {
			case <-stop:
				return nil
			case <-time.After(st.Wait):
			}
			if st.Type == 0 {
				continue
			}
			var body []byte
			if st.Type != crtlink.TypeReset {
				r := st.Rep
				r.At = time.Now()
				body = crtlink.EncodeReport(r)
			}
			if err := send(st.Type, body); err != nil {
				return err
			}
			log.Printf("模拟主机发帧：%s（%s）", crtlink.TypeName(st.Type), st.Note)
		}
	}
}
