# V2-to-V3 differential claims audit

Audit date: 6 November 2026. The row-level record is `claims_differential_audit.csv`; `claims_differential_audit_summary.json` contains machine-checked counts and digests.

## Scope and result

The original V2 claim ledger is preserved unchanged: 553 entries, comprising 487 prose/equation sentences and 66 table rows. Its SHA-256 remains `a83f261ab4881794576c959526a56eb51ac4016101f36c5c85fc97e629351187`. It remains a historical qualification record; its previous decisions are not automatically inherited by V3.

The V3 audit records 500 current units: 488 substantive scientific, methodological, evidence-boundary, or availability claims and 12 author/AI disclosure records. It also records three removed V2 related-work statements, for 503 rows total. The current statuses are:

| Differential status | Count | Meaning |
|---|---:|---|
| Retained | 166 | The substantive result or contract remains the same and was rechecked against its source. |
| Modified | 305 | Wording, scope, interpretation, or qualification changed and was checked again. |
| New | 17 | Introduced in V3, including the new related-work comparison and explicit research-question framing. |
| Removed | 3 | Prior V2 statements no longer asserted in V3; listed below. |
| Administrative disclosures | 12 | Authorship, funding, ethics, and AI statements; not counted as scientific claims. |

The row-level inventory contains 356 prose-sentence units, 10 scientific figure captions, 9 table captions, 108 table rows, 5 displayed equation blocks, 3 removed V2 statements, and 12 administrative disclosures. It spans both the main article and technical supplement, including all 18 route records, all 24 public six-cell/root rows, 6 bootstrap records, the architecture and formulation matrices, and the nested-camp/ablation values.

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
