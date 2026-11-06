# Data and software availability assessment

Assessment date: 6 November 2026. This is an owner-review assessment, not a journal decision or an approved controlled-access plan.

## Publicly available

- The research software release is public under Apache-2.0 as v1.1.0, pinned to immutable source commit `401f87aad1e4ef4108011fa0c1d769a24f1ad329`.
- The V3 package contains 35 release-linked source snapshots with per-file SHA-256 identities, the public formulation catalog, public synthetic-study protocol and receipts, sanitized summaries of restricted model qualification, calculation and figure-generation scripts, and generated tables and figures.
- The public synthetic results, six-cell values, root summaries, recorded bootstrap endpoints, and ablation/nested-camp summaries can be checked against the included public receipts. Figures can be regenerated from those public summaries. The V3 build validator also checks source hashes, bibliography metadata, receipt arithmetic, and package checksums.
- Public scientific contracts define the native H72/D7 measurement and evaluation interface. They do not include athlete observations or an empirical athlete score.

## Not publicly available

- Original fitted Gate7 checkpoint bytes, fitted preprocessing values, and original inference arrays.
- Restricted historical run, observation, and source-reconciliation records that establish the original model-to-artifact associations.
- A public execution environment capable of rerunning the original 18 checkpoint routes against their saved historical arrays.

The V3 package contains only public-safe summaries for these materials. The package does not document an approved controlled-access mechanism or independent institutional contact for them. The paper therefore does not invite access requests and does not state that restricted artifacts are “available upon request.”

## Reproducibility of the principal claims

| Manuscript claim | Evidence in the public package | Can an external reader reproduce it from only the public package? | Qualification |
|---|---|---|---|
| v1.1.0 software identity and the 35 release-linked source snapshots | `evidence/release_sources/sources.json`, `S16`–`S20`, and the V3 checksum inventory | Yes: verify the immutable source identities and hashes | This authenticates public software and records, not private fitted artifacts. |
| Eight historical formulation identities and their recorded lineage | `S17_lineage.json`, `S18_formulation-methods.json` | Yes: inspect the published identities and draw the recorded parent links | Three direct ancestry relationships remain unresolved; the package does not infer them. |
| Nine original Gate7 neural families and architecture descriptions | `S16_gate7.json` and `evidence/v2_audit/architecture_qualification.csv` | Partly: architecture topology and listed parameter counts are inspectable; checkpoint contents are not | Topology is not evidence of predictive performance or of the saved checkpoint bytes. |
| Exact source-CPU equality on all 18 original routes | `S06_RES-546_INFERENCE_VERIFICATION.md`, `S12`–`S15`, and the sanitized route summary | No: only the privately recorded result is public | The original source/model execution cannot be independently rerun from this package. |
| Saved-CUDA passes for M0–M3 and failures for M4–M8 under the unchanged tolerance | The same sanitized route summary and public description of the historical acceptance rule | No: the pass/fail summary is inspectable, but saved arrays and checkpoints are not | No fresh historical GPU replay was performed; the failure cause is unresolved. |
| Native force/impulse definitions and H72/D7 assessment contracts | `S09_GATE7_NATIVE_MEASUREMENT_V1.md`, `S10_GATE7_NATIVE_ANALYSIS_V1.md`, and public source snapshots | Yes: inspect and calculate from the public formulas and contract | This does not establish that an empirical athlete trace was measured or scored. |
| Four-model public synthetic benchmark protocol and six-cell NRMSE definitions | `S01`, `S02`, `S23`, and the registered protocol digests | Yes: independently inspect the protocol and public runner | This is a separate synthetic study and not an original Gate7 model evaluation. |
| Synthetic six-cell results, three-root summaries, bootstrap records, and ablations | `S01`, `S04`, `evidence/v2_audit/six_cell_results.csv`, and `recorded_uncertainty.csv` | Yes for receipt arithmetic and figure regeneration; the reported values can also be rerun with the public study runner | This V3 correction did not repeat training, scoring, selection, or resampling. Root variation is descriptive; no ridge-versus-structured interval is recorded. |
| Rich-history row-count differences | `S03_M8_REPRODUCTION_RESULTS.md` and `S04_M8_PUBLIC_REPRODUCTION_RECEIPTS.json` | Yes: compare the published receipt counts | Counts do not prove historical split identity or a response effect. |
| The analytical force–time illustration | `S21_native_mechanics.py` and `figure_source/generate_figures.py` | Yes: regenerate from the displayed equation and fixed illustrative parameters | It is not athlete data. |
| No demonstrated athlete predictive validity, clinical utility, or transportability | Article scope, public package contents, and the separate native measurement/evaluation contracts | A reader can verify that the package reports no athlete validation analysis | This is a boundary on the evidence presented, not evidence that all future models lack validity. |

## PLOS ONE feasibility

The manuscript follows a full-length research-article structure that can be used as a format reference. PLOS ONE's current criteria include research methods and software and allow negative results, but require supported conclusions and community-compliant data availability. Its data policy requires the data underlying the findings to be available without restriction except for limited legal or ethical circumstances. For restricted third-party data it asks for the source, applicable permission, access instructions, and known restrictions; it also says an author cannot be the sole access contact. It separately states that manuscripts whose conclusions depend solely on inaccessible proprietary data are not considered, while public data used to validate such conclusions may support a submission.

Here, the public synthetic benchmark supports RQ3 only. It does not validate the private original-route qualification reported for RQ1/RQ2. No rights-cleared checkpoint release, approved controlled-access route, or nonauthor institutional access contact is documented in this package. As a result, PLOS ONE is **not currently qualified as a submission destination**; whether its legal/ethical or third-party data provisions could apply is unresolved. The full-length paper must not be submitted on the assumption that citing a private receipt satisfies data availability.

No alternative venue is designated submission-ready. A realistic next venue decision depends first on an internal rights/access determination. If controlled access cannot be established, a future owner decision could narrow the article to public-reproducible evidence and then reassess a research-software or reproducibility-case-study venue against its current scope and artifact policy. This report does not initiate that separate rewrite or contact a journal.

## Official PLOS ONE pages checked

- [Publication criteria](https://journals.plos.org/plosone/s/criteria-for-publication)
- [Submission guidelines](https://journals.plos.org/plosone/s/submission-guidelines)
- [Data availability](https://journals.plos.org/plosone/s/data-availability)
- [LaTeX instructions](https://journals.plos.org/plosone/s/latex)
- [Figure guidelines](https://journals.plos.org/plosone/s/figures)
