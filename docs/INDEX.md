# Research documentation index

This is the single navigation path from the repository to the research paper,
software, experiments, figures and reproducibility evidence.

Gate7 v1.1.0 is the published software release. The historical v1.0.0 release and
fixed-mode M8 receipts retain their original identities. Recovered CPU inference
and synthetic qualification do not establish athlete predictive accuracy.

## 0. Flagship paper (M12, owner review pending)

The science-first article, *Modeling Countermovement-Jump Recovery: Biomechanical
Measurement, Neural Architectures, and a Controlled Synthetic Benchmark*, covers CMJ
force-time measurement, mathematical recovery models, the nine original neural
architectures and the public four-model synthetic experiment. It is an unsubmitted
draft. The retrospective reconstruction paper below is its companion.

| Read | File |
| --- | --- |
| Illustrated flagship paper | [full_illustrated_manuscript.pdf](manuscript/v4/full_illustrated_manuscript.pdf) |
| Review edition and supplement | [academic_review_manuscript.pdf](manuscript/v4/academic_review_manuscript.pdf), [technical_supplement.pdf](manuscript/v4/technical_supplement.pdf) |
| Package guide and regeneration | [v4 README](manuscript/v4/README.md) |
| Claims/evidence register, terminology, storyboard | [science/](science/README.md) |

## 1. Research paper (retrospective companion)

The current paper is the V3 illustrated research manuscript, *Retrospective
reconstruction and numerical qualification of historical countermovement-jump
recovery research: An evidence-bounded case study*. It is an **unsubmitted research
draft**. It has not been peer reviewed, submitted to a journal or preprint server,
or assigned a DOI.

| Read | File |
| --- | --- |
| Illustrated research paper (canonical) | [full_illustrated_research_manuscript.pdf](manuscript/v3/full_illustrated_research_manuscript.pdf) |
| Academic review edition (single column, line-numbered) | [academic_review_manuscript.pdf](manuscript/v3/academic_review_manuscript.pdf) |
| Technical supplement | [technical_supplement.pdf](manuscript/v3/technical_supplement.pdf) |
| Reproducible figures Fig1–Fig10 (PDF, SVG, PNG, TIFF) | [figures/](manuscript/v3/figures/) |
| Per-figure quantitative receipts | [figure_receipts/](manuscript/v3/reproducibility/figure_receipts/) |
| Figure and PDF regeneration | [V3 package guide](manuscript/v3/README.md) |
| Force-target terminology note | [force_target_provenance_note.md](manuscript/v3/reports/force_target_provenance_note.md) |
| Data availability and limitations | Paper sections *Limitations and threats to validity* and *Reproducibility and availability* |

The [manuscript editions page](manuscript/README.md) lists the earlier M10 (V2)
export. That package is preserved, checksum-verified historical evidence; it is not
the latest manuscript.

## 2. Software, experiments and methods

| Topic | Reference |
| --- | --- |
| Install, public API, optional inference extra | [Scientific README](../README.rst) |
| Published software release v1.1.0 | [GitHub release](https://github.com/Litju/CMJRecoveryDynamicsBench/releases/tag/v1.1.0), [changelog](../CHANGELOG.md) |
| Public synthetic benchmark (H24/H48/H72, six cells) | [M8 fixed-mode study](M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md), [results receipt](M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json), [reproducibility matrix](M8_REPRODUCIBILITY_MATRIX.md) |
| Recovered neural models M0–M8, repeat qualification, safe loading | [Research API and model loading](RESEARCH_API.md), [inference verification](RES-546_INFERENCE_VERIFICATION.md) |
| Native biomechanics: force, impulse, trial and baseline arithmetic | [Measurement methods](GATE7_NATIVE_MEASUREMENT_V1.md) |
| Native evaluation (H72/D7, four distinct cells) | [Evaluation methods](GATE7_NATIVE_EVALUATION_V1.md), [scientific protocol](GATE7_SCIENTIFIC_EVALUATION_PROTOCOL_V1.md) |
| Dataset authority and admission | [Readiness](GATE7_TARGET_AUTHORITY_AND_DATA_READINESS_V1.md), [preflight](NATIVE_PREFLIGHT_V1.md) |
| Offline execution and rights grants | [Offline study](GATE7_OFFLINE_STUDY_V1.md) |

The public synthetic H24/H48/H72 six-cell experiment and the original native
H72/D7 four-cell evaluation are different experiments with different targets and
evidence authority. Do not compare their scores.

The synthetic force outcome is the **mean concentric-force innovation (N/kg)**: the
baseline-relative change in gross time-mean concentric force per unit body mass,
averaged over three simulated trials per assessment. Frozen receipts keep the
registered evaluation key `relative_peak_mean_force_innovation`, which scores the
generated target `label.relative_mean_concentric_force_innovation`. It is not peak
force and not gravity-adjusted net impulse.

## 3. Interactive companion and operations

| Topic | Reference |
| --- | --- |
| Recovery Observatory (live) | <https://recovery-observatory.vercel.app> |
| Website source, figures and provenance | [Website README](../website/README.md), [science and data](../website/docs/SCIENCE_AND_DATA.md), [model atlas](../website/docs/GATE7_ATLAS.md) |
| Deployment and rollback | [Operations](../website/docs/DEPLOYMENT.md) |
| Accessibility acceptance | [Windows/NVDA status](GATE7_NVDA_ACCEPTANCE_V1.md) |

## 4. Citation and licensing

Cite the software with the repository-root [CITATION.cff](../CITATION.cff)
(version 1.1.0) and the v1.1.0 release. No DOI is assigned. The manuscript is an
unsubmitted draft; cite it, if at all, as an unpublished draft. The website keeps a
separate, historical M8 citation file pinned to its original source commit; it is
provenance for those receipts, not the current software citation. See the
[license](../LICENSE).

## Historical records

The earlier research documents describe their own qualification snapshots; they
are evidence, not claims that every historical limitation has since closed.
Original checkpoint bytes and fitted parameters are not public package data.
No external dataset is needed to build the public presentation.
Historical research filenames and pinned source paths retain their original
identifiers for provenance; the reader-facing navigation labels are descriptive.
