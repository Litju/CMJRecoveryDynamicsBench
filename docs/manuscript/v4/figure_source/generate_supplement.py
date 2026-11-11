"""Generate the technical supplement LaTeX and the figure/table data ledger from public receipts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT.parents[1]
RES_PATH = DOCS / "M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json"
RES = json.loads(RES_PATH.read_text())
VAR = RES["across_root_variability"]
SUP = DOCS / "manuscript/supplement"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def esc(text: str) -> str:
    return text.replace("_", r"\_").replace("&", r"\&").replace("→", r"$\to$").replace("×", r"$\times$")


def longtable(head: list[str], rows: list[list[str]], spec: str) -> str:
    out = ["\\begin{longtable}{" + spec + "}", "\\toprule", " & ".join(head) + r" \\", "\\midrule", "\\endhead"]
    out += [" & ".join(esc(c) for c in r) + r" \\" for r in rows]
    out += ["\\bottomrule", "\\end{longtable}"]
    return "\n".join(out)


def build() -> None:
    s1 = [[k, f"{v['root_mean_nrmse']:.6f}", f"{v['root_sample_sd_nrmse']:.6f}", f"{v['root_min_nrmse']:.6f}", f"{v['root_max_nrmse']:.6f}"] for k, v in VAR.items()]
    six = list(csv.DictReader((SUP / "six_cell_results.csv").open()))
    s2 = [[r["model"], r["cell"].replace("relative_peak_mean_force_innovation", "mean_force_innovation[legacy key]"), *(f"{float(r[c]):.4f}" for c in ("root_a", "root_b", "root_c", "mean"))] for r in six]
    s3 = []
    for letter, root in zip("ABC", RES["independent_test_roots"], strict=True):
        for key, b in root["paired_camp_bootstrap"]["models"].items():
            lo, hi = b["mean_six_cell_nrmse_95_percentile_interval"]
            dl, dh = b["paired_nrmse_delta_vs_zero_95_percentile_interval"]
            s3.append([letter, key, f"[{lo:.4f}, {hi:.4f}]", f"[{dl:.4f}, {dh:.4f}]"])
    arch = list(csv.DictReader((SUP / "architecture_qualification.csv").open()))
    s4 = [[r["model"], r["repeat"], r["parameters"], r["cpu_source"], r["saved_cuda"]] for r in arch]
    text = "\n".join([
        r"\documentclass[9pt,a4paper]{extarticle}",
        r"\usepackage[T1]{fontenc}\usepackage{newpxtext,newpxmath}\usepackage{booktabs,longtable,array}\usepackage[margin=18mm]{geometry}\usepackage{hyperref}\usepackage{xurl}",
        r"\begin{document}",
        r"\section*{Technical supplement: Modeling Countermovement-Jump Recovery}",
        r"All values are read from the public fixed-mode reference-study receipt and the public model-qualification summary. Descriptive synthetic results; not athlete accuracy.",
        r"\subsection*{S1 All evaluated variants: mean six-cell NRMSE across three roots}",
        longtable(["Variant", "Mean", "SD", "Min", "Max"], s1, "lrrrr"),
        r"\subsection*{S2 Per-cell NRMSE by root (four reference models)}\small",
        longtable(["Model", "Cell", "Root A", "Root B", "Root C", "Mean"], s2, "llrrrr"),
        r"\subsection*{S3 Recorded camp-bootstrap intervals (all 17 variants; difference is from zero innovation)}\small",
        longtable(["Root", "Variant", "NRMSE 95\\% interval", "Difference from zero"], s3, "llrr"),
        r"\subsection*{S4 Original architecture routes (descriptive, no performance)}\small",
        longtable(["Family", "Repeat", "Parameters", "CPU vs original source", "Saved CUDA arrays"], s4, "llrll"),
        r"\end{document}",
    ])
    (ROOT / "supplement/technical_supplement.tex").write_text(text + "\n", encoding="utf-8")
    ledger = []
    for fig, keys in {
        "Fig7": "across_root_variability.*.cell_nrmse_across_roots", "Fig8": "across_root_variability.*", "Fig9": "independent_test_roots[*].paired_camp_bootstrap",
        "Fig10": "across_root_variability.{ridge,structured,training_constant}_{n24,n48,n96,no_*}", "Fig6": "data.*; independent_test_roots[*].data",
    }.items():
        ledger.append({"item": fig, "source": "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json", "keys": keys, "source_sha256": sha(RES_PATH)})
    for tab in ("overall", "cells", "intervals", "ablations", "nested"):
        ledger.append({"item": f"tables/{tab}.tex", "source": "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json", "keys": "across_root_variability / paired_camp_bootstrap", "source_sha256": sha(RES_PATH)})
    arch_path = SUP / "architecture_qualification.csv"
    ledger += [{"item": it, "source": "docs/manuscript/supplement/architecture_qualification.csv", "keys": "all rows", "source_sha256": sha(arch_path)} for it in ("Fig5", "tables/architectures.tex", "Fig11")]
    ledger += [{"item": it, "source": "src/cmj_recovery_dynamics (trial and response routines)", "keys": "realize_concentric_trial; fixed_mode_response; assessment_trials", "source_sha256": ""} for it in ("Fig2", "Fig3", "Fig4")]
    with (ROOT / "reproducibility/data_ledger.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["item", "source", "keys", "source_sha256"])
        writer.writeheader()
        writer.writerows(ledger)


if __name__ == "__main__":
    build()
    print("supplement and ledger written")
