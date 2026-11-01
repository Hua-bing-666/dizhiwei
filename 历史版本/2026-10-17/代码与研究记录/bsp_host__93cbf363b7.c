/* Host replay implementation of bsp.h.
 *
 * Feeds a recorded trajectory (t_ms, p0_kpa, p1_kpa, q_lpm) through the real
 * conversion chain: pressure -> 4-20 mA -> 150 ohm -> 12-bit code, and flow ->
 * 540 pulses/L with true integer truncation. Quantisation is therefore
 * reproduced, not skipped, so the 10 s window can be verified numerically.
 */
#define BSP_HOST 1
#include "bsp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define FEED_MAX 4096

static struct {
    uint32_t t_ms[FEED_MAX];
    double   p0[FEED_MAX];
    double   p1[FEED_MAX];
    double   q[FEED_MAX];
    size_t   n;
} feed;

static uint32_t g_now = 0;
static size_t   g_idx = 0;
static double   g_pulse_acc = 0.0;
static uint32_t g_pulse_pending = 0;
static FILE    *g_out = NULL;
static int      g_24v = 0;
static uint32_t g_lines = 0;
static uint32_t g_frames = 0;

static void feed_value(uint32_t t_ms, double *p0, double *p1, double *q)
{
    size_t i = g_idx;
    while (i + 1 < feed.n && feed.t_ms[i + 1] <= t_ms) i++;
    if (feed.n == 0) { *p0 = *p1 = *q = 0.0; return; }
    if (i + 1 < feed.n) {
        uint32_t t0 = feed.t_ms[i], t1 = feed.t_ms[i + 1];
        double w = (t1 > t0) ? (double)(t_ms - t0) / (double)(t1 - t0) : 0.0;
        if (w < 0.0) w = 0.0;
        if (w > 1.0) w = 1.0;
        *p0 = feed.p0[i] + (feed.p0[i + 1] - feed.p0[i]) * w;
        *p1 = feed.p1[i] + (feed.p1[i + 1] - feed.p1[i]) * w;
        *q  = feed.q[i]  + (feed.q[i + 1]  - feed.q[i])  * w;
    } else {
        *p0 = feed.p0[i]; *p1 = feed.p1[i]; *q = feed.q[i];
    }
}

int bsp_init(void)
{
    g_now = 0; g_idx = 0; g_pulse_acc = 0.0; g_pulse_pending = 0;
    g_24v = 0; g_lines = 0; g_frames = 0;
    return 0;
}

uint32_t bsp_now_ms(void) { return g_now; }

void bsp_sleep_ms(uint32_t ms)
{
    uint32_t done = 0;
    while (done < ms) {
        uint32_t step = (ms - done > 100u) ? 100u : (ms - done);
        double p0, p1, q;
        feed_value(g_now, &p0, &p1, &q);
        /* pulses accumulate continuously, also while the core sleeps */
        g_pulse_acc += q / 60.0 * 540.0 * ((double)step / 1000.0);
        while (g_pulse_acc >= 1.0) { g_pulse_acc -= 1.0; g_pulse_pending++; }
        g_now += step;
        done += step;
        if (feed.n && g_now >= feed.t_ms[feed.n - 1]) { g_idx = feed.n - 1; }
        else { g_idx = 0; { size_t i = g_idx; while (i + 1 < feed.n && feed.t_ms[i + 1] <= g_now) i++; g_idx = i; } }
    }
}

void bsp_24v_set(int on) { g_24v = on ? 1 : 0; }

int bsp_adc_read(uint16_t *dp_code, uint16_t *p1_code, uint16_t *vref_code)
{
    double p0, p1, q, dp, mv;
    long code;
    (void)q;
    if (!g_24v) return -1;                 /* never sample with the rail off */
    feed_value(g_now, &p0, &p1, &q);
    dp = p0 - p1;
    if (dp < 0.0) dp = 0.0;

    /* pressure -> mA -> mV across 150 ohm -> 12-bit code at VDDA = 3.300 V */
    mv = (4.0 + 16.0 * (dp / 35.0)) * 150.0;
    code = lround(mv / 3300.0 * 4095.0);
    if (code < 0) code = 0;
    if (code > 4095) code = 4095;
    *dp_code = (uint16_t)code;

    mv = (4.0 + 16.0 * (p1 / 200.0)) * 150.0;
    code = lround(mv / 3300.0 * 4095.0);
    if (code < 0) code = 0;
    if (code > 4095) code = 4095;
    *p1_code = (uint16_t)code;

    *vref_code = (uint16_t)lround(1200.0 / 3300.0 * 4095.0);
    return 0;
}

uint32_t bsp_pulse_take(void)
{
    uint32_t v = g_pulse_pending;
    g_pulse_pending = 0;
    return v;
}

int bsp_csv_line(const char *line)
{
    FILE *f = g_out ? g_out : stdout;
    if (fputs(line, f) < 0) return -1;
    if (fputc('\n', f) < 0) return -1;
    g_lines++;
    return 0;
}

int bsp_csv_sync(void)
{
    if (g_out) fflush(g_out);
    return 0;
}

int bsp_lora_send(const uint8_t *frame, size_t n)
{
    size_t i;
    printf("LORA ");
    for (i = 0; i < n; ++i) printf("%02x", frame[i]);
    printf("\n");
    g_frames++;
    return 0;
}

uint32_t bsp_rtc_unix(void) { return 1760000000u + g_now / 1000u; }

void bsp_log(const char *msg) { fprintf(stderr, "%s\n", msg); }

int bsp_host_load(const char *csv_path)
{
    FILE *f;
    char line[256];
    if (!csv_path) return -1;
    f = fopen(csv_path, "r");
    if (!f) return -1;
    feed.n = 0;
    while (feed.n < FEED_MAX && fgets(line, sizeof(line), f)) {
        unsigned long t;
        double p0, p1, q;
        if (line[0] == '#' || line[0] == 's') continue;
        if (sscanf(line, "%lu,%lf,%lf,%lf", &t, &p0, &p1, &q) == 4) {
            feed.t_ms[feed.n] = (uint32_t)t;
            feed.p0[feed.n] = p0;
            feed.p1[feed.n] = p1;
            feed.q[feed.n] = q;
            feed.n++;
        }
    }
    fclose(f);
    g_idx = 0;
    return (int)feed.n;
}

int bsp_host_eof(void)
{
    if (feed.n == 0) return 1;
    return g_now >= feed.t_ms[feed.n - 1] ? 1 : 0;
}

void bsp_host_set_out(const char *csv_path)
{
    if (g_out) { fclose(g_out); g_out = NULL; }
    if (csv_path) g_out = fopen(csv_path, "w");
}

void bsp_host_close(void)
{
    if (g_out) { fclose(g_out); g_out = NULL; }
    fprintf(stderr, "host: %lu csv lines, %lu lora frames\n",
            (unsigned long)g_lines, (unsigned long)g_frames);
}
