/* Node application: one 1 s bin per loop iteration.
 *
 * Sequence per bin (review v2.2 section 4.2):
 *   open 24 V -> wait T_set -> read ADC -> close 24 V -> finish the bin
 *   -> take pulses -> feed the sampler -> write CSV -> send on alarm.
 *
 * The same main() drives the host replay build and the target build.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "bsp.h"
#include "../core/sampler.h"

extern int protocol_v2_encode(const uint8_t *body, size_t n,
                              uint8_t *wire, size_t capacity);

#ifndef T_SET_MS
#define T_SET_MS 100u
#endif

#define CSV_HEADER "seq,unix_ms,p0_centi,p1_centi,dp_centi,q_milli,count10,quality,zq_milli,zr_milli,sq_milli,alarm"

static void put_u32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)(v & 0xffu);
    p[1] = (uint8_t)((v >> 8) & 0xffu);
    p[2] = (uint8_t)((v >> 16) & 0xffu);
    p[3] = (uint8_t)((v >> 24) & 0xffu);
}

static void put_i32(uint8_t *p, int32_t v) { put_u32(p, (uint32_t)v); }

/* type 1 event frame, 53 bytes. code=2, detail = 1 leak / 2 restriction. */
static size_t build_event_frame(uint8_t *body, uint32_t seq,
                                int32_t p0, int32_t p1, int32_t q,
                                uint8_t detail)
{
    uint8_t *s;
    memset(body, 0, 53);
    body[0] = 2u;
    body[1] = 1u;
    body[2] = 37u; body[3] = 0u;
    put_u32(body + 4, 0x00000001u);      /* device id */
    put_u32(body + 8, 0x00000001u);      /* session id */
    put_u32(body + 12, seq + 1u);        /* wire sample_seq, never zero */

    s = body + 16;
    put_u32(s + 0, 1760000000u);         /* wall clock placeholder */
    put_u32(s + 4, 1u);
    put_u32(s + 8, 1u);
    /* s+12 numeric flag: leak frame keeps numeric, restriction frame drops it */
    s[12] = (detail == 1u) ? 1u : 0u;
    s[13] = 0u;
    put_i32(s + 18, p0);
    put_i32(s + 22, p1);
    put_i32(s + 26, q);
    s[30] = (detail == 1u) ? 1u : 2u;    /* status: 1 leak, 2 restriction */
    s[31] = (detail == 1u) ? 0x01u : 0x02u;
    s[32] = 4u;                          /* pattern */
    s[33] = 0u;                          /* p0 quality ok */
    s[34] = 0u;                          /* p1 quality ok */
    s[35] = 2u;                          /* code */
    s[36] = detail;                      /* detail */
    return 53;
}

int main(int argc, char **argv)
{
    Sampler s;
    SampleRow row;
    char line[256];
    uint32_t bins = 0u, sent = 0u, first_alarm_seq = 0u;
    uint8_t last_alarm = 0u;

    sampler_init(&s);
    if (bsp_init() != 0) { bsp_log("bsp init failed"); return 1; }

#ifdef BSP_HOST
    if (argc > 1 && bsp_host_load(argv[1]) <= 0) { bsp_log("feed load failed"); return 1; }
    bsp_host_set_out(argc > 2 ? argv[2] : NULL);
#else
    (void)argc; (void)argv;
#endif

    bsp_csv_line(CSV_HEADER);

#ifdef BSP_HOST
    while (!bsp_host_eof()) {
#else
    while (1) {
#endif
        uint32_t bin_start = bsp_now_ms();
        uint16_t dpc = 0u, p1c = 0u, vref = 0u;
        int32_t dp_centi = 0, p1_centi = 0;
        uint8_t quality = QUALITY_OK;
        uint32_t count, elapsed;

        bsp_24v_set(1);
        bsp_sleep_ms(T_SET_MS);
        if (bsp_adc_read(&dpc, &p1c, &vref) != 0) {
            quality = QUALITY_TIMING;
        } else {
            int32_t dp_mv = adc_code_to_mv(dpc, vref);
            int32_t p1_mv = adc_code_to_mv(p1c, vref);
            dp_centi = mv_to_centi_kpa(dp_mv, FS_DP_CENTI);
            p1_centi = mv_to_centi_kpa(p1_mv, FS_P1_CENTI);
            if (dp_centi == -1 || p1_centi == -1) {
                quality = QUALITY_OPEN_LOOP;
                dp_centi = 0; p1_centi = 0;
            } else if (dp_centi == -2 || p1_centi == -2) {
                quality = QUALITY_SATURATED;
                if (dp_centi < 0) dp_centi = FS_DP_CENTI;
                if (p1_centi < 0) p1_centi = FS_P1_CENTI;
            }
        }
        bsp_24v_set(0);

        elapsed = bsp_now_ms() - bin_start;
        if (elapsed < BIN_MS) bsp_sleep_ms(BIN_MS - elapsed);

        count = bsp_pulse_take();
        sampler_feed(&s, count, dp_centi, p1_centi, quality, &row);
        row.unix_ms = bsp_now_ms();
        sampler_row_csv(&row, line, sizeof(line));
        bsp_csv_line(line);
        if ((row.seq % 10u) == 0u) bsp_csv_sync();
        bins++;

        if (row.alarm && row.alarm != last_alarm) {
            uint8_t body[64], wire[64];
            int n;
            size_t bl = build_event_frame(body, row.seq, row.p0_centi,
                                          row.p1_centi, row.q_milli, row.alarm);
            n = protocol_v2_encode(body, bl, wire, sizeof(wire));
            if (n > 0) { bsp_lora_send(wire, (size_t)n); sent++; }
            else fprintf(stderr, "warn: frame encode failed at seq %lu\n",
                         (unsigned long)row.seq);
            if (!first_alarm_seq) first_alarm_seq = row.seq;
        }
        last_alarm = row.alarm;
    }

    fprintf(stderr,
            "bins=%lu csv_ok=%d cal_done=%d n=%.4f a=%.4f gain=%.4f r0=%.4f "
            "s_q=%.6f s_r=%.6f first_alarm_seq=%lu frames=%lu "
            "open=%lu sat=%lu timing=%lu\n",
            (unsigned long)bins, 1, (int)s.cal_done, s.n_exp, s.a_coef, s.gain,
            s.r0, s.s_q, s.s_r, (unsigned long)first_alarm_seq,
            (unsigned long)sent, (unsigned long)s.bins_open,
            (unsigned long)s.bins_sat, (unsigned long)s.bins_timing);

#ifdef BSP_HOST
    bsp_host_close();
#endif
    return 0;
}
