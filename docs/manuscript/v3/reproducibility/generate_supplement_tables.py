"""Write LaTeX supplement tables directly from frozen source receipts."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "evidence" / "release_sources"
AUDIT = ROOT / "evidence" / "v2_audit"
OUT = ROOT / "supplement" / "tables"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def tex_escape(value) -> str:
    s = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(ch, ch) for ch in s)


def code(value) -> str:
    return r"\texttt{" + tex_escape(value) + "}"


def write_longtable(filename, column_spec, headers, rows, caption, label, *, spacing="3pt", font=r"\footnotesize"):
    out = [
        font,
        rf"\setlength{{\tabcolsep}}{{{spacing}}}",
        r"\renewcommand{\arraystretch}{1.12}",
        rf"\begin{{longtable}}{{{column_spec}}}",
        rf"\caption{{{caption}}}\label{{{label}}}\\",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
        r"\endhead",
        r"\midrule",
        r"\multicolumn{" + str(len(headers)) + r"}{r}{Continued on next page}\\",
        r"\endfoot",
        r"\bottomrule",
        r"\endlastfoot",
    ]
    out.extend(" & ".join(row) + r" \\" for row in rows)
    out.append(r"\end{longtable}")
    (OUT / filename).write_text("\n".join(out) + "\n", encoding="utf-8")


def generate_formulations():
    lineage = read_json(RELEASE / "S17_lineage.json")
    methods = read_json(RELEASE / "S18_formulation-methods.json")
    label_by_id = {row["id"]: row["label"] for row in lineage}
    rows = []
    for row in lineage:
        m = methods[row["id"]]
        parent = label_by_id.get(row["parent"], "Unresolved") if row["parent"] else "Unresolved"
        world = m["world"].replace("_", " ")
        rows.append(
            [
                code(row["label"]),
                tex_escape(row["status"].replace("_", " ") + "; parent: " + parent),
                tex_escape(world + "; " + m["observation"].replace("_", " ")),
                tex_escape(m["task"]),
                tex_escape(m["limitation"]),
            ]
        )
    write_longtable(
        "generated_formulations.tex",
        ">{\\raggedright\\arraybackslash}p{0.95in}>{\\raggedright\\arraybackslash}p{1.10in}>{\\raggedright\\arraybackslash}p{1.50in}>{\\raggedright\\arraybackslash}p{1.10in}>{\\raggedright\\arraybackslash}p{1.15in}",
        ["Identity", "Status / parent", "Response / observation", "Horizon / task", "Limitation"],
        rows,
        "Complete formulation matrix from the recorded lineage and methods register. A missing direct parent is shown as unresolved, not inferred.",
        "supp:formulations",
        spacing="2.6pt",
    )


def generate_architecture():
    rows_in = read_csv(AUDIT / "architecture_qualification.csv")
    by_model = {}
    for row in rows_in:
        by_model.setdefault(row["model"], row)
    rows = []
    for model in [f"M{i}" for i in range(9)]:
        row = by_model[model]
        rows.append(
            [
                code(f"{model} (r0/r1)"),
                tex_escape(row["inputs"]),
                tex_escape(row["architecture"]),
                f"{int(row['parameters']):,}",
            ]
        )
    write_longtable(
        "generated_architecture.tex",
        ">{\\raggedright\\arraybackslash}p{0.80in}>{\\raggedright\\arraybackslash}p{1.05in}>{\\raggedright\\arraybackslash}p{3.25in}r",
        ["Model / repeats", "Inputs", "Architecture", "Parameters"],
        rows,
        "Sanitized architecture and inference contract by family. Repeat-specific private weights and hashes are excluded.",
        "supp:architecture",
        spacing="2.3pt",
    )


def generate_routes():
    rows_in = read_csv(AUDIT / "model_identity_sanitized.csv")
    rows = []
    for row in rows_in:
        rows.append(
            [
                code(row["route"]),
                "Exact",
                tex_escape(row["saved_cuda"]),
                f"{float(row['atol']):.0e} / {float(row['rtol']):.0e}",
                f"{float(row['max_absolute_error']):.8e}",
                tex_escape(row["failing_elements"]),
            ]
        )
    write_longtable(
        "generated_routes.tex",
        ">{\\raggedright\\arraybackslash}p{0.70in}>{\\raggedright\\arraybackslash}p{0.85in}>{\\raggedright\\arraybackslash}p{0.85in}p{0.95in}p{1.40in}p{1.35in}",
        ["Route", "CPU-source", "Saved CUDA", "ATOL/RTOL", "Max abs. error", "Failing elements"],
        rows,
        "All 18 sanitized model-repeat records. The recorded inference-rerun flag is false for every route. The maximum absolute error pools force and impulse outputs with different units and is descriptive only.",
        "supp:routes",
        spacing="4pt",
        font=r"\small",
    )


def generate_sixcells():
    source = read_csv(AUDIT / "six_cell_results.csv")
    rows = []
    order = {model: i for i, model in enumerate(["zero_innovation", "training_constant", "ridge_full", "structured_full"])}
    source.sort(key=lambda r: (r["cell"].split("/")[0], r["cell"].split("/")[1], order[r["model"]]))
    for row in source:
        model_labels = {
            "zero_innovation": "Zero innovation",
            "training_constant": "Training mean",
            "ridge_full": "Ridge",
            "structured_full": "Structured",
        }
        horizon = row["cell"].split("/")[0]
        force_cell = "relative_peak_mean_force" in row["cell"]
        cell_label = "force innovation (N/kg)" if force_cell else "net impulse (m/s)"
        rows.append(
            [
                tex_escape(model_labels[row["model"]]),
                tex_escape(f"{horizon} / {cell_label}"),
                *(f"{float(row[k]):.6f}" for k in ["root_a", "root_b", "root_c", "mean", "sample_sd"]),
            ]
        )
    write_longtable(
        "generated_sixcell.tex",
        ">{\\raggedright\\arraybackslash}p{0.80in}>{\\raggedright\\arraybackslash}p{1.62in}rrrrr",
        ["Model", "Outcome-horizon cell", "Root A", "Root B", "Root C", "Mean", "Sample SD"],
        rows,
        r"Stored cellwise NRMSE by public evaluation root. Values are rounded to 6 decimal places for display; \texttt{six\_cell\_results.csv} retains the full stored values.",
        "supp:sixcell",
        spacing="2.0pt",
    )


def generate_uncertainty():
    rows_in = read_csv(AUDIT / "recorded_uncertainty.csv")
    rows = []
    for row in rows_in:
        rows.append(
            [
                row["root"],
                code(row["model"]),
                f"{float(row['nrmse_lower']):.6f}",
                f"{float(row['nrmse_upper']):.6f}",
                f"{float(row['paired_delta_vs_zero_lower']):.6f}",
                f"{float(row['paired_delta_vs_zero_upper']):.6f}",
                row["valid_replicates"],
            ]
        )
    write_longtable(
        "generated_uncertainty.tex",
        "p{0.42in}p{1.15in}rrrrr",
        ["Root", "Model", "NRMSE low", "NRMSE high", "Delta low", "Delta high", "Replicates"],
        rows,
        r"Recorded 95\% camp-bootstrap percentile endpoints by root. Delta is model minus zero innovation. No ridge-versus-structured interval is recorded.",
        "supp:uncertainty",
        spacing="2.1pt",
    )


def generate_sample_efficiency():
    study = read_json(RELEASE / "S01_M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json")
    results = study["across_root_variability"]
    variants = [
        ("ridge_full", 96, "Full ridge"),
        ("ridge_no_prior_history", 96, "Ridge without prior history"),
        ("ridge_no_current_exposure", 96, "Ridge without current exposure"),
        ("ridge_no_participant_context", 96, "Ridge without participant context"),
        ("structured_no_prior_history", 96, "Structured without prior history"),
        ("ridge_n24", 24, "Ridge, nested 24 camps"),
        ("ridge_n48", 48, "Ridge, nested 48 camps"),
        ("ridge_n96", 96, "Ridge, nested 96 camps"),
        ("structured_n24", 24, "Structured, nested 24 camps"),
        ("structured_n48", 48, "Structured, nested 48 camps"),
        ("structured_n96", 96, "Structured, nested 96 camps"),
    ]
    rows = []
    for key, n, label in variants:
        item = results[key]
        rows.append(
            [
                tex_escape(label),
                str(n),
                "; ".join(f"{r} {float(v):.6f}" for r, v in zip("ABC", item["root_values"], strict=True)),
                "$" + f"{float(item['root_mean_nrmse']):.6f}" + r"\pm" + f"{float(item['root_sample_sd_nrmse']):.6f}" + "$",
            ]
        )
    write_longtable(
        "generated_sample_efficiency.tex",
        ">{\\raggedright\\arraybackslash}p{1.30in}r>{\\raggedright\\arraybackslash}p{2.45in}>{\\raggedright\\arraybackslash}p{1.45in}",
        ["Variant", "Training camps", "Evaluation-root NRMSE", "Root mean ± sample SD"],
        rows,
        "Recorded six-cell NRMSE root values for selected ablation and nested-camp comparisons. Values are rounded to 6 decimal places; source receipt retains full precision.",
        "supp:sample-efficiency",
        spacing="2.0pt",
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert len(read_json(RELEASE / "S17_lineage.json")) == 8
    assert len(read_csv(AUDIT / "architecture_qualification.csv")) == 18
    assert len(read_csv(AUDIT / "model_identity_sanitized.csv")) == 18
    assert len(read_csv(AUDIT / "six_cell_results.csv")) == 24
    assert len(read_csv(AUDIT / "recorded_uncertainty.csv")) == 6
    generate_formulations()
    generate_architecture()
    generate_routes()
    generate_sixcells()
    generate_uncertainty()
    generate_sample_efficiency()
    print("Generated six LaTeX supplement tables from frozen receipts and sanitized records.")


if __name__ == "__main__":
    main()
