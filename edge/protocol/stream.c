#include "stream.h"
#include <string.h>
bool edge_stream_byte(edge_stream *s, uint8_t byte, uint32_t now, edge_message *m) {
    if ((uint32_t)(now - s->last_ms) > 100) s->used = 0;
    s->last_ms = now;
    s->data[s->used++] = byte;
    if (s->used < EDGE_FRAME_SIZE) return false;
    if (edge_decode(s->data, s->used, m)) { s->used = 0; return true; }
    memmove(s->data, s->data + 1, EDGE_FRAME_SIZE - 1);
    s->used = EDGE_FRAME_SIZE - 1; return false;
}
