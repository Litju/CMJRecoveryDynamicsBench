# LinkedIn post draft (RES-783)

Status: draft for owner review. Not posted. Attach
`output/CMJ_From_Force_Plate_to_Forecast_carousel.pdf` as a document post; LinkedIn shows the
PDF title "From Force Plate to Forecast: Modeling CMJ Performance Changes Following Training".
Every number below is in the carousel ledger or the claims register (checked by
`tests/test_linkedin_carousel.py`); URLs were checked to resolve on 2026-11-24.

---

From force plate to forecast: how much can a model learn about the change in a countermovement jump (CMJ) after training? We studied that question in a controlled synthetic setting, and the carousel walks through the whole research path in eight pages.

1. Measurement. A CMJ force–time record gives three different quantities: gross mean concentric force (N/kg), peak force (N/kg) and net concentric impulse (m/s). We model mean concentric force and net impulse, and the target is the additive change from a three-trial baseline, never a percentage.

2. Mathematical model. In our generator, the post-training change is the sum of two fixed exponential modes, 24 h and 84 h. These are modeling assumptions of the simulation, not measured human recovery constants.

3. Architectures. Nine original neural network families (M0–M8, 1,346 to 10,796 parameters) progress from a small MLP to a history encoder, a GRU over prior sessions, a horizon embedding and a public-schedule basis. They were not scored in the experiment below, so we do not rank them.

4. Experiment. Four reference models (zero innovation, training mean, ridge regression and a structured comparator built on the generator's 24 h / 84 h modes) forecast both outcomes at 24, 48 and 72 h: six cells, on three evaluation roots from one generator.

5. Results. Six-cell mean NRMSE, lower is better: zero 2.430659, training mean 1.036038, ridge 0.736270, structured 0.773316. Ridge was lowest in every root; the comparator that knows the generator's own modes did not beat it.

6. Interpretation. Removing current-exposure fields (0.867735) or prior history (0.819681) raised ridge error; removing participant context barely changed it (0.736346). Error hardly moved between 24 and 96 training camps.

What this does not show: no ridge-versus-structured interval was recorded, so the ordering is descriptive, not a tested difference. Nothing here establishes predictive validity for athletes or generalization beyond one generator. No athlete was measured.

Explore every figure with live controls in the Recovery Observatory:
https://recovery-observatory.vercel.app/

Manuscript (unsubmitted owner-review draft, not peer reviewed):
https://github.com/Litju/CMJRecoveryDynamicsBench/blob/main/docs/manuscript/v4/full_illustrated_manuscript.pdf

Code, generator and checksummed study results:
https://github.com/Litju/CMJRecoveryDynamicsBench

#Biomechanics #SportsScience #MachineLearning
