# Science-first flagship manuscript (owner-review draft)

**Modeling Countermovement-Jump Recovery: Biomechanical Measurement, Neural Architectures, and a Controlled Synthetic Benchmark**

A computational and synthetic study. No athlete was measured; nothing here establishes predictive validity for real recovery. It is an unsubmitted draft: not peer reviewed, not submitted, no DOI.

## Read

| File | Purpose |
|---|---|
| [full_illustrated_manuscript.pdf](full_illustrated_manuscript.pdf) | Two-column illustrated article with 11 figures and 6 tables beside the argument |
| [academic_review_manuscript.pdf](academic_review_manuscript.pdf) | Single-column, line-numbered review copy; captions in order, figures in `figures/` |
| [technical_supplement.pdf](technical_supplement.pdf) | All 17 evaluated variants, per-cell/per-root values, all recorded intervals, architecture routes |
| [figures/](figures/) | Fig1-Fig11 as PDF, SVG and PNG |
| [reproducibility/data_ledger.csv](reproducibility/data_ledger.csv) | Every figure and table mapped to its receipt, keys and SHA-256 |
| [../../science/](../../science/) | Claims/evidence register, verified references, terminology, storyboard |

Structure: introduction and four research questions; biomechanical framework; mathematical recovery models; nine original neural architectures (M0-M8, not scored); the synthetic experiment (ADEMP); quantitative results; discussion; reproducibility; limitations; conclusions.

The nine original families and the four evaluated reference models are never merged: no NRMSE is attached to M0-M8. The retrospective reconstruction paper ([V3](../v3/full_illustrated_research_manuscript.pdf)) and the V2 export stay unchanged as companion historical artifacts.

## Regenerate

Python 3.12 with `reproducibility/requirements.lock` and Tectonic 0.17.0 (XeTeX engine; support bundle downloaded on first build):

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r reproducibility/requirements.lock
mkdir -p toolchain && cp /path/to/tectonic-0.17.0 toolchain/tectonic   # or have `tectonic` on PATH
bash reproducibility/build.sh
```

The build reads only `docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json`, `docs/manuscript/supplement/*.csv` and the simulator's own trial and response routines (Fig2-Fig4). It performs no training, fitting, inference or scoring. `SOURCE_DATE_EPOCH` is fixed so the PDFs are deterministic for a given toolchain.

Verify: `sha256sum -c ARTIFACT_SHA256SUMS`; `pytest tests/test_flagship_manuscript.py`.

## Evidence identity

Scientific source: release v1.1.0 (`401f87aad1e4`). Results receipt scientific SHA-256 `25032133d6f3293f722d06d3a618ec1aecec7cef35d2d35524c7431620e4bc71`; protocol SHA-256 `972733eb2d85e49f61281955eaad327f06adadce8b66a1ec32e74fcba7838f48`.

Author names, affiliations, roles, funding and conflicts remain for the owner to confirm. Human domain review of the cited literature, and any submission, are outside this package.
