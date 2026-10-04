#include "gateway.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_netif_sntp.h"
#include "esp_random.h"
#include "esp_timer.h"
#include "esp_log.h"
#include <string.h>

gateway_config gateway;
QueueHandle_t requests, receipts, events;
SemaphoreHandle_t state_lock;
uint32_t boot_id, core_seen_ms;
bool pico_healthy;
uint32_t gateway_now(void) { return (uint32_t)(esp_timer_get_time() / 1000); }
static bool load(void) {
    nvs_handle_t handle;
    if (nvs_open("oscar", NVS_READONLY, &handle) != ESP_OK) return false;
    const char *keys[] = {"ssid", "password", "url", "node", "session", "token", "ca"};
    char *values[] = {gateway.ssid, gateway.password, gateway.url, gateway.node,
                      gateway.session, gateway.token, gateway.ca};
    size_t sizes[] = {33,65,256,65,65,129,2048};
    bool ok = true;
    for (int i = 0; i < 7; ++i)
        if (nvs_get_str(handle, keys[i], values[i], &sizes[i]) != ESP_OK) ok = false;
    nvs_close(handle);
    return ok && !strncmp(gateway.url, "https://", 8) && strlen(gateway.ca) > 100 &&
           strlen(gateway.session) == 32 && strlen(gateway.token) >= 32;
}
static void wifi_event(void *arg, esp_event_base_t base, int32_t id, void *data) {
    (void)arg; (void)data;
    if (base == WIFI_EVENT && (id == WIFI_EVENT_STA_START || id == WIFI_EVENT_STA_DISCONNECTED))
        esp_wifi_connect(); /* IDF Wi-Fi driver owns scan/reassociation; HTTP backs off separately. */
}
void app_main(void) {
    /* Never silently erase owner provisioning on NVS errors. */
    ESP_ERROR_CHECK(nvs_flash_init());
    if (!load()) { ESP_LOGW("edge", "Unprovisioned; no physical commands enabled"); return; }
    boot_id = esp_random(); if (!boot_id) boot_id = 1;
    requests = xQueueCreate(1, sizeof(edge_message));
    receipts = xQueueCreate(1, sizeof(edge_message));
    events = xQueueCreate(8, sizeof(edge_message));
    state_lock = xSemaphoreCreateMutex();
    configASSERT(requests && receipts && events && state_lock);
    ESP_ERROR_CHECK(esp_netif_init()); ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event, NULL));
    wifi_config_t config = {0};
    memcpy(config.sta.ssid, gateway.ssid, strlen(gateway.ssid));
    memcpy(config.sta.password, gateway.password, strlen(gateway.password));
    config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    config.sta.pmf_cfg.capable = true;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &config));
    ESP_ERROR_CHECK(esp_wifi_start());
    esp_sntp_config_t sntp = ESP_NETIF_SNTP_DEFAULT_CONFIG("pool.ntp.org");
    ESP_ERROR_CHECK(esp_netif_sntp_init(&sntp));
    configASSERT(xTaskCreate(link_task, "edge_link", 4096, NULL, 8, NULL) == pdPASS);
    configASSERT(xTaskCreate(network_task, "edge_network", 8192, NULL, 4, NULL) == pdPASS);
}
