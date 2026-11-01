/* Target implementation of bsp.h for STM32F103 (LQFP48).
 *
 * STATUS: skeleton written against the STM32F1 HAL API. It has NOT been
 * compiled on the target toolchain yet - no board, no toolchain installed.
 * Every function below is the exact place where a driver has to be proven on
 * hardware. Do not merge into a release claim before a real build passes.
 *
 * Pin map (docs/hardware software review v2.2 section H6):
 *   PA0  ADC12_IN0  differential pressure, 150 ohm sample
 *   PA1  ADC12_IN1  gauge pressure P1
 *   PA4-7 SPI1      microSD
 *   PA9/10 USART1   E220-400T22D
 *   PB6  TIM4_CH1   flow meter pulses (external clock)
 *   PB8/9 I2C1 remap DS3231
 *   PB0  GPIO       24 V high-side switch / XL6009 EN
 *   PA13/14 SWD
 */
#include "bsp.h"

#ifdef STM32F103xB

#include "stm32f1xx_hal.h"

#define PIN_24V_GPIO GPIOB
#define PIN_24V_PIN  GPIO_PIN_0

static ADC_HandleTypeDef hadc1;
static TIM_HandleTypeDef htim4;
static UART_HandleTypeDef huart1;
static SPI_HandleTypeDef hspi1;
static uint32_t g_tick = 0;

void SysTick_Handler(void)
{
    HAL_IncTick();
    g_tick++;
}

int bsp_init(void)
{
    GPIO_InitTypeDef gpio;
    ADC_ChannelConfTypeDef ch;

    HAL_Init();
    SystemClock_Config();          /* provided by the board support package */

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_ADC1_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();
    __HAL_RCC_SPI1_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();

    /* 24 V rail, high side. Default off. */
    gpio.Pin = PIN_24V_PIN;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(PIN_24V_GPIO, &gpio);
    HAL_GPIO_WritePin(PIN_24V_GPIO, PIN_24V_PIN, GPIO_PIN_RESET);

    /* PA0 / PA1 analogue */
    gpio.Pin = GPIO_PIN_0 | GPIO_PIN_1;
    gpio.Mode = GPIO_MODE_ANALOG;
    HAL_GPIO_Init(GPIOA, &gpio);

    /* PB6 = TIM4_CH1 external clock source */
    gpio.Pin = GPIO_PIN_6;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOB, &gpio);

    hadc1.Instance = ADC1;
    hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
    hadc1.Init.ContinuousConvMode = DISABLE;
    hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    hadc1.Init.NbrOfConversion = 1;
    HAL_ADC_Init(&hadc1);

    ch.Channel = ADC_CHANNEL_0;
    ch.Rank = ADC_REGULAR_RANK_1;
    ch.SamplingTime = ADC_SAMPLETIME_28CYCLES_5;
    HAL_ADC_ConfigChannel(&hadc1, &ch);

    /* TIM4 counts external pulses on CH1; the counter must never stop. */
    htim4.Instance = TIM4;
    htim4.Init.Prescaler = 0;
    htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim4.Init.Period = 0xFFFF;
    htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    HAL_TIM_IC_Init(&htim4);
    HAL_TIM_IC_ConfigChannel(&htim4, &(TIM_IC_InitTypeDef){
        .ICPolarity = TIM_INPUTCHANNELPOLARITY_RISING,
        .ICSelection = TIM_ICSELECTION_DIRECTTI,
        .ICPrescaler = TIM_ICPSC_DIV1,
        .ICFilter = 4
    }, TIM_CHANNEL_1);
    HAL_TIM_IC_Start(&htim4, TIM_CHANNEL_1);

    return 0;
}

uint32_t bsp_now_ms(void) { return HAL_GetTick(); }

void bsp_sleep_ms(uint32_t ms)
{
    uint32_t start = HAL_GetTick();
    /* SLEEP, never STOP: TIM4 must keep counting flow pulses. */
    while (HAL_GetTick() - start < ms) {
        __WFI();
    }
}

void bsp_24v_set(int on)
{
    HAL_GPIO_WritePin(PIN_24V_GPIO, PIN_24V_PIN, on ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

static uint16_t adc_one(uint32_t channel)
{
    ADC_ChannelConfTypeDef ch;
    uint32_t acc = 0, i;
    ch.Channel = channel;
    ch.Rank = ADC_REGULAR_RANK_1;
    ch.SamplingTime = ADC_SAMPLETIME_28CYCLES_5;
    HAL_ADC_ConfigChannel(&hadc1, &ch);
    for (i = 0; i < 16u; ++i) {          /* 16x oversampling, +2 bits */
        HAL_ADC_Start(&hadc1);
        if (HAL_ADC_PollForConversion(&hadc1, 10u) == HAL_OK) {
            acc += HAL_ADC_GetValue(&hadc1);
        }
    }
    return (uint16_t)((acc + 8u) / 16u);
}

int bsp_adc_read(uint16_t *dp_code, uint16_t *p1_code, uint16_t *vref_code)
{
    if (!dp_code || !p1_code || !vref_code) return -1;
    *dp_code  = adc_one(ADC_CHANNEL_0);
    *p1_code  = adc_one(ADC_CHANNEL_1);
    *vref_code = adc_one(ADC_CHANNEL_VREFINT);
    return 0;
}

uint32_t bsp_pulse_take(void)
{
    uint32_t v = (uint32_t)__HAL_TIM_GET_COUNTER(&htim4);
    __HAL_TIM_SET_COUNTER(&htim4, 0);
    return v;
}

int bsp_csv_line(const char *line)
{
    /* FatFs: f_puts into the open log file. See the TODO list in the review. */
    (void)line;
    return 0;
}

int bsp_csv_sync(void)
{
    /* f_sync every N lines so a power cut cannot destroy the filesystem. */
    return 0;
}

int bsp_lora_send(const uint8_t *frame, size_t n)
{
    if (n == 0) return 0;
    return HAL_UART_Transmit(&huart1, (uint8_t *)frame, (uint16_t)n, 200u) == HAL_OK ? 0 : -1;
}

uint32_t bsp_rtc_unix(void) { return 0; }   /* DS3231 driver pending */

void bsp_log(const char *msg) { (void)msg; }

#else

/* Compiled out on the host build. Keeps the file present for the target build. */
#include <stddef.h>
int bsp_init(void) { return -1; }
unsigned long bsp_now_ms_stub(void);
unsigned long bsp_now_ms_stub(void) { return 0; }
void bsp_24v_set(int on) { (void)on; }
int bsp_adc_read(unsigned short *a, unsigned short *b, unsigned short *c)
{ (void)a; (void)b; (void)c; return -1; }
unsigned long bsp_pulse_take(void) { return 0; }
int bsp_csv_line(const char *l) { (void)l; return -1; }
int bsp_csv_sync(void) { return -1; }
int bsp_lora_send(const unsigned char *f, size_t n) { (void)f; (void)n; return -1; }
unsigned long bsp_rtc_unix(void) { return 0; }
void bsp_log(const char *m) { (void)m; }
void bsp_sleep_ms(unsigned long ms) { (void)ms; }

#endif
