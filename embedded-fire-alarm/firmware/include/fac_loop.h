// fac_loop.h — two-wire loop-bus master driver
//
// 每条回路一个 fac_loop 实例。主控 MCU 用 UART + 电流环驱动 + 短路保护
// 电路实现物理层；本接口仅暴露应用层。
//
// 详见 docs/protocols/loop-bus-draft.md。

#ifndef FAC_LOOP_H
#define FAC_LOOP_H

#include <stdbool.h>
#include <stdint.h>

#define FAC_LOOP_MAX_DATA  32

typedef enum {
    FAC_CMD_POLL          = 0x01,
    FAC_CMD_READ_STATE    = 0x02,
    FAC_CMD_READ_ANALOG   = 0x03,
    FAC_CMD_SET_THRESHOLD = 0x04,
    FAC_CMD_RESET         = 0x05,
    FAC_CMD_SHIELD        = 0x06,
    FAC_CMD_UNSHIELD      = 0x07,
    FAC_CMD_OUTPUT_ON     = 0x08,
    FAC_CMD_OUTPUT_OFF    = 0x09,
    FAC_CMD_SELF_TEST     = 0x0A,
    FAC_CMD_READ_FAULT    = 0x0B,
} fac_loop_cmd_t;

typedef enum {
    FAC_ACK_NORMAL   = 0x81,
    FAC_ACK_ALARM    = 0x82,
    FAC_ACK_FAULT    = 0x83,
    FAC_ACK_ACTION   = 0x84,
    FAC_ACK_FEEDBACK = 0x85,
    FAC_ACK_DATA     = 0x86,
    FAC_NACK         = 0xFE,
} fac_loop_ack_t;

typedef enum {
    FAC_LOOP_HEALTH_OK         = 0,
    FAC_LOOP_HEALTH_SHORT,
    FAC_LOOP_HEALTH_OPEN,
    FAC_LOOP_HEALTH_DEGRADED,  // CRC errors above threshold
    FAC_LOOP_HEALTH_OFF,
} fac_loop_health_t;

typedef struct {
    uint8_t        loop_id;
    uint8_t        dst_addr;
    fac_loop_ack_t ack;
    uint8_t        data_len;
    uint8_t        data[FAC_LOOP_MAX_DATA];
} fac_loop_event_t;

// Lifecycle.
int  fac_loop_init(uint8_t loop_id);
int  fac_loop_start(uint8_t loop_id);   // begin polling
int  fac_loop_stop(uint8_t loop_id);

// Health.
fac_loop_health_t fac_loop_health(uint8_t loop_id);

// One-shot command, blocking until response or timeout.
// `timeout_ms` is bounded by polling deadlines; callers must not exceed 200 ms.
int fac_loop_request(uint8_t        loop_id,
                     uint8_t        dst_addr,
                     fac_loop_cmd_t cmd,
                     const uint8_t* data,
                     uint8_t        data_len,
                     uint32_t       timeout_ms,
                     fac_loop_event_t* out_response);

// Subscribe to asynchronous events (alarm / fault / feedback from polling).
typedef void (*fac_loop_event_cb_t)(const fac_loop_event_t* event, void* user);
int fac_loop_subscribe(fac_loop_event_cb_t cb, void* user);

#endif // FAC_LOOP_H
