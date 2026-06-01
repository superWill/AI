#include "firebus_protocol.h"

#include <stdio.h>

static uint32_t g_seq = 1;

static void uart_send_bytes(const uint8_t *data, size_t len)
{
    printf("uart tx:");
    for (size_t i = 0; i < len; ++i) {
        printf(" %02X", data[i]);
    }
    printf("\n");
}

static void send_frame(uint8_t cmd, const uint8_t *payload, uint16_t payload_len)
{
    uint8_t frame[FB_MAX_FRAME];
    size_t frame_len = 0;

    if (!fb_encode_frame(cmd, g_seq++, payload, payload_len, frame, sizeof(frame), &frame_len)) {
        return;
    }

    uart_send_bytes(frame, frame_len);
}

static void report_firebus_event(uint16_t address,
                                 uint8_t device_type,
                                 uint8_t event_type,
                                 uint32_t bus_time_ms)
{
    uint8_t payload[16];
    fb_event_payload_t event = {
        .address = address,
        .device_type = device_type,
        .event_type = event_type,
        .flags = 0,
        .bus_time_ms = bus_time_ms
    };
    uint16_t payload_len = fb_pack_event_payload(&event, payload);

    send_frame(FB_CMD_EVENT_REPORT, payload, payload_len);
}

static void send_heartbeat(uint16_t pending_events, uint8_t bus_state, uint8_t rk_online)
{
    uint8_t payload[8];

    fb_put_u16_le(&payload[0], 1);
    fb_put_u16_le(&payload[2], 128);
    fb_put_u16_le(&payload[4], pending_events);
    payload[6] = bus_state;
    payload[7] = rk_online;

    send_frame(FB_CMD_HEARTBEAT, payload, sizeof(payload));
}

static void handle_rk_frame(const uint8_t *frame, size_t frame_len)
{
    uint8_t cmd = 0;
    uint32_t seq = 0;
    const uint8_t *payload = NULL;
    uint16_t payload_len = 0;

    if (!fb_decode_frame(frame, frame_len, &cmd, &seq, &payload, &payload_len)) {
        printf("bad frame from rk3506\n");
        return;
    }

    switch (cmd) {
    case FB_CMD_ACK:
        printf("rk3506 ack seq=%lu\n", (unsigned long)seq);
        break;
    case FB_CMD_GET_SNAPSHOT:
        printf("rk3506 requested snapshot\n");
        break;
    case FB_CMD_RESET_LOOP:
        printf("rk3506 requested fire bus reset\n");
        break;
    default:
        printf("unsupported rk3506 cmd=0x%02X len=%u\n", cmd, payload_len);
        break;
    }
}

int main(void)
{
    send_heartbeat(0, 0, 1);

    report_firebus_event(23, FB_DEVICE_SMOKE, FB_EVENT_ALARM, 143218);
    report_firebus_event(41, FB_DEVICE_IO_MODULE, FB_EVENT_OFFLINE, 143950);

    uint8_t reset_frame[FB_MAX_FRAME];
    size_t reset_frame_len = 0;
    fb_encode_frame(FB_CMD_RESET_LOOP, 9001, NULL, 0, reset_frame, sizeof(reset_frame), &reset_frame_len);
    handle_rk_frame(reset_frame, reset_frame_len);

    return 0;
}

