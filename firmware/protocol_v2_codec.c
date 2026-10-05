/* Portable byte codec reference. Host tested; no STM32/HAL or radio driver. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <limits.h>

#define WIRE_MAX 64u

static uint16_t get16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}
static uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static int32_t geti32(const uint8_t *p) {
    uint32_t u = get32(p);
    return u <= INT32_MAX ? (int32_t)u : (int32_t)((int64_t)u - 4294967296LL);
}
static uint16_t crc16(const uint8_t *p, size_t n) {
    uint16_t crc = 0xffffu;
    size_t i;
    unsigned bit;
    for (i = 0; i < n; ++i) {
        crc ^= (uint16_t)((uint16_t)p[i] << 8);
        for (bit = 0; bit < 8; ++bit)
            crc = (uint16_t)((crc & 0x8000u) ? ((uint32_t)crc << 1) ^ 0x1021u : (uint32_t)crc << 1);
    }
    return crc;
}
static int valid_body(const uint8_t *b, size_t n) {
    const uint8_t *s;
    uint8_t type, status, flags, pattern, code, detail;
    int numeric, approved, short_valid, short_active;
    int32_t p0, p1, q;
    if (n < 16u || b[0] != 2u) return 0;
    type = b[1];
    if (type < 1u || type > 3u || get16(b + 2) != n - 16u ||
        !get32(b + 4) || !get32(b + 8) || !get32(b + 12)) return 0;
    if (type == 2u) return n == 20u;
    if (n != (type == 1u ? 53u : 51u)) return 0;
    s = b + 16;
    if (!get32(s + 4) || !get32(s + 8)) return 0;
    p0 = geti32(s + 18); p1 = geti32(s + 22); q = geti32(s + 26);
    status = s[30]; flags = s[31]; pattern = s[32];
    if (status > 5u || pattern > 4u || (flags & 0x70u)) return 0;
    if ((p0 == INT32_MIN) != (s[33] == 255u) ||
        (p1 == INT32_MIN) != (s[34] == 255u)) return 0;
    if ((s[33] != 255u && s[33] > 30u) || (s[34] != 255u && s[34] > 30u)) return 0;
    numeric = (flags & 1u) != 0u; approved = (flags & 2u) != 0u;
    short_valid = (flags & 4u) != 0u; short_active = (flags & 8u) != 0u;
    if (numeric != (get16(s + 12) != 0u)) return 0;
    if ((short_active && !short_valid) || (short_valid && !(numeric && approved))) return 0;
    if (status == 0u) {
        if (!numeric || !approved || p0 < 0 || p0 > 20000 || p1 < 1000 || p1 > 20000 || q < 500 || pattern == 4u) return 0;
    } else if (pattern != 4u) return 0;
    if ((status == 1u || status == 2u) && (short_valid || short_active)) return 0;
    if ((status == 1u && approved) || (status == 2u && numeric)) return 0;
    if (type == 1u) {
        code = s[35]; detail = s[36];
        if (code < 1u || code > 6u) return 0;
        if (code == 1u && detail > 5u && detail != 255u) return 0;
        if (code == 2u && (detail < 1u || detail > 4u)) return 0;
        if (code >= 3u) {
            if (detail != 0u || (flags & 3u) != 3u) return 0;
            if (code == 3u && !short_active) return 0;
            if (code >= 4u && pattern != code - 3u) return 0;
        }
    }
    return 1;
}

int protocol_v2_encode(const uint8_t *body, size_t n, uint8_t *wire, size_t capacity) {
    uint8_t raw[62];
    size_t i, w = 1u, code_at = 0u;
    uint8_t code = 1u;
    uint16_t crc;
    if (!body || !wire || n > 60u || capacity < WIRE_MAX || !valid_body(body, n)) return -1;
    memcpy(raw, body, n); crc = crc16(body, n);
    raw[n] = (uint8_t)crc; raw[n+1u] = (uint8_t)(crc >> 8);
    for (i = 0; i < n+2u; ++i) {
        if (raw[i] == 0u) {
            wire[code_at] = code; code_at = w++; code = 1u;
        } else {
            wire[w++] = raw[i]; ++code;
        }
    }
    wire[code_at] = code; wire[w++] = 0u;
    return (int)w;
}

int protocol_v2_decode(const uint8_t *wire, size_t n, uint8_t *body, size_t capacity) {
    uint8_t raw[62];
    size_t i = 0u, r = 0u, end;
    uint8_t code;
    if (!wire || !body || n < 2u || n > WIRE_MAX || wire[n-1u] != 0u) return -1;
    while (i < n-1u) {
        code = wire[i];
        if (!code) return -1;
        end = i + code;
        if (end > n-1u) return -1;
        ++i;
        while (i < end) {
            if (!wire[i] || r >= sizeof(raw)) return -1;
            raw[r++] = wire[i++];
        }
        if (code < 255u && i < n-1u) {
            if (r >= sizeof(raw)) return -1;
            raw[r++] = 0u;
        }
    }
    if (r < 18u || crc16(raw, r-2u) != get16(raw+r-2u) ||
        capacity < r-2u || !valid_body(raw, r-2u)) return -1;
    memcpy(body, raw, r-2u);
    return (int)(r-2u);
}

#ifdef BUILD_HARNESS
#include <stdio.h>
static int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
int main(void) {
    char line[160];
    uint8_t in[70], out[64];
    size_t i, chars, n;
    int a, b, result, good;
    while (fgets(line, sizeof(line), stdin)) {
        chars = strcspn(line+2, "\r\n"); n = chars/2u; good = chars%2u == 0u && n <= sizeof(in);
        for (i = 0; i < n && good; ++i) {
            a = hex_digit(line[2u+2u*i]); b = hex_digit(line[3u+2u*i]);
            if (a < 0 || b < 0) good = 0;
            else in[i] = (uint8_t)(a*16+b);
        }
        if (!good) result = -1;
        else if (line[0] == 'E') result = protocol_v2_encode(in, n, out, sizeof(out));
        else if (line[0] == 'D') result = protocol_v2_decode(in, n, out, sizeof(out));
        else result = -1;
        if (result < 0) puts("ERR");
        else {
            for (i = 0; i < (size_t)result; ++i) printf("%02x", (unsigned)out[i]);
            putchar('\n');
        }
    }
    return 0;
}
#endif
