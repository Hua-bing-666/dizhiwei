"""Ideal polling bounds, not diagnosis validation, physical data or energy estimates.

A detectable threshold crossing occurs at a random phase of a periodic monitor.
The monitor observes only at its own scheduled instants. Reference event timing
is used for evaluation, never to advance the monitor. No noise, conversion time,
flow-window lag, classification persistence, or radio delay is modeled here.
"""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'simulation' / 'event_monitoring_review'
PERIODS_S = [1, 5, 10, 30, 60, 600]
PHASE_COUNT = 1200
PULSE_DURATIONS_S = [1, 5, 20, 60]
DEADLINES_S = [30, 60]


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for period in PERIODS_S:
        # Midpoint quadrature of a uniform phase; excludes endpoint ambiguities.
        phases = [(i + .5) * period / PHASE_COUNT for i in range(PHASE_COUNT)]
        waits = [period - phase for phase in phases]
        row = {
            'monitor_period_s': period,
            'mean_poll_wait_s': sum(waits) / len(waits),
            'maximum_sampled_wait_s': max(waits),
            'worst_case_wait_supremum_s': period,
        }
        for duration in PULSE_DURATIONS_S:
            fraction = sum(wait < duration for wait in waits) / len(waits)
            ideal = min(1., duration / period)
            assert abs(fraction - ideal) <= 1 / PHASE_COUNT + 1e-12
            row[f'ideal_transient_seen_fraction_duration_{duration}s'] = fraction
        for deadline in DEADLINES_S:
            fraction = sum(wait <= deadline for wait in waits) / len(waits)
            ideal = min(1., deadline / period)
            assert abs(fraction - ideal) <= 1 / PHASE_COUNT + 1e-12
            row[f'ideal_persistent_seen_by_{deadline}s_fraction'] = fraction
        assert abs(row['mean_poll_wait_s'] - period / 2) < 1e-9
        rows.append(row)
    with (OUT / 'ideal_polling_bounds.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    report = {
        'date': '2026-10-05',
        'classification': 'ideal_periodic_monitoring_phase_analysis',
        'physical_validation': False,
        'diagnosis_accuracy_evaluated': False,
        'energy_evaluated': False,
        'random_data': False,
        'phase_quadrature_points_per_period': PHASE_COUNT,
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'assumptions': [
            'threshold crossing is immediately detectable if observed',
            'event start phase is uniform within a monitoring period',
            'monitoring instants are fixed and do not use reference event knowledge',
            'persistent change remains detectable; finite transient returns to baseline',
            'processing, confirmation, sensor settling, noise, rolling flow window and radio delay omitted',
        ],
        'interpretation': [
            'mean monitoring wait is T/2; supremum is T',
            'finite transient seen probability is min(1, duration/T) under these ideal assumptions',
            'persistent change observed within L seconds has probability min(1, L/T)',
            'a missed transient is not equivalent to an eventually observed persistent leak',
            'these results do not measure field faults or prove a particular adaptive strategy is superior',
        ],
        'formula_agreement_check': 'passed',
        'rows': rows,
    }
    (OUT / 'ideal_polling_bounds.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for row in rows:
        print(f"T={row['monitor_period_s']:3}s: mean wait={row['mean_poll_wait_s']:6.1f}s; "
              f"5s pulse seen={row['ideal_transient_seen_fraction_duration_5s']:.3f}; "
              f"persistent seen by 60s={row['ideal_persistent_seen_by_60s_fraction']:.3f}")
    print('Analytical agreement passed; ideal timing only, no physical diagnosis or energy claim.')


if __name__ == '__main__':
    run()
