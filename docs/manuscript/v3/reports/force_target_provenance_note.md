# Force-target provenance note (RES-585)

**Reader-facing name:** mean concentric-force innovation, in N/kg.

**Physical quantity.** For each simulated assessment, three concentric-phase trials are generated. Each trial's gross mean force per unit mass is the time average of the vertical force trace over the concentric interval (onset to takeoff). The assessment value is the arithmetic mean of the three trial values. The target is the criterion-assessment value minus the baseline-assessment value at the same horizon. It is **not** peak force and **not** gravity-adjusted net impulse (which is `(mean force − g)·T`, in m/s).

**Legacy registered identifier.** The registered evaluation cell is `relative_peak_mean_force_innovation` (`OutcomeVariable.RELATIVE_PEAK_MEAN_FORCE_INNOVATION`). That name is retained unchanged in the frozen results, score-cell keys and metrics so historical numbers remain addressable. The generated target it scores is `label.relative_mean_concentric_force_innovation`.

| Layer | Identifier | Source (immutable `401f87aa`) |
|---|---|---|
| Registered cell | `H{24,48,72}/relative_peak_mean_force_innovation` | `docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json` (`protocol.registered_cells`) |
| Outcome→target map | `OUTCOME_TARGETS[0]` | `src/cmj_recovery_dynamics/studies/fixed_mode_reference_study.py` |
| Generated target | `label.relative_mean_concentric_force_innovation` (N/kg) | `src/cmj_recovery_dynamics/reproduction/single_exposure.py` (`TARGET_FIELDS`, `TARGET_UNITS`) |
| Force realization | `ConcentricTrial.mean_force_n_per_kg`, `PhaseConsistentAssessment.force_mean` | `src/cmj_recovery_dynamics/observations/phase_consistent_force_impulse.py` |
| Innovation | `criterion.force_mean − baseline.force_mean` | `single_exposure.py` (`_observed_episode`) |

Regression coverage: `tests/test_force_target_semantics.py` checks the mapping, the preserved legacy identifier in the frozen results, the mean/peak/net-impulse distinction on a realized trial, and the three-trial mean and criterion-minus-baseline arithmetic. No generated observation, selected model, checkpoint, evaluation key, metric or historical numerical result is altered.

This synthetic H24/H48/H72 six-cell benchmark remains separate from the native H72/D7 four-cell contract.
