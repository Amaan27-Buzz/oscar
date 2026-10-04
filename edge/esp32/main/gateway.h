#ifndef OSCAR_GATEWAY_H
#define OSCAR_GATEWAY_H
#include "edge.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
typedef struct {
    char ssid[33], password[65], url[256], node[65], session[65], token[129], ca[2048];
} gateway_config;
extern gateway_config gateway;
extern QueueHandle_t requests, receipts, events;
extern SemaphoreHandle_t state_lock;
extern uint32_t boot_id, core_seen_ms;
extern bool pico_healthy;
uint32_t gateway_now(void);
void network_task(void *unused);
void link_task(void *unused);
#endif
