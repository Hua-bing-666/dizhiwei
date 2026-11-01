#ifndef BSP_H
#define BSP_H
#include <stdint.h>
#include <stddef.h>

/* Board support layer for the DripGuard node.
 *
 * Two implementations share this header:
 *   bsp_host.c   - replay on the PC, used to verify the whole chain today
 *   bsp_stm32.c  - real target, compiled against STM32F1 HAL
 *
 * The contract follows docs/hardware_software review v2.2:
 *   1 s submission period, 10 s judgement window, transmitters powered only
 *   inside the sampling slot, high-side switch, ADC never read while the
 *   24 V rail is off.
 */

int      bsp_init(void);
uint32_t bsp_now_ms(void);
void     bsp_sleep_ms(uint32_t ms);

/* 24 V transmitter rail. High-side switch; on before ADC, off after. */
void bsp_24v_set(int on);

/* Two analogue channels plus the internal reference, after 16x oversampling.
 * Returns 0 on success, non-zero if the conversion is not trustworthy. */
int  bsp_adc_read(uint16_t *dp_code, uint16_t *p1_code, uint16_t *vref_code);

/* Pulses accumulated since the previous call. The counter must keep running
 * while the core sleeps, which is why STOP mode is not allowed. */
uint32_t bsp_pulse_take(void);

/* Storage. One line = one completed 1 s bin. */
int  bsp_csv_line(const char *line);
int  bsp_csv_sync(void);

/* Radio. Frame is already encoded by protocol_v2_codec. */
int  bsp_lora_send(const uint8_t *frame, size_t n);

/* Wall clock, unix seconds. 0 when unavailable. */
uint32_t bsp_rtc_unix(void);

void bsp_log(const char *msg);

/* Host-only entry points. Not present on the target build. */
#ifdef BSP_HOST
int  bsp_host_load(const char *csv_path);
int  bsp_host_eof(void);
void bsp_host_set_out(const char *csv_path);
void bsp_host_close(void);
#endif

#endif
