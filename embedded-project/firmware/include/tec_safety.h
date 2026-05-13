#ifndef TEC_SAFETY_H
#define TEC_SAFETY_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    TEC_SAFETY_LEVEL_NORMAL = 0,
    TEC_SAFETY_LEVEL_WARNING,
    TEC_SAFETY_LEVEL_ALARM,
    TEC_SAFETY_LEVEL_EMERGENCY
} tec_safety_level_t;

typedef struct {
    tec_safety_level_t level;
    const char *rule_id;
    const char *message;
    uint32_t timestamp_ms;
} tec_safety_event_t;

void tec_safety_init(void);
void tec_safety_tick(void);
tec_safety_level_t tec_safety_get_level(void);
bool tec_safety_has_emergency(void);
bool tec_safety_get_last_event(tec_safety_event_t *out_event);

#endif

