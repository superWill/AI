// fac_alarm.h — alarm decision engine
//
// 单点报警立即触发；同一防火分区内"两点报警"交叉确认后触发联动允许。
// 手动报警按钮 / 消火栓按钮立即触发，不走交叉确认（GB 50116 § 4.1）。

#ifndef FAC_ALARM_H
#define FAC_ALARM_H

#include <stdbool.h>
#include <stdint.h>

#include "fac_point.h"

typedef enum {
    FAC_ALARM_KIND_SINGLE        = 0,  // 单点报警（探测器或模块）
    FAC_ALARM_KIND_MANUAL_CALL,        // 手动报警按钮
    FAC_ALARM_KIND_HYDRANT_BTN,        // 消火栓按钮
    FAC_ALARM_KIND_CROSS_CONFIRMED,    // 同区域两点交叉确认
} fac_alarm_kind_t;

typedef struct {
    uint32_t          event_id;
    uint32_t          timestamp;
    fac_alarm_kind_t  kind;
    uint16_t          zone_id;
    uint8_t           loop_id;
    uint8_t           device_addr;
    fac_dev_type_t    device_type;
    uint16_t          analog_value;    // raw sensor reading at trigger
} fac_alarm_event_t;

// Configuration.
typedef struct {
    uint8_t  cross_zone_confirm_count;   // default 2 (GB 50116)
    uint32_t cross_zone_window_ms;       // default 30 000
    uint32_t fault_recover_stable_ms;    // default 60 000
} fac_alarm_config_t;

int fac_alarm_init(const fac_alarm_config_t* cfg);

// Called by fac_loop on every event it receives from the loop bus.
void fac_alarm_on_loop_event(const fac_loop_event_t* event);

// Reset semantics:
// - clears alarms for the given scope only after all triggering points
//   have returned to NORMAL on the loop. If any source is still alarming
//   the reset is silently rejected. Caller must observe the next event
//   stream to confirm.
typedef enum {
    FAC_RESET_SYSTEM = 0,
    FAC_RESET_LOOP,
    FAC_RESET_ZONE,
    FAC_RESET_DEVICE,
} fac_reset_scope_t;

int fac_alarm_reset(fac_reset_scope_t scope, uint16_t scope_id);

// Subscribe — fires on every confirmed alarm event.
typedef void (*fac_alarm_event_cb_t)(const fac_alarm_event_t* event, void* user);
int fac_alarm_subscribe(fac_alarm_event_cb_t cb, void* user);

#endif // FAC_ALARM_H
