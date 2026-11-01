#include "sampler.h"
#include <math.h>
#include <string.h>
#include <stdio.h>

/* ---------------- small statistics helpers ---------------- */

static void copy_sort(double *dst, const double *src, uint32_t n)
{
    uint32_t i, j;
    for (i = 0; i < n; ++i) dst[i] = src[i];
    for (i = 1; i < n; ++i) {
        double key = dst[i];
        j = i;
        while (j > 0 && dst[j - 1] > key) { dst[j] = dst[j - 1]; --j; }
        dst[j] = key;
    }
}

static double median_sorted(const double *sorted, uint32_t n)
{
    if (n == 0) return 0.0;
    if (n % 2u == 1u) return sorted[n / 2u];
    return 0.5 * (sorted[n / 2u - 1u] + sorted[n / 2u]);
}

static double mad_scale(const double *x, uint32_t n, double floor_value)
{
    double sorted[CAL_BINS];
    double absdev[CAL_BINS];
    double med, dev, s;
    uint32_t i;
    if (n == 0 || n > CAL_BINS) return floor_value;

    copy_sort(sorted, x, n);
    med = median_sorted(sorted, n);
    for (i = 0; i < n; ++i) {
        dev = x[i] - med;
        absdev[i] = (dev < 0.0) ? -dev : dev;
    }
    copy_sort(sorted, absdev, n);
    s = 1.4826 * median_sorted(sorted, n);
    return (s > floor_value) ? s : floor_value;
}

/* ---------------- unit conversion ---------------- */

int32_t adc_code_to_mv(uint16_t code, uint16_t vref_code)
{
    if (vref_code == 0u) return -1;
    /* VDDA = 1200 mV * 4095 / vref_code ; code -> mV cancels 4095 */
    return (int32_t)(((uint32_t)code * 1200u) / (uint32_t)vref_code);
}

int32_t mv_to_centi_kpa(int32_t mv, int32_t fs_centi)
{
    /* mA_milli = mv * 1000 / 150 = mv * 20 / 3  */
    int32_t ma_milli = (int32_t)(((int64_t)mv * 20) / 3);
    if (ma_milli < I4_MA_MILLI - 200) return -1;          /* open loop */
    if (ma_milli > I4_MA_MILLI + I_SPAN_MILLI + 2000) return -2;  /* over range */
    return (int32_t)(((int64_t)(ma_milli - I4_MA_MILLI) * fs_centi) / I_SPAN_MILLI);
}

int32_t pulses_to_q_milli(uint32_t pulses, uint32_t window_bins)
{
    /* L/min = pulses / 540 * 60 / window_seconds -> 0.001 L/min */
    uint32_t secs = window_bins * (BIN_MS / 1000u);
    if (secs == 0u) return 0;
    return (int32_t)(((uint64_t)pulses * 60000u) / ((uint64_t)PULSE_PER_L * secs));
}

/* ---------------- sampler ---------------- */

void sampler_init(Sampler *s)
{
    if (!s) return;
    memset(s, 0, sizeof(*s));
    s->n_exp = 0.5;
    s->a_coef = 1.0;
    s->gain = 1.0;
    s->s_q = 1.0;
    s->s_r = 1.0;
}

static void calibrate(Sampler *s)
{
    double eq[CAL_BINS], er[CAL_BINS], ratio[CAL_BINS], sorted[CAL_BINS];
    uint32_t i, n = s->cal_n;

#if SAMPLER_FIT_N
    {
        double sx = 0.0, sy = 0.0, sxx = 0.0, sxy = 0.0, xbar, ybar, den;
        for (i = 0; i < n; ++i) {
            double x = log(s->cal_p1[i] / 100.0);
            double y = log(s->cal_q[i]);
            sx += x; sy += y; sxx += x * x; sxy += x * y;
        }
        xbar = sx / (double)n;
        ybar = sy / (double)n;
        den = sxx - (double)n * xbar * xbar;
        s->n_exp = (den > 1e-12) ? (sxy - (double)n * xbar * ybar) / den
                                 : SAMPLER_N_FIXED;
    }
#else
    s->n_exp = SAMPLER_N_FIXED;
#endif

    /* level from the median ratio, so the gain correction stays 1 by
       construction and a wrong exponent cannot be compensated by a */
    for (i = 0; i < n; ++i) {
        double base = pow(s->cal_p1[i] / 100.0, s->n_exp);
        ratio[i] = (base > 0.0) ? s->cal_q[i] / base : 1.0;
    }
    copy_sort(sorted, ratio, n);
    s->a_coef = median_sorted(sorted, n);
    if (s->a_coef < 1e-9) s->a_coef = 1.0;
    s->gain = 1.0;

    copy_sort(sorted, s->cal_rh, n);
    s->r0 = median_sorted(sorted, n);

    for (i = 0; i < n; ++i) {
        double qref = s->a_coef * pow(s->cal_p1[i] / 100.0, s->n_exp);
        eq[i] = (qref > 0.0) ? s->cal_q[i] / qref - 1.0 : 0.0;
        er[i] = s->cal_rh[i] - s->r0;
    }
    s->s_q = mad_scale(eq, n, 1e-5);
    s->s_r = mad_scale(er, n, 1e-4);
    s->cal_done = 1u;
}

int sampler_feed(Sampler *s, uint32_t count, int32_t dp_centi,
                 int32_t p1_centi, uint8_t quality, SampleRow *out)
{
    uint32_t i, sum = 0;
    double q_lpm, p1_kpa, dp_kpa, qref, eq, er, zq, zr;
    uint8_t block_edge = 0u;

    if (!s || !out) return -1;
    memset(out, 0, sizeof(*out));

    out->seq = s->bin_index;
    out->dp_centi = dp_centi;
    out->p1_centi = p1_centi;
    out->p0_centi = p1_centi + dp_centi;
    out->quality = quality;

    if (quality == QUALITY_OPEN_LOOP) s->bins_open++;
    else if (quality == QUALITY_SATURATED) s->bins_sat++;
    else if (quality == QUALITY_TIMING) s->bins_timing++;

    if (count > PULSE_MAX_DELTA) quality = QUALITY_TIMING;

    s->ring[s->head] = count;
    s->p1_hist[s->head] = p1_centi;
    s->dp_hist[s->head] = dp_centi;
    s->head = (uint8_t)((s->head + 1u) % WINDOW_BINS);
    if (s->fill < WINDOW_BINS) s->fill++;
    s->bin_index++;

    /* Block edge: the judgement (and the calibration sample) is taken once per
       non-overlapping WINDOW_BINS block. At this instant the sliding ring holds
       exactly the last 10 bins, i.e. one complete block - so the smoothed p1
       and dp are block means, not overlapping means. */
    block_edge = (s->bin_index % WINDOW_BINS) == 0u;

    {
        int64_t p1_acc = 0, dp_acc = 0;
        for (i = 0; i < s->fill; ++i) {
            sum += s->ring[i];
            p1_acc += s->p1_hist[i];
            dp_acc += s->dp_hist[i];
        }
        /* the health reference is evaluated on smoothed values, never on the
           raw sample: noise on p1 attenuates the fitted exponent badly */
        s->p1_smooth_centi = (int32_t)(p1_acc / (int64_t)s->fill);
        s->dp_smooth_centi = (int32_t)(dp_acc / (int64_t)s->fill);
    }
    out->count10 = sum;
    s->dp_centi = dp_centi;
    s->p1_centi = p1_centi;
    s->p0_centi = out->p0_centi;

    if (s->fill < WINDOW_BINS) {
        out->quality = QUALITY_NOT_READY;
        return 0;
    }

    s->q_milli = pulses_to_q_milli(sum, WINDOW_BINS);
    out->q_milli = s->q_milli;

    q_lpm = (double)s->q_milli / 1000.0;
    p1_kpa = (double)s->p1_smooth_centi / 100.0;
    dp_kpa = (double)s->dp_smooth_centi / 100.0;

    if (q_lpm <= 0.01 || p1_kpa <= 1.0) {
        out->quality = QUALITY_TIMING;
        return 0;
    }

    if (!s->cal_done) {
        if (block_edge) {
            double rh = dp_kpa / (q_lpm * q_lpm);
            if (s->cal_n < CAL_BINS) {
                s->cal_p1[s->cal_n] = p1_kpa;
                s->cal_q[s->cal_n] = q_lpm;
                s->cal_rh[s->cal_n] = rh;
                s->cal_n++;
            }
        }
        if (s->cal_n >= CAL_BINS) calibrate(s);
        else {
            out->quality = QUALITY_NOT_READY;
            return 0;
        }
    }

    qref = s->a_coef * pow(p1_kpa / 100.0, s->n_exp);
    eq = (qref > 0.0) ? q_lpm / (s->gain * qref) - 1.0 : 0.0;
    er = dp_kpa / (q_lpm * q_lpm) - s->r0;
    zq = eq / s->s_q;
    zr = er / s->s_r;

    out->zq_milli = (int32_t)(zq * 1000.0);
    out->zr_milli = (int32_t)(zr * 1000.0);

    /* CUSUM accumulates on block edges only. Doing it every 1 s bin would feed
       the detector 10 overlapping copies of the same data and require a ~57x
       larger threshold; see E9 and the header comment. */
    if (quality == QUALITY_OK && block_edge) {
        s->sq_state += out->zq_milli - CUSUM_K_MILLI;
        if (s->sq_state < 0) s->sq_state = 0;
        s->sr_state += out->zr_milli - CUSUM_K_MILLI;
        if (s->sr_state < 0) s->sr_state = 0;
        s->blocks_scored++;
    }
    out->sq_milli = s->sq_state;
    out->sr_milli = s->sr_state;

    if (s->sq_state > CUSUM_H_MILLI && s->sr_state > CUSUM_H_MILLI) out->alarm = 3;
    else if (s->sq_state > CUSUM_H_MILLI) { out->alarm = 1; s->alarms_leak++; }
    else if (s->sr_state > CUSUM_H_MILLI) { out->alarm = 2; s->alarms_restr++; }

    return 0;
}

void sampler_row_csv(const SampleRow *r, char *buf, size_t cap)
{
    if (!r || !buf || cap == 0) return;
    snprintf(buf, cap,
             "%lu,%lu,%ld,%ld,%ld,%ld,%lu,%u,%d,%d,%d,%u",
             (unsigned long)r->seq, (unsigned long)r->unix_ms,
             (long)r->p0_centi, (long)r->p1_centi, (long)r->dp_centi,
             (long)r->q_milli, (unsigned long)r->count10,
             (unsigned)r->quality,
             (int)r->zq_milli, (int)r->zr_milli,
             (int)r->sq_milli, (unsigned)r->alarm);
}

const char *sampler_quality_name(uint8_t q)
{
    switch (q) {
    case QUALITY_OK:        return "ok";
    case QUALITY_OPEN_LOOP: return "open_loop";
    case QUALITY_SATURATED: return "saturated";
    case QUALITY_TIMING:    return "timing";
    default:                return "not_ready";
    }
}
