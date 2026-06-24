// gatewayc —— 网关配置工具链（Go）。子命令：
//
//	gatewayc compile <draft.json> [--out DIR] [--validate-only]     （对照 compiler.py）
//	gatewayc load <build_dir> [--device-id ID] [--source sim|modbus] [--emit-app-config FILE]  （对照 loader.py）
package main

import (
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
)

func main() {
	if len(os.Args) < 2 {
		usage()
	}
	switch os.Args[1] {
	case "compile":
		runCompile(os.Args[2:])
	case "load":
		runLoad(os.Args[2:])
	case "simpoll":
		runSimPoll(os.Args[2:])
	case "modbusframe":
		runModbusFrame(os.Args[2:])
	case "modbuspoll":
		runModbusPoll(os.Args[2:])
	case "modbusread":
		runModbusRead(os.Args[2:])
	case "modbuswrite":
		runModbusWrite(os.Args[2:])
	case "controllercase":
		runControllerCase(os.Args[2:])
	case "simcontrolcase":
		runSimControlCase(os.Args[2:])
	case "controllerloop":
		runControllerLoop(os.Args[2:])
	case "runtimecase":
		runRuntimeCase(os.Args[2:])
	case "run":
		runGateway(os.Args[2:])
	case "shadow":
		runShadow(os.Args[2:])
	case "health":
		runHealth(os.Args[2:])
	default:
		usage()
	}
}

// modbuspoll: 用脚本化的读结果序列驱动 ModbusSource.Poll()，逐步输出（状态机对拍用）。
func runModbusPoll(args []string) {
	if len(args) < 1 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc modbuspoll <scenario.json>")
		os.Exit(2)
	}
	raw, err := os.ReadFile(args[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "读取场景失败: %v\n", err)
		os.Exit(2)
	}
	var sc obj
	if err := json.Unmarshal(raw, &sc); err != nil {
		fmt.Fprintf(os.Stderr, "解析场景失败: %v\n", err)
		os.Exit(2)
	}
	var curReads obj
	var curMono, curWall float64
	readFn := func(addr, start, count int, t float64, retries int) ([]uint16, string) {
		r := asObj(curReads[strconv.Itoa(addr)])
		if e := asStr(get(r, "err")); e != "" {
			return nil, e
		}
		ra := asArr(r["regs"])
		regs := make([]uint16, len(ra))
		for i, x := range ra {
			regs[i] = uint16(toF(x))
		}
		return regs, ""
	}
	m := NewModbusSource(asArr(sc["devices"]), asObj(sc["reliability"]), readFn,
		func() float64 { return curMono }, func() float64 { return curWall })
	results := arr{}
	for _, si := range asArr(sc["steps"]) {
		s := asObj(si)
		curMono = toF(s["mono"])
		curWall = toF(s["wall"])
		curReads = asObj(s["reads"])
		results = append(results, m.Poll())
	}
	b, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(b))
}

// modbusframe: Modbus 协议帧构造/解析（逐字节对拍用）。
//
//	req <addr> <start> <count>   读保持寄存器请求 hex
//	write <addr> <reg> <value>   写单寄存器请求 hex
//	parse <resp_hex>             解析应答 -> {regs, err}
func runModbusFrame(args []string) {
	atoi := func(s string) int { n, _ := strconv.Atoi(s); return n }
	if len(args) < 1 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc modbusframe req|write|parse ...")
		os.Exit(2)
	}
	switch args[0] {
	case "crc":
		b, _ := hex.DecodeString(args[1])
		fmt.Println(hex.EncodeToString(ModbusCRC(b)))
	case "req":
		fmt.Println(hex.EncodeToString(BuildReadHolding(atoi(args[1]), atoi(args[2]), atoi(args[3]))))
	case "write":
		fmt.Println(hex.EncodeToString(BuildWriteRegister(atoi(args[1]), atoi(args[2]), atoi(args[3]))))
	case "parse":
		b, err := hex.DecodeString(args[1])
		if err != nil {
			fmt.Fprintf(os.Stderr, "hex 解码失败: %v\n", err)
			os.Exit(2)
		}
		regs, e := ParseReadHolding(b)
		bb, _ := json.Marshal(obj{"regs": regs, "err": e})
		fmt.Println(string(bb))
	default:
		fmt.Fprintln(os.Stderr, "未知子动作: "+args[0])
		os.Exit(2)
	}
}

// simpoll: 仿真源单次采样（迁移对拍用）。固定 t0/采样时刻使结果确定。
func runSimPoll(args []string) {
	if len(args) < 3 {
		fmt.Fprintln(os.Stderr, "用法: gatewayc simpoll <t0> <tpoll> <devices.json>")
		os.Exit(2)
	}
	t0, _ := strconv.ParseFloat(args[0], 64)
	tpoll, _ := strconv.ParseFloat(args[1], 64)
	raw, err := os.ReadFile(args[2])
	if err != nil {
		fmt.Fprintf(os.Stderr, "读取设备配置失败: %v\n", err)
		os.Exit(2)
	}
	var devs arr
	if err := json.Unmarshal(raw, &devs); err != nil {
		fmt.Fprintf(os.Stderr, "解析设备配置失败: %v\n", err)
		os.Exit(2)
	}
	cur := t0
	s := NewSimSource(devs, func() float64 { return cur })
	cur = tpoll
	b, _ := json.MarshalIndent(s.Poll(), "", "  ")
	fmt.Println(string(b))
}

func usage() {
	fmt.Fprintln(os.Stderr, "用法:")
	fmt.Fprintln(os.Stderr, "  gatewayc compile <draft.json> [--out DIR] [--validate-only]")
	fmt.Fprintln(os.Stderr, "  gatewayc load <build_dir> [--device-id ID] [--source sim|modbus] [--emit-app-config FILE]")
	fmt.Fprintln(os.Stderr, "  gatewayc controllercase <scenario.json>")
	fmt.Fprintln(os.Stderr, "  gatewayc simcontrolcase <scenario.json>")
	fmt.Fprintln(os.Stderr, "  gatewayc modbuswrite <dev> <baud> <point_id> <value> <addr> <reg> <scale> [timeoutSec]")
	os.Exit(2)
}

// positional 容忍 flag 在前后任意顺序（对齐 Python argparse）
func splitArgs(fs *flag.FlagSet, args []string) string {
	fs.Parse(args)
	rest := fs.Args()
	if len(rest) < 1 {
		fs.Usage()
		os.Exit(2)
	}
	pos := rest[0]
	fs.Parse(rest[1:])
	return pos
}

func runCompile(args []string) {
	fs := flag.NewFlagSet("compile", flag.ExitOnError)
	out := fs.String("out", "build", "产物输出目录")
	validateOnly := fs.Bool("validate-only", false, "仅校验")
	draftPath := splitArgs(fs, args)

	raw, err := os.ReadFile(draftPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[错误] 读取草稿失败: %v\n", err)
		os.Exit(2)
	}
	var draft obj
	if err := json.Unmarshal(raw, &draft); err != nil {
		fmt.Fprintf(os.Stderr, "[错误] 读取草稿失败: %v\n", err)
		os.Exit(2)
	}

	errs := Validate(draft)
	if len(errs) > 0 {
		fmt.Fprintf(os.Stderr, "[校验失败] %d 项:\n", len(errs))
		for _, e := range errs {
			fmt.Fprintf(os.Stderr, "  - %s\n", e)
		}
		os.Exit(1)
	}
	fmt.Println("[校验通过]")
	if *validateOnly {
		return
	}

	products := Compile(draft)
	if err := os.MkdirAll(*out, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "[错误] 建目录失败: %v\n", err)
		os.Exit(2)
	}
	for _, name := range []string{"point_registry.json", "poll_plan.json", "display_model.json", "safety_policy.json"} {
		path := filepath.Join(*out, name)
		b, _ := json.MarshalIndent(products[name], "", "  ")
		if err := os.WriteFile(path, append(b, '\n'), 0o644); err != nil {
			fmt.Fprintf(os.Stderr, "[错误] 写产物失败: %v\n", err)
			os.Exit(2)
		}
		fmt.Printf("[产物] %s\n", path)
	}
}

func runLoad(args []string) {
	fs := flag.NewFlagSet("load", flag.ExitOnError)
	deviceID := fs.String("device-id", "rk3506-gw-01", "设备ID")
	source := fs.String("source", "sim", "采集源 sim|modbus")
	emit := fs.String("emit-app-config", "", "写出 app.py 可直接 --config 的 json")
	buildDir := splitArgs(fs, args)

	cfg, err := LoadRuntimeCfg(buildDir, *deviceID, *source)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[错误] 读取编译产物失败: %v\n", err)
		os.Exit(2)
	}
	nDev := len(asArr(cfg["devices"]))
	nCtl := len(asObj(cfg["control_map"]))
	if *emit != "" {
		b, _ := json.MarshalIndent(cfg, "", "  ")
		if err := os.WriteFile(*emit, append(b, '\n'), 0o644); err != nil {
			fmt.Fprintf(os.Stderr, "[错误] 写运行配置失败: %v\n", err)
			os.Exit(2)
		}
		fmt.Printf("[运行配置] %s  (%d 设备, %d 可控点)\n", *emit, nDev, nCtl)
	} else {
		b, _ := json.MarshalIndent(cfg, "", "  ")
		fmt.Println(string(b))
	}
}
