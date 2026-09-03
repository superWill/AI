#!/usr/bin/env python3
"""用 app.py 真实实现对拍 Go Controller 的 L1 决策与 L2 SimSource 闭环。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP_PATH = HERE.parent / "app.py"
REAL_THREAD = threading.Thread
REAL_TIME = time.time
REAL_SLEEP = time.sleep


def load_app():
    spec = importlib.util.spec_from_file_location("rk3506_app", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class FakeRuntime:
    def __init__(self):
        self.snapshot = {"devices": []}
        self.records = []
        self.events = []

    def view(self):
        return self.snapshot

    def record_command(self, rec):
        self.records.append(dict(rec))

    def add_event(self, event):
        self.events.append(dict(event))


class FakeSource:
    def __init__(self):
        self.ok = True
        self.writes = []

    def write_setpoint(self, point_id, value, *_):
        self.writes.append({"point_id": point_id, "value": float(value)})
        return self.ok


def run_python(scenario):
    app = load_app()
    runtime = FakeRuntime()
    source = FakeSource()
    now = [0.0]
    feedback = []
    threads = []
    thread_gate = threading.Event()

    def fake_time():
        return now[0]

    def fake_sleep(seconds):
        now[0] += seconds
        if feedback:
            runtime.snapshot = feedback.pop(0)

    class TrackingThread:
        def __init__(self, *args, **kwargs):
            target = kwargs.pop("target")
            target_args = kwargs.pop("args", ())

            def gated_target():
                thread_gate.wait()
                target(*target_args)

            self.thread = REAL_THREAD(target=gated_target, *args, **kwargs)

        def start(self):
            threads.append(self.thread)
            self.thread.start()

    app.time.time = fake_time
    app.time.sleep = fake_sleep
    app.threading.Thread = TrackingThread
    controller = app.Controller(
        runtime, source, {}, safety_policy=scenario.get("policy") or {}
    )
    results = []
    try:
        for command in scenario["commands"]:
            thread_gate.clear()
            now[0] = command["at"]
            runtime.snapshot = command.get("snapshot", runtime.snapshot)
            feedback[:] = command.get("feedback_snapshots", [])
            source.ok = command.get("write_ok", True)
            ok, reason = controller.apply(
                command["point_id"],
                command["value"],
                command.get("command_id", ""),
                command.get("origin", "local"),
            )
            thread_gate.set()
            while threads:
                threads.pop(0).join()
            results.append({"ok": ok, "reason": reason})
    finally:
        app.threading.Thread = REAL_THREAD
        app.time.time = REAL_TIME
        app.time.sleep = REAL_SLEEP

    alarms = [
        {"action": event["action"], "detail": event["detail"]}
        for event in runtime.events
        if event.get("kind") == "alarm"
    ]
    return {
        "results": results,
        "writes": source.writes,
        "records": runtime.records,
        "alarms": alarms,
    }


def run_go(scenario, go_bin):
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as f:
        json.dump(scenario, f, ensure_ascii=False)
        f.flush()
        if go_bin:
            command = [go_bin, "controllercase", f.name]
        else:
            command = ["go", "run", ".", "controllercase", f.name]
        output = subprocess.check_output(command, cwd=HERE, text=True)
    return json.loads(output)


def run_python_sim(scenario):
    app = load_app()
    runtime = FakeRuntime()
    now = [float(scenario["at"])]
    threads = []
    thread_gate = threading.Event()

    def fake_time():
        return now[0]

    source = None

    def fake_sleep(seconds):
        now[0] += seconds
        runtime.snapshot = {
            "devices": list(source.poll().values()),
        }

    class TrackingThread:
        def __init__(self, *args, **kwargs):
            target = kwargs.pop("target")
            target_args = kwargs.pop("args", ())

            def gated_target():
                thread_gate.wait()
                target(*target_args)

            self.thread = REAL_THREAD(target=gated_target, *args, **kwargs)

        def start(self):
            threads.append(self.thread)
            self.thread.start()

    app.time.time = fake_time
    app.time.sleep = fake_sleep
    app.threading.Thread = TrackingThread
    try:
        source = app.SimSource(scenario["devices"])
        runtime.snapshot = {"devices": list(source.poll().values())}
        controller = app.Controller(
            runtime, source, {}, safety_policy=scenario["policy"]
        )
        command = scenario["command"]
        thread_gate.clear()
        ok, reason = controller.apply(
            command["point_id"], command["value"],
            command["command_id"], command["origin"],
        )
        thread_gate.set()
        while threads:
            threads.pop(0).join()
    finally:
        app.threading.Thread = REAL_THREAD
        app.time.time = REAL_TIME
        app.time.sleep = REAL_SLEEP

    alarms = [
        {"action": event["action"], "detail": event["detail"]}
        for event in runtime.events
        if event.get("kind") == "alarm"
    ]
    return {
        "result": {"ok": ok, "reason": reason},
        "records": runtime.records,
        "alarms": alarms,
        "snapshot": runtime.snapshot,
    }


def run_go_sim(scenario, go_bin):
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as f:
        json.dump(scenario, f, ensure_ascii=False)
        f.flush()
        if go_bin:
            command = [go_bin, "simcontrolcase", f.name]
        else:
            command = ["go", "run", ".", "simcontrolcase", f.name]
        output = subprocess.check_output(command, cwd=HERE, text=True)
    return json.loads(output)


def scenarios():
    empty = {"devices": []}
    feedback_40 = {
        "devices": [{"points": {"sec_supply_temp": {"v": 40.0, "q": "good"}}}]
    }
    feedback_50 = {
        "devices": [{"points": {"sec_supply_temp": {"v": 50.0, "q": "good"}}}]
    }
    return {
        "fallback_and_write_failure": {
            "policy": {},
            "commands": [
                {"at": 100, "point_id": "valve_open_sp", "value": 80,
                 "command_id": "a", "origin": "hmi", "snapshot": empty},
                {"at": 101, "point_id": "pump_freq_sp", "value": 30,
                 "command_id": "b", "origin": "hmi", "write_ok": False},
                {"at": 102, "point_id": "unknown", "value": 1,
                 "command_id": "c", "origin": "platform"},
            ],
        },
        "rate_and_interlock": {
            "policy": {
                "valve_open_sp": {"lo": 0, "hi": 100, "rate_per_s": 1},
                "pump_freq_sp": {
                    "lo": 0, "hi": 50,
                    "interlocks": [{"point": "emergency_stop", "equals": 0}],
                },
            },
            "commands": [
                {"at": 100, "point_id": "valve_open_sp", "value": 80,
                 "command_id": "d", "origin": "platform", "snapshot": empty},
                {"at": 101, "point_id": "valve_open_sp", "value": 82,
                 "command_id": "e", "origin": "platform"},
                {"at": 102, "point_id": "pump_freq_sp", "value": 30,
                 "command_id": "f", "origin": "platform",
                 "snapshot": {"devices": [{"points": {
                     "emergency_stop": {"v": 1, "q": "good"}
                 }}]}},
            ],
        },
        "feedback_confirmed": {
            "policy": {
                "sec_supply_temp_sp": {
                    "lo": 20, "hi": 75, "feedback": "sec_supply_temp",
                    "confirm_timeout_s": 2, "confirm_tolerance": 1,
                }
            },
            "commands": [
                {"at": 100, "point_id": "sec_supply_temp_sp", "value": 50,
                 "command_id": "g", "origin": "platform", "snapshot": feedback_40,
                 "feedback_snapshots": [feedback_40, feedback_50]},
            ],
        },
        "feedback_timeout": {
            "policy": {
                "sec_supply_temp_sp": {
                    "lo": 20, "hi": 75, "feedback": "sec_supply_temp",
                    "confirm_timeout_s": 1, "confirm_tolerance": 0.1,
                }
            },
            "commands": [
                {"at": 100, "point_id": "sec_supply_temp_sp", "value": 50,
                 "command_id": "h", "origin": "platform", "snapshot": feedback_40,
                 "feedback_snapshots": [feedback_40, feedback_40]},
            ],
        },
        "multidecimal_reasons": {
            "policy": {
                "valve_open_sp": {"lo": 0, "hi": 100},
                "pump_freq_sp": {
                    "lo": 0, "hi": 50,
                    "interlocks": [{"point": "water_level", "min": 30.5}],
                },
            },
            "commands": [
                {"at": 100, "point_id": "valve_open_sp", "value": 120.25,
                 "command_id": "m1", "origin": "platform", "snapshot": empty},
                {"at": 101, "point_id": "pump_freq_sp", "value": 30,
                 "command_id": "m2", "origin": "platform",
                 "snapshot": {"devices": [{"points": {
                     "water_level": {"v": 29.97, "q": "good"}
                 }}]}},
            ],
        },
    }


def sim_scenario():
    return {
        "at": 100,
        "devices": [{
            "addr": 1,
            "name": "二次供温",
            "type": "仿真",
            "points": [{"id": "sec_supply_temp", "unit": "degC"}],
        }],
        "policy": {
            "sec_supply_temp_sp": {
                "lo": 20,
                "hi": 75,
                "feedback": "sec_supply_temp",
                "confirm_timeout_s": 8,
                "confirm_tolerance": 1,
            }
        },
        "command": {
            "point_id": "sec_supply_temp_sp",
            "value": 60,
            "command_id": "sim-1",
            "origin": "hmi",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--go-bin", help="已有 gatewayc 路径；缺省使用 go run .")
    args = parser.parse_args()
    failed = False
    for name, scenario in scenarios().items():
        python_result = run_python(scenario)
        go_result = run_go(scenario, args.go_bin)
        if python_result != go_result:
            failed = True
            print(f"[FAIL] {name}")
            print("python:", json.dumps(python_result, ensure_ascii=False, indent=2))
            print("go:", json.dumps(go_result, ensure_ascii=False, indent=2))
        else:
            print(f"[PASS] {name}")
    scenario = sim_scenario()
    python_result = run_python_sim(scenario)
    go_result = run_go_sim(scenario, args.go_bin)
    if python_result != go_result:
        failed = True
        print("[FAIL] sim_source_closed_loop")
        print("python:", json.dumps(python_result, ensure_ascii=False, indent=2))
        print("go:", json.dumps(go_result, ensure_ascii=False, indent=2))
    else:
        print("[PASS] sim_source_closed_loop")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
