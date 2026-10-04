#include "edge.h"
#include <string.h>
void edge_init(edge_controller *c) { memset(c, 0, sizeof(*c)); }
void edge_safe(edge_controller *c, bool latch) {
    c->output = false;
    if (latch) c->stopped = true;
}
void edge_tick(edge_controller *c, uint32_t now, bool interlock) {
    if (interlock) edge_safe(c, true);
    if (c->connected && (uint32_t)(now - c->last_ms) >= EDGE_TIMEOUT_MS) {
        edge_safe(c, false); c->connected = false;
    }
}
static bool same(edge_message a, edge_message b) {
    return a.kind == b.kind && a.session == b.session && a.sequence == b.sequence &&
           a.channel == b.channel && a.value == b.value;
}
edge_message edge_handle(edge_controller *c, edge_message r, uint32_t now,
                         bool input, uint32_t sensor) {
    edge_message reply = r;
    reply.kind = EDGE_ERROR; reply.value = 1;
    edge_tick(c, now, false);
    /* Safety overrides session fencing; cannot remotely clear the stop latch. */
    if (r.kind == EDGE_E_STOP || r.kind == EDGE_SAFE_STATE || r.kind == EDGE_REFLEX_TRIGGER) {
        if (r.channel || r.value) return reply;
        edge_safe(c, r.kind == EDGE_E_STOP);
        reply.kind = EDGE_ACK; reply.value = 0; return reply;
    }
    if (r.kind == EDGE_HELLO) {
        if (r.channel || r.value != EDGE_VERSION || !r.session || !r.sequence) return reply;
        if (c->connected && c->session == r.session) {
            if (same(r, c->last_request)) return c->last_reply;
            return reply;
        }
        edge_safe(c, false); c->session = r.session; c->sequence = r.sequence;
        c->connected = true; c->last_ms = now;
        reply.kind = EDGE_ACK; reply.value = EDGE_VERSION;
    } else {
        if (!c->connected || r.session != c->session) return reply;
        if (r.sequence == c->sequence) {
            if (same(r, c->last_request)) return c->last_reply;
            return reply;
        }
        if (r.sequence < c->sequence) return reply;
        /* No arbitrary GPIO. Logical input 0, test output/LED 1, sensor 2. */
        switch (r.kind) {
        case EDGE_HEALTH:
            if (r.channel || r.value) return reply;
            reply.value = (c->stopped ? 2u : 0u) | (c->output ? 4u : 0u); break;
        case EDGE_CAPABILITIES:
            if (r.channel || r.value) return reply;
            reply.value = 0x3f; break;
        case EDGE_GPIO_READ:
            if (r.channel > 1 || r.value) return reply;
            reply.value = r.channel == 0 ? input : c->output; break;
        case EDGE_SENSOR_SAMPLE:
            if (r.channel != 2 || r.value) return reply;
            reply.value = sensor; break;
        case EDGE_GPIO_WRITE: case EDGE_DISPLAY:
            if (r.channel != 1 || r.value > 1 || c->stopped) return reply;
            c->output = r.value != 0; c->writes++; reply.value = c->output; break;
        default: return reply;
        }
        reply.kind = EDGE_ACK;
        c->sequence = r.sequence; c->last_ms = now;
    }
    c->last_request = r; c->last_reply = reply;
    return reply;
}
