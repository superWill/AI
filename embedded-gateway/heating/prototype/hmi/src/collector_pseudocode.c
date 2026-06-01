/*
 * Device display MVP pseudocode.
 *
 * Goal:
 * Collect device information and refresh embedded HMI.
 */

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    float value;
    bool valid;
    uint32_t updated_at_ms;
} point_value_t;

typedef struct {
    point_value_t primary_supply_temp;
    point_value_t primary_return_temp;
    point_value_t primary_supply_pressure;
    point_value_t primary_flow;
    point_value_t primary_valve_open;

    point_value_t secondary_supply_temp;
    point_value_t secondary_return_temp;
    point_value_t secondary_supply_pressure;
    point_value_t secondary_return_pressure;
    point_value_t secondary_flow;

    bool circulation_pump_run;
    bool circulation_pump_fault;
    point_value_t circulation_pump_frequency;
    point_value_t circulation_pump_current;

    bool refill_pump_run;
    bool refill_pump_fault;
    bool mqtt_online;
} station_snapshot_t;

static station_snapshot_t g_snapshot;

static point_value_t read_ai_point(int channel);
static bool read_di_point(int channel);
static void validate_snapshot(station_snapshot_t *snapshot);
static void hmi_update(const station_snapshot_t *snapshot);
static void mqtt_upload_telemetry(const station_snapshot_t *snapshot);

void main_loop_1s(void)
{
    g_snapshot.primary_supply_temp = read_ai_point(0);
    g_snapshot.primary_return_temp = read_ai_point(1);
    g_snapshot.primary_supply_pressure = read_ai_point(2);
    g_snapshot.primary_flow = read_ai_point(3);
    g_snapshot.primary_valve_open = read_ai_point(4);

    g_snapshot.secondary_supply_temp = read_ai_point(5);
    g_snapshot.secondary_return_temp = read_ai_point(6);
    g_snapshot.secondary_supply_pressure = read_ai_point(7);
    g_snapshot.secondary_return_pressure = read_ai_point(8);
    g_snapshot.secondary_flow = read_ai_point(9);

    g_snapshot.circulation_pump_run = read_di_point(0);
    g_snapshot.circulation_pump_fault = read_di_point(1);
    g_snapshot.circulation_pump_frequency = read_ai_point(10);
    g_snapshot.circulation_pump_current = read_ai_point(11);

    g_snapshot.refill_pump_run = read_di_point(2);
    g_snapshot.refill_pump_fault = read_di_point(3);

    validate_snapshot(&g_snapshot);
    hmi_update(&g_snapshot);
}

void communication_loop_5s(void)
{
    if (g_snapshot.mqtt_online) {
        mqtt_upload_telemetry(&g_snapshot);
    }
}

