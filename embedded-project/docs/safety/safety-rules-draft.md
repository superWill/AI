# Safety Rules Draft

## Rule Priority

Safety rules are evaluated before normal automatic control.

## Initial Rules

| Rule | Trigger | Action |
| --- | --- | --- |
| Over temperature | Secondary supply temperature exceeds high limit | Close or reduce primary valve, keep circulation pump running for heat dissipation, raise alarm |
| High pressure | Secondary supply pressure exceeds high limit | Reduce pump frequency, stop refill, open relief if available, raise alarm |
| Low pressure | Secondary return pressure or refill pressure below low limit | Start refill, stop circulation pump if refill fails, raise alarm |
| Pump fault | Pump run command is on but feedback or VFD status is faulty | Stop faulty pump, switch standby pump if available, raise alarm |
| Sensor fault | Critical sensor offline or out of physical range | Disable related automatic control, enter degraded mode or emergency stop |
| Communication offline | MQTT disconnected | Continue local autonomous control, cache telemetry and alarms |

