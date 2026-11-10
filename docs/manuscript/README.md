# Research manuscript editions

## Current paper — V3 (read this)

**[Full illustrated research manuscript (PDF)](v3/full_illustrated_research_manuscript.pdf)** —
*Retrospective reconstruction and numerical qualification of historical
countermovement-jump recovery research: An evidence-bounded case study.*

- [Academic review edition](v3/academic_review_manuscript.pdf) (single column, line-numbered)
- [Technical supplement](v3/technical_supplement.pdf)
- [Figures Fig1–Fig10](v3/figures/) and [per-figure receipts](v3/reproducibility/figure_receipts/)
- [V3 package guide and regeneration](v3/README.md)
- [Force-target terminology note](v3/reports/force_target_provenance_note.md)

V3 is an **unsubmitted research draft**. It has not been peer reviewed, submitted to a
journal or preprint server, or assigned a DOI. Its scientific source is the immutable
v1.1.0 release, 401f87aad1e4ef4108011fa0c1d769a24f1ad329. The force outcome is the
*mean concentric-force innovation (N/kg)*; the frozen evaluation key
`relative_peak_mean_force_innovation` keeps its legacy name.

## Historical edition — M10 owner-review export (V2)

The files in this directory, outside `v3/`, are the public, sanitized export of the
qualified V2 manuscript for RES-585. They are preserved as historical evidence and are
**not the latest manuscript**. Where V2 tables use the registered key
`relative_peak_mean_force_innovation`, the quantity is the same target that V3 names
mean concentric-force innovation.

- [V2 manuscript PDF](manuscript.pdf) and [source](manuscript/manuscript.md)
- [V2 technical supplement](supplement/technical_appendix.pdf)
- [V2 figures](figures/) and [regeneration instructions](reproducibility/README.md)
- [Claims/evidence register](evidence/claims.json), [source identities](evidence/sources.json), and [model qualification table](supplement/model_identity_sanitized.csv)
- [Venue assessment](venue_assessment.md) and [research integrity disclosure](research_integrity.md)

The V2 scientific source is also v1.1.0 / 401f87aad1e4ef4108011fa0c1d769a24f1ad329.
Private reconciliation records, checkpoint/configuration identifiers, restricted
artifacts, publisher response/template files and internal inspection images are
excluded. No public checkpoint replay is promised.

## Verify

From this directory, `sha256sum -c SHA256SUMS` verifies the V2 export; from `v3/`,
`sha256sum -c ARTIFACT_SHA256SUMS` verifies V3. This page is a navigation document:
in M11 (RES-627) it replaced the M10 export README, whose original text is preserved in
Git history at commit 1311404d (manifest digest
695dbda02c58c8dcf4405883c926c960f534180a79d2f6da95a76e474cc034a9). Only this README's
entry in `SHA256SUMS` changed; every V2 scientific file keeps its recorded digest.
