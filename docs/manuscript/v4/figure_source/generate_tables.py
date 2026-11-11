"""Write LaTeX tables for the manuscript directly from the pinned public receipts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT.parents[1]
RES = json.loads((DOCS / "M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json").read_text())
VAR = RES["across_root_variability"]
ARCH = list(csv.DictReader((DOCS / "manuscript/supplement/architecture_qualification.csv").open()))
OUT = ROOT / "tables"
OUT.mkdir(exist_ok=True)
MODELS = [("zero_innovation", "Zero innovation"), ("training_constant", "Training mean"),
          ("ridge_full", "Ridge regression"), ("structured_full", "Structured comparator")]
CELLS = [f"H{h}/{o}" for o in ("relative_peak_mean_force_innovation", "net_impulse_innovation") for h in (24, 48, 72)]


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text, encoding="utf-8")


def overall() -> None:
    rows = [r"\toprule", r"Model & Mean & SD across roots & Range \\", r"\midrule"]
    for key, label in MODELS:
        v = VAR[key]
        rows.append(f"{label} & {v['root_mean_nrmse']:.6f} & {v['root_sample_sd_nrmse']:.6f} & "
                    f"{v['root_min_nrmse']:.4f}--{v['root_max_nrmse']:.4f} \\\\")
    rows.append(r"\bottomrule")
    write("overall.tex", "\\footnotesize\\setlength{\\tabcolsep}{3pt}\\begin{tabular*}{\\columnwidth}{@{\\extracolsep{\\fill}}lrrr}\n" + "\n".join(rows) + "\n\\end{tabular*}\n")


def cells() -> None:
    heads = ["F24", "F48", "F72", "J24", "J48", "J72"]
    rows = [r"\toprule", "Model & " + " & ".join(heads) + r" \\", r"\midrule"]
    for key, label in MODELS:
        vals = [f"{VAR[key]['cell_nrmse_across_roots'][c]['root_mean_nrmse']:.3f}" for c in CELLS]
        rows.append(f"{label} & " + " & ".join(vals) + r" \\")
    rows.append(r"\bottomrule")
    write("cells.tex", "\\footnotesize\\setlength{\\tabcolsep}{3pt}\\begin{tabular*}{\\columnwidth}{@{\\extracolsep{\\fill}}lrrrrrr}\n" + "\n".join(rows) + "\n\\end{tabular*}\n")


def intervals() -> None:
    rows = [r"\toprule", r"Root & Model & NRMSE 95\% interval & Difference from zero \\", r"\midrule"]
    for letter, root in zip("ABC", RES["independent_test_roots"], strict=True):
        for key, label in (("ridge_full", "Ridge"), ("structured_full", "Structured")):
            b = root["paired_camp_bootstrap"]["models"][key]
            lo, hi = b["mean_six_cell_nrmse_95_percentile_interval"]
            dl, dh = b["paired_nrmse_delta_vs_zero_95_percentile_interval"]
            rows.append(f"{letter} & {label} & [{lo:.4f}, {hi:.4f}] & [{dl:.4f}, {dh:.4f}] \\\\")
    rows.append(r"\bottomrule")
    write("intervals.tex", "\\footnotesize\\setlength{\\tabcolsep}{3pt}\\begin{tabular*}{\\columnwidth}{@{\\extracolsep{\\fill}}llrr}\n" + "\n".join(rows) + "\n\\end{tabular*}\n")


def ablations() -> None:
    rows = [r"\toprule", r"Variant & Mean NRMSE & $\Delta$ vs full \\", r"\midrule"]
    for base, label, variants in (
        ("ridge_full", "Ridge", (("ridge_no_prior_history", "without prior history"), ("ridge_no_current_exposure", "without current exposure"), ("ridge_no_participant_context", "without participant context"))),
        ("structured_full", "Structured", (("structured_no_prior_history", "without prior history"),)),
    ):
        rows.append(f"{label}, full & {VAR[base]['root_mean_nrmse']:.6f} & -- \\\\")
        for key, name in variants:
            d = VAR[key]["root_mean_nrmse"] - VAR[base]["root_mean_nrmse"]
            rows.append(f"{label}, {name} & {VAR[key]['root_mean_nrmse']:.6f} & {d:+.6f} \\\\")
    rows.append(r"\bottomrule")
    write("ablations.tex", "\\footnotesize\\setlength{\\tabcolsep}{3pt}\\begin{tabular*}{\\columnwidth}{@{\\extracolsep{\\fill}}lrr}\n" + "\n".join(rows) + "\n\\end{tabular*}\n")


def nested() -> None:
    rows = [r"\toprule", r"Training camps & Ridge & Structured & Training mean \\", r"\midrule"]
    for n in (24, 48, 96):
        vals = [VAR[f"{f}_n{n}"]["root_mean_nrmse"] for f in ("ridge", "structured", "training_constant")]
        rows.append(f"{n} & " + " & ".join(f"{v:.6f}" for v in vals) + r" \\")
    rows.append(r"\bottomrule")
    write("nested.tex", "\\footnotesize\\setlength{\\tabcolsep}{3pt}\\begin{tabular*}{\\columnwidth}{@{\\extracolsep{\\fill}}lrrr}\n" + "\n".join(rows) + "\n\\end{tabular*}\n")


def architectures() -> None:
    seen: dict[str, dict[str, str]] = {}
    for r in ARCH:
        seen.setdefault(r["model"], r)
    rows = [r"\toprule", r"Family & Parameters & Inputs & Structure \\", r"\midrule"]
    for m, r in seen.items():
        arch = r["architecture"].replace("→", r"$\to$").replace("×", r"$\times$").replace("&", r"\&")
        inputs = r["inputs"].replace("×", r"$\times$")
        rows.append(f"{m} & {int(r['parameters']):,} & {inputs} & {arch} \\\\")
    rows.append(r"\bottomrule")
    write("architectures.tex", "\\small\\setlength{\\tabcolsep}{3pt}\\begin{tabularx}{\\textwidth}{@{}lrlX@{}}\n" + "\n".join(rows) + "\n\\end{tabularx}\n")


if __name__ == "__main__":
    overall(); cells(); intervals(); ablations(); nested(); architectures()
    print("tables written")
