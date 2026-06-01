#ifndef TEC_STATE_MACHINE_H
#define TEC_STATE_MACHINE_H

#include <stdbool.h>

typedef enum {
    TEC_STATE_POWER_ON = 0,
    TEC_STATE_SELF_CHECK,
    TEC_STATE_STANDBY,
    TEC_STATE_STARTING,
    TEC_STATE_RUNNING,
    TEC_STATE_ADJUSTING,
    TEC_STATE_ALARM,
    TEC_STATE_EMERGENCY_STOP,
    TEC_STATE_MAINTENANCE,
    TEC_STATE_OTA_UPDATING
} tec_state_t;

typedef enum {
    TEC_MODE_AUTO = 0,
    TEC_MODE_MANUAL,
    TEC_MODE_LOCAL,
    TEC_MODE_REMOTE,
    TEC_MODE_MAINTENANCE
} tec_mode_t;

void tec_state_machine_init(void);
void tec_state_machine_tick(void);
tec_state_t tec_state_machine_get_state(void);
bool tec_state_machine_request_mode(tec_mode_t mode);
bool tec_state_machine_is_action_allowed(const char *action_id);

#endif

