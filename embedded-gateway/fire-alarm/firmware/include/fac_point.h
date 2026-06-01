// fac_point.h — runtime point-table data model
//
// 三层数据模型：Device → Zone → Group。所有运行时报警/动作/故障状态
// 都以这三层为索引。其他模块只读访问；写入只允许 fac_loop（来自回路
// 的状态上报）与 fac_alarm（确认报警后更新 zone 状态）。
//
// 详见 docs/point-table/initial-point-table.md。

#ifndef FAC_POINT_H
#define FAC_POINT_H

#include <stdbool.h>
#include <stdint.h>

#define FAC_MAX_LOOPS              8
#define FAC_MAX_DEVICES_PER_LOOP   200
#define FAC_MAX_ZONES              64
#define FAC_MAX_GROUPS             32

typedef enum {
    FAC_DEV_SMOKE_PHOTO = 0x01,
    FAC_DEV_SMOKE_ION   = 0x02,
    FAC_DEV_HEAT_DIFF   = 0x10,
    FAC_DEV_HEAT_FIX    = 0x11,
    FAC_DEV_HEAT_COMBO  = 0x12,
    FAC_DEV_FLAME_IR    = 0x20,
    FAC_DEV_GAS_CO      = 0x30,
    FAC_DEV_GAS_FLAM    = 0x31,
    FAC_DEV_MANUAL_CALL = 0x40,
    FAC_DEV_HYDRANT_BTN = 0x41,
    FAC_DEV_MOD_INPUT   = 0x50,
    FAC_DEV_MOD_OUTPUT  = 0x51,
    FAC_DEV_MOD_IO      = 0x52,
    FAC_DEV_SOUNDER     = 0x60,
    FAC_DEV_BROADCAST   = 0x61,
    FAC_DEV_PHONE       = 0x62,
} fac_dev_type_t;

typedef enum {
    FAC_STATE_NORMAL = 0,
    FAC_STATE_ALARM,
    FAC_STATE_ACTION,
    FAC_STATE_FEEDBACK,
    FAC_STATE_FAULT,
    FAC_STATE_SHIELDED,
    FAC_STATE_UNREGISTERED,
} fac_dev_state_t;

typedef enum {
    FAC_FAULT_OPEN     = 1 << 0,
    FAC_FAULT_SHORT    = 1 << 1,
    FAC_FAULT_TIMEOUT  = 1 << 2,
    FAC_FAULT_INVALID  = 1 << 3,
} fac_fault_flag_t;

typedef struct {
    uint8_t          loop_id;
    uint8_t          addr;
    fac_dev_type_t   type;
    uint8_t          subtype_code;
    fac_dev_state_t  state;
    uint16_t         value;            // 模拟量（烟雾浓度、温度等）
    uint16_t         threshold_alarm;  // 报警阈值
    uint32_t         last_seen_tick;
    uint8_t          fault_flags;
    bool             shielded;
    uint16_t         zone_id;
} fac_device_t;

typedef struct {
    uint16_t zone_id;
    uint16_t device_count;
    uint16_t alarm_count;
    uint32_t first_alarm_at;
    bool     confirmed;
    uint8_t  cross_confirm_threshold;
} fac_zone_t;

typedef enum {
    FAC_GROUP_TRIG_ANY    = 0,
    FAC_GROUP_TRIG_ALL    = 1,
    FAC_GROUP_TRIG_N_OF_M = 2,
} fac_group_logic_t;

typedef struct {
    uint16_t          group_id;
    uint8_t           zone_count;
    uint16_t          zones[16];
    fac_group_logic_t trigger_logic;
    uint8_t           n_threshold;    // for N_OF_M
} fac_group_t;

// Lookup. NULL when index/id is unknown.
const fac_device_t* fac_point_device(uint8_t loop_id, uint8_t addr);
const fac_zone_t*   fac_point_zone(uint16_t zone_id);
const fac_group_t*  fac_point_group(uint16_t group_id);

// Aggregate query.
uint16_t fac_point_zone_alarm_count(uint16_t zone_id);
bool     fac_point_zone_confirmed(uint16_t zone_id);

// Persistence.
int  fac_point_load_from_flash(void);
int  fac_point_save_to_flash(void);

#endif // FAC_POINT_H
