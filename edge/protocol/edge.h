#ifndef OSCAR_EDGE_H
#define OSCAR_EDGE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Wire contract source of truth. Little endian, 20 bytes, CRC-16/CCITT-FALSE. */
#define EDGE_VERSION 1
#define EDGE_FRAME_SIZE 20
#define EDGE_TIMEOUT_MS 1500
#define EDGE_HELLO 1
#define EDGE_HEALTH 2
#define EDGE_CAPABILITIES 3
#define EDGE_GPIO_READ 4
#define EDGE_GPIO_WRITE 5
#define EDGE_SENSOR_SAMPLE 6
#define EDGE_EVENT 7
#define EDGE_SAFE_STATE 8
#define EDGE_REFLEX_TRIGGER 9
#define EDGE_E_STOP 10
#define EDGE_ACK 11
#define EDGE_ERROR 12
#define EDGE_DISPLAY 13

typedef struct {
    uint8_t kind;
    uint32_t session, sequence;
    uint16_t channel;
    uint32_t value;
} edge_message;
typedef struct {
    uint32_t session, sequence, last_ms;
    edge_message last_request, last_reply;
    bool connected, stopped, output;
    uint32_t writes;
} edge_controller;
uint16_t edge_crc(const uint8_t *data, size_t n);
bool edge_decode(const uint8_t *data, size_t n, edge_message *message);
void edge_encode(const edge_message *message, uint8_t data[EDGE_FRAME_SIZE]);
void edge_init(edge_controller *controller);
void edge_safe(edge_controller *controller, bool latch);
void edge_tick(edge_controller *controller, uint32_t now_ms, bool interlock);
edge_message edge_handle(edge_controller *controller, edge_message request,
                         uint32_t now_ms, bool input, uint32_t sensor);
#endif
