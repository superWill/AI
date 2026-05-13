#include "tec_mvp.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LOOP_COUNT 36

static const char *state_name(tec_state_t state)
{
    switch (state) {
    case TEC_STATE_POWER_ON:
        return "POWER_ON";
    case TEC_STATE_SELF_CHECK:
        return "SELF_CHECK";
    case TEC_STATE_STANDBY:
        return "STANDBY";
    case TEC_STATE_STARTING:
        return "STARTING";
    case TEC_STATE_RUNNING:
        return "RUNNING";
    case TEC_STATE_ALARM:
        return "ALARM";
    case TEC_STATE_EMERGENCY_STOP:
        return "EMERGENCY_STOP";
    default:
        return "UNKNOWN";
    }
}

static tec_scenario_t parse_scenario(const char *arg)
{
    if (arg == NULL || strcmp(arg, "normal") == 0) {
        return TEC_SCENARIO_NORMAL;
    }
    if (strcmp(arg, "low_pressure") == 0) {
        return TEC_SCENARIO_LOW_PRESSURE;
    }
    if (strcmp(arg, "over_temp") == 0) {
        return TEC_SCENARIO_OVER_TEMP;
    }
    if (strcmp(arg, "mqtt_offline") == 0) {
        return TEC_SCENARIO_MQTT_OFFLINE;
    }
    if (strcmp(arg, "sensor_fault") == 0) {
        return TEC_SCENARIO_SENSOR_FAULT;
    }

    return TEC_SCENARIO_NORMAL;
}

static void controller_init(tec_controller_t *ctl)
{
    ctl->state = TEC_STATE_POWER_ON;
    ctl->input.outdoor_temp_c = -2.0;
    ctl->input.primary_supply_temp_c = 75.0;
    ctl->input.secondary_supply_temp_c = 35.0;
    ctl->input.secondary_return_temp_c = 30.0;
    ctl->input.secondary_supply_pressure_mpa = 0.30;
    ctl->input.secondary_return_pressure_mpa = 0.22;
    ctl->input.secondary_supply_temp_sensor_ok = true;
    ctl->input.pressure_sensor_ok = true;
    ctl->input.mqtt_online = true;

    ctl->output.primary_valve_percent = 18.0;
    ctl->output.circulation_pump_freq_hz = 30.0;
    ctl->output.circulation_pump_run = false;
    ctl->output.refill_pump_run = false;
    ctl->output.alarm_output = false;

    ctl->target_supply_temp_c = 45.0;
    ctl->target_diff_pressure_mpa = 0.08;
    ctl->last_alarm = "none";
}

static void apply_scenario(tec_controller_t *ctl, tec_scenario_t scenario, int tick)
{
    if (scenario == TEC_SCENARIO_LOW_PRESSURE && tick >= 14) {
        ctl->input.secondary_return_pressure_mpa = 0.10;
        ctl->input.secondary_supply_pressure_mpa = 0.16;
    }

    if (scenario == TEC_SCENARIO_OVER_TEMP && tick >= 18) {
        ctl->input.secondary_supply_temp_c = 68.0;
    }

    if (scenario == TEC_SCENARIO_MQTT_OFFLINE && tick >= 10) {
        ctl->input.mqtt_online = false;
    }

    if (scenario == TEC_SCENARIO_SENSOR_FAULT && tick >= 12) {
        ctl->input.secondary_supply_temp_sensor_ok = false;
    }
}

static void simulate_physics(tec_controller_t *ctl)
{
    if (!ctl->output.circulation_pump_run) {
        return;
    }

    if (ctl->output.primary_valve_percent > 0.0) {
        double heat_gain = ctl->output.primary_valve_percent * 0.004;
        ctl->input.secondary_supply_temp_c += heat_gain;
    }

    if (ctl->input.secondary_supply_temp_c > ctl->target_supply_temp_c) {
        ctl->input.secondary_supply_temp_c -= 0.08;
    }

    if (ctl->output.refill_pump_run) {
        ctl->input.secondary_return_pressure_mpa += 0.015;
        ctl->input.secondary_supply_pressure_mpa += 0.015;
    }
}

static void transition_state(tec_controller_t *ctl, int tick)
{
    switch (ctl->state) {
    case TEC_STATE_POWER_ON:
        ctl->state = TEC_STATE_SELF_CHECK;
        break;
    case TEC_STATE_SELF_CHECK:
        ctl->state = TEC_STATE_STANDBY;
        break;
    case TEC_STATE_STANDBY:
        if (tick >= 3) {
            ctl->state = TEC_STATE_STARTING;
        }
        break;
    case TEC_STATE_STARTING:
        ctl->output.circulation_pump_run = true;
        ctl->output.circulation_pump_freq_hz = 28.0;
        ctl->output.primary_valve_percent = 10.0;
        ctl->state = TEC_STATE_RUNNING;
        break;
    case TEC_STATE_RUNNING:
    case TEC_STATE_ALARM:
    case TEC_STATE_EMERGENCY_STOP:
        break;
    }
}

static bool run_safety(tec_controller_t *ctl)
{
    ctl->output.alarm_output = false;
    ctl->last_alarm = "none";

    if (!ctl->input.secondary_supply_temp_sensor_ok || !ctl->input.pressure_sensor_ok) {
        ctl->state = TEC_STATE_EMERGENCY_STOP;
        ctl->output.primary_valve_percent = 0.0;
        ctl->output.circulation_pump_run = false;
        ctl->output.refill_pump_run = false;
        ctl->output.alarm_output = true;
        ctl->last_alarm = "critical_sensor_fault";
        return true;
    }

    if (ctl->input.secondary_supply_temp_c >= 65.0) {
        ctl->state = TEC_STATE_EMERGENCY_STOP;
        ctl->output.primary_valve_percent = 0.0;
        ctl->output.circulation_pump_run = true;
        ctl->output.refill_pump_run = false;
        ctl->output.alarm_output = true;
        ctl->last_alarm = "secondary_supply_over_temperature";
        return true;
    }

    if (ctl->input.secondary_supply_pressure_mpa >= 0.60) {
        ctl->state = TEC_STATE_EMERGENCY_STOP;
        ctl->output.primary_valve_percent = 0.0;
        ctl->output.circulation_pump_freq_hz = 20.0;
        ctl->output.refill_pump_run = false;
        ctl->output.alarm_output = true;
        ctl->last_alarm = "secondary_high_pressure";
        return true;
    }

    if (ctl->input.secondary_return_pressure_mpa <= 0.12) {
        ctl->state = TEC_STATE_ALARM;
        ctl->output.refill_pump_run = true;
        ctl->output.alarm_output = true;
        ctl->last_alarm = "secondary_low_pressure_refilling";
        return false;
    }

    return false;
}

static void run_control(tec_controller_t *ctl)
{
    if (ctl->state != TEC_STATE_RUNNING && ctl->state != TEC_STATE_ALARM) {
        return;
    }

    double temp_error = ctl->target_supply_temp_c - ctl->input.secondary_supply_temp_c;
    if (temp_error > 1.0) {
        ctl->output.primary_valve_percent += 2.0;
    } else if (temp_error < -1.0) {
        ctl->output.primary_valve_percent -= 2.0;
    }

    if (ctl->output.primary_valve_percent < 0.0) {
        ctl->output.primary_valve_percent = 0.0;
    }
    if (ctl->output.primary_valve_percent > 100.0) {
        ctl->output.primary_valve_percent = 100.0;
    }

    double diff_pressure = ctl->input.secondary_supply_pressure_mpa - ctl->input.secondary_return_pressure_mpa;
    double pressure_error = ctl->target_diff_pressure_mpa - diff_pressure;
    if (pressure_error > 0.01) {
        ctl->output.circulation_pump_freq_hz += 1.0;
    } else if (pressure_error < -0.01) {
        ctl->output.circulation_pump_freq_hz -= 1.0;
    }

    if (ctl->output.circulation_pump_freq_hz < 20.0) {
        ctl->output.circulation_pump_freq_hz = 20.0;
    }
    if (ctl->output.circulation_pump_freq_hz > 50.0) {
        ctl->output.circulation_pump_freq_hz = 50.0;
    }

    if (ctl->input.secondary_return_pressure_mpa >= 0.25) {
        ctl->output.refill_pump_run = false;
    }
}

static void mqtt_publish(const tec_controller_t *ctl, int tick)
{
    if (!ctl->input.mqtt_online) {
        printf("[mqtt] offline, local autonomous control active, telemetry cached\n");
        return;
    }

    printf("[mqtt] telemetry t=%02d state=%s sec_temp=%.1f valve=%.0f%% pump=%.0fHz refill=%s alarm=%s\n",
           tick,
           state_name(ctl->state),
           ctl->input.secondary_supply_temp_c,
           ctl->output.primary_valve_percent,
           ctl->output.circulation_pump_freq_hz,
           ctl->output.refill_pump_run ? "on" : "off",
           ctl->last_alarm);
}

static void print_snapshot(const tec_controller_t *ctl, int tick)
{
    double diff_pressure = ctl->input.secondary_supply_pressure_mpa - ctl->input.secondary_return_pressure_mpa;
    printf("t=%02d state=%-15s temp=%.1f/%.1fC diffP=%.3fMPa valve=%5.1f%% pump=%4.1fHz refill=%s alarm=%s\n",
           tick,
           state_name(ctl->state),
           ctl->input.secondary_supply_temp_c,
           ctl->target_supply_temp_c,
           diff_pressure,
           ctl->output.primary_valve_percent,
           ctl->output.circulation_pump_freq_hz,
           ctl->output.refill_pump_run ? "on " : "off",
           ctl->last_alarm);
}

int main(int argc, char **argv)
{
    tec_scenario_t scenario = parse_scenario(argc > 1 ? argv[1] : NULL);
    tec_controller_t ctl;
    controller_init(&ctl);

    printf("Thermal Energy Co-controller MVP Simulator\n");
    printf("Scenario: %s\n\n", argc > 1 ? argv[1] : "normal");

    for (int tick = 0; tick < LOOP_COUNT; tick++) {
        apply_scenario(&ctl, scenario, tick);
        transition_state(&ctl, tick);

        bool emergency = run_safety(&ctl);
        if (!emergency) {
            run_control(&ctl);
        }

        simulate_physics(&ctl);
        print_snapshot(&ctl, tick);

        if (tick % 5 == 0) {
            mqtt_publish(&ctl, tick);
        }
    }

    return EXIT_SUCCESS;
}
