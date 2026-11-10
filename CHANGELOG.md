# Changelog

## Unreleased — documentation and website only

No Python package code, release artifact or scientific result changes.

- Documentation now has one path to the current V3 research paper
  (`docs/manuscript/v3/full_illustrated_research_manuscript.pdf`), an unsubmitted
  research draft. The M10 (V2) export is labeled historical evidence.
- Reader-facing force-outcome wording is *mean concentric-force innovation (N/kg)*;
  the registered key `relative_peak_mean_force_innovation` is unchanged.
- Current software citation guidance points to the root `CITATION.cff` (1.1.0); the
  website's historical M8 citation copy stays pinned to its source commit.

## 1.1.0 — 2026-11-04

This release packages the Gate7 engineering interfaces integrated into `main`.
It does not retrain models, change scientific results, or alter the historical
`v1.0.0` release. The matching annotated tag and public artifacts are published
on the [GitHub release page](https://github.com/Litju/CMJRecoveryDynamicsBench/releases/tag/v1.1.0).

### Included

- Recovery Observatory Gate7 research atlas with 18 route contracts, analytical
  force-time mechanics, native windows, guided chapters and pinned public source
  hashes; navigable research documentation and figure regeneration guide.


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

- Recovered CPU inference verifies execution contracts; it is not proof of
  predictive accuracy. This software has no established human-athlete predictive
  validity, clinical utility, or production readiness.
- Original historical results and newly generated synthetic results have different
  evidence authority. The public M8 six-cell NRMSE comparison is a historical
  synthetic result and is not a Gate7-native four-cell score.
- The public synthetic rich-history reproduction retains the documented row-count
  differences: training 15,134 vs 15,182 and validation 3,799 vs 3,795. These are
  not silently reconciled or presented as historical score replay.
- Model checkpoints, private hash pins, restricted observations, and private
  execution evidence are not included. A package installation does not authorize
  checkpoint use, empirical scoring, or disclosure.
- CPU-source reproducibility is distinct from historical CUDA replay. M4–M8 remain
  outside their recorded historical CUDA tolerances; the discrepancies remain
  unresolved and the criteria are unchanged.
- The Windows/NVDA manual acceptance remains
  `SCREEN_READER_ACCEPTANCE_PENDING` until a qualified session is completed.
- The `v1.0.0` release remains a distinct historical publication. No PyPI,
  Zenodo, DOI, or manual Vercel production promotion is part of this release.
- The Recovery Observatory is a separately deployed static website. Python release
  publication does not itself deploy or promote the site.

See `README.rst` for installation and supported entrypoints.
