# Paper and website storyboard

## Paper chapters (canonical manuscript, RES-632)

| # | Chapter | Question | Main evidence ids | Figures |
|---|---|---|---|---|
| 1 | Scientific introduction | What does a CMJ measure and why model post-exposure change? | M-01, X1-X8 | F1 |
| 2 | Biomechanical framework | How are force, impulse, trials and innovation defined? | M-01..M-08 | F2, F3 |
| 3 | Mathematical recovery models | What exposure-response hypotheses does the generator encode? | A-01..A-04, X9-X10 | F4 |
| 4 | Neural ML architectures | How do nine original families encode inputs, history, horizon and basis? | N-01..N-04 | F5 |
| 5 | Synthetic experiment | Generator, partitions, four reference models, ADEMP | E-01..E-04 | F6 |
| 6 | Quantitative results | Six-cell NRMSE, roots, intervals, ablations, nested camps | R-01..R-19 | F7-F10 |
| 7 | Discussion | What the controlled findings say about the synthetic task | R-*, N-04 | F7, F10 |
| 8 | Reproducibility | CPU/GPU verification, private checkpoints, source identity | V-01, V-02 | F11 |
| 9 | Limitations, conclusion, supplement | Nonclaims | all | |

## Figure storyboard

| Fig | Content | Data source | Label |
|---|---|---|---|
| F1 | Study map: measurement, response model, architectures, experiment, findings | schematic | conceptual |
| F2 | Analytical force-time: half-sine concentric trace, g line, mean force, peak, net-impulse area | closed-form from M-01..M-04 | analytical illustration of the synthetic trace |
| F3 | Three trials, assessment mean, baseline, criterion, innovation | closed-form | analytical illustration |
| F4 | r(tau) family and the two modes at example amplitudes | closed-form from A-01/A-02 | synthetic assumption, not biology |
| F5 | M0-M8 progression with exact parameter counts | architecture table | contract only; no accuracy |
| F6 | Generator, camps/episodes, roots, horizons, leakage boundary | results JSON | design |
| F7 | Six-cell NRMSE by model, root points and mean | results JSON | descriptive |
| F8 | Model-by-cell NRMSE heatmap | results JSON | descriptive |
| F9 | Recorded bootstrap intervals by root | results JSON | descriptive, vs zero only |
| F10 | Ablations and nested 24/48/96-camp diagnostic | results JSON | descriptive |
| F11 | 18-route numerical qualification (evidence boundary) | architecture table | numerical only |

All ten existing V3 figure families stay available as secondary material.

## Website journey (RES-633)

1. What does a countermovement jump measure? (interactive F2)
2. What happens after training exposure? (interactive F4, synthetic label)
3. How do we model that process? (F5 progression, no accuracy)
4. How was the synthetic experiment designed? (F6)
5. What did the models actually predict? (F7-F10; central exhibit)
6. What can we conclude? (nonclaims, limitations)
7. How was the research verified? (provenance, 18 routes, software; not on the homepage hero)

Existing Observatory deep links stay resolvable; `/paper/` leads with the new manuscript and
lists the retrospective paper as a companion; `noindex,nofollow` stays.
