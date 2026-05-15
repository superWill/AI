// fac_interlock.h — interlock matrix engine
//
// 最高优先级。触发条件一旦满足，必须直接输出联动指令，不受手动屏蔽
// 或远程隔离逻辑覆盖。手动允许状态下，操作员只能"额外启动"或"停止"
// 单台设备，不能阻止已触发的自动联动。
//
// 联动规则见 docs/safety/interlock-rules-draft.md。

#ifndef FAC_INTERLOCK_H
#define FAC_INTERLOCK_H

#include <stdbool.h>
#include <stdint.h>

#include "fac_alarm.h"

typedef enum {
    FAC_TRIG_SINGLE_ALARM = 0,
    FAC_TRIG_CROSS_ALARM,
    FAC_TRIG_WATER_FLOW,
    FAC_TRIG_PRESSURE_SWITCH,
    FAC_TRIG_GAS_RELEASE,
    FAC_TRIG_MANUAL_START,
} fac_trigger_kind_t;

typedef enum {
    FAC_ACTION_SOUND_LIGHT = 0,
    FAC_ACTION_BROADCAST,
    FAC_ACTION_DOOR_RELEASE,
    FAC_ACTION_SHUTTER_DESCEND,
    FAC_ACTION_ELEVATOR_RECALL,
    FAC_ACTION_SMOKE_DAMPER_OPEN,
    FAC_ACTION_AIR_DAMPER_OPEN,
    FAC_ACTION_SMOKE_FAN_ON,
    FAC_ACTION_SUPPLY_FAN_ON,
    FAC_ACTION_FIRE_PUMP_ON,
    FAC_ACTION_SPRINKLER_PUMP_ON,
    FAC_ACTION_STABILIZE_PUMP_OFF,
    FAC_ACTION_NON_FIRE_POWER_OFF,
    FAC_ACTION_GAS_RELEASE,
} fac_action_kind_t;

typedef struct {
    fac_action_kind_t kind;
    uint16_t          target_id;     // zone_id 或 device_id
    uint16_t          delay_ms;
    uint8_t           stage;         // 用于多段动作（防火卷帘等）
    uint16_t          param;         // 动作附加参数（广播片段 id 等）
} fac_action_t;

typedef struct {
    uint16_t          rule_id;
    fac_trigger_kind_t trigger_kind;
    uint16_t          trigger_scope_id;
    uint8_t           action_count;
    fac_action_t      actions[8];
} fac_rule_t;

typedef enum {
    FAC_RULE_IDLE = 0,
    FAC_RULE_DELAYING,
    FAC_RULE_EXECUTING,
    FAC_RULE_DONE,
    FAC_RULE_FAULT,
    FAC_RULE_MANUAL_STOPPED,
} fac_rule_state_t;

// Lifecycle.
int fac_interlock_init(void);
int fac_interlock_load_rules(const fac_rule_t* rules, uint16_t count);

// Wiring.
void fac_interlock_on_alarm(const fac_alarm_event_t* alarm);
void fac_interlock_on_field_signal(fac_trigger_kind_t kind,
                                   uint8_t loop_id,
                                   uint8_t device_addr);

// Manual override — requires both a password-authenticated caller AND
// the physical key switch armed at the panel. Callers must verify both
// before calling these functions; the engine assumes that gate is closed
// upstream.
int fac_interlock_manual_start(uint8_t loop_id, uint8_t device_addr);
int fac_interlock_manual_stop(uint8_t loop_id, uint8_t device_addr);

// Rule-state inspection.
fac_rule_state_t fac_interlock_rule_state(uint16_t rule_id);

// Reset (only allowed when all triggering alarms have been cleared).
int fac_interlock_reset_rule(uint16_t rule_id);

#endif // FAC_INTERLOCK_H
