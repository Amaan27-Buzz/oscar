#include "edge.h"
#include <string.h>
static uint32_t get(const uint8_t *p, size_t n) {
    uint32_t v = 0;
    for (size_t i = 0; i < n; ++i) v |= (uint32_t)p[i] << (8 * i);
    return v;
}
static void put(uint8_t *p, uint32_t v, size_t n) {
    for (size_t i = 0; i < n; ++i) p[i] = (uint8_t)(v >> (8 * i));
}
uint16_t edge_crc(const uint8_t *p, size_t n) {
    uint16_t crc = 0xffff;
    for (size_t i = 0; i < n; ++i) {
        crc ^= (uint16_t)p[i] << 8;
        for (int bit = 0; bit < 8; ++bit)
            crc = (uint16_t)((crc & 0x8000) ? (crc << 1) ^ 0x1021 : crc << 1);
    }
    return crc;
}
bool edge_decode(const uint8_t *p, size_t n, edge_message *m) {
    if (n != EDGE_FRAME_SIZE || p[0] != 'O' || p[1] != 'E' ||
        p[2] != EDGE_VERSION || p[3] < EDGE_HELLO || p[3] > EDGE_DISPLAY ||
        get(p + 18, 2) != edge_crc(p, 18)) return false;
    m->kind = p[3]; m->session = get(p + 4, 4); m->sequence = get(p + 8, 4);
    m->channel = (uint16_t)get(p + 12, 2); m->value = get(p + 14, 4);
    return m->session != 0 && m->sequence != 0;
}
void edge_encode(const edge_message *m, uint8_t *p) {
    p[0] = 'O'; p[1] = 'E'; p[2] = EDGE_VERSION; p[3] = m->kind;
    put(p + 4, m->session, 4); put(p + 8, m->sequence, 4);
    put(p + 12, m->channel, 2); put(p + 14, m->value, 4);
    put(p + 18, edge_crc(p, 18), 2);
}
