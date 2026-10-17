#ifndef SAMPLER_H
#define SAMPLER_H
#include <stdint.h>
#include <stddef.h>

/* Sampling orchestration for the node.
 *
 * Frozen contract (docs/hardware software review v2.2 section 5 + E9 revision):
 *   submission period 1 s, non-overlapping judgement block 10 s,
 *   pulse coefficient 540 /L, 4-20 mA over 150 ohm,
 *   CUSUM k=0.5 h=26 in thousandths.
 *
 * Why the judgement must be block-wise (E9, simulation/project_review/):
 *   running CUSUM on the 1 s sliding-mean series makes adjacent samples share
 *   90% of their raw data, which breaks the independent-increment assumption
 *   and inflates the threshold by ~57x (measured: 1028 vs 18 for a 5% false
 *   alarm rate). Accumulating once per non-overlapping 10 s block restores the
 *   assumption; the threshold then comes from a target ARL0 instead of an
 *   ad-hoc "max peak x 1.2".
 *
 * Units used across this module:
 *   pressure  int32, 0.01 kPa      (100.00 kPa -> 10000)
 *   flow      int32, 0.001 L/min   (2.922 L/min -> 2922)
 *   residual  int32, thousandths   (z = residual / robust scale)
 */

#define BIN_MS           1000u
#define WINDOW_BINS      10u     /* judgement block length, in 1 s bins */
#define CAL_BINS         16u     /* calibration BLOCKS (= 160 s).
                                  * Was 100 when calibration ran per 1 s bin;
                                  * with block-wise judgement it is 16 blocks,
                                  * matching E9 (calibration blocks 2..17). */

#define FS_DP_CENTI      3500      /* 35.00 kPa differential span  */
#define FS_P1_CENTI      20000     /* 200.00 kPa gauge span        */
#define PULSE_PER_L      540u
#define PULSE_MAX_DELTA  450u      /* kernel limit: window <= 13 s */
#define SAMPLE_OHM       150u
#define I4_MA_MILLI      4000
#define I_SPAN_MILLI     16000

/* k = 0.5, h = 26.0 (thousandths). h comes from E9: target false-alarm rate
 * <= 1% over a 420 s healthy window, zero-failure ARL0 lower bound > 6.2 h.
 * Do NOT revert to 61000 - that value belongs to the overlapping-window
 * variant, which is deprecated. */
#define CUSUM_K_MILLI    500
#define CUSUM_H_MILLI    26000

enum {
    QUALITY_OK = 0,
    QUALITY_OPEN_LOOP,      /* current below 4 mA -> broken wire      */
    QUALITY_SATURATED,      /* differential out of span -> alarm only */
    QUALITY_TIMING,         /* bin late or pulse delta out of range   */
    QUALITY_NOT_READY       /* calibration window not filled yet      */
};

typedef struct {
    uint32_t seq;
    uint32_t unix_ms;
    int32_t  p0_centi, p1_centi, dp_centi;
    int32_t  q_milli;
    uint32_t count10;
    uint8_t  quality;
    int32_t  zq_milli, zr_milli;
    int32_t  sq_milli, sr_milli;
    uint8_t  alarm;
} SampleRow;

/* Health reference exponent.
 * 0 = fix n at 0.5 (orifice flow value). This is the default because the
 *   identifiability study showed the exponent is NOT identifiable inside one
 *   supply regime: the calibration window spans only ~0.34% in P1, and the
 *   regression returns anything from -1.46 to -0.19 depending on noise.
 *   Fixing the physical exponent keeps extrapolation into the fault segment
 *   correct; the level is absorbed by the median ratio calibration.
 * 1 = fit n by log-log regression (only valid when the calibration data spans
 *   several supply regimes, i.e. pressure span >= 20%).
 */
#ifndef SAMPLER_FIT_N
#define SAMPLER_FIT_N 0
#endif

#ifndef SAMPLER_N_FIXED
#define SAMPLER_N_FIXED 0.5
#endif

typedef struct {
    uint8_t  cal_done;
    uint32_t cal_n;
    double   cal_p1[CAL_BINS];
    double   cal_q[CAL_BINS];
    double   cal_rh[CAL_BINS];
    double   n_exp, a_coef, gain, r0, s_q, s_r;

    uint32_t ring[WINDOW_BINS];
    int32_t  p1_hist[WINDOW_BINS];
    int32_t  dp_hist[WINDOW_BINS];
    uint8_t  head, fill;
    uint32_t bin_index;

    int32_t  sq_state, sr_state;
    uint32_t blocks_scored;     /* judgement blocks fed to CUSUM           */
    int32_t  p0_centi, p1_centi, dp_centi, q_milli;
    int32_t  p1_smooth_centi;
    int32_t  dp_smooth_centi;

    uint32_t alarms_leak, alarms_restr, bins_open, bins_sat, bins_timing;
} Sampler;

void sampler_init(Sampler *s);

/* Feed one completed 1 s bin. count is the pulse total inside that bin.
 * Returns 0 on success. */
int  sampler_feed(Sampler *s, uint32_t count, int32_t dp_centi,
                  int32_t p1_centi, uint8_t quality, SampleRow *out);

/* Convert a 12-bit code to millivolts using the internal reference. */
int32_t adc_code_to_mv(uint16_t code, uint16_t vref_code);
/* Millivolts across the sample resistor -> pressure in 0.01 kPa. */
int32_t mv_to_centi_kpa(int32_t mv, int32_t fs_centi);
/* Pulses collected over the 10 s window -> flow in 0.001 L/min. */
int32_t pulses_to_q_milli(uint32_t pulses, uint32_t window_bins);

void sampler_row_csv(const SampleRow *r, char *buf, size_t cap);
const char *sampler_quality_name(uint8_t q);

#endif
