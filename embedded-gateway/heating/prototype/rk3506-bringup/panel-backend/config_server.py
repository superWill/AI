#!/usr/bin/env python3
"""面板配置后台(跑在 RK3506 网关上,纯标准库)。

手机/电脑浏览器打开 → 编辑 panel_config.json(加/删点、改上哪页/控件/单位/换算)
→ 保存即写盘 + 重载面板(killall hmi_lvgl,守护脚本自动用新配置重起)。

用法:  python3 config_server.py            # 默认 :8080,配置 /root/panel_config.json
"""
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CFG = sys.argv[1] if len(sys.argv) > 1 else "/root/panel_config.json"
HTML = "/root/config.html"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8080


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/config"):
            try:
                self._send(200, open(CFG, "rb").read())
            except OSError:
                self._send(200, b'{"pages":[]}')
        else:
            try:
                self._send(200, open(HTML, "rb").read(), "text/html; charset=utf-8")
            except OSError:
                self._send(500, "config.html 未部署")

    def do_POST(self):
        if not self.path.startswith("/api/config"):
            self._send(404, b'{}'); return
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        try:
            obj = json.loads(data)                       # 校验合法 JSON
            with open(CFG, "w") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            subprocess.run(["killall", "hmi_lvgl"], stderr=subprocess.DEVNULL)  # 触发面板重载
            self._send(200, b'{"ok":true}')
        except Exception as e:
            self._send(400, json.dumps({"ok": False, "err": str(e)}).encode())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("配置后台: http://0.0.0.0:%d/  (config=%s)" % (PORT, CFG), flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
