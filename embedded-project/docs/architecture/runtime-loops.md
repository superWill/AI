# Runtime Loops

## Fast Loop: 100 ms

```text
feed_watchdog()
scan_emergency_inputs()
update_critical_io()
run_hard_protection()
```

Purpose:

- Keep watchdog alive.
- Detect emergency input quickly.
- Execute hard safety protection before normal control.

## Main Loop: 1 s

```text
read_all_points()
validate_points()
update_state_machine()
run_safety_protection()
run_control_algorithms()
dispatch_device_commands()
update_hmi_snapshot()
```

Purpose:

- Execute normal station control.
- Keep the local screen updated.
- Ensure all commands pass through safety and state checks.

## Communication Loop: 5 s

```text
mqtt_heartbeat()
upload_telemetry()
upload_alarms()
process_remote_commands()
sync_parameters()
```

Purpose:

- Keep platform visibility.
- Process remote parameters and commands.
- Cache important data when offline.

## Maintenance Loop: 60 s

```text
persist_runtime_data()
rotate_logs()
check_ota_task()
check_device_health()
```

Purpose:

- Save parameters and runtime state.
- Maintain logs.
- Check upgrade tasks and device health.

