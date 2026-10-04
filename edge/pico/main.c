#include "edge.h"
#include "stream.h"
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/adc.h"
#include "hardware/watchdog.h"

int main(void) {
    edge_controller controller; edge_init(&controller);
    edge_stream stream = {0};
    /* External pulldown guarantees LOW while reset/boot/high impedance. */
    gpio_init(15); gpio_put(15, 0); gpio_set_dir(15, GPIO_OUT);
    gpio_init(14); gpio_set_dir(14, GPIO_IN); gpio_pull_up(14);
    gpio_init(13); gpio_set_dir(13, GPIO_IN); gpio_pull_up(13);
    adc_init(); adc_gpio_init(26); adc_select_input(0);
    uart_init(uart0, 115200); gpio_set_function(0, GPIO_FUNC_UART);
    gpio_set_function(1, GPIO_FUNC_UART);
    watchdog_enable(1000, true);
#ifdef EDGE_WATCHDOG_TEST
    gpio_init(12); gpio_set_dir(12, GPIO_IN); gpio_pull_up(12);
    gpio_init(11); gpio_set_dir(11, GPIO_OUT); gpio_put(11, 1);
    uint32_t boot_ms = to_ms_since_boot(get_absolute_time());
#endif
    uint32_t event_sequence = 0, last_event_ms = 0;
    bool previous_input = gpio_get(14), previous_stop = false;
    while (true) {
        uint32_t now = to_ms_since_boot(get_absolute_time());
        edge_tick(&controller, now, !gpio_get(13));
        /* Bound work per iteration so serial floods cannot starve safety. */
        for (int i = 0; i < 40 && uart_is_readable(uart0); ++i) {
            edge_message request;
            if (edge_stream_byte(&stream, uart_getc(uart0), now, &request)) {
                edge_message reply = edge_handle(&controller, request, now,
                                                 gpio_get(14), adc_read());
                edge_tick(&controller, now, !gpio_get(13));
                gpio_put(15, controller.output);
                uint8_t wire[EDGE_FRAME_SIZE]; edge_encode(&reply, wire);
                uart_write_blocking(uart0, wire, sizeof(wire));
            }
        }
        gpio_put(15, controller.output);
        bool input = gpio_get(14);
        if (controller.connected &&
            (input != previous_input || controller.stopped != previous_stop ||
             (uint32_t)(now - last_event_ms) >= 500)) {
            edge_message event = {.kind=EDGE_EVENT, .session=controller.session,
                .sequence=++event_sequence, .channel=2, .value=adc_read()};
            if (input != previous_input) { event.channel = 0; event.value = input; }
            else if (controller.stopped != previous_stop) { event.channel = 1; event.value = 2; }
            uint8_t wire[EDGE_FRAME_SIZE]; edge_encode(&event, wire);
            uart_write_blocking(uart0, wire, sizeof(wire));
            previous_input = input; previous_stop = controller.stopped; last_event_ms = now;
        }
#ifdef EDGE_WATCHDOG_TEST
        if ((uint32_t)(now - boot_ms) >= 100) gpio_put(11, 0);
        if (!gpio_get(12)) {
            edge_safe(&controller, false); gpio_put(15, 0);
        } else watchdog_update();
#else
        watchdog_update();
#endif
        sleep_ms(1);
    }
}
