# V2-to-V3 differential claims audit

Audit date: 6 November 2026. The row-level record is `claims_differential_audit.csv`; `claims_differential_audit_summary.json` contains machine-checked counts and digests.

## Scope and result

The original V2 claim ledger is preserved unchanged: 553 entries (SHA-256 `a83f261ab4881794576c959526a56eb51ac4016101f36c5c85fc97e629351187`). It is a historical qualification record; its decisions are not inherited automatically by V3.

The V3 audit now records **510 current units** (485 substantive scientific, methodological, evidence-boundary or availability claims and 25 author/AI declaration records) plus three removed V2 statements, 513 rows in all. Differential status against V2: retained 128, modified 312, new 45, removed 3, administrative 25. Unit types: 348 prose sentences, 10 figure captions, 9 table captions, 108 table rows, 10 displayed equations, 25 declaration records, 3 removed statements.

## RES-585 reconciliation (illustrated edition)

The RES-585 redesign changed the manuscript source (two-column layout, merged biomechanics figure, new heatmap, force-target wording, split equations). `reproducibility/refresh_claims_audit.py` re-extracts every claim-bearing unit from `manuscript.tex`, carries the evidence mapping across from the best-matching earlier row, marks wording changes as modified and unmatched units as new, and checks every number in changed or new units against the pinned evidence corpus (rounded presentation values, and values re-derived by `verify_quantitative_figures.py` such as the analytical 14.79 N/kg, 24.09 N/kg and 2.74 m/s, are accepted only through those checks). Result: 145 changed or new units, 0 numeric-check failures. 47 earlier rows no longer correspond to a current unit; most are sentences that were split, merged or replaced (for example the retired Fig. 5/6 captions). Every dropped row and every changed or new unit is listed in `claims_differential_changes_RES-585.csv`.

This remains agent-only internal source review; it is not human scientific validation. Inherited evidence mappings for revised or new units were assigned from the surrounding section, so the owner-confirmation items below still apply.

## Removed V2 statements

The audit removes these specific prior-work claims from the current argument:

- `M-P010-S02`: “ModelHub [R10] treats learned parameters and their versions as lifecycle artifacts.” ModelHub is no longer used as a proxy for MLflow, DVC, or the standards cited in V3.
- `M-P011-S02`: “The Open Provenance Model [R11] represents past executions through annotated causal relationships.” V3 instead distinguishes W3C PROV-O from the RO-Crate specification.
- `M-P007-S04`: “Hashes identify bytes; they neither establish permission nor authenticate an empirical instrument.” The current manuscript replaces this general sentence with case-specific rights and measurement-authority limits.

The source-ledger claims that supported those topics remain available in the unchanged V2 audit. Removal here means the statements above are not asserted as current V3 wording; it does not erase the historical audit.

## Audit fields and method

Each current row has a stable claim ID, manuscript file and line or table location, exact displayed statement, supporting source path/ID or DOI, source commit/version and SHA-256, evidence level, public-reproducibility status, qualification, verification decision, and V2 crosswalk candidates.

The V2 crosswalk uses text similarity only to suggest candidate legacy IDs. It is not treated as semantic verification and it does not determine the retained/modified/new/removed status. Statuses reflect the claim's source, changed interpretation, and evidence boundary. Numerical source checks are recorded separately from private execution evidence.

Verification decisions are agent-only internal review: 290 source-checked, 197 source-checked with explicit qualification, 13 owner confirmations pending, and 3 removed historical statements. No current row is marked unsupported by this agent audit. The audit is not human peer review or independent owner validation; authors must review the scientific interpretation and outstanding declarations before submission.

## Evidence authority summary

Public source files and M8 receipts support public software identity, formulation records, the synthetic protocol and score arithmetic, figure regeneration, and the native measurement/evaluation contracts. The 18 original Gate7 route outcomes remain privately recorded qualification summarized in public-safe records. Their checkpoint inference and saved-array comparisons cannot be independently rerun from the public package. The V3 availability assessment maps the main claims to these distinct evidence levels.
