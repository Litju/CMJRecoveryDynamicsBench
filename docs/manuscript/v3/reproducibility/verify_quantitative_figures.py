"""Check figure inputs against pinned receipts and write per-figure records."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "evidence" / "release_sources"
AUDIT = ROOT / "evidence" / "v2_audit"
FIGURES = ROOT / "figures"
OUTPUT = ROOT / "reproducibility" / "figure_receipts"


SPECS = {
    "Fig2": {
        "label": "fig:workflow",
        "title": "Public synthetic study sample structure",
        "source_ids": ["S01", "S02"],
        "local_inputs": [],
        "population": "Existing public fixed-mode synthetic study; no athlete observations.",
        "metric": "Counts of camps, episodes, and horizon rows by study split.",
        "units": "Camps; episodes; horizon rows.",
        "grouping": "Training, development, and each of three caller-supplied evaluation roots; H24/H48/H72 queries stay within episode.",
        "sample_sizes": "Training 96 camps/24,000 episodes/72,000 rows; development 16/4,000/12,000; each evaluation root 16/4,000/12,000.",
        "uncertainty": "Not applicable; these are fixed generator sample counts.",
        "test_id": "sample_split_counts_match_pinned_receipt",
    },
    "Fig3": {
        "label": "fig:architecture",
        "title": "Original Gate7 architectures and parameter counts",
        "source_ids": ["S16", "S24", "S25", "S26"],
        "local_inputs": ["evidence/v2_audit/architecture_qualification.csv"],
        "population": "Nine original Gate7 model families M0–M8, with repeats r0 and r1.",
        "metric": "Recorded trainable parameter count per family.",
        "units": "Parameters; architecture widths are dimensionless node counts.",
        "grouping": "Model family; both repeats share the listed family topology and count.",
        "sample_sizes": "9 model families; 18 model-repeat records.",
        "uncertainty": "Not applicable; architecture counts are deterministic records.",
        "test_id": "architecture_families_and_parameter_counts_match_record",
    },
    "Fig4": {
        "label": "fig:numerical",
        "title": "18-route numerical qualification",
        "source_ids": ["S06", "S12", "S13", "S14", "S15", "S16"],
        "local_inputs": ["evidence/v2_audit/model_identity_sanitized.csv"],
        "population": "Privately qualified original Gate7 model-repeat routes; sanitized results only.",
        "metric": "Exact original-source CPU equality; saved-array elementwise tolerance status; recorded maximum absolute difference and failing-element counts.",
        "units": "512 validation rows × 2 output elements/route; raw maximum difference mixes N/kg and m/s outputs.",
        "grouping": "Nine model families M0–M8, two repeats per family.",
        "sample_sizes": "18 routes; 1,024 saved-array elements per route.",
        "uncertainty": "No interval; qualification is a recorded deterministic comparison, not an empirical accuracy estimate.",
        "test_id": "route_population_and_recorded_pass_fail_counts_match_receipt",
    },
    "Fig5": {
        "label": "fig:chronology",
        "title": "Native and public synthetic forecast windows",
        "source_ids": ["S02", "S09", "S16"],
        "local_inputs": [],
        "population": "Native measurement/evaluation contract and a separate public synthetic forecast contract; no observed assessment events.",
        "metric": "Time windows and nominal horizons relative to index exposure.",
        "units": "Hours.",
        "grouping": "Native baseline search, native H72 and D7 target windows, and synthetic H24/H48/H72 query horizons.",
        "sample_sizes": "Three valid trials per native assessment; baseline uses the two latest qualifying assessments. No event sample is plotted.",
        "uncertainty": "Not applicable; windows are protocol definitions.",
        "test_id": "native_windows_and_synthetic_horizons_match_pinned_protocol",
    },
    "Fig6": {
        "label": "fig:mechanics",
        "title": "Analytical vertical force-time measurement illustration",
        "source_ids": ["S09", "S21"],
        "local_inputs": [],
        "population": "Equation-generated analytical signal; not athlete data.",
        "metric": "Vertical force over concentric time; shaded gross force and signed force-minus-bodyweight areas illustrate separate measurement definitions.",
        "units": "Force N; mass kg; time s; gross mean force N/kg; net impulse m/s.",
        "grouping": "One piecewise analytical curve with onset, peak, and takeoff boundaries.",
        "sample_sizes": "361 evenly spaced time points for display; no empirical sample.",
        "uncertainty": "Not applicable; deterministic mathematical illustration.",
        "test_id": "analytical_curve_endpoints_and_signed_integral_are_valid",
    },
    "Fig7": {
        "label": "fig:performance",
        "title": "Four-model public synthetic performance across six cells",
        "source_ids": ["S01", "S23"],
        "local_inputs": ["evidence/v2_audit/six_cell_results.csv"],
        "population": "Four reference models evaluated on three fixed roots from one public synthetic generator.",
        "metric": "Cellwise NRMSE: RMSE divided by that cell's population SD; three root values and the stored root mean are shown.",
        "units": "NRMSE dimensionless; force target N/kg and net-impulse target m/s remain separate cells.",
        "grouping": "Four models × three horizons × two outcomes × three evaluation roots.",
        "sample_sizes": "Each root has 16 camps, 4,000 episodes, and 12,000 horizon rows; 4,000 rows per outcome-horizon cell.",
        "uncertainty": "No confidence interval; root points and their stored mean show descriptive variation across these three fixed same-generator roots.",
        "test_id": "all_24_cell_root_values_means_and_sample_sds_match_receipt",
    },
    "Fig8": {
        "label": "fig:uncertainty",
        "title": "Recorded paired camp-bootstrap intervals",
        "source_ids": ["S01", "S23"],
        "local_inputs": ["evidence/v2_audit/recorded_uncertainty.csv"],
        "population": "Ridge and structured reference models within each of three fixed synthetic roots.",
        "metric": "Stored 95% percentile interval for mean six-cell NRMSE and paired model-minus-zero NRMSE.",
        "units": "NRMSE dimensionless.",
        "grouping": "Model × root; paired model-versus-zero camp resampling within root.",
        "sample_sizes": "5,000 stored replicates; 16 camps resampled per root, preserving 250 episodes and three horizons per camp.",
        "uncertainty": "Conditional within-root bootstrap intervals; no interval is recorded for ridge versus structured or across roots.",
        "test_id": "all_six_stored_bootstrap_intervals_match_receipt",
    },
    "Fig9": {
        "label": "fig:ablation",
        "title": "Recorded ablations and nested training-camp diagnostics",
        "source_ids": ["S01", "S23"],
        "local_inputs": [],
        "population": "Ablation and nested-training results from the same public synthetic generator, evaluated on the same three fixed roots.",
        "metric": "Mean six-cell NRMSE; panel A shows root values and means, panel B shows root-specific nested-camp scores.",
        "units": "NRMSE dimensionless.",
        "grouping": "Model variant × root; nested training sets contain 24, 48, or 96 camps and use the full-data-selected alpha.",
        "sample_sizes": "Three evaluation roots; each has 16 camps. Training subset sizes are 24/48/96 camps.",
        "uncertainty": "No interval; root-specific diagnostics are descriptive and do not identify causal feature effects or athlete sample efficiency.",
        "test_id": "ablations_and_nested_camp_values_match_receipt",
    },
    "Fig10": {
        "label": "fig:scope",
        "title": "Rich-history clean-room and historical row-count differences",
        "source_ids": ["S03", "S04"],
        "local_inputs": [],
        "population": "Recorded clean-room and historical rich-history training and validation materializations.",
        "metric": "Clean-room minus historical horizon-row count.",
        "units": "Horizon rows.",
        "grouping": "Training and public-validation splits.",
        "sample_sizes": "Training 15,134 clean-room vs 15,182 historical rows; validation 3,799 vs 3,795.",
        "uncertainty": "Not applicable; these are recorded membership counts, not response estimates.",
        "test_id": "rich_history_row_counts_and_differences_match_pinned_receipt",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def near(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-14)


def macro_arguments(text: str, start: int) -> list[str]:
    cursor = start
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor < len(text) and text[cursor] == "[":
        cursor = text.index("]", cursor) + 1
    args = []
    for _ in range(3):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        assert text[cursor] == "{", "Malformed EvidenceFigure invocation"
        cursor += 1
        begin = cursor
        depth = 1
        while depth:
            char = text[cursor]
            if char == "\\":
                cursor += 2
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            cursor += 1
        args.append(text[begin : cursor - 1])
    return args


def figure_captions() -> dict[str, str]:
    text = (ROOT / "manuscript.tex").read_text(encoding="utf-8")
    captions = {}
    for match in re.finditer(r"(?m)^\\EvidenceFigure\b", text):
        _, caption, label = macro_arguments(text, match.end())
        captions[label] = caption
    assert set(captions.values())
    return captions


def verify_data():
    study = read_json(RELEASE / "S01_M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json")
    s16 = read_json(RELEASE / "S16_gate7.json")
    routes = read_csv(AUDIT / "model_identity_sanitized.csv")
    architectures = read_csv(AUDIT / "architecture_qualification.csv")
    six_cells = read_csv(AUDIT / "six_cell_results.csv")
    uncertainty = read_csv(AUDIT / "recorded_uncertainty.csv")
    reproduction = read_json(RELEASE / "S04_M8_PUBLIC_REPRODUCTION_RECEIPTS.json")

    split_counts = {}
    for split in ["training", "development"]:
        record = study["data"][split]
        assert record["rows"] == record["episodes"] * 3
        split_counts[split] = {key: record[key] for key in ["camps", "episodes", "rows"]}
    assert split_counts == {
        "training": {"camps": 96, "episodes": 24000, "rows": 72000},
        "development": {"camps": 16, "episodes": 4000, "rows": 12000},
    }
    roots = study["independent_test_roots"]
    assert len(roots) == 3
    assert [root["data"]["root_seed"] for root in roots] == study["protocol"]["test_roots"]
    assert all(root["data"]["rows"] == root["data"]["episodes"] * 3 == 12000 for root in roots)
    assert all(root["data"]["camps"] == 16 and root["data"]["episodes"] == 4000 for root in roots)

    architecture_by_model = {}
    for row in architectures:
        architecture_by_model.setdefault(row["model"], []).append(row)
    assert set(architecture_by_model) == {f"M{i}" for i in range(9)}
    assert all(len(rows) == 2 and len({int(row["parameters"]) for row in rows}) == 1 for rows in architecture_by_model.values())
    parameter_counts = {model: int(rows[0]["parameters"]) for model, rows in architecture_by_model.items()}
    assert min(parameter_counts.values()) == 1346 and max(parameter_counts.values()) == 10796
    assert len(s16["models"]) == 9 and all(model["repeats"] == ["r0", "r1"] for model in s16["models"])

    assert len(routes) == 18
    assert [row["route"] for row in routes] == [f"M{i}-r{r}" for i in range(9) for r in range(2)]
    assert all(row["cpu_source"].startswith("Exact recorded") for row in routes)
    assert all(row["inference_rerun"] == "False" for row in routes)
    cuda_pass = [row for row in routes if row["saved_cuda"].lower() == "pass"]
    cuda_fail = [row for row in routes if row["saved_cuda"].lower() == "fail"]
    assert len(cuda_pass) == 8 and len(cuda_fail) == 10
    assert all(row["saved_cuda"].lower() == ("pass" if int(row["route"][1]) <= 3 else "fail") for row in routes)
    assert all(int(row["failing_elements"]) > 0 for row in cuda_fail)
    assert all(float(row["max_absolute_error"]) > 0 for row in routes)
    statuses_by_family = {model["id"]: model["cuda"] for model in s16["models"]}
    assert all(("pass" if statuses_by_family[row["route"].split("-")[0]] == "Within recorded tolerance" else "fail") == row["saved_cuda"].lower() for row in routes)
    routes_by_id = {row["route"]: row for row in routes}
    assert near(float(routes_by_id["M8-r0"]["max_absolute_error"]), 0.00022125244140625)
    assert near(float(routes_by_id["M8-r1"]["max_absolute_error"]), 0.00030422210693359375)
    assert (int(routes_by_id["M8-r0"]["failing_elements"]), int(routes_by_id["M8-r1"]["failing_elements"])) == (98, 145)

    windows = {window["id"]: window for window in s16["windows"]}
    assert (windows["baseline"]["start"], windows["baseline"]["end"]) == (-240, -24)
    assert (windows["H72"]["start"], windows["H72"]["end"]) == (66, 78)
    assert (windows["D7"]["start"], windows["D7"]["end"]) == (156, 180)
    s09 = (RELEASE / "S09_GATE7_NATIVE_MEASUREMENT_V1.md").read_text(encoding="utf-8")
    s02 = (RELEASE / "S02_M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md").read_text(encoding="utf-8")
    assert "exactly **three valid trials**" in s09
    assert "two latest distinct valid qualifying assessment summaries" in s09
    assert "H24, H48, and H72" in s02

    # The plotted signal is an equation-based teaching example, not a measured trace.
    mass, gravity, amplitude, peak, duration = 70.0, 9.80665, 1000.0, 0.22, 0.55

    def force(time):
        if time <= peak:
            return mass * gravity + amplitude * math.sin(math.pi * time / (2 * peak))
        return (mass * gravity + amplitude) * (1 - (time - peak) / (duration - peak))

    assert near(force(0), mass * gravity)
    assert near(force(peak), mass * gravity + amplitude)
    assert near(force(duration), 0.0)
    gross_area = mass * gravity * peak + 2 * amplitude * peak / math.pi
    gross_area += 0.5 * (mass * gravity + amplitude) * (duration - peak)
    assert gross_area > 0 and near((gross_area - mass * gravity * duration) / mass, 2.739850606012398)

    assert len(six_cells) == 24
    for row in six_cells:
        source = study["across_root_variability"][row["model"]]["cell_nrmse_across_roots"][row["cell"]]
        for letter in "ABC":
            assert near(float(row[f"root_{letter.lower()}"]), source["root_values"][ord(letter) - ord("A")])
        values = [float(row[f"root_{letter.lower()}"]) for letter in "ABC"]
        assert near(float(row["mean"]), statistics.mean(values))
        assert near(float(row["sample_sd"]), statistics.stdev(values))

    assert len(uncertainty) == 6
    roots_by_letter = {}
    for root in roots:
        match = re.search(r"root-([abc])-", root["data"]["root_seed"])
        assert match
        roots_by_letter[match.group(1).upper()] = root
    for row in uncertainty:
        bootstrap = roots_by_letter[row["root"]]["paired_camp_bootstrap"]["models"][row["model"]]
        assert int(row["valid_replicates"]) == bootstrap["valid_replicates"] == 5000
        assert near(float(row["nrmse_lower"]), bootstrap["mean_six_cell_nrmse_95_percentile_interval"][0])
        assert near(float(row["nrmse_upper"]), bootstrap["mean_six_cell_nrmse_95_percentile_interval"][1])
        assert near(float(row["paired_delta_vs_zero_lower"]), bootstrap["paired_nrmse_delta_vs_zero_95_percentile_interval"][0])
        assert near(float(row["paired_delta_vs_zero_upper"]), bootstrap["paired_nrmse_delta_vs_zero_95_percentile_interval"][1])

    across_root = study["across_root_variability"]
    diagnostic_keys = [
        "ridge_full", "ridge_no_prior_history", "ridge_no_current_exposure",
        "ridge_no_participant_context", "structured_no_prior_history",
        "ridge_n24", "ridge_n48", "ridge_n96", "structured_n24", "structured_n48", "structured_n96",
    ]
    for key in diagnostic_keys:
        record = across_root[key]
        assert len(record["root_values"]) == 3
        assert near(record["root_mean_nrmse"], statistics.mean(record["root_values"]))
    assert study["protocol"]["sample_efficiency"]["camp_counts"] == [24, 48, 96]

    rich_runs = [
        run for run in reproduction["runs"]
        if run["kind"] == "public_split_generation"
        and run["run_spec"]["benchmark"] == "rich_history_camp_recovery"
    ]
    rich = {run["run_spec"]["split"]: run["dataset_output"] for run in rich_runs}
    expected_rows = {"training": (15134, 15182), "public_validation": (3799, 3795)}
    row_differences = {}
    for split, (clean_expected, historical_expected) in expected_rows.items():
        clean = rich[split]["row_count"]
        historical = rich[split]["m2_historical_row_count"]
        assert (clean, historical) == (clean_expected, historical_expected)
        row_differences[split] = clean - historical
    assert row_differences == {"training": -48, "public_validation": 4}
    s03 = (RELEASE / "S03_M8_REPRODUCTION_RESULTS.md").read_text(encoding="utf-8")
    assert "| `rich_history_camp_recovery` | 15,134 / 15,182 | 3,799 / 3,795 |" in s03

    return {
        "training_and_development_split_counts": True,
        "architecture_families_and_parameter_counts": True,
        "18_route_cpu_and_cuda_counts": {"cpu_exact": 18, "cuda_pass": len(cuda_pass), "cuda_fail": len(cuda_fail)},
        "native_protocol_windows": True,
        "analytical_curve_endpoints_and_integral": True,
        "six_cell_root_aggregates_checked": len(six_cells),
        "stored_bootstrap_rows_checked": len(uncertainty),
        "ablation_and_nested_diagnostics_checked": len(diagnostic_keys),
        "rich_history_row_differences": row_differences,
        "new_model_execution": False,
        "new_bootstrap": False,
    }


def main():
    numerical_tests = verify_data()
    source_manifest = read_json(RELEASE / "sources.json")
    source_by_id = {record["source_id"]: record for record in source_manifest}
    caption_by_label = figure_captions()
    generator_sha = sha256(ROOT / "figure_source" / "generate_figures.py")
    tex_sha = sha256(ROOT / "manuscript.tex")
    sources_manifest_sha = sha256(RELEASE / "sources.json")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for figure, spec in SPECS.items():
        assert spec["label"] in caption_by_label, f"Missing caption for {figure}"
        source_digests = {}
        for source_id in spec["source_ids"]:
            record = source_by_id[source_id]
            staged = RELEASE / Path(record["staged_path"]).name
            actual = sha256(staged)
            assert actual == record["sha256"], f"Pinned source mismatch: {source_id}"
            source_digests[source_id] = {
                "path": record["path"],
                "commit": record["commit"],
                "sha256": actual,
            }
        local_digests = {path: sha256(ROOT / path) for path in spec["local_inputs"]}
        inputs = {
            "release_source_manifest_sha256": sources_manifest_sha,
            "release_sources": source_digests,
            "local_data": local_digests,
            "figure_generator_sha256": generator_sha,
            "manuscript_source_sha256": tex_sha,
        }
        pdf = FIGURES / f"{figure}.pdf"
        assert pdf.is_file(), f"Missing figure export {pdf.name}"
        receipt = {
            "figure": figure,
            "title": spec["title"],
            "source_label": spec["label"],
            "population": spec["population"],
            "source_ids": spec["source_ids"],
            "metric": spec["metric"],
            "units": spec["units"],
            "grouping": spec["grouping"],
            "sample_sizes": spec["sample_sizes"],
            "uncertainty": spec["uncertainty"],
            "caption_tex": caption_by_label[spec["label"]],
            "input_digests": inputs,
            "figure_pdf_sha256": sha256(pdf),
            "numerical_test": {
                "id": spec["test_id"],
                "passed": True,
                "checks": numerical_tests,
            },
        }
        (OUTPUT / f"{figure}.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"figure_receipts": len(SPECS), "numerical_tests": numerical_tests}, indent=2))


if __name__ == "__main__":
    main()
