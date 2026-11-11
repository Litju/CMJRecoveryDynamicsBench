# M12 independent qualification record (RES-634)

Scope: the flagship paper (`docs/manuscript/v4`) and the reframed Observatory (`website`). This is an agent-run
qualification by the same agent that built the work, with fresh automated checks. It is **not** peer review,
independent human scientific review, manual screen-reader testing or physical-device testing; those remain unqualified.

## Scientific and numerical checks

| Check | Method | Result |
|---|---|---|
| Every 4+-decimal number in the three PDFs comes from the receipt | `qa/audit_pdf_numbers.py` reads the rendered PDFs (references excluded) and matches each number to a receipt value or a derived ablation difference | 80 / 68 / 295 numbers in full / review / supplement; 0 unmatched; no forbidden phrases (`audit_pdf_numbers.out.txt`) |
| Headline scores | `tests/test_flagship_manuscript.py`, `website/tests/flagship.test.mjs` | 2.430659 / 1.036038 / 0.736270 / 0.773316 equal the receipt, appear in the paper abstract and on the site |
| Tables regenerate identically | `test_generated_tables_match_the_receipts` | all six tables equal a fresh regeneration |
| Nine architectures vs four reference models | guard tests plus `science.spec.ts` (architecture section has no NRMSE) | no score attached to M0-M8 anywhere in paper or site |
| Force-time math and units | simulator routines vs `website/src/lib/cmj-science.mjs` (node tests); `test_register_formulas_match_the_generator` | mean force gross (N/kg), net impulse (m/s), peak differs; duration 0.264879 s at 20 N/kg, 2.7 m/s |
| Fixed modes labelled assumptions | paper text, exhibit label and limitations, guard tests | present in abstract, Section 3, Fig. 4 caption, site Chapter 2, limitations |
| Statistical claims | register R-18; paper Section 6.2 | intervals only vs zero; no ridge-vs-structured test claimed |
| Literature | metadata verified against Crossref/arXiv (`docs/science/verified_references.json`) | full-text claim verification by a human domain reviewer is **pending** |

## Visual inspection

Rendered and inspected: all 9 pages of the illustrated PDF (pages 1, 3, 6 singly; 2, 4, 5 and 7-9 in sheets), all 16
pages of the review edition (contact sheet; page 1, 8 and 14 also at reading size), supplement pages 1-2. Defects found
and fixed before commit: overlapping labels in Fig. 2 and Fig. 4, clipped title and footer in Fig. 3, overfull
equation (3) and wide tables. Browser: before/after desktop and mobile screenshots of `/`, `/paper/`, `/results/`,
`/models/` in `website/docs/m12/` (home before: "Reconstructing a historical ... research program"; after: "One jump,
three days: modeling how countermovement-jump outcomes change after training").

## Software and packaging

| Check | Result |
|---|---|
| Python: pytest, ruff check/format | pass |
| Website: typecheck, 36 node tests, build, full Playwright suite (57 tests: existing, updated, new) | pass locally |
| 320 px overflow | a Chapter heading overflowed at 320 px; fixed (`overflow-wrap`); spec added |
| Existing interactions and links | 96 benchmark views, model-atlas deep link, anchors `#explorer #question #world #lineage #lab #evidence #model-atlas`, `/models/#fig-3`, `/results/#fig-6`, noindex: pass |
| Frozen files | `git diff origin/main...` touches no `src/`, no `docs/M8_*`, no `docs/manuscript/` V2 or `v3/` file, no tag |
| Release | tag v1.1.0 still peels to commit 401f87aad1e4; no release, DOI or submission created |
| Wheel | built from main and from this branch: 99 files, byte-identical contents |
| sdist | differs only by two added test files (`test_science_foundation.py`, `test_flagship_manuscript.py`) |
| Public boundary | `test_architecture.py` extended for `docs/science` and `docs/manuscript/v4` manifests; no private paths, checkpoints or restricted data |

## Known limits and follow-ups

- Exact-head CI for #42-#44 is reported in the PR threads; one earlier CI run of #43 failed on a pre-existing
  WebGL canvas spec (`journey.spec.ts:112`) and was re-run.
- Manual screen-reader review, Safari/Firefox and physical devices: not performed.
- Independent human scientific review of the paper and its citations: not performed.
- Author names, affiliations, funding and conflicts: owner to confirm. No submission, DOI or preprint.
- The website's stage animation and 3D scenes are unchanged from M11; their WebGL fallbacks are covered by existing specs.
