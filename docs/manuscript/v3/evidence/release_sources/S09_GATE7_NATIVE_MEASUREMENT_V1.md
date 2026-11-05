# Gate7-native measurement and basis specification, version 1

Status: authenticated source mathematics and implementation behavior, independently reconstructed with synthetic checks. This specification does not establish empirical measurement authority, exact historical final-split materialization, canonical target crosswalks or permission to evaluate a cohort. The companion `GATE7_NATIVE_DEPENDENCIES_V1.json` records the machine-readable dependency graph. Detailed authenticated-source locators, pins and differential receipts remain private.

## Authority levels

| Level | Established | Remaining boundary |
| --- | --- | --- |
| Mathematical definitions | Gross concentric time-mean force, net concentric impulse, explicit system mass, three-trial criterion, baseline and horizon contracts | The symbols do not authenticate an empirical instrument or dataset. |
| Original implementation | Supplied-event interpolation/trapezoid, scalar aggregation, public-schedule five-value basis and fitted preprocessing behavior were inspected directly in authenticated original source | Source validity is not evidence that an external record used those methods. |
| Historical materialization | Original run-bound split identity is preserved by prior recovery evidence | Exact final invocation, every row's arithmetic lineage and serialization remain unresolved; no historical labels were read or scored here. |
| Empirical measurement | Required signal, event, mass, trial, timestamp and provenance fields are explicit | Instrument calibration, filtering, empirical onset/takeoff detector, mass convention, cohort linkage and permissions require independent steward authority. |

## Native targets and force-time arithmetic

Use upward gross vertical ground-reaction force `Fz(t)` in N, time in seconds, explicit constant accelerated system mass `m > 0` in kg and supplied positive gravity `g` in m/s². The system includes the athlete and any mechanically accelerated attached mass. Do not substitute body mass or infer mass from quiet standing. The original implementation provides a standard gravity constant of 9.80665 m/s², while the direct mechanics function takes gravity explicitly.

For supplied concentric onset `t_co` and takeoff `t_to`, `T = t_to - t_co > 0`:

- `relative_mean_concentric_force = integral(Fz dt) / (m * T)`, N/kg: **gross time mean**, never peak force or net mean force.
- `relative_concentric_net_impulse = integral((Fz - m*g) dt) / m`, m/s: **concentric net impulse** with the same explicit mass.
- Mathematical cross-checks: `J_rel = Δv_COM` and `F_rel = g + J_rel/T`. These identities do not close a canonical outcome crosswalk.

The event contract requires `movement_start < t_co < t_to <= assessment_end`; the scored events must lie inside the supplied force-time domain. The authenticated source does **not** implement empirical event detection from force thresholds or velocity zero crossings: it accepts event times from the caller. Thus no detector threshold or instrument-specific filter can be claimed as source-authorized by this specification.

The original numerical rule accepts finite strictly increasing, potentially nonuniform timestamps. At an exact-sample event, use the original sample once. Otherwise linearly interpolate the boundary force from its two bracketing samples. Retain original samples strictly inside the interval and integrate the closed support `[t_co,t_to]` by sequential composite trapezoids. A bracketing sample beyond takeoff can support interpolation at the event, but its timestamp/value is not included as a separate integration node. The terminal contact force is the supplied/interpolated value at takeoff, not a subsequent airborne value. Net force is subtracted at support nodes before integration. The original velocity cross-check starts its identity coordinate at zero velocity at `t_co`; this arbitrary offset is not an empirical absolute velocity estimate.

The new `native_force_metrics_v1` independently implements only this deterministic arithmetic. A caller still authenticates event detection, full event ordering/domain, signal calibration, protocol metadata and trial validity. Reject nonfinite input, non-increasing timestamps, invalid support, nonpositive mass/gravity and nonfinite numerical output. Additional finite-real and overflow safeguards do not claim historical acceptance behavior.

## Trials, assessments, baseline and labels

The original criterion is the arithmetic mean of exactly **three valid trials** with distinct trial IDs, one assessment identity and one assessment timestamp. Every trial passes signal, event, mechanical and protocol validation; invalid trials are not silently imputed, replaced, dropped or selected by performance. The source uses scalar sums divided by three, not a best-of-three or median criterion. Explicit depth is reference COM position minus bottom COM position in m, nonnegative, with source positions retained; it is not inferred from a velocity-drift proxy.

The baseline is the arithmetic mean of the two latest distinct valid qualifying assessment summaries in the inclusive **24–240-hour pre-origin interval**. The original selector sorts descending by `(assessment_time, assessment_id)`, then keeps the first occurrence of each identity. It skips invalid or internally mismatched assessment records. Tied assessment times therefore have an implementation tie-break, but do not establish that empirical duplicates are independent assessments. The preflight layer must reject ambiguous/contradictory identity records rather than reinterpret them as new assessments.

H72 is nominal 72 h, assessment window **66–78 h**; D7 is nominal 168 h, window **156–180 h**, relative to the registered origin. Both native targets refer to the same assessment/time per query. The four cells remain separate; N/kg and m/s are never pooled. Target selection and all baseline identities must be locked and authenticated; a nominal visit name does not prove its timestamp.

Outputs are additive baseline-relative innovations, in order force then impulse. In authenticated dynamics source, absolute target is evaluated as `(baseline + latent_state) + measurement_error`, while innovation is evaluated separately as `latent_state + measurement_error`; the model output transform is identity. Subtracting serialized absolute and baseline fields is not guaranteed bitwise equal to separately evaluated innovation. No percentage transform or calibrated historical score is implied.

## Five-value basis: closed source construction

This is a **fixed nominal public-schedule basis**, not a fitted physiological dose or an inferred latent state. Original source consumes only each row's `history_exposures`, `known_plan` and `target_time_hours`. Each duration is divided by **100 minutes**, producing dimensionless dose `d_i`. Events are sorted as `(time_hours, dose)` tuples; the original function skips events after target time `T`. No assessment value or target label enters the computation.

The index exposure is already a time-zero entry in the original query-specific `known_plan`. Do not append `index_exposure` separately. The recovered public observation converter follows this convention. The new constructor validates one pre-origin historical exposure, two/three query-specific plans, distinct event times, exactly one matching time-zero plan, nonnegative finite durations and each plan's `known_at_origin=True`. These admission safeguards are stricter than the original arithmetic function, which trusts the supplied schedule. A boolean assertion alone does not prove availability; source snapshots/version timestamps must authenticate it outside this constructor.

For events with `t_i <= T`, define chronological cumulative `C_i = sum_{j<=i} d_j`, `C_0=0`, `h(C)=10*C/(1+C)` with `h(0)=0`, `Δ_i=h(C_i)-h(C_{i-1})`, and `w_tau(i)=exp(-(max(0,T-t_i)/tau)^1)`:

| Position | Name | Exact construction | Unit |
| --- | --- | --- | --- |
| 0 | `w2_fast_duration_weighted` | `sum d_i*w_36(i)` | dimensionless |
| 1 | `w2_slow_duration_weighted` | `sum d_i*w_120(i)` | dimensionless |
| 2 | `w3_total_dose` | `h(C_final)` | dimensionless |
| 3 | `w3_fast_increment_weighted` | `sum Δ_i*w_36(i)` | dimensionless |
| 4 | `w3_slow_increment_weighted` | `sum Δ_i*w_120(i)` | dimensionless |

Constants: fast 36 h, slow 120 h, beta 1, kappa 10, delta 1. Gamma 1 is declared in the original configuration but is **not separately used** by its rational `_w3` arithmetic; this is not an adjustable gamma implementation. Values at target time receive decay weight one. Zero-duration events contribute zero, and an all-zero schedule returns five zeros. Empirical durations and plans must actually exist; no fabricated exposure events or physiological mappings are permitted.

All basis components are computable at origin **if and only if** the complete relevant history, origin duration, future plan snapshots and forecast query are authenticated as known at that origin. Future event execution is not an input. The source's synthetic generator supplies a predetermined plan; it does not prove prospective availability in an empirical archive. The source basis function itself performs no availability or rights checks.

Original preprocessing constructs raw/history/basis arrays from the same ordered input-row list, with no separate key join. The basis matrix is float64 `(N,5)`; history is float64 `(N,4,4)`, oldest to latest; horizon is int64 H72=0/D7=1. Every external row must preserve participant/origin/query/input identity across these tensors. Train-only basis means and sample standard deviations (`ddof=1`) are frozen in each checkpoint configuration; zero training scales become one. Standardize using those frozen statistics, then cast tensors to float32. No cohort fitting is needed or permitted for original preprocessing. M6 validates/preprocesses all five basis values but consumes only the first two; M7 consumes five; M8 consumes five in its nonlinear and linear basis branches. No fitted values are published here.

## Numerical and serialization limits

The mechanics source uses Python float operations, sequential trapezoid accumulation and scalar three-/two-item arithmetic means. The reference model uses NumPy float64 schedule arithmetic and exponentials; transformations cast to float32 only after standardization. Independently authored tests compare analytic signals and a separate sum formulation; the private source-differential check additionally executes isolated original arithmetic on invented inputs only. Cross-platform transcendental bit identity is not claimed; exact differential equality is recorded for the qualified local environment.

The earlier world-generation source declares decimal rounding to nine places and canonical sorted-key compact JSON. The inspected pre-final shadow code converts NumPy scalars to Python floats and serializes JSON without that explicit rounding step. These are **distinct source paths**, neither a verified final-split serialization lineage. This phase does not assign either behavior to every historical Gate7 row, regenerate the historical split, recompute its labels or scores, or resolve the generic canonical force/impulse crosswalks.
