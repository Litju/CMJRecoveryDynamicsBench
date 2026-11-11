# Science foundation for the flagship paper and Observatory

| File | Purpose |
|---|---|
| [SCIENTIFIC_POSITIONING.md](SCIENTIFIC_POSITIONING.md) | Title, research questions, evidence boundaries, nonclaims |
| [CONTRACT_AND_TERMINOLOGY.md](CONTRACT_AND_TERMINOLOGY.md) | Study inventory, formulas and units, terminology, model-set guard |
| [claims_evidence_register.csv](claims_evidence_register.csv) | Every claim: class, value, source locator, source SHA-256, permitted and forbidden wording |
| [verified_references.json](verified_references.json), [citation_matrix.csv](citation_matrix.csv) | External literature with verified metadata and the limits of what each supports |
| [STORYBOARD.md](STORYBOARD.md) | Chapter and figure plan for paper and website |
| [source_digests.json](source_digests.json) | Pinned SHA-256 of the receipts and source files used |
| [SHA256SUMS](SHA256SUMS) | Integrity manifest for this directory |

Evidence classes: `repository_result`, `repository_definition`, `synthetic_assumption`,
`nonclaim`. External literature is kept apart in the reference files.
`tests/test_science_foundation.py` re-derives every numeric value from the receipts.
