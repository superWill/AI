#ifndef TEC_POINT_H
#define TEC_POINT_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    TEC_POINT_QUALITY_GOOD = 0,
    TEC_POINT_QUALITY_SUSPECT,
    TEC_POINT_QUALITY_FAULT,
    TEC_POINT_QUALITY_OFFLINE
} tec_point_quality_t;

typedef enum {
    TEC_POINT_TYPE_BOOL = 0,
    TEC_POINT_TYPE_INT,
    TEC_POINT_TYPE_FLOAT,
    TEC_POINT_TYPE_ENUM
} tec_point_type_t;

typedef struct {
    const char *id;
    const char *name;
    const char *unit;
    tec_point_type_t type;
    tec_point_quality_t quality;
    double value;
    uint32_t updated_at_ms;
} tec_point_t;

bool tec_point_get(const char *id, tec_point_t *out_point);
bool tec_point_set_value(const char *id, double value, uint32_t timestamp_ms);
bool tec_point_set_quality(const char *id, tec_point_quality_t quality);

#endif

