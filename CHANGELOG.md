# Changelog

## 1.1.0 — release candidate (not yet published)

This candidate packages the Gate7 engineering interfaces already integrated into
`main`. It changes release metadata and documentation; it does not retrain models,
change scientific results, or alter the historical `v1.0.0` release.

### Included

- Synthetic benchmark generation and reproducibility interfaces, public model and
  experiment lineage, native measurement mechanics, observation/projection
  contracts, and statistical evaluation with a synthetic-only rehearsal.
- CPU inference interfaces for the recovered Gate7 M0–M8 routes, with two repeats
  per model. The optional `inference` extra installs PyTorch (`torch>=2.6`).
- Safe, CPU-only checkpoint loading that requires independently authenticated
  config and checkpoint SHA-256 pins and uses weights-only deserialization.
- The offline `execute_native_study` API, which requires separate authorization and
  operator-provided grants for every model route.
- Public scientific documentation and limitations, with a discoverable list of
  module entrypoints in `README.rst`.
- The build backend minimum is raised to `setuptools>=84.1.0` following the
  dependency audit.

### Release boundary and limitations

- Model checkpoints, private hash pins, restricted observations, and private
  execution evidence are not included. A package installation does not authorize
  checkpoint use, empirical scoring, or disclosure.
- Synthetic fixtures and engineering qualification are not empirical athlete
  validation and do not establish human-athlete predictive validity, clinical
  utility, or production readiness. Historical results retain their original
  identities and limitations.
- CPU-source reproducibility is distinct from historical CUDA replay. M4–M8 remain
  outside their recorded historical CUDA tolerances; those criteria are unchanged.
- The Windows/NVDA manual acceptance remains
  `SCREEN_READER_ACCEPTANCE_PENDING` until a qualified session is completed.
- The official `v1.0.0` GitHub release remains the current published release. This
  candidate is not a publication, DOI, tag, or production deployment.

See `README.rst` for installation and supported entrypoints.
