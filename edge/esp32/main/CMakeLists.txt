idf_component_register(SRCS "main.c" "network.c" "link.c"
  "../../protocol/codec.c" "../../protocol/stream.c"
  INCLUDE_DIRS "." "../../protocol"
  REQUIRES esp_wifi esp_event esp_netif nvs_flash esp_http_client esp_driver_uart
           esp_timer esp_system mbedtls esp_driver_gpio)
target_compile_options(${COMPONENT_LIB} PRIVATE -Wall -Wextra -Werror)
