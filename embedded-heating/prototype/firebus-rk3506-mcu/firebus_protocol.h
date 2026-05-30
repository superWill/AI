#ifndef FIREBUS_PROTOCOL_H
#define FIREBUS_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define FB_MAGIC0 0xAAu
#define FB_MAGIC1 0x55u
#define FB_VERSION 0x01u
#define FB_HEADER_SIZE 10u
#define FB_CRC_SIZE 2u
#define FB_MAX_PAYLOAD 128u
#define FB_MAX_FRAME (FB_HEADER_SIZE + FB_MAX_PAYLOAD + FB_CRC_SIZE)

typedef enum {
    FB_CMD_HEARTBEAT = 0x01,
    FB_CMD_EVENT_REPORT = 0x10,
    FB_CMD_STATUS_SNAPSHOT = 0x11,
    FB_CMD_BUS_FAULT = 0x12,
    FB_CMD_ACK = 0x80,
    FB_CMD_GET_SNAPSHOT = 0x81,
    FB_CMD_RESET_LOOP = 0x82,
    FB_CMD_SET_CONFIG = 0x83
} fb_cmd_t;

typedef enum {
    FB_EVENT_ALARM = 1,
    FB_EVENT_FAULT = 2,
    FB_EVENT_RESTORE = 3,
    FB_EVENT_FEEDBACK = 4,
    FB_EVENT_OFFLINE = 5
} fb_event_type_t;

typedef enum {
    FB_DEVICE_SMOKE = 1,
    FB_DEVICE_HEAT = 2,
    FB_DEVICE_MANUAL_CALL = 3,
    FB_DEVICE_IO_MODULE = 4
} fb_device_type_t;

typedef struct {
    uint16_t address;
    uint8_t device_type;
    uint8_t event_type;
    uint16_t flags;
    uint32_t bus_time_ms;
} fb_event_payload_t;

typedef struct {
    uint16_t poll_start;
    uint16_t poll_end;
    uint16_t pending_events;
    uint8_t bus_state;
    uint8_t rk_online;
} fb_heartbeat_payload_t;

static inline uint16_t fb_crc16_ccitt(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFFu;

    for (size_t i = 0; i < len; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (uint8_t bit = 0; bit < 8; ++bit) {
            if ((crc & 0x8000u) != 0u) {
                crc = (uint16_t)((crc << 1) ^ 0x1021u);
            } else {
                crc = (uint16_t)(crc << 1);
            }
        }
    }

    return crc;
}

static inline void fb_put_u16_le(uint8_t *dst, uint16_t value)
{
    dst[0] = (uint8_t)(value & 0xFFu);
    dst[1] = (uint8_t)((value >> 8) & 0xFFu);
}

static inline void fb_put_u32_le(uint8_t *dst, uint32_t value)
{
    dst[0] = (uint8_t)(value & 0xFFu);
    dst[1] = (uint8_t)((value >> 8) & 0xFFu);
    dst[2] = (uint8_t)((value >> 16) & 0xFFu);
    dst[3] = (uint8_t)((value >> 24) & 0xFFu);
}

static inline uint16_t fb_get_u16_le(const uint8_t *src)
{
    return (uint16_t)src[0] | ((uint16_t)src[1] << 8);
}

static inline uint32_t fb_get_u32_le(const uint8_t *src)
{
    return (uint32_t)src[0] |
           ((uint32_t)src[1] << 8) |
           ((uint32_t)src[2] << 16) |
           ((uint32_t)src[3] << 24);
}

static inline bool fb_encode_frame(uint8_t cmd,
                            uint32_t seq,
                            const uint8_t *payload,
                            uint16_t payload_len,
                            uint8_t *out,
                            size_t out_cap,
                            size_t *out_len)
{
    if (payload_len > FB_MAX_PAYLOAD || out_cap < FB_HEADER_SIZE + payload_len + FB_CRC_SIZE) {
        return false;
    }

    out[0] = FB_MAGIC0;
    out[1] = FB_MAGIC1;
    out[2] = FB_VERSION;
    out[3] = cmd;
    fb_put_u32_le(&out[4], seq);
    fb_put_u16_le(&out[8], payload_len);

    for (uint16_t i = 0; i < payload_len; ++i) {
        out[FB_HEADER_SIZE + i] = payload[i];
    }

    uint16_t crc = fb_crc16_ccitt(out, FB_HEADER_SIZE + payload_len);
    fb_put_u16_le(&out[FB_HEADER_SIZE + payload_len], crc);
    *out_len = FB_HEADER_SIZE + payload_len + FB_CRC_SIZE;
    return true;
}

static inline bool fb_decode_frame(const uint8_t *frame,
                            size_t frame_len,
                            uint8_t *cmd,
                            uint32_t *seq,
                            const uint8_t **payload,
                            uint16_t *payload_len)
{
    if (frame_len < FB_HEADER_SIZE + FB_CRC_SIZE) {
        return false;
    }
    if (frame[0] != FB_MAGIC0 || frame[1] != FB_MAGIC1 || frame[2] != FB_VERSION) {
        return false;
    }

    uint16_t len = fb_get_u16_le(&frame[8]);
    if (len > FB_MAX_PAYLOAD || frame_len != FB_HEADER_SIZE + len + FB_CRC_SIZE) {
        return false;
    }

    uint16_t expected_crc = fb_get_u16_le(&frame[FB_HEADER_SIZE + len]);
    uint16_t actual_crc = fb_crc16_ccitt(frame, FB_HEADER_SIZE + len);
    if (expected_crc != actual_crc) {
        return false;
    }

    *cmd = frame[3];
    *seq = fb_get_u32_le(&frame[4]);
    *payload = &frame[FB_HEADER_SIZE];
    *payload_len = len;
    return true;
}

static inline uint16_t fb_pack_event_payload(const fb_event_payload_t *event, uint8_t *out)
{
    fb_put_u16_le(&out[0], event->address);
    out[2] = event->device_type;
    out[3] = event->event_type;
    fb_put_u16_le(&out[4], event->flags);
    fb_put_u32_le(&out[6], event->bus_time_ms);
    return 10u;
}

static inline bool fb_unpack_event_payload(const uint8_t *payload,
                                    uint16_t payload_len,
                                    fb_event_payload_t *event)
{
    if (payload_len < 10u) {
        return false;
    }

    event->address = fb_get_u16_le(&payload[0]);
    event->device_type = payload[2];
    event->event_type = payload[3];
    event->flags = fb_get_u16_le(&payload[4]);
    event->bus_time_ms = fb_get_u32_le(&payload[6]);
    return true;
}

#endif
