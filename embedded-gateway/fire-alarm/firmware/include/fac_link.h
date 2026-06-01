// fac_link.h — upstream link to graphics-workstation (CRT)
//
// GB 16806 第 4.10 节规定的接口（RS-485 / RS-232 / Ethernet）。本接口
// 上行 6 类事件（火警 / 动作 / 反馈 / 故障 / 屏蔽 / 监管 + 心跳），下行
// 查询、复位、手动启动、广播触发。
//
// 详见 docs/protocols/crt-link-draft.md。

#ifndef FAC_LINK_H
#define FAC_LINK_H

#include <stdbool.h>
#include <stdint.h>

#include "fac_alarm.h"
#include "fac_interlock.h"

typedef enum {
    FAC_LINK_DOWN = 0,
    FAC_LINK_UP,
    FAC_LINK_DEGRADED,
} fac_link_state_t;

typedef enum {
    FAC_TX_ALARM = 0x10,
    FAC_TX_ACTION,
    FAC_TX_FEEDBACK,
    FAC_TX_FAULT,
    FAC_TX_SHIELD,
    FAC_TX_SUPERVISORY,
    FAC_TX_RESET,
    FAC_TX_POWER,
} fac_tx_kind_t;

// Lifecycle.
int fac_link_init(void);
int fac_link_start(void);
fac_link_state_t fac_link_state(void);

// Upstream — append to retransmission window. Reliable (ACKed within 5 s,
// 3 retries, then queued to flash for replay).
int fac_link_send_alarm(const fac_alarm_event_t* event);
int fac_link_send_action(uint16_t rule_id, fac_action_kind_t action, uint8_t loop, uint8_t addr);
int fac_link_send_feedback(uint8_t loop_id, uint8_t addr, uint8_t feedback_type);
int fac_link_send_fault(uint8_t loop_id, uint8_t addr, uint8_t fault_flags);
int fac_link_send_shield(uint8_t loop_id, uint8_t addr, bool shielded, uint8_t by_user);
int fac_link_send_supervisory(uint8_t loop_id, uint8_t addr, uint8_t supervisory_type);
int fac_link_send_power_event(uint8_t event_type);

// Downstream — handler hooks. Implementations of these enforce authentication
// (HMAC + optional key-switch gating) before forwarding to fac_interlock /
// fac_alarm. Returning non-zero from a handler causes the engine to NACK the
// downstream frame.
typedef int (*fac_link_handler_reset_t)(fac_reset_scope_t scope, uint16_t scope_id, const uint8_t hmac[32]);
typedef int (*fac_link_handler_manual_t)(uint8_t loop_id, uint8_t addr, bool start, const uint8_t hmac[32]);
typedef int (*fac_link_handler_shield_t)(uint8_t loop_id, uint8_t addr, bool shielded, const uint8_t hmac[32]);
typedef int (*fac_link_handler_param_t)(uint16_t param_id, const uint8_t* value, uint16_t value_len, const uint8_t hmac[32]);

typedef struct {
    fac_link_handler_reset_t  on_reset;
    fac_link_handler_manual_t on_manual;
    fac_link_handler_shield_t on_shield;
    fac_link_handler_param_t  on_set_param;
} fac_link_handlers_t;

int fac_link_register_handlers(const fac_link_handlers_t* handlers);

#endif // FAC_LINK_H
