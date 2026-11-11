# Contract and terminology

## Study inventory (what exists, and what it can support)

| Id | Study | Cells | Models | Status |
|---|---|---|---|---|
| S-A | Native biomechanics contract | H72 and D7 x (force N/kg, impulse m/s): four physical-unit cells | Zero-innovation primary comparator; training-only constant option | Contract, analysis code and an invented-fixture rehearsal. No cohort evaluated; no scores. |
| S-B | Public fixed-mode reference study | H24/H48/H72 x two outcomes: six normalized cells | Zero, training mean, ridge, structured (+ ablations, nested subsets) | Executed on synthetic data; source of every quantitative result in the paper. |
| S-C | Original architectures M0-M8 | Native H72/D7 targets | Nine families x two repeats = 18 routes | Architecture contracts and CPU/GPU numerical qualification. No comparable public performance experiment. |
| S-D | Historical studies | Various | Various | Reconstruction and provenance; supporting material only. |

## Formulas (units checked against the generator source)

Let `Fz(t)` be vertical ground-reaction force (N), `m` the accelerated mass (kg), `g = 9.80665 m/s^2`,
`t_co` concentric onset, `t_to` takeoff, `T = t_to - t_co`.

- Gross mean concentric force per mass: `F_bar = (1/(m T)) * integral_{t_co}^{t_to} Fz dt` [N/kg]. Gross: gravity is not subtracted.
- Concentric net impulse per mass: `J = (1/m) * integral (Fz - m g) dt = (F_bar - g) T` [m/s] (equals the center-of-mass velocity change over the concentric phase).
- Peak force is a different quantity: `max Fz / m`. For the synthetic half-sine net-force pulse `peak = g + (pi/2)(F_bar - g)`; this relation belongs to the synthetic trace shape only.
- Trial duration in the generator: `T = J / (F_bar - g)`, supported on 0.075-0.80 s; each trial is a 65-node trace integrated with composite trapezoids.
- Assessment value: arithmetic mean of three trials (`A = (1/3) sum_k F_bar,k`).
- Baseline-relative innovation: `Delta F = A_criterion - A_baseline` [N/kg]; `Delta J = J_criterion - J_baseline` [m/s]. Additive, never percentage, never pooled across units.
- Synthetic response: `A_criterion_truth = A_baseline_truth * (1 + r(tau) + e)`, `r(tau) = -a_f exp(-tau/24 h) - a_s exp(-tau/84 h)`; amplitudes bounded (`a_f` 0.01-0.08, `a_s` 0-0.08) and driven by exposure axes, participant sensitivities and camp offsets; `e` is bounded discrepancy.
- Normalized RMSE per cell: `RMSE / SD_truth` (population SD); six-cell score is the equal-weight mean.

## Required terminology

| Use | Do not use |
|---|---|
| mean concentric-force innovation (N/kg); legacy key `relative_peak_mean_force_innovation` | "peak mean force", "peak force innovation" |
| net impulse innovation (m/s) | "impulse" without net/baseline-relative qualifier |
| fixed mathematical response modes (24 h, 84 h) of the synthetic generator | "recovery time constants", "physiological timescales" |
| original neural architecture family M0-M8; evaluated reference model | "the models" without saying which set |
| synthetic NRMSE; research progress | "accuracy", "skill" without "synthetic" |
| three independently seeded roots from one generator | "independent datasets", "replication" |
| recorded camp-bootstrap interval vs the zero baseline | "significant", "p-value", "confidence in ridge > structured" |

Two sets of constants must not be merged: the generator's response modes (24 h, 84 h) and the
architecture-side five-value public-schedule basis (36 h, 120 h decays, saturating total dose).

## Model-family versus reference-model guard

Every figure, table, sentence and web component names one of two sets. A mechanical check
(`tests/test_science_foundation.py`) forbids NRMSE values on M0-M8 rows of the register and
requires the four reference-model values to equal the receipt. Downstream builds repeat that
check on their own text.
