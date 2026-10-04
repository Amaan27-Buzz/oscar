/* Host reference uses the EXACT firmware codec, parser and controller. */
#include "edge.h"
#include "stream.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
    edge_controller c; edge_init(&c);
    edge_stream stream = {0};
    char line[256];
    while (fgets(line, sizeof(line), stdin)) {
        unsigned now, input, sensor, stop;
        char hex[100] = {0};
        if (sscanf(line, "%u %u %u %u %99s", &now, &input, &sensor, &stop, hex) != 5) return 2;
        if (!strcmp(hex, "reset")) { edge_init(&c); memset(&stream, 0, sizeof(stream)); }
        edge_tick(&c, now, stop != 0);
        edge_message request, reply;
        bool got = false;
        for (size_t i = 0; i + 1 < strlen(hex) && strcmp(hex, "reset"); i += 2) {
            char byte[3] = {hex[i], hex[i + 1], 0};
            if (edge_stream_byte(&stream, (uint8_t)strtoul(byte, NULL, 16), now, &request)) {
                reply = edge_handle(&c, request, now, input != 0, sensor);
                edge_tick(&c, now, stop != 0); got = true;
            }
        }
        if (got) {
            uint8_t wire[EDGE_FRAME_SIZE]; edge_encode(&reply, wire);
            for (size_t i = 0; i < sizeof(wire); ++i) printf("%02x", wire[i]);
        } else printf("-");
        printf(" %u %u %u %u\n", c.output, c.stopped, c.connected, c.writes);
        fflush(stdout);
    }
    return 0;
}
