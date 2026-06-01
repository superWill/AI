# MQTT Protocol Draft

## Topic Draft

```text
station/{device_id}/telemetry
station/{device_id}/event
station/{device_id}/alarm
station/{device_id}/property/get
station/{device_id}/property/set
station/{device_id}/command
station/{device_id}/command_reply
station/{device_id}/ota
station/{device_id}/heartbeat
```

## Command Reply States

- `accepted`
- `rejected`
- `running`
- `success`
- `failed`
- `blocked_by_safety`

## Command Message Shape

```json
{
  "command_id": "cmd-001",
  "timestamp": 1715570000,
  "operator": "platform",
  "command_type": "set_mode",
  "payload": {
    "mode": "AUTO"
  }
}
```

## Reply Message Shape

```json
{
  "command_id": "cmd-001",
  "timestamp": 1715570002,
  "status": "success",
  "reason": ""
}
```

