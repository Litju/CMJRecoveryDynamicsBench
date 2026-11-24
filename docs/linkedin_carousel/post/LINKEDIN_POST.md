# LinkedIn post draft (RES-783)

Status: draft for owner review. Not posted. Attach
`output/CMJ_From_Force_Plate_to_Forecast_carousel.pdf` as a document post; LinkedIn shows the
PDF title "From Force Plate to Forecast: Modeling CMJ Performance Changes Following Training".
The body below is about 150 words. Every number in it comes from the carousel's source ledger
or the pinned results (checked by `tests/test_linkedin_carousel.py`); the links were checked
on 2026-11-24.

---

From force plate to forecast: a controlled synthetic study of how countermovement-jump (CMJ) performance changes after training.

We start with biomechanics, defining gross mean concentric force and net concentric impulse from the force–time record, and forecast their change from a three-trial baseline. A simulator describes that change with two fixed exponential modes, 24 h and 84 h: modeling assumptions, not measured human constants. We also document nine original neural architecture families (M0–M8), recorded as 18 inference routes.

Those nine architectures were not part of the benchmark. It evaluated four reference models on simulated data, and one result stood out: ridge regression had lower descriptive NRMSE (0.736270) than a structured model built on the simulator's own response modes (0.773316). No paired test of that difference was recorded, and no athlete was measured.

Interactive Recovery Observatory: https://recovery-observatory.vercel.app/

Manuscript (unsubmitted draft, not peer reviewed): https://github.com/Litju/CMJRecoveryDynamicsBench/blob/main/docs/manuscript/v4/full_illustrated_manuscript.pdf

Code and results: https://github.com/Litju/CMJRecoveryDynamicsBench
