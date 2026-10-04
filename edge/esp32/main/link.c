#include "gateway.h"
#include "stream.h"
#include "driver/uart.h"
#include "esp_task_wdt.h"
#ifdef CONFIG_OSCAR_EDGE_WATCHDOG_TEST
#include "driver/gpio.h"
#endif

static void send(edge_message m) {
    uint8_t raw[EDGE_FRAME_SIZE]; edge_encode(&m, raw);
    uart_write_bytes(UART_NUM_1, raw, sizeof(raw));
}
static bool transact(edge_message request, edge_message *reply) {
    edge_stream stream = {0};
    /* Same sequence on retry; Pico caches the last reply, no duplicate mutation. */
    for (unsigned attempt = 0; attempt < 3; ++attempt) {
        send(request);
        uint32_t started = gateway_now();
        while ((uint32_t)(gateway_now() - started) < 100) {
            uint8_t byte;
            if (uart_read_bytes(UART_NUM_1, &byte, 1, pdMS_TO_TICKS(5)) == 1 &&
                edge_stream_byte(&stream, byte, gateway_now(), reply)) {
                if (reply->kind == EDGE_EVENT && reply->session == boot_id) {
                    xQueueSend(events, reply, 0); continue;
                }
                if (reply->session == request.session && reply->sequence == request.sequence &&
                    reply->channel == request.channel &&
                    (reply->kind == EDGE_ACK || reply->kind == EDGE_ERROR)) return true;
            }
        }
    }
    return false;
}
void link_task(void *unused) {
    (void)unused;
    uart_config_t config = {.baud_rate=115200, .data_bits=UART_DATA_8_BITS,
        .parity=UART_PARITY_DISABLE, .stop_bits=UART_STOP_BITS_1,
        .flow_ctrl=UART_HW_FLOWCTRL_DISABLE, .source_clk=UART_SCLK_DEFAULT};
    ESP_ERROR_CHECK(uart_param_config(UART_NUM_1, &config));
    ESP_ERROR_CHECK(uart_set_pin(UART_NUM_1, 17, 16, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    ESP_ERROR_CHECK(uart_driver_install(UART_NUM_1, 256, 0, 0, NULL, 0));
    ESP_ERROR_CHECK(esp_task_wdt_add(NULL));
#ifdef CONFIG_OSCAR_EDGE_WATCHDOG_TEST
    gpio_config_t fault = {.pin_bit_mask=1ULL << 27, .mode=GPIO_MODE_INPUT,
        .pull_up_en=GPIO_PULLUP_ENABLE, .pull_down_en=GPIO_PULLDOWN_DISABLE,
        .intr_type=GPIO_INTR_DISABLE};
    ESP_ERROR_CHECK(gpio_config(&fault));
#endif
    edge_message reply;
    uint32_t sequence = 1;
    bool negotiated = false;
    edge_message previous = {0}, cached = {0};
    bool cached_valid = false;
    while (true) {
#ifdef CONFIG_OSCAR_EDGE_WATCHDOG_TEST
        if (!gpio_get_level(27)) {
            edge_message safe = {.kind=EDGE_SAFE_STATE, .session=boot_id, .sequence=sequence};
            send(safe); vTaskSuspend(NULL); /* Intentionally trip subscribed task watchdog. */
        }
#endif
        xSemaphoreTake(state_lock, portMAX_DELAY);
        bool online = core_seen_ms && (uint32_t)(gateway_now() - core_seen_ms) < 1000;
        xSemaphoreGive(state_lock);
        bool healthy = false;
        if (!online) {
            edge_message safe = {.kind=EDGE_SAFE_STATE, .session=boot_id, .sequence=sequence};
            send(safe); negotiated = false;
            xQueueReset(requests);
        } else {
            if (!negotiated) {
                edge_message hello = {.kind=EDGE_HELLO, .session=boot_id, .sequence=sequence,
                                      .value=EDGE_VERSION};
                negotiated = transact(hello, &reply) && reply.kind == EDGE_ACK;
                /* Same session reconnect: health probe succeeds if Pico session remained alive. */
                if (!negotiated) {
                    edge_message health = {.kind=EDGE_HEALTH, .session=boot_id, .sequence=++sequence};
                    negotiated = transact(health, &reply) && reply.kind == EDGE_ACK;
                }
            }
            if (negotiated) {
                edge_message caps = {.kind=EDGE_CAPABILITIES, .session=boot_id,
                                     .sequence=++sequence};
                negotiated = transact(caps, &reply) && reply.kind == EDGE_ACK && reply.value == 0x3f;
            }
            if (negotiated) {
                edge_message command;
                if (xQueueReceive(requests, &command, 0) == pdTRUE) {
                    if (cached_valid && command.sequence == previous.sequence &&
                        command.kind == previous.kind && command.channel == previous.channel &&
                        command.value == previous.value) {
                        healthy = true; xQueueOverwrite(receipts, &cached);
                    } else if (command.sequence > previous.sequence) {
                        previous = command;
                        command.sequence = ++sequence;
                        healthy = transact(command, &reply);
                        if (healthy) {
                            reply.sequence = previous.sequence;
                            cached = reply; cached_valid = true;
                            xQueueOverwrite(receipts, &reply);
                        } else cached_valid = false;
                    }
                    else negotiated = false;
                } else {
                    edge_message health = {.kind=EDGE_HEALTH, .session=boot_id, .sequence=++sequence};
                    healthy = transact(health, &reply) && reply.kind == EDGE_ACK && !(reply.value & 2);
                    if (!healthy) negotiated = false;
                }
            }
        }
        xSemaphoreTake(state_lock, portMAX_DELAY);
        pico_healthy = healthy; xSemaphoreGive(state_lock);
        ESP_ERROR_CHECK(esp_task_wdt_reset());
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
