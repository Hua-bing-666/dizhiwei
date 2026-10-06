#ifndef INTEGER_DIAGNOSIS_H
#define INTEGER_DIAGNOSIS_H
#include <stdint.h>
#include <stddef.h>
#define DIAG_POINTS 381u
#define DIAG_MISSING INT32_MIN
#define DIAG_MAX_DELTA 450u
/* Configuration is registered before monitoring; health approval is independent. */
typedef struct {
    uint32_t predicted_micro[DIAG_POINTS];
    int32_t r0_micro;
    uint32_t main_leak_micro, main_restriction_micro;
    uint32_t rapid_leak_micro, rapid_restriction_micro;
    uint8_t numeric, approved, rapid_available;
} DiagConfig;
typedef struct { uint32_t count; int32_t p0, p1; uint8_t issue; } DiagSample;
typedef struct {
    DiagSample ring[11];
    const DiagConfig *config;
    uint32_t last_t, last_count;
    uint8_t started, size, head, pressure_run, counter_run;
    uint8_t pending, confirmed, active, rapid_pending, rapid_active, last_status;
} DiagState;
typedef struct {
    uint8_t status, pattern, rapid_valid, rapid_active, rapid_positive;
    int8_t main_label;
    uint8_t event_mask, quality_reason;
    int32_t flow_milli;
} DiagOutput;
int diag_init(DiagState *state, const DiagConfig *config);
/* t is a completed-bin index: wire sample_seq=t+1, end_ms=(t+1)*1000.
 * issue: 0 valid, 1 missing/nonfinite, 2 raw range failure, 3 timing failure.
 * Invalid sequence/representation/count rate is rejected without state change. */
int diag_update(DiagState *state, uint32_t t, uint32_t count,
                int32_t p0, int32_t p1, uint8_t issue, DiagOutput *out);
/* Helpers require an initialized numeric config, n=3/10, accepted sums
 * and domain-valid positive flow; use diag_update for external inputs. */
uint32_t diag_predict(const DiagConfig *config, int32_t p1_sum, uint32_t window);
uint8_t diag_flags(const DiagConfig *config, int32_t p0_sum, int32_t p1_sum,
                   uint32_t delta, uint32_t window, int rapid);
/* Capacity schema only: this does not implement the recovery/admission queue. */
typedef struct {
    uint8_t wire[64];
    uint32_t born_ms, last_ms, next_ms, source_seq;
    uint8_t length, initial_attempts, recovery_attempts, state;
} CandidateSlot;
typedef struct {
    CandidateSlot live[16], probe[1], history[64];
    uint8_t last_telemetry[64], snapshot[35], metadata[64];
} CandidateStorage;
#endif
