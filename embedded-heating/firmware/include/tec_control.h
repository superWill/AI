#ifndef TEC_CONTROL_H
#define TEC_CONTROL_H

#include <stdbool.h>

typedef struct {
    double primary_valve_percent;
    double circulation_pump_freq_hz;
    bool circulation_pump_run;
    bool refill_pump_run;
} tec_control_output_t;

void tec_control_init(void);
void tec_control_tick(void);
bool tec_control_get_output(tec_control_output_t *out_control);

#endif

