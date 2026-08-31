// facgw 是消防控制室图形显示装置（CRT）侧的网关：
// 对下按 crt-link 协议接火灾报警控制器，对上提供消防页面。
//
//	facgw                          # 监听 :7801(链路) :8080(页面)
//	facgw -sim                     # 同时拉起模拟主机，无硬件也能看页面
//	facgw -points points.json      # 装载工程点表（点位名称/类型）
package main

import (
	"encoding/json"
	"flag"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/superwill/fire-alarm/gateway/internal/model"
	"github.com/superwill/fire-alarm/gateway/internal/server"
	"github.com/superwill/fire-alarm/gateway/internal/sim"
)

func main() {
	linkAddr := flag.String("link", ":7801", "控制器链路监听地址（TCP）")
	httpAddr := flag.String("http", ":8080", "页面与 API 监听地址")
	points := flag.String("points", "", "工程点表 JSON 路径")
	withSim := flag.Bool("sim", false, "同时启动模拟主机（无硬件演示/协议靶场）")
	flag.Parse()

	srv := server.New()

	if *points != "" {
		b, err := os.ReadFile(*points)
		if err != nil {
			log.Fatalf("读取点表失败：%v", err)
		}
		var ps []model.Point
		if err := json.Unmarshal(b, &ps); err != nil {
			log.Fatalf("解析点表失败：%v", err)
		}
		srv.State.LoadPoints(ps)
		log.Printf("已装载点表 %d 条：%s", len(ps), *points)
	}

	go func() {
		if err := srv.ServeLink(*linkAddr); err != nil {
			log.Fatalf("链路监听失败：%v", err)
		}
	}()

	stop := make(chan struct{})
	if *withSim {
		go func() {
			// 等链路监听就位后再拨号；断开后自动重连，方便反复演示。
			time.Sleep(300 * time.Millisecond)
			for {
				if err := sim.Run(*linkAddr, stop); err != nil {
					log.Printf("模拟主机断开：%v，2 s 后重连", err)
				}
				select {
				case <-stop:
					return
				case <-time.After(2 * time.Second):
				}
			}
		}()
	}

	httpSrv := &http.Server{Addr: *httpAddr, Handler: srv.Routes()}
	go func() {
		log.Printf("消防页面 http://127.0.0.1%s", *httpAddr)
		if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("HTTP 监听失败：%v", err)
		}
	}()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	close(stop)
	log.Println("退出")
}
