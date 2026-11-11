# Scientific positioning: CMJ recovery modeling (M12 foundation)

Status: evidence reconciliation for the science-first flagship paper and Recovery
Observatory. No new data, fitting, scoring or release. Everything quantitative traces to
[`claims_evidence_register.csv`](claims_evidence_register.csv) and the pinned digests in
[`source_digests.json`](source_digests.json). Base: public `main` at `be777a921237`;
scientific source identity unchanged (v1.1.0, `401f87aad1e4`).

## Why the story changes

The V3 paper and the M11 Observatory lead with archival reconstruction and CPU/GPU
verification. Those results are legitimate and stay, as methodology, reproducibility and
limitations. The research subject is different: how a countermovement jump (CMJ) measures
neuromuscular output, how a post-exposure change in that measurement can be represented
mathematically, how neural architectures are structured to forecast it, and what a controlled
synthetic experiment shows about forecasting error.

## Working title

**Modeling Countermovement-Jump Recovery: Biomechanical Measurement, Neural Architectures,
and a Controlled Synthetic Benchmark**

Descriptor: a computational and synthetic research study. No real athlete was evaluated.

## Research questions and their evidence

| RQ | Question | Evidence it can rest on | Boundary |
|---|---|---|---|
| RQ1 Measurement | How are CMJ mean concentric force and net impulse defined, measured in the synthetic system, and expressed as baseline-relative change? | Native measurement specification; generator source (half-sine trace, three-trial mean, noise CVs); force-target provenance note | Mathematical definitions and a synthetic instrument. External CMJ literature motivates the quantities; it does not validate the generator. |
| RQ2 Recovery modeling | How are exposure, time, history and participant variation represented by response models and the nine recovered architectures? | `fixed_mode_discrepancy_response.py`; architecture contracts and parameter counts (M0-M8, 18 routes) | The 24 h / 84 h modes are synthetic-system assumptions. Architectures are described, not ranked. |
| RQ3 Prediction | What do the four-model synthetic experiment results establish about error across outcomes, horizons and roots? | Fixed-mode public reference results (17 evaluated variants including ablations and nested subsets) | Descriptive. One generator, three seeds, 16 camps per root. |
| RQ4 Limitations | What do uncertainty, ablations, sample-size diagnostics and reproducibility evidence support? | Recorded camp-bootstrap intervals; ablations; 24/48/96-camp diagnostics; CPU/GPU qualification | Intervals compare each model with zero only. Reproducibility is numerical, not scientific validation. |

## Two bodies of work that must never be conflated

| | Original neural architectures | Public synthetic experiment |
|---|---|---|
| Models | Nine families, M0-M8, two recorded repeats each (18 routes) | Zero innovation, training mean, full ridge, structured fixed-mode comparator (plus ablation/nested variants of the last three) |
| Targets / grid | Native H72/D7 contract (four physical-unit cells) for the original routes | Public H24/H48/H72 six normalized cells |
| What exists | Architecture contracts, parameter counts, recorded CPU/GPU numerical qualification | Source-backed descriptive NRMSE, camp-bootstrap intervals, ablations, nested diagnostics |
| What does not exist | An authenticated, comparable public predictive-performance experiment across the nine networks | Any score for M0-M8 |

Consequences for every deliverable: no nine-network leaderboard; no sentence that attaches an
NRMSE to M0-M8; the four reference-model scores are never described as neural-network results
or as human-athlete accuracy.

## Headline numbers (descriptive, synthetic)

Across-root mean six-cell NRMSE (lower is better): zero innovation 2.430659; training mean
1.036038; full ridge 0.736270; structured fixed-mode comparator 0.773316. Root-to-root SDs are
0.008127, 0.007308, 0.003349 and 0.005490. In this synthetic setting ridge was lower than the
structured comparator in each root, and removing current-exposure fields (0.867735) or prior
history (0.819681) raised ridge error far more than removing participant context (0.736346).
Recorded intervals are camp-bootstrap percentile intervals against the zero baseline; no
ridge-versus-structured interval was recorded and none is invented.

## Explicit nonclaims

1. No real-athlete evaluation, clinical, load-management or return-to-play claim.
2. No predictive validity for real recovery; synthetic NRMSE is not accuracy.
3. The fixed 24 h and 84 h modes are mathematical assumptions, not measured recovery constants.
4. The three roots are one generator, so they measure seed variation, not external validity.
5. No nine-network comparison; M0-M8 were not scored in the four-model experiment.
6. CPU/GPU agreement establishes numerical reproducibility of recovered routes only.
7. Mean concentric force is not peak force; the legacy key `relative_peak_mean_force_innovation` is a frozen identifier.
8. No new significance tests, refits, scores, releases, DOI or submission.

## Historical material

The V3 retrospective reconstruction paper and the V2 export remain byte-identical companions.
Their verified ledgers are untouched. In the new narrative, reconstruction supports source
authenticity (what is the source of these architectures and numbers), numerical
reproducibility (18-route qualification) and limitations (private checkpoints, historical
differences). It is not a research question.
