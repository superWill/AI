#ifndef TEC_MVP_H
#define TEC_MVP_H

#include <stdbool.h>

typedef enum {
    TEC_STATE_POWER_ON = 0,
    TEC_STATE_SELF_CHECK,
    TEC_STATE_STANDBY,
    TEC_STATE_STARTING,
    TEC_STATE_RUNNING,
    TEC_STATE_ALARM,
    TEC_STATE_EMERGENCY_STOP
} tec_state_t;

typedef enum {
    TEC_SCENARIO_NORMAL = 0,
    TEC_SCENARIO_LOW_PRESSURE,
    TEC_SCENARIO_OVER_TEMP,
    TEC_SCENARIO_MQTT_OFFLINE,
    TEC_SCENARIO_SENSOR_FAULT
} tec_scenario_t;

typedef struct {
    double outdoor_temp_c;
    double primary_supply_temp_c;
    double secondary_supply_temp_c;
    double secondary_return_temp_c;
    double secondary_supply_pressure_mpa;
    double secondary_return_pressure_mpa;
    bool secondary_supply_temp_sensor_ok;
    bool pressure_sensor_ok;
    bool mqtt_online;
} tec_inputs_t;

typedef struct {
    double primary_valve_percent;
    double circulation_pump_freq_hz;
    bool circulation_pump_run;
    bool refill_pump_run;
    bool alarm_output;
} tec_outputs_t;

typedef struct {
    tec_state_t state;
    tec_inputs_t input;
    tec_outputs_t output;
    double target_supply_temp_c;
    double target_diff_pressure_mpa;
    const char *last_alarm;
} tec_controller_t;

#endif

