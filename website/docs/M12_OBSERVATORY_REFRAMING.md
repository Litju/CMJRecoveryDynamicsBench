# M12 Observatory reframing: science first

The Observatory now opens with countermovement-jump (CMJ) science and the controlled synthetic experiment, and
treats reconstruction and verification as supporting evidence (Chapter 7).

## Information architecture

The home page is seven chapters, indexed at the top and in the sticky progress bar:

1. What does a countermovement jump measure? Interactive force-time exhibit (flagship Fig. 2): mean force, peak force,
   net impulse; sliders constrained to the simulator's duration support.
2. What happens after training exposure? Interactive fixed-mode response exhibit (flagship Fig. 4), labelled a
   synthetic assumption; episode theater and Recovery Lab.
3. How do we model that process? Nine original architecture families with exact parameter counts and an explicit
   banner that they were not compared for predictive accuracy.
4. How was the synthetic experiment designed? Generator, camps, roots, horizons, leakage boundary.
5. What did the models actually predict? The four-model benchmark explorer (all 96 views); `/results/` holds the
   six-cell, heatmap, bootstrap and ablation figures.
6. What can we conclude? Supported findings, nonclaims, open questions.
7. How was the research verified? Lineage, evidence, research tour and the model atlas.

`/paper/` leads with the flagship paper (PDFs copied at build time after digest verification against the v4
manifest); the retrospective V3 paper is a companion section with its previous anchors unchanged. Nav order:
The science, Results, Architectures, Methods, Verification, Research paper. `noindex,nofollow` is unchanged.

## Preserved

Routes, anchors (`#explorer`, `#question`, `#world`, `#lineage`, `#lab`, `#evidence`, `#model-atlas`), the
`?architecture=…&run=…` model-atlas link, all ten V3 figure components, exports, accessible tables and the 96
benchmark selector combinations.

## Data

`scripts/prepare-flagship.mjs` verifies `docs/manuscript/v4/ARTIFACT_SHA256SUMS` against
`source/flagship-manifest.json`, writes `src/data/flagship.json` and copies three PDFs to `public/paper/flagship/`.
`src/lib/cmj-science.mjs` mirrors the simulator's trial and response routines; `tests/cmj-science.test.mjs` checks it
against values computed by the Python source.

## Before/after

`docs/m12/` holds matched desktop and mobile screenshots of `/`, `/paper/`, `/results/` and `/models/` from the
previous main (`before-*`) and this branch (`after-*`). Regenerate with `scripts/capture-m12.mjs`.

## Not done

Manual screen-reader, Safari/Firefox and physical-device review are not performed here.
