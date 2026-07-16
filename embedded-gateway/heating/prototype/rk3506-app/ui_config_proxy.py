#!/usr/bin/env python3
"""gatewayc UI 前置代理：补齐设备/标签草稿持久化，其余请求原样转发。"""
from __future__ import annotations

import argparse
import http.client
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import nexus_server as nexus


HOP_HEADERS = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
               "te", "trailers", "transfer-encoding", "upgrade", "content-length"}


def upstream_request(host, port, method, path, headers, body):
    forwarded = {k: v for k, v in headers.items()
                 if k.lower() not in HOP_HEADERS and k.lower() != "host"}
    conn = http.client.HTTPConnection(host, port, timeout=35)
    try:
        conn.request(method, path, body=body, headers=forwarded)
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        conn.close()


def make_handler(upstream_host="127.0.0.1", upstream_port=8093):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, status, headers, body):
            self.send_response(status)
            for key, value in headers.items():
                if key.lower() not in HOP_HEADERS:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _json(self, status, value):
            body = json.dumps(value, ensure_ascii=False).encode()
            self._send(status, {"Content-Type": "application/json; charset=utf-8",
                                "Cache-Control": "no-store"}, body)

        def _upstream(self, method=None, body=None):
            return upstream_request(upstream_host, upstream_port, method or self.command,
                                    self.path, self.headers, body)

        def _upstream_init(self):
            status, headers, raw = upstream_request(
                upstream_host, upstream_port, "GET", "/api/init", self.headers, None)
            if status != 200:
                return status, headers, raw, None
            try:
                return status, headers, raw, json.loads(raw)
            except ValueError:
                return 502, {}, b"", None

        def _read_body(self):
            length = int(self.headers.get("Content-Length", 0))
            if length > 4 * 1024 * 1024:
                raise ValueError("request body too large")
            return self.rfile.read(length) if length else b""

        def _local_only(self):
            return self.client_address[0] in ("127.0.0.1", "::1")

        def _local_inventory(self):
            return {"ok": True, "nodes": nexus._read_ui_collection("nodes"),
                    "tags": nexus._read_ui_collection("tags")}

        def do_GET(self):
            if self.path.split("?", 1)[0] == "/api/local/device-config":
                if not self._local_only():
                    return self._json(403, {"ok": False, "error": "local only"})
                return self._json(200, self._local_inventory())
            if self.path.split("?", 1)[0] != "/api/init":
                status, headers, body = self._upstream()
                return self._send(status, headers, body)
            status, headers, raw, value = self._upstream_init()
            if value is None:
                return self._send(status, headers, raw)
            runtime_nodes = value.get("nodes", [])
            runtime_tags = value.get("tags", [])
            for item in runtime_nodes + runtime_tags:
                if isinstance(item, dict):
                    item.update({"managedBy": "runtime", "configState": "active"})
            value["nodes"] = nexus.merge_ui_collection(runtime_nodes, "nodes")
            value["tags"] = nexus.merge_ui_collection(runtime_tags, "tags")
            return self._json(200, value)

        def do_POST(self):
            try:
                body = self._read_body()
            except ValueError as exc:
                return self._json(413, {"ok": False, "error": str(exc)})
            path = self.path.split("?", 1)[0]
            if path == "/api/local/device-config":
                if not self._local_only():
                    return self._json(403, {"ok": False, "error": "local only"})
                try:
                    payload = json.loads(body or b"[]")
                except ValueError:
                    return self._json(400, {"ok": False, "error": "JSON 格式错误"})
                ok, errors, saved = nexus.save_ui_nodes(payload, ())
                return self._json(200 if ok else 400, {
                    "ok": ok, "errors": errors, "error": errors[0] if errors else None,
                    "nodes": saved, "configurationState": "draft_manual_required"})
            if path not in ("/api/nodes", "/api/tags"):
                status, headers, result = self._upstream(body=body)
                return self._send(status, headers, result)
            status, headers, raw, current = self._upstream_init()
            if current is None:
                return self._send(status, headers, raw)
            try:
                payload = json.loads(body or b"[]")
            except ValueError:
                return self._json(400, {"ok": False, "error": "JSON 格式错误"})
            runtime_nodes = current.get("nodes", [])
            runtime_tags = current.get("tags", [])
            if path == "/api/nodes":
                ok, errors, saved = nexus.save_ui_nodes(payload, runtime_nodes)
                key = "nodes"
            else:
                ok, errors, saved = nexus.save_ui_tags(payload, runtime_nodes, runtime_tags)
                key = "tags"
            return self._json(200 if ok else 400, {
                "ok": ok, "errors": errors, "error": errors[0] if errors else None,
                key: saved, "configurationState": "draft_manual_required"})

        def do_DELETE(self):
            body = self._read_body()
            status, headers, result = self._upstream(body=body)
            return self._send(status, headers, result)

        def do_PUT(self):
            body = self._read_body()
            status, headers, result = self._upstream(body=body)
            return self._send(status, headers, result)

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--upstream-port", type=int, default=8093)
    parser.add_argument("--port", type=int, default=8092)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(args.host, args.upstream_port))
    print("[ui-proxy] http://0.0.0.0:%d -> http://%s:%d" %
          (args.port, args.host, args.upstream_port), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
