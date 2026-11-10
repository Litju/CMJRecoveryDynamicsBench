# Qualified V2 regeneration

Preserved predecessor: M10_SCIENTIFIC_MANUSCRIPT_V1_20261104 (unchanged). This directory is the separate V2 qualification output. No software repository or release was edited.

Use Python 3.12 and the pinned requirements.txt in an isolated environment. DejaVu Sans fonts must exist at the paths recorded in render_pdf.py. From this directory run:

    python figure_source/generate_figures.py
    python reproducibility/check_numerics.py
    python reproducibility/render_pdf.py
    python reproducibility/audit_claims.py
    python reproducibility/verify.py

These commands render documents and check existing evidence only. They do not train, refit, score models, execute checkpoint inference or acquire athlete records. Frozen study commands reproduced inside S02 are historical documentation, not part of regeneration.

Public evidence is extracted from v1.1.0 source 401f87aad1e4ef4108011fa0c1d769a24f1ad329. sources.json retains original paths, commit and file digests; plot_inputs.json contains the unchanged original M8 receipt. The older study retains its own code/package/selection identities. Current main is editorial context only.

All six figures have deterministic SVG/PDF/PNG exports; PDF manuscript figures and equations are vector content. check_numerics.py rechecks all 306 recorded RMSE/truth-SD ratios and the root/cell aggregation chain, preserving the six reported bootstrap intervals without rerunning them. audit_claims.py emits source-bound sentence/table entries; excerpt matching helps locate support and is not a semantic proof. The final recorded acceptance also includes source inspection and rendered-page review.

Private artifact reconciliation and source-binding details are in evidence/private. They cannot be reproduced with public evidence alone. Do not distribute that directory or any original checkpoint, private hash, source locator or configuration. The original artifact audit only hashed bytes and parsed JSON; no unsafe checkpoint deserialization occurred.

Publication-safe candidate files are explicitly listed in publication_export_manifest.json, subject to owner approval. Bibliographic publisher documents are research evidence, not licensed for republication; external response/template files are excluded from that export list. Nothing has been uploaded or submitted. SHA256SUMS covers all files except itself; after authorized regeneration recompute the manifest if local renderer/version metadata differs. File consistency does not prove athlete validity or successful original CUDA replay.
