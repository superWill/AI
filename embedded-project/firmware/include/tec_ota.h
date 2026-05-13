#ifndef TEC_OTA_H
#define TEC_OTA_H

#include <stdbool.h>

typedef enum {
    TEC_OTA_IDLE = 0,
    TEC_OTA_CHECKING,
    TEC_OTA_DOWNLOADING,
    TEC_OTA_VERIFYING,
    TEC_OTA_READY_TO_SWITCH,
    TEC_OTA_FAILED
} tec_ota_state_t;

void tec_ota_init(void);
void tec_ota_tick(void);
tec_ota_state_t tec_ota_get_state(void);
bool tec_ota_request_upgrade(const char *version, const char *url, const char *signature);

#endif

