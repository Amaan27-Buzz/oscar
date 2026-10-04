#include "gateway.h"
#include "esp_http_client.h"
#include "esp_task_wdt.h"
#include <string.h>
#include <stdio.h>

void network_task(void *unused) {
    (void)unused;
    ESP_ERROR_CHECK(esp_task_wdt_add(NULL));
    char auth[140]; snprintf(auth, sizeof(auth), "Bearer %s", gateway.token);
    esp_http_client_config_t config = {
        .url = gateway.url, .cert_pem = gateway.ca, .timeout_ms = 700,
        .disable_auto_redirect = true, .keep_alive_enable = true,
    };
    esp_http_client_handle_t http = esp_http_client_init(&config);
    configASSERT(http);
    esp_http_client_set_method(http, HTTP_METHOD_POST);
    esp_http_client_set_header(http, "Authorization", auth);
    esp_http_client_set_header(http, "X-OSCAR-Session", gateway.session);
    esp_http_client_set_header(http, "Content-Type", "application/octet-stream");
    unsigned attempt = 0;
    edge_message receipt = {0}, event = {0};
    bool have_receipt = false, have_event = false;
    while (true) {
        uint8_t body[45] = {0}, raw[EDGE_FRAME_SIZE + 1];
        for (int i = 0; i < 4; ++i) body[i] = (uint8_t)(boot_id >> (8 * i));
        xSemaphoreTake(state_lock, portMAX_DELAY);
        body[4] = pico_healthy;
        xSemaphoreGive(state_lock);
        if (!have_receipt) have_receipt = xQueueReceive(receipts, &receipt, 0) == pdTRUE;
        if (!have_event) have_event = xQueueReceive(events, &event, 0) == pdTRUE;
        if (have_receipt) edge_encode(&receipt, body + 5);
        if (have_event) edge_encode(&event, body + 25);
        uint32_t started = gateway_now();
        bool ok = esp_http_client_open(http, sizeof(body)) == ESP_OK;
        if (ok) ok = esp_http_client_write(http, (const char *)body, sizeof(body)) == sizeof(body);
        int status = 0, got = 0;
        if (ok && esp_http_client_fetch_headers(http) >= 0) {
            status = esp_http_client_get_status_code(http);
            if (status == 200) got = esp_http_client_read_response(http, (char *)raw, sizeof(raw));
        }
        esp_http_client_close(http);
        ok = ok && (status == 204 || (status == 200 && got == EDGE_FRAME_SIZE)) &&
             (uint32_t)(gateway_now() - started) < 1000;
        if (ok) {
            xSemaphoreTake(state_lock, portMAX_DELAY);
            core_seen_ms = gateway_now(); xSemaphoreGive(state_lock);
            have_receipt = have_event = false; attempt = 0;
            edge_message command;
            if (status == 200 && edge_decode(raw, got, &command) && command.session == boot_id)
                xQueueSend(requests, &command, 0); /* bounded: never build an offline mutation queue */
        }
        ESP_ERROR_CHECK(esp_task_wdt_reset());
        unsigned delay = ok ? 250 : (250u << (attempt < 4 ? attempt++ : 4));
        vTaskDelay(pdMS_TO_TICKS(delay));
    }
}
