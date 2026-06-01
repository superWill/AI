// fac_panel.h — local HMI (LCD + keypad + LED matrix + printer + audio)
//
// 大尺寸 LCD + 数字键盘 + 状态指示灯阵列 + 内置打印机 + 接警话筒。
// 三级权限（操作员 / 操作员授权 / 维护级）逐级密码。
//
// 钥匙开关由本模块感知，但权限验证只在调用方一侧使用（fac_interlock
// 不直接读 keypad，避免循环依赖）。

#ifndef FAC_PANEL_H
#define FAC_PANEL_H

#include <stdbool.h>
#include <stdint.h>

#include "fac_alarm.h"

typedef enum {
    FAC_LED_FIRE_ALARM = 0,
    FAC_LED_ACTION,
    FAC_LED_FEEDBACK,
    FAC_LED_SHIELD,
    FAC_LED_FAULT,
    FAC_LED_START_ALLOWED,
    FAC_LED_SUPERVISORY,
    FAC_LED_DELAY,
    FAC_LED_MANUAL_ALLOWED,
    FAC_LED_MAINS_POWER,
    FAC_LED_BATTERY_POWER,
    FAC_LED_BATTERY_FAULT,
    FAC_LED_COUNT,
} fac_led_t;

typedef enum {
    FAC_LED_OFF = 0,
    FAC_LED_ON,
    FAC_LED_BLINK_SLOW,    // 0.5 Hz
    FAC_LED_BLINK_FAST,    // 1 Hz
} fac_led_mode_t;

typedef enum {
    FAC_LEVEL_OPERATOR = 1,    // 默认级；查看 + 消音 + 自检
    FAC_LEVEL_AUTHORIZED,      // 操作员授权级；复位 + 手动启停（密码 + 钥匙开关）
    FAC_LEVEL_MAINTENANCE,     // 维护级；参数 + 屏蔽 + 固件升级（密码 + 钥匙开关）
} fac_access_level_t;

typedef enum {
    FAC_PAGE_HOME = 0,         // 系统状态汇总
    FAC_PAGE_EVENT_LIST,       // 事件历史
    FAC_PAGE_DEVICE_DETAIL,
    FAC_PAGE_RULE_LIST,
    FAC_PAGE_SHIELDED_LIST,
    FAC_PAGE_FAULT_LIST,
    FAC_PAGE_SETTINGS,
    FAC_PAGE_SELF_TEST,
} fac_page_t;

// Lifecycle.
int fac_panel_init(void);

// LCD pages.
int fac_panel_set_page(fac_page_t page);
int fac_panel_refresh(void);            // request redraw

// LED matrix.
int fac_panel_set_led(fac_led_t led, fac_led_mode_t mode);

// Audio.
int fac_panel_buzz_alarm(void);         // 1 Hz tone until silenced
int fac_panel_buzz_fault(void);         // 0.5 Hz tone
int fac_panel_buzz_supervisory(void);
int fac_panel_silence(void);            // 消音

// Printer queue. Returns -1 if queue is full; events 不丢，会写入 flash 待重打。
int fac_panel_print_alarm(const fac_alarm_event_t* event);
int fac_panel_print_text(const char* text);

// Key switch + auth.
bool fac_panel_key_switch_armed(void);
fac_access_level_t fac_panel_current_level(void);
int  fac_panel_authenticate(fac_access_level_t target, const char* password);
int  fac_panel_logout(void);

// Keypad event hook (UI layer subscribes; engines do NOT).
typedef enum {
    FAC_KEY_DIGIT_0 = 0, FAC_KEY_DIGIT_1, FAC_KEY_DIGIT_2, FAC_KEY_DIGIT_3,
    FAC_KEY_DIGIT_4,     FAC_KEY_DIGIT_5, FAC_KEY_DIGIT_6, FAC_KEY_DIGIT_7,
    FAC_KEY_DIGIT_8,     FAC_KEY_DIGIT_9,
    FAC_KEY_ENTER, FAC_KEY_CANCEL, FAC_KEY_UP, FAC_KEY_DOWN,
    FAC_KEY_RESET, FAC_KEY_SILENCE, FAC_KEY_SELF_TEST, FAC_KEY_MANUAL_TOGGLE,
} fac_key_t;

typedef void (*fac_panel_key_cb_t)(fac_key_t key, void* user);
int fac_panel_subscribe_keys(fac_panel_key_cb_t cb, void* user);

#endif // FAC_PANEL_H
