#ifndef TEC_MQTT_H
#define TEC_MQTT_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    TEC_MQTT_DISCONNECTED = 0,
    TEC_MQTT_CONNECTING,
    TEC_MQTT_CONNECTED
} tec_mqtt_status_t;

void tec_mqtt_init(void);
void tec_mqtt_tick(void);
tec_mqtt_status_t tec_mqtt_get_status(void);
bool tec_mqtt_publish_telemetry(void);
bool tec_mqtt_publish_alarm(const char *alarm_id, const char *message);
bool tec_mqtt_process_command(const char *payload, uint32_t length);

#endif

