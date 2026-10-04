#ifndef EDGE_STREAM_H
#define EDGE_STREAM_H
#include "edge.h"
typedef struct { uint8_t data[EDGE_FRAME_SIZE]; size_t used; uint32_t last_ms; } edge_stream;
bool edge_stream_byte(edge_stream *stream, uint8_t byte, uint32_t now, edge_message *m);
#endif
