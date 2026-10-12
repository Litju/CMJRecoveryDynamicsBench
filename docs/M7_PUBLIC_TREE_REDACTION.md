# M7 public-tree redaction report

## Decision

The M0 rights registry marks the White-related empirical source and its derivatives `DO_NOT_REDISTRIBUTE`. The public tree now preserves that decision as typed metadata and omits the restricted result details. No scientific values were replaced with estimates, and no rights permission was inferred.

## Redactions

- Removed the empirical metric and result records, including exact values, validation sample counts, split counts, model identities, and direct model comparison.
- Removed the source-specific ranking claim and removed restricted evidence bindings from broader M6 claims.
- Retained the program-level conclusion that empirical recovery grounding is unresolved because no rights-cleared source, split, and scorer crosswalk is publicly established. It does not claim validation or invalidation.
- Retained the source as `restricted_empirical_grounding_source` with `PRESERVED_PRIVATELY` availability and `PROHIBITED` redistribution.
- Retained only an unknown split placeholder with no row, participant, camp, origin, or label metadata.
- Retained a typed crosswalk status with an empty values tuple, no model names, and `RIGHTS_WITHHELD` M4 result authority.
- Removed result aliases for the restricted models and removed their result comparison from public lineage.

The remaining M6 synthesis claims validate against their registered public M1–M5 bindings. One source-specific ranking claim was removed. Six program-level claims were retained with the restricted support removed; the empirical-grounding limitation remains unresolved.

## Rights and release boundary

RES-362 and RES-363 remain the authority for this classification. They record no permission to redistribute the empirical source, participant-level derivatives, split details, model comparisons, or result summaries. The code exposes the prohibition and the missing crosswalk without restating those details.

The owner has not selected a project license. This remediation adds no `LICENSE`, license metadata, or citation identity. M7 remains blocked.

## Changed records

- `lineage/datasets.py`: generic rights-restricted dataset and undisclosed split record.
- `lineage/experiments.py`, `lineage/evaluations.py`, and `lineage/results.py`: crosswalk-only public record; no restricted metrics or values.
- `lineage/models.py` and `provenance/lineage_aliases.py`: removed restricted model records and aliases.
- `study_reconstruction/registry.py` and `study_reconstruction/contracts.py`: preserve the crosswalk limitation and rights-withheld authority.
- `synthesis/registry.py`: remove the source-specific ranking claim and its support from broader claims while preserving the unresolved grounding boundary.

No historical Git rewrite was performed. Earlier public commits still contain the pre-redaction tree; that history blocker is recorded in the occurrence classification report.
