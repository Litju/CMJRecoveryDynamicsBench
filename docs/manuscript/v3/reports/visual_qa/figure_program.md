# Figure program inventory (RES-585)

Every figure is authored at its printed size (180 mm) and placed at scale 1.0. Quantitative figures read only pinned release sources or sanitized public summaries; per-figure receipts in `reproducibility/figure_receipts/` hold the exact SHA-256 digests, caption, units and numerical test.

| Figure | Manuscript page | Title | Data sources | Numerical test | Min. text (pt) |
|---|---:|---|---|---|---:|
| Fig1 | 3 | Formulation genealogy | S17, S18 (lineage and formulation-method records) | `recorded links only; 8 nodes, 5 parent links (checked in generator)` | 5.4 |
| Fig2 | 3 | Public synthetic study sample structure | S01, S02 | `sample_split_counts_match_pinned_receipt` | 6.2 |
| Fig3 | 5 | Historical neural model architectures and parameter counts | S16, S24, S25, S26; architecture_qualification.csv | `architecture_families_and_parameter_counts_match_record` | 5.4 |
| Fig4 | 6 | 18-route CPU and archived GPU-output qualification | S06, S12, S13, S14, S15, S16; model_identity_sanitized.csv | `route_population_and_recorded_pass_fail_counts_match_receipt` | 5.4 |
| Fig5 | 7 | Native force-time definitions and assessment chronology | S02, S09, S16, S21 | `analytical_curve_endpoints_integrals_and_native_windows_are_valid` | 5.5 |
| Fig6 | 8 | Four-model synthetic performance across six outcome-horizon cells | S01, S23; six_cell_results.csv | `all_24_cell_root_values_means_and_sample_sds_match_receipt` | 5.4 |
| Fig7 | 9 | Model-by-cell NRMSE heatmap and per-root structured-minus-ridge differences | S01, S23; six_cell_results.csv | `heatmap_cell_means_six_cell_means_and_ridge_structured_differences_match_receipt` | 5.6 |
| Fig8 | 10 | Recorded paired camp-bootstrap intervals | S01, S23; recorded_uncertainty.csv | `all_six_stored_bootstrap_intervals_match_receipt` | 5.4 |
| Fig9 | 10 | Ablation and nested camp-size diagnostics | S01, S23 | `ablations_and_nested_camp_values_match_receipt` | 5.4 |
| Fig10 | 11 | Rich-history reconstruction and historical row-count differences | S03, S04 | `rich_history_row_counts_and_differences_match_pinned_receipt` | 5.6 |

Minimum plain text is 5.4 pt; the smallest mathematical subscript (the z of F_z in axis labels) is 4.6 pt. Colour encodes the model or evidence category, marker shape encodes the evaluation root, and the heatmap uses a diverging scale centred at NRMSE = 1 with printed values. Grayscale rendering is in `figures_grayscale_check.png`.
