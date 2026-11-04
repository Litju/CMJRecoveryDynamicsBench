# RES-546 CPU-source integration policy, version 1

This limited qualification is additional to, and does not replace, any historical full-qualification standard. Integration requires independent review and explicit merge authorization.

## CPU_SOURCE_QUALIFIED

Each final repeat requires independently authenticated original checkpoint and configuration, complete final-repeat identification, the exact source-defined architecture and original fitted preprocessing, authenticated input tensor identities, exact original CPU source parity on frozen synthetic and historical inputs, deterministic execution, preserved CPU prediction-array reproduction, safe weights-only checkpoint loading, and complete regression, packaging and security checks. Qualification permits source-faithful research inference code to be considered for public integration. It does not authorize checkpoint publication.

## HISTORICAL_CUDA_COMPATIBILITY

Record historical CUDA prediction identity, the original predeclared rule `abs(replayed-saved) <= 1e-5 + 1e-4*abs(saved)`, exact maximum differences, failing element counts, established original GPU/runtime identity, and whether authentic historical GPU replay passed. M4–M6 CPU-to-saved-CUDA checks FAILED; see the separate historical records. A CPU TF32 approximation is an explanatory diagnostic, not authentic CUDA replay. The TF32 mechanism is strongly supported; historical RTX 5090 runtime attribution remains unresolved.

## SCIENTIFIC_VALIDITY

Predictive accuracy, generalization, robustness, clinical applicability, production readiness and historical score equivalence beyond existing evidence remain unestablished. CPU source parity implies none of these.

## ARTIFACT RIGHTS AND RELEASE

First-party ownership decisions, checkpoint distribution rights, private dataset permissions and release status remain unchanged. Public source-code integration is distinct from redistributing original trained weights or restricted scientific evidence. No original trained checkpoint is distributed by this preparation.

## Integration preparation

The independent composed-source replay found exact CPU source parity and preserved synthetic and historical CPU arrays for all six M4–M6 final repeats. The separate historical records preserve the original failed CPU-to-saved-CUDA comparisons. CPU-source qualification remains subject to the complete engineering checks and independent review described above; it does not establish predictive performance or production readiness.

The source blocks and tests are mapped to PR #20 (M4), PR #21 (M5), and PR #22 (M6). Each candidate's inference classes and functions are preserved independently; the shared M0–M3 implementation is unchanged. The branch-specific historical findings are retained in `RES-546_M4_HISTORICAL_FINDINGS.md`, `RES-546_M5_HISTORICAL_FINDINGS.md`, and `RES-546_M6_HISTORICAL_FINDINGS.md`.
