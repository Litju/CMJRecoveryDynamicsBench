# Qualified V2 regeneration

This is the public, sanitized export of the privately qualified M10 V2 manuscript. Its V1 predecessor and restricted V2 qualification records are not part of this repository. This draft is publicly available for review but has not been submitted to a journal; the v1.1.0 scientific software release has not been modified.

Use Python 3.12 and the pinned requirements.txt in an isolated environment. DejaVu Sans fonts must exist at the paths recorded in render_pdf.py. From this directory run:

    python figure_source/generate_figures.py
    python reproducibility/check_numerics.py
    python reproducibility/render_pdf.py
    python reproducibility/audit_claims.py
    python reproducibility/verify.py

These commands render documents and check existing evidence only. They do not train, refit, score models, execute checkpoint inference or acquire athlete records. Frozen study commands reproduced inside S02 are historical documentation, not part of regeneration.

Public evidence is extracted from v1.1.0 source 401f87aad1e4ef4108011fa0c1d769a24f1ad329. sources.json retains original paths, commit and file digests; plot_inputs.json contains the unchanged original M8 receipt. The older study retains its own code/package/selection identities. Current main is editorial context only.

All six figures have deterministic SVG/PDF/PNG exports; PDF manuscript figures and equations are vector content. check_numerics.py rechecks all 306 recorded RMSE/truth-SD ratios and the root/cell aggregation chain, preserving the six reported bootstrap intervals without rerunning them. audit_claims.py emits source-bound sentence/table entries; excerpt matching helps locate support and is not a semantic proof. The final recorded acceptance also includes source inspection and rendered-page review.

The private artifact-reconciliation records are NOT included in this public export. The 18-route identities were checked during restricted internal qualification; that private reconciliation cannot be independently repeated from the public files alone. The released documents support the public numerical and source-contract claims, not public replay of original private checkpoints. Do not distribute original checkpoints, private hashes, archive locators, fitted configurations or restricted observations. The original artifact audit read and hashed bytes and parsed JSON; no unsafe checkpoint deserialization occurred.

The public export inventory is `SHA256SUMS` in the parent `docs/manuscript/` directory; no separate `publication_export_manifest.json` is distributed. The private review images, publisher templates/responses and restricted reconciliation records are excluded. The manuscript branch has been pushed to GitHub for owner-authorized public review; no journal submission, preprint, DOI, acceptance or peer review has occurred. `SHA256SUMS` covers all shipped manuscript files except itself. Different rendering environments may change output bytes; verify scientific content and source digests before recording any regenerated checksum manifest. File consistency does not prove athlete validity or historical CUDA replay.
