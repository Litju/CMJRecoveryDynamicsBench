"""Render the RES-783 scientific LinkedIn carousel from pinned public receipts.

The carousel is authored as an editable HTML template (``source/carousel.template.html``)
and stylesheet (``source/carousel.css``). This script

1. verifies the SHA-256 of every receipt it reads against the pinned digests;
2. derives every displayed number from those receipts or from the synthetic
   generator's own trial and response routines (no fitting, scoring or resampling);
3. draws the figures as inline SVG, so every mark is placed from a receipt value;
4. writes ``output/carousel.html`` and ``ledger/figure_source_ledger.csv``, which maps
   every displayed value to its page, source file, key and source SHA-256.

``tools/export.mjs`` then prints the PDF, page PNGs and previews. ``tools/build.sh`` runs
both steps and finalizes the PDF metadata and checksums.
"""

# ruff: noqa: E501  (SVG markup, aria labels and receipt keys are long literal strings)
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import math
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from cmj_recovery_dynamics.dynamics.fixed_mode_discrepancy_response import (  # noqa: E402
    AMPLITUDE_FAST_SUPPORT,
    AMPLITUDE_SLOW_SUPPORT,
    FAST_MODE_HOURS,
    SLOW_MODE_HOURS,
    fixed_mode_response,
)
from cmj_recovery_dynamics.observations.episode_summary import assessment_trials  # noqa: E402
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (  # noqa: E402
    GRAVITATIONAL_ACCELERATION_M_PER_S2 as G,
)
from cmj_recovery_dynamics.observations.phase_consistent_force_impulse import (  # noqa: E402
    realize_concentric_trial,
)
from cmj_recovery_dynamics.reproduction.single_exposure import KeyedRandomStreams  # noqa: E402

TEMPLATE = HERE / "source" / "carousel.template.html"
OUTPUT_HTML = HERE / "output" / "carousel.html"
LEDGER = HERE / "ledger" / "figure_source_ledger.csv"

RESULTS = "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json"
ARCHITECTURES = "docs/manuscript/supplement/architecture_qualification.csv"
TRIAL_SOURCE = "src/cmj_recovery_dynamics/observations/phase_consistent_force_impulse.py"
RESPONSE_SOURCE = "src/cmj_recovery_dynamics/dynamics/fixed_mode_discrepancy_response.py"
SUMMARY_SOURCE = "src/cmj_recovery_dynamics/observations/episode_summary.py"
MANUSCRIPT = "docs/manuscript/v4/README.md"
TERMINOLOGY = "docs/science/CONTRACT_AND_TERMINOLOGY.md"
MEASUREMENT = "docs/GATE7_NATIVE_MEASUREMENT_V1.md"

# Digests pinned in docs/science/source_digests.json and the claims register.
PINNED = {
    RESULTS: "cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9",
    ARCHITECTURES: "ff1ae117ee6c29599a97f6aa1dc34913d89a7c00c8a9251a0a94ea2c1b378432",
}
RESULTS_SCIENTIFIC_SHA256 = "25032133d6f3293f722d06d3a618ec1aecec7cef35d2d35524c7431620e4bc71"

OBSERVATORY_URL = "https://recovery-observatory.vercel.app/"
REPOSITORY_URL = "https://github.com/Litju/CMJRecoveryDynamicsBench"
MANUSCRIPT_URL = f"{REPOSITORY_URL}/blob/main/docs/manuscript/v4/full_illustrated_manuscript.pdf"

# Illustrative generator inputs, identical to the manuscript's Fig 2-4 (not athlete data).
ILLUSTRATIVE_FORCE = 20.0  # N/kg
ILLUSTRATIVE_IMPULSE = 2.7  # m/s
ILLUSTRATIVE_AMPLITUDES = (0.04, 0.03)  # fast, slow fraction of baseline
HORIZONS = (24, 48, 72)

MODELS = ("zero_innovation", "training_constant", "ridge_full", "structured_full")
MODEL_LABEL = {
    "zero_innovation": "Zero innovation",
    "training_constant": "Training mean",
    "ridge_full": "Ridge regression",
    "structured_full": "Structured comparator",
}
ROOTS = ("A", "B", "C")
CELLS = [
    (f"H{h}/{key}", label, h)
    for label, key in (
        ("F", "relative_peak_mean_force_innovation"),
        ("J", "net_impulse_innovation"),
    )
    for h in HORIZONS
]

# Observatory palette (website/src/app/tokens.css and website/src/lib/plot-theme.mjs).
INK = "#202c33"
MUTED = "#566169"
GRID = "#ccd1ce"
RULE = "#bfc3bd"
PANEL = "#fffdf7"
PAPER = "#f3f0e7"
COBALT = "#2854b8"
VERMILION = "#b6422b"
OCHRE = "#a5720c"
ZERO = "#586773"
TEAL = "#1f7a6d"
COBALT_WASH = "#e5ebf7"
VERMILION_WASH = "#f6e1dc"
OCHRE_WASH = "#f3ead7"
MODEL_COLOR = {
    "zero_innovation": ZERO,
    "training_constant": OCHRE,
    "ridge_full": COBALT,
    "structured_full": VERMILION,
}


def sha256(path: str) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- tokens


@dataclass(frozen=True)
class Token:
    name: str
    text: str
    unit: str
    source: str
    key: str
    claim: str
    kind: str  # repository_result | repository_definition | synthetic_assumption | illustration | link


class Registry:
    """Every displayed value is a named token with a source; usage is logged per page."""

    def __init__(self) -> None:
        self.tokens: dict[str, Token] = {}
        self.page = 0
        self.used: list[tuple[int, str]] = []

    def add(self, name, text, unit, source, key, claim="", kind="repository_result") -> None:
        if name in self.tokens:
            raise ValueError(f"duplicate token {name}")
        self.tokens[name] = Token(name, str(text), unit, source, key, claim, kind)

    def __call__(self, name: str) -> str:
        token = self.tokens[name]
        if (self.page, name) not in self.used:
            self.used.append((self.page, name))
        return token.text


def f6(x: float) -> str:
    return f"{x:.6f}"


def signed(x: float, digits: int) -> str:
    return f"{x:+.{digits}f}".replace("-", "−")


def build_registry() -> tuple[Registry, dict]:
    for path, digest in PINNED.items():
        actual = sha256(path)
        if actual != digest:
            raise SystemExit(f"{path}: SHA-256 {actual} does not match pinned {digest}")
    results = json.loads((REPO / RESULTS).read_text())
    if results["scientific_results_sha256"] != RESULTS_SCIENTIFIC_SHA256:
        raise SystemExit("results receipt scientific SHA-256 changed")
    var = results["across_root_variability"]
    reg = Registry()
    R = RESULTS

    # Headline six-cell means and per-root values (claims R-01..R-04).
    for claim, model in zip(("R-01", "R-02", "R-03", "R-04"), MODELS, strict=True):
        v = var[model]
        reg.add(
            f"{model}.mean",
            f6(v["root_mean_nrmse"]),
            "NRMSE",
            R,
            f"across_root_variability.{model}.root_mean_nrmse",
            claim,
        )
        reg.add(
            f"{model}.sd",
            f6(v["root_sample_sd_nrmse"]),
            "NRMSE",
            R,
            f"across_root_variability.{model}.root_sample_sd_nrmse",
            claim,
        )
        for root, value in zip(ROOTS, v["root_values"], strict=True):
            reg.add(
                f"{model}.root{root}",
                f"{value:.4f}",
                "NRMSE",
                R,
                f"across_root_variability.{model}.root_values[{ROOTS.index(root)}]",
                claim,
            )
        for cell, short, h in CELLS:
            reg.add(
                f"{model}.{short}{h}",
                f"{v['cell_nrmse_across_roots'][cell]['root_mean_nrmse']:.3f}",
                "NRMSE",
                R,
                f"across_root_variability.{model}.cell_nrmse_across_roots['{cell}'].root_mean_nrmse",
                "R-01..R-04",
            )
    ridge_lower = all(
        r < s
        for r, s in zip(
            var["ridge_full"]["root_values"], var["structured_full"]["root_values"], strict=True
        )
    )
    if not ridge_lower:
        raise SystemExit(
            "ridge is no longer lower than structured in every root; revise the results statement"
        )

    # Ablations (R-05..R-08) and nested training camps (R-09..R-11).
    ablations = {
        "ridge_no_current_exposure": ("ridge_full", "R-06"),
        "ridge_no_prior_history": ("ridge_full", "R-05"),
        "ridge_no_participant_context": ("ridge_full", "R-07"),
        "structured_no_prior_history": ("structured_full", "R-08"),
    }
    for model, (full, claim) in ablations.items():
        value = var[model]["root_mean_nrmse"]
        reg.add(
            f"{model}.mean",
            f6(value),
            "NRMSE",
            R,
            f"across_root_variability.{model}.root_mean_nrmse",
            claim,
        )
        reg.add(
            f"{model}.delta",
            signed(value - var[full]["root_mean_nrmse"], 6),
            "NRMSE",
            R,
            f"{model} minus {full} (root_mean_nrmse)",
            claim,
        )
    for base, claim in (("ridge", "R-09"), ("structured", "R-10"), ("training_constant", "R-11")):
        for n in (24, 48, 96):
            reg.add(
                f"{base}_n{n}",
                f6(var[f"{base}_n{n}"]["root_mean_nrmse"]),
                "NRMSE",
                R,
                f"across_root_variability.{base}_n{n}.root_mean_nrmse",
                claim,
            )

    # Recorded camp-bootstrap intervals (R-12..R-18).
    claims = iter(("R-12", "R-13", "R-14", "R-15", "R-16", "R-17"))
    intervals: dict[tuple[str, str], tuple[float, float]] = {}
    for index, root in enumerate(ROOTS):
        boot = results["independent_test_roots"][index]["paired_camp_bootstrap"]
        if index == 0:
            reg.add(
                "boot.replicates",
                f"{boot['replicates_requested']:,}",
                "replicates",
                R,
                "independent_test_roots[*].paired_camp_bootstrap.replicates_requested",
                "R-12",
            )
            reg.add(
                "boot.camps",
                str(boot["represented_camps"]),
                "camps",
                R,
                "independent_test_roots[*].paired_camp_bootstrap.represented_camps",
                "R-12",
            )
        for model in ("ridge_full", "structured_full"):
            claim = next(claims)
            m = boot["models"][model]
            if m["valid_replicates"] != boot["replicates_requested"]:
                raise SystemExit("invalid bootstrap replicates")
            lo, hi = m["mean_six_cell_nrmse_95_percentile_interval"]
            intervals[(root, model)] = (lo, hi)
            key = f"independent_test_roots[{index}].paired_camp_bootstrap.models.{model}"
            reg.add(
                f"{model}.ci{root}",
                f"[{lo:.4f}, {hi:.4f}]",
                "NRMSE",
                R,
                f"{key}.mean_six_cell_nrmse_95_percentile_interval",
                claim,
            )
            dlo, dhi = m["paired_nrmse_delta_vs_zero_95_percentile_interval"]
            reg.add(
                f"{model}.dz{root}",
                f"[{dlo:.4f}, {dhi:.4f}]".replace("-", "−"),
                "NRMSE",
                R,
                f"{key}.paired_nrmse_delta_vs_zero_95_percentile_interval",
                claim,
            )
            if not dhi < 0:
                raise SystemExit(
                    f"{model} root {root}: paired difference from zero is no longer entirely below 0; revise page 7"
                )
            if "ridge_full_minus_structured_full" in boot["models"]:
                raise SystemExit("a ridge-versus-structured interval now exists; revise page 7")
    alphas = {
        cfg["selected_alpha"]
        for cfg in results["selection"].values()
        if isinstance(cfg, dict) and "selected_alpha" in cfg
    }
    if alphas != {0.01}:
        raise SystemExit(f"selected alphas changed: {alphas}")
    reg.add("alpha", "0.01", "", R, "selection.*.selected_alpha", "R-19")

    # Study design (E-01..E-04).
    data = results["data"]
    for split in ("training", "development"):
        for field in ("camps", "episodes", "rows"):
            reg.add(
                f"{split}.{field}",
                f"{data[split][field]:,}",
                field,
                R,
                f"data.{split}.{field}",
                "E-01",
            )
    roots = [r["data"] for r in results["independent_test_roots"]]
    if len({(r["camps"], r["episodes"], r["rows"]) for r in roots}) != 1 or len(roots) != 3:
        raise SystemExit("evaluation roots no longer share one size")
    reg.add("roots.count", str(len(roots)), "roots", R, "independent_test_roots (length)", "E-02")
    for field in ("camps", "episodes", "rows"):
        reg.add(
            f"root.{field}",
            f"{roots[0][field]:,}",
            field,
            R,
            f"independent_test_roots[*].data.{field}",
            "E-02",
        )
    reg.add(
        "episodes_per_camp",
        f"{data['training']['episodes'] // data['training']['camps']}",
        "episodes",
        R,
        "data.training.episodes / data.training.camps",
        "E-01",
    )
    reg.add(
        "rows_per_camp",
        f"{data['training']['rows'] // data['training']['camps']}",
        "rows",
        R,
        "data.training.rows / data.training.camps",
        "E-01",
    )
    fc = results["feature_contract"]
    reg.add(
        "features.source",
        str(fc["source_fields"]),
        "fields",
        R,
        "feature_contract.source_fields",
        "E-03",
    )
    reg.add(
        "features.encoded",
        str(fc["encoded_fields"]),
        "columns",
        R,
        "feature_contract.encoded_fields",
        "E-03",
    )

    # Architecture contracts (N-01..N-03); never paired with an NRMSE.
    rows = list(csv.DictReader((REPO / ARCHITECTURES).open(encoding="utf-8")))
    families: dict[str, dict] = {}
    for row in rows:
        families.setdefault(row["model"], row)
    if sorted(families) != [f"M{i}" for i in range(9)] or len(rows) != 18:
        raise SystemExit("architecture table no longer has nine families x two repeats")
    for fam, row in families.items():
        reg.add(
            f"{fam}.params",
            f"{int(row['parameters']):,}",
            "parameters",
            ARCHITECTURES,
            f"{fam}.parameters",
            "N-01",
            "repository_definition",
        )
    reg.add(
        "routes",
        str(len(rows)),
        "routes",
        ARCHITECTURES,
        "row count (9 families x r0, r1)",
        "N-01",
        "repository_definition",
    )
    inputs = re.fullmatch(
        r"(\d+) raw \+ (\d+) × (\d+) history \+ horizon \+ (\d+) basis values",
        families["M8"]["inputs"],
    )
    if not inputs:
        raise SystemExit(f"unexpected M8 inputs: {families['M8']['inputs']}")
    raw, records, values, basis = inputs.groups()
    reg.add(
        "arch.raw",
        raw,
        "features",
        ARCHITECTURES,
        "M8.inputs (raw)",
        "N-02",
        "repository_definition",
    )
    reg.add(
        "arch.history",
        f"{records} × {values}",
        "records x values",
        ARCHITECTURES,
        "M8.inputs (history)",
        "N-02",
        "repository_definition",
    )
    reg.add(
        "arch.basis",
        basis,
        "values",
        ARCHITECTURES,
        "M8.inputs (basis)",
        "N-02",
        "repository_definition",
    )

    # Measurement definitions (M-01..M-08) and generator assumptions (A-01..A-02).
    reg.add(
        "g",
        f"{G:.5f}",
        "m/s²",
        TRIAL_SOURCE,
        "GRAVITATIONAL_ACCELERATION_M_PER_S2",
        "M-03",
        "repository_definition",
    )
    reg.add(
        "mode.fast",
        f"{FAST_MODE_HOURS:.0f}",
        "h",
        RESPONSE_SOURCE,
        "FAST_MODE_HOURS",
        "A-01",
        "synthetic_assumption",
    )
    reg.add(
        "mode.slow",
        f"{SLOW_MODE_HOURS:.0f}",
        "h",
        RESPONSE_SOURCE,
        "SLOW_MODE_HOURS",
        "A-01",
        "synthetic_assumption",
    )
    reg.add(
        "af.lo",
        f"{AMPLITUDE_FAST_SUPPORT[0]:.2f}",
        "fraction",
        RESPONSE_SOURCE,
        "AMPLITUDE_FAST_SUPPORT[0]",
        "A-02",
        "synthetic_assumption",
    )
    reg.add(
        "af.hi",
        f"{AMPLITUDE_FAST_SUPPORT[1]:.2f}",
        "fraction",
        RESPONSE_SOURCE,
        "AMPLITUDE_FAST_SUPPORT[1]",
        "A-02",
        "synthetic_assumption",
    )
    reg.add(
        "as.lo",
        f"{AMPLITUDE_SLOW_SUPPORT[0]:.0f}",
        "fraction",
        RESPONSE_SOURCE,
        "AMPLITUDE_SLOW_SUPPORT[0]",
        "A-02",
        "synthetic_assumption",
    )
    reg.add(
        "as.hi",
        f"{AMPLITUDE_SLOW_SUPPORT[1]:.2f}",
        "fraction",
        RESPONSE_SOURCE,
        "AMPLITUDE_SLOW_SUPPORT[1]",
        "A-02",
        "synthetic_assumption",
    )
    reg.add(
        "basis.fast",
        "36",
        "h",
        MEASUREMENT,
        "Five-value basis (36 h decay)",
        "N-03",
        "repository_definition",
    )
    reg.add(
        "basis.slow",
        "120",
        "h",
        MEASUREMENT,
        "Five-value basis (120 h decay)",
        "N-03",
        "repository_definition",
    )

    trial = realize_concentric_trial(ILLUSTRATIVE_FORCE, ILLUSTRATIVE_IMPULSE)
    peak = max(trial.vertical_force_n_per_kg)
    assert math.isclose(
        trial.net_impulse_m_per_s,
        (trial.mean_force_n_per_kg - G) * trial.concentric_duration_seconds,
        abs_tol=1e-9,
    )
    ill = "illustration"
    reg.add(
        "trace.mean",
        f"{trial.mean_force_n_per_kg:.2f}",
        "N/kg",
        TRIAL_SOURCE,
        "realize_concentric_trial(20.0, 2.7).mean_force_n_per_kg",
        "M-01",
        ill,
    )
    reg.add(
        "trace.net",
        f"{trial.net_impulse_m_per_s:.2f}",
        "m/s",
        TRIAL_SOURCE,
        "realize_concentric_trial(20.0, 2.7).net_impulse_m_per_s",
        "M-02",
        ill,
    )
    reg.add(
        "trace.peak",
        f"{peak:.2f}",
        "N/kg",
        TRIAL_SOURCE,
        "max(realize_concentric_trial(20.0, 2.7).vertical_force_n_per_kg)",
        "M-04",
        ill,
    )
    reg.add(
        "trace.duration",
        f"{trial.concentric_duration_seconds:.3f}",
        "s",
        TRIAL_SOURCE,
        "realize_concentric_trial(20.0, 2.7).concentric_duration_seconds",
        "M-04",
        ill,
    )
    reg.add(
        "trace.input_force",
        f"{ILLUSTRATIVE_FORCE:.0f}",
        "N/kg",
        TRIAL_SOURCE,
        "illustrative input (manuscript Fig 2)",
        "M-04",
        ill,
    )
    reg.add(
        "trace.input_impulse",
        f"{ILLUSTRATIVE_IMPULSE}",
        "m/s",
        TRIAL_SOURCE,
        "illustrative input (manuscript Fig 2)",
        "M-04",
        ill,
    )

    a_f, a_s = ILLUSTRATIVE_AMPLITUDES
    reg.add(
        "ill.af",
        f"{a_f:.2f}",
        "fraction",
        RESPONSE_SOURCE,
        "illustrative amplitude (manuscript Fig 4)",
        "A-02",
        ill,
    )
    reg.add(
        "ill.as",
        f"{a_s:.2f}",
        "fraction",
        RESPONSE_SOURCE,
        "illustrative amplitude (manuscript Fig 4)",
        "A-02",
        ill,
    )
    for h in HORIZONS:
        reg.add(
            f"r{h}",
            f"{fixed_mode_response(float(h), a_f, a_s) * 100:.2f}".replace("-", "−"),
            "% of baseline",
            RESPONSE_SOURCE,
            f"fixed_mode_response({h}, {a_f}, {a_s}) x 100",
            "A-01",
            ill,
        )

    # Three-trial assessments: the manuscript's Fig 3 stream, reproduced exactly.
    streams = KeyedRandomStreams("manuscript-illustration")
    criterion_truth = ILLUSTRATIVE_FORCE * (1.0 + fixed_mode_response(24.0, a_f, a_s))
    base = assessment_trials(
        ILLUSTRATIVE_FORCE, metric="force", streams=streams, assessment_key="baseline"
    )
    crit = assessment_trials(
        criterion_truth, metric="force", streams=streams, assessment_key="criterion:H24"
    )
    base_mean, crit_mean = sum(base) / 3, sum(crit) / 3
    for i, v in enumerate(base):
        reg.add(
            f"base.t{i + 1}",
            f"{v:.2f}",
            "N/kg",
            SUMMARY_SOURCE,
            f"assessment_trials(20.0, 'baseline')[{i}]",
            "M-05",
            ill,
        )
    for i, v in enumerate(crit):
        reg.add(
            f"crit.t{i + 1}",
            f"{v:.2f}",
            "N/kg",
            SUMMARY_SOURCE,
            f"assessment_trials(criterion H24, 'criterion:H24')[{i}]",
            "M-05",
            ill,
        )
    reg.add(
        "base.mean",
        f"{base_mean:.2f}",
        "N/kg",
        SUMMARY_SOURCE,
        "mean of the three baseline trials",
        "M-05",
        ill,
    )
    reg.add(
        "crit.mean",
        f"{crit_mean:.2f}",
        "N/kg",
        SUMMARY_SOURCE,
        "mean of the three criterion trials",
        "M-05",
        ill,
    )
    reg.add(
        "innovation",
        signed(crit_mean - base_mean, 2),
        "N/kg",
        SUMMARY_SOURCE,
        "criterion mean minus baseline mean",
        "M-06",
        ill,
    )

    reg.add(
        "release",
        "v1.1.0",
        "",
        MANUSCRIPT,
        "Evidence identity: release v1.1.0",
        "",
        "repository_definition",
    )
    reg.add(
        "receipt.short",
        PINNED[RESULTS][:12],
        "",
        RESULTS,
        "file SHA-256 (first 12 hex)",
        "E-01",
        "repository_definition",
    )
    reg.add(
        "paper.figures",
        "11",
        "figures",
        MANUSCRIPT,
        "full_illustrated_manuscript.pdf: 11 figures",
        "",
        "repository_definition",
    )
    reg.add(
        "paper.tables",
        "6",
        "tables",
        MANUSCRIPT,
        "full_illustrated_manuscript.pdf: 6 tables",
        "",
        "repository_definition",
    )
    for name, url in (
        ("url.observatory", OBSERVATORY_URL),
        ("url.repository", REPOSITORY_URL),
        ("url.manuscript", MANUSCRIPT_URL),
    ):
        reg.add(
            name,
            url,
            "",
            "docs/INDEX.md; README.rst" if name == "url.observatory" else REPOSITORY_URL,
            "public link",
            "",
            "link",
        )

    geometry = {
        "trace": trial,
        "peak": peak,
        "base": base,
        "crit": crit,
        "base_mean": base_mean,
        "crit_mean": crit_mean,
        "intervals": intervals,
        "var": var,
        "families": families,
    }
    return reg, geometry


# ---------------------------------------------------------------------------- SVG kit


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def fmt(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".")


def text(x, y, s, cls="lab", anchor="start", fill=None, extra="", halo=True) -> str:
    """SVG text; by default it carries a paper-coloured halo so it stays legible over lines."""
    fill_attr = f' style="fill:{fill}"' if fill else ""
    cls = f"{cls} h" if halo else cls
    return f'<text x="{fmt(x)}" y="{fmt(y)}" class="{cls}" text-anchor="{anchor}"{fill_attr}{extra}>{s}</text>'


def line(x1, y1, x2, y2, stroke=INK, width=2.0, dash="", extra="") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{stroke}" stroke-width="{width}"{d}{extra}/>'


def rect(x, y, w, h, fill, stroke="none", width=0.0, rx=0.0, extra="") -> str:
    return f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="{fmt(rx)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{extra}/>'


def path(points, stroke=INK, width=3.0, fill="none", dash="", close=False) -> str:
    d = "M" + " L".join(f"{fmt(x)},{fmt(y)}" for x, y in points) + (" Z" if close else "")
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{dash_attr}/>'


def marker(shape, x, y, r, fill, stroke=PANEL, width=2.0) -> str:
    if shape == "A":
        return f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
    if shape == "B":
        return rect(x - r * 0.9, y - r * 0.9, r * 1.8, r * 1.8, fill, stroke, width)
    pts = [(x, y - r * 1.15), (x + r * 1.05, y + r * 0.75), (x - r * 1.05, y + r * 0.75)]
    return path(pts, stroke=stroke, width=width, fill=fill, close=True)


def arrowhead(x, y, direction, size=12, fill=INK) -> str:
    dx, dy = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}[direction]
    px, py = -dy, dx
    pts = [
        (x, y),
        (x - dx * size + px * size * 0.55, y - dy * size + py * size * 0.55),
        (x - dx * size - px * size * 0.55, y - dy * size - py * size * 0.55),
    ]
    return path(pts, stroke=fill, width=1, fill=fill, close=True)


def svg(width, height, body, label) -> str:
    return (
        f'<svg class="fig" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{esc(label)}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(body)}</svg>'
    )


class Scale:
    def __init__(self, d0, d1, r0, r1):
        self.d0, self.d1, self.r0, self.r1 = d0, d1, r0, r1

    def __call__(self, v: float) -> float:
        return self.r0 + (v - self.d0) / (self.d1 - self.d0) * (self.r1 - self.r0)


# ------------------------------------------------------------------------------ figures


def fig_cover(reg: Registry, geo: dict) -> str:
    """Three-step journey: one generator trace, the response curve, the forecast horizons."""
    trial = geo["trace"]
    b: list[str] = []
    W, H = 952, 430
    panels = [
        (0, "01", "Measure", "one simulated jump"),
        (330, "02", "Model", "change after training"),
        (660, "03", "Forecast", "24 · 48 · 72 h ahead"),
    ]
    pw, top, ph = 292, 96, 268
    for x0, num, title, sub in panels:
        b.append(rect(x0, 0, pw, H, PANEL, RULE, 1.5))
        b.append(text(x0 + 22, 44, num, "mono-s", fill=COBALT))
        b.append(text(x0 + 66, 44, title, "labb"))
        b.append(text(x0 + 22, 80, sub, "ax"))
    for x in (300, 630):
        b.append(line(x - 2, H / 2, x + 22, H / 2, INK, 2.5))
        b.append(arrowhead(x + 28, H / 2, "right", 12))
    # 1: force-time trace (Fz/m vs time).
    t, f = trial.time_seconds, trial.vertical_force_n_per_kg
    sx, sy = Scale(0, t[-1], 24, pw - 24), Scale(0, 28, top + ph, top + 20)
    pts = [(sx(a), sy(c)) for a, c in zip(t, f, strict=True)]
    b.append(
        path(
            [(sx(0), sy(G))] + pts + [(sx(t[-1]), sy(G))],
            stroke="none",
            width=0,
            fill=VERMILION_WASH,
            close=True,
        )
    )
    b.append(line(sx(0), sy(G), sx(t[-1]), sy(G), MUTED, 2, "7 5"))
    b.append(path(pts, COBALT, 4.5))
    b.append(line(sx(0), sy(0), sx(t[-1]), sy(0), MUTED, 1.5))
    b.append(text(sx(t[-1]), sy(G) + 28, "g", "ax", "end"))
    b.append(text(sx(0), sy(0) + 30, "force per kg vs time", "ax-s"))
    # 2: response r(tau), illustrative amplitudes.
    a_f, a_s = ILLUSTRATIVE_AMPLITUDES
    x0 = 330
    tx, ty = Scale(0, 96, x0 + 24, x0 + pw - 24), Scale(-8, 1, top + ph, top + 20)
    curve = [
        (tx(h), ty(fixed_mode_response(h, a_f, a_s) * 100)) for h in [i * 0.5 for i in range(193)]
    ]
    b.append(line(tx(0), ty(0), tx(96), ty(0), MUTED, 1.5))
    b.append(path(curve, INK, 4.5))
    b.append(text(tx(0), ty(-8) + 30, "change vs hours", "ax-s"))
    b.append(text(tx(96), ty(0) - 12, "baseline", "ax-xs", "end"))
    # 3: forecast horizons on the same curve.
    x0 = 660
    tx3 = Scale(0, 96, x0 + 24, x0 + pw - 24)
    curve3 = [
        (tx3(h), ty(fixed_mode_response(h, a_f, a_s) * 100)) for h in [i * 0.5 for i in range(193)]
    ]
    b.append(line(tx3(0), ty(0), tx3(96), ty(0), MUTED, 1.5))
    b.append(path(curve3, RULE, 3.5, dash="2 8"))
    for h in HORIZONS:
        y = ty(fixed_mode_response(float(h), a_f, a_s) * 100)
        b.append(line(tx3(h), ty(0), tx3(h), y, COBALT, 2, "4 4"))
        b.append(
            f'<circle cx="{fmt(tx3(h))}" cy="{fmt(y)}" r="11" fill="{COBALT}" stroke="{PANEL}" stroke-width="3"/>'
        )
        b.append(text(tx3(h), ty(0) - 14, f"H{h}", "mono-s", "middle", COBALT))
    b.append(text(tx3(0), ty(-8) + 30, "change at 3 horizons", "ax-s"))
    return svg(
        W,
        H,
        b,
        "Three steps: a simulated force-time trace, the response after training, and forecasts at 24, 48 and 72 hours.",
    )


def fig_force_time(reg: Registry, geo: dict) -> str:
    trial = geo["trace"]
    t, f = trial.time_seconds, trial.vertical_force_n_per_kg
    W, H = 952, 436
    L, R, T, B = 92, 930, 24, 360
    sx, sy = Scale(-0.006, 0.272, L, R), Scale(0, 30, B, T)
    b: list[str] = [rect(0, 0, W, H, PANEL, RULE, 1.5)]
    for v in range(0, 31, 5):
        b.append(line(L, sy(v), R, sy(v), GRID, 1.2))
        b.append(text(L - 14, sy(v) + 8, str(v), "ax", "end"))
    for v in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25):
        b.append(text(sx(v), B + 34, f"{v:.2f}", "ax", "middle"))
    b.append(text((L + R) / 2, H - 14, "time since concentric onset (s)", "ax", "middle"))
    b.append(
        text(
            26,
            (T + B) / 2,
            "force per kg, Fz/m (N/kg)",
            "ax",
            "middle",
            extra=f' transform="rotate(-90 26 {fmt((T + B) / 2)})"',
        )
    )
    pts = [(sx(a), sy(c)) for a, c in zip(t, f, strict=True)]
    b.append(
        path(
            [(sx(0), sy(0))]
            + [(sx(a), sy(min(c, G))) for a, c in zip(t, f, strict=True)]
            + [(sx(t[-1]), sy(0))],
            stroke="none",
            width=0,
            fill=COBALT_WASH,
            close=True,
        )
    )
    b.append(
        path(
            [(sx(0), sy(G))] + pts + [(sx(t[-1]), sy(G))],
            stroke="none",
            width=0,
            fill=VERMILION_WASH,
            close=True,
        )
    )
    b.append(line(L, B, R, B, MUTED, 1.5))
    b.append(line(sx(0), sy(G), sx(t[-1]), sy(G), MUTED, 2.2, "8 6"))
    mean = trial.mean_force_n_per_kg
    b.append(line(sx(0), sy(mean), sx(t[-1]), sy(mean), INK, 3.2))
    b.append(path(pts, COBALT, 5))
    i_peak = max(range(len(f)), key=lambda i: f[i])
    px, py = sx(t[i_peak]), sy(f[i_peak])
    b.append(arrowhead(px, py - 5, "down", 16, INK))
    b.append(line(px + 12, py - 14, 636, py - 14, MUTED, 1.5))
    b.append(text(R - 6, py - 6, f"peak force {reg('trace.peak')} N/kg", "lab", "end"))
    b.append(text(R - 6, py + 22, "not a modeled target", "ax-s", "end"))
    b.append(
        text(px, sy(mean) + 34, f"mean concentric force {reg('trace.mean')} N/kg", "labb", "middle")
    )
    b.append(
        text(
            px,
            sy(G) - 22,
            f"net impulse = area above g = {reg('trace.net')} m/s",
            "lab-s",
            "middle",
            VERMILION,
        )
    )
    b.append(text(px, sy(G) + 36, f"g = {reg('g')} N/kg (body weight per kg)", "ax", "middle"))
    b.append(text(sx(0) + 8, B - 16, "onset", "ax-s", fill=TEAL))
    b.append(
        text(
            sx(t[-1]) - 8,
            B - 16,
            f"takeoff · T = {reg('trace.duration')} s",
            "ax-s",
            "end",
            VERMILION,
        )
    )
    return svg(
        W,
        H,
        b,
        "One simulated concentric trial: force per kilogram against time, with mean force, peak force and the net-impulse area above g.",
    )


def fig_trials(reg: Registry, geo: dict) -> str:
    base, crit = geo["base"], geo["crit"]
    W, H = 952, 196
    b: list[str] = [rect(0, 0, W, H, PANEL, RULE, 1.5)]
    sy = Scale(19.0, 20.3, 178, 96)
    groups = [
        (24, "baseline", "≈ 2 h before", base, "base", COBALT),
        (300, "criterion", "24 h after", crit, "crit", VERMILION),
    ]
    guide_x = 650
    for x0, name, when, vals, key, color in groups:
        mean = sum(vals) / 3
        b.append(text(x0, 38, name, "labb"))
        b.append(text(x0 + (122 if key == "base" else 132), 38, when, "ax-s"))
        b.append(
            line(
                x0 + (346 if key == "base" else 330), sy(mean), guide_x, sy(mean), RULE, 1.5, "5 5"
            )
        )
        b.append(line(x0, sy(mean), x0 + 168, sy(mean), INK, 3.5))
        for i, v in enumerate(vals):
            b.append(
                f'<circle cx="{fmt(x0 + 34 + i * 50)}" cy="{fmt(sy(v))}" r="10" fill="{color}" stroke="{PANEL}" stroke-width="2.5"/>'
            )
        b.append(text(x0 + 184, sy(mean) + 9, f"mean {reg(key + '.mean')}", "mono-s"))
        for i in (1, 2, 3):
            reg(f"{key}.t{i}")
    b.append(text(24, 70, "3 trials each; line = assessment mean (N/kg)", "ax-xs"))
    y_base, y_crit = sy(geo["base_mean"]), sy(geo["crit_mean"])
    b.append(line(guide_x, y_base, guide_x, y_crit - 12, INK, 3))
    b.append(arrowhead(guide_x, y_crit, "down", 14))
    b.append(text(686, 38, "innovation ΔF", "labb"))
    b.append(text(686, 70, "criterion − baseline", "ax-xs"))
    b.append(text(686, 140, reg("innovation"), "big", fill=VERMILION))
    b.append(text(686, 174, "N/kg", "mono-s", fill=VERMILION))
    return svg(
        W,
        H,
        b,
        "Three baseline trials and three criterion trials, their means, and the innovation between them.",
    )


def fig_response(reg: Registry, geo: dict) -> str:
    a_f, a_s = ILLUSTRATIVE_AMPLITUDES
    W, H = 952, 470
    L, R, T, B = 92, 930, 24, 398
    sx, sy = Scale(0, 96, L, R), Scale(-16.5, 1.5, B, T)
    hours = [i * 0.25 for i in range(385)]
    b: list[str] = [rect(0, 0, W, H, PANEL, RULE, 1.5)]
    for v in range(-15, 1, 5):
        b.append(line(L, sy(v), R, sy(v), GRID, 1.2))
        b.append(text(L - 14, sy(v) + 8, f"{v}%".replace("-", "−"), "ax", "end"))
    for h in (0, 24, 48, 72, 96):
        b.append(text(sx(h), B + 34, str(h), "ax", "middle"))
    b.append(text((L + R) / 2, H - 12, "time since training exposure, τ (h)", "ax", "middle"))
    lo = [
        (
            sx(h),
            sy(fixed_mode_response(h, AMPLITUDE_FAST_SUPPORT[0], AMPLITUDE_SLOW_SUPPORT[0]) * 100),
        )
        for h in hours
    ]
    hi = [
        (
            sx(h),
            sy(fixed_mode_response(h, AMPLITUDE_FAST_SUPPORT[1], AMPLITUDE_SLOW_SUPPORT[1]) * 100),
        )
        for h in hours
    ]
    b.append(path(lo + hi[::-1], stroke="none", width=0, fill=OCHRE_WASH, close=True))
    for h in HORIZONS:
        b.append(line(sx(h), T, sx(h), B, RULE, 2))
    fast = [(sx(h), sy(-a_f * math.exp(-h / FAST_MODE_HOURS) * 100)) for h in hours]
    slow = [(sx(h), sy(-a_s * math.exp(-h / SLOW_MODE_HOURS) * 100)) for h in hours]
    total = [(sx(h), sy(fixed_mode_response(h, a_f, a_s) * 100)) for h in hours]
    b.append(path(fast, COBALT, 3, dash="10 7"))
    b.append(path(slow, VERMILION, 3, dash="10 7"))
    b.append(path(total, INK, 5))
    b.append(line(L, sy(0), R, sy(0), MUTED, 1.6))
    for h in HORIZONS:
        y = sy(fixed_mode_response(float(h), a_f, a_s) * 100)
        b.append(
            f'<circle cx="{fmt(sx(h))}" cy="{fmt(y)}" r="10" fill="{INK}" stroke="{PANEL}" stroke-width="3"/>'
        )
        b.append(text(sx(h) + 14, y + 36, f"{reg(f'r{h}')}%", "labb"))
        b.append(text(sx(h) - 8, T + 26, f"H{h}", "mono-s", "end", COBALT))
    lx = 560
    b.append(rect(lx - 16, 210, 370, 176, PANEL, RULE, 1.2))
    b.append(rect(lx, 358, 46, 18, OCHRE_WASH, OCHRE, 1.2))
    b.append(text(lx + 58, 374, "range allowed by the bounds", "lab"))
    b.append(line(lx, 238, lx + 46, 238, COBALT, 3, "10 7"))
    b.append(text(lx + 58, 246, f"fast mode · {reg('mode.fast')} h", "lab"))
    b.append(line(lx, 278, lx + 46, 278, VERMILION, 3, "10 7"))
    b.append(text(lx + 58, 286, f"slow mode · {reg('mode.slow')} h", "lab"))
    b.append(line(lx, 318, lx + 46, 318, INK, 5))
    b.append(
        text(
            lx + 58,
            326,
            f'r(τ): a<tspan baseline-shift="sub" font-size="18">f</tspan> = {reg("ill.af")}, a<tspan baseline-shift="sub" font-size="18">s</tspan> = {reg("ill.as")}',
            "lab",
        )
    )
    return svg(
        W,
        H,
        b,
        "Response r(tau) as the sum of a fast 24-hour and a slow 84-hour mode, with values at 24, 48 and 72 hours.",
    )


COMPONENTS = [
    ("raw", "raw", "MLP"),
    ("hist", "history", "encoder"),
    ("gru", "GRU", "4→32"),
    ("hor", "horizon", "embed"),
    ("basis", "basis", "values"),
    ("head", "basis", "head"),
]
FAMILY_COMPONENTS = {
    "M0": {"raw"},
    "M1": {"raw"},
    "M2": {"raw"},
    "M3": {"raw", "hist"},
    "M4": {"raw", "gru"},
    "M5": {"raw", "gru", "hor"},
    "M6": {"raw", "gru", "hor", "basis"},
    "M7": {"raw", "gru", "hor", "basis"},
    "M8": {"raw", "gru", "hor", "basis", "head"},
}
FAMILY_NOTE = {
    "M0": "39→32→2",
    "M1": "39→64→2",
    "M2": "39→64→64→2",
    "M6": "2 of 5",
    "M7": "5 of 5",
    "M8": "5 of 5",
}


def fig_architectures(reg: Registry, geo: dict) -> str:
    families = geo["families"]
    W, H = 952, 612
    b: list[str] = [rect(0, 0, W, H, PANEL, RULE, 1.5)]
    col0, colw, top, rowh = 88, 87, 104, 52
    barx, barw = 640, 196
    scale = Scale(0, 11000, barx, barx + barw)
    for i, (_, l1, l2) in enumerate(COMPONENTS):
        cx = col0 + colw / 2 + i * colw
        b.append(text(cx, 42, l1, "ax-s", "middle"))
        b.append(text(cx, 70, l2, "ax-s", "middle"))
    b.append(text(barx, 42, "trainable", "ax-s"))
    b.append(text(barx, 70, "parameters", "ax-s"))
    b.append(line(24, top - 16, W - 24, top - 16, INK, 2))
    for r, fam in enumerate(f"M{i}" for i in range(9)):
        y = top + r * rowh + rowh / 2
        if r % 2 == 0:
            b.append(rect(16, y - rowh / 2, W - 32, rowh, "#f7f4ec"))
        b.append(text(34, y + 9, fam, "labb"))
        comps = FAMILY_COMPONENTS[fam]
        for i, (key, _, _) in enumerate(COMPONENTS):
            cx = col0 + colw / 2 + i * colw
            if key in comps:
                b.append(f'<circle cx="{fmt(cx)}" cy="{fmt(y)}" r="12" fill="{INK}"/>')
                if key == "basis":
                    b.append(
                        text(cx, y + 6, FAMILY_NOTE[fam][0], "dot-n", "middle", PANEL, halo=False)
                    )
            else:
                b.append(f'<circle cx="{fmt(cx)}" cy="{fmt(y)}" r="3.5" fill="{RULE}"/>')
        params = int(families[fam]["parameters"])
        b.append(rect(barx, y - 12, scale(params) - barx, 24, COBALT))
        b.append(text(scale(params) + 10, y + 8, reg(f"{fam}.params"), "mono", "start"))
    b.append(
        text(
            col0 + 4 * colw + colw / 2,
            H - 14,
            "number = basis values used (of 5)",
            "ax-xs",
            "middle",
        )
    )
    return svg(
        W,
        H,
        b,
        "Component matrix of the nine original families M0 to M8 with exact trainable parameter counts.",
    )


def fig_design(reg: Registry, geo: dict) -> str:
    W, H = 952, 400
    b: list[str] = [rect(0, 0, W, H, PANEL, RULE, 1.5)]
    sq, gap = 22, 5
    step = sq + gap

    def grid(x0, y0, cols, rows, color):
        for r in range(rows):
            for c in range(cols):
                b.append(rect(x0 + c * step, y0 + r * step, sq, sq, color))

    x_tr, x_dev, x_root, y0 = 28, 390, 650, 104
    b.append(text(x_tr, 44, f"Training · {reg('training.camps')} camps", "labb", fill=COBALT))
    b.append(
        text(x_tr, 76, f"{reg('training.episodes')} episodes · {reg('training.rows')} rows", "ax-s")
    )
    grid(x_tr, y0, 12, 8, COBALT)
    b.append(text(x_dev, 44, f"Development · {reg('development.camps')}", "labb", fill=OCHRE))
    b.append(text(x_dev, 76, "tunes the penalty", "ax-s"))
    grid(x_dev, y0, 8, 2, OCHRE)
    b.append(text(x_root, 44, f"Evaluation · {reg('roots.count')} roots", "labb", fill=VERMILION))
    b.append(text(x_root, 76, f"{reg('root.camps')} camps each", "ax-s"))
    for i, (root, shade) in enumerate(zip(ROOTS, (VERMILION, "#d27a66", "#e6ad9f"), strict=True)):
        yy = y0 + i * 76
        grid(x_root + 30, yy, 8, 2, shade)
        b.append(text(x_root, yy + 35, root, "labb", fill=VERMILION))
    for k, words in enumerate(
        ("same generator,", "different seeds:", "seed variation,", "not new populations")
    ):
        b.append(text(x_dev, y0 + 102 + k * 28, words, "ax-s"))
    b.append(line(24, 334, W - 24, 334, RULE, 1.2))
    b.append(
        text(
            28,
            362,
            f"1 square = 1 camp = {reg('episodes_per_camp')} episodes = {reg('rows_per_camp')} horizon rows",
            "ax-s",
        )
    )
    b.append(
        text(
            28,
            390,
            f"{reg('features.source')} public predictors per row → {reg('features.encoded')} encoded columns",
            "ax-s",
        )
    )
    return svg(
        W,
        H,
        b,
        "Camps per split: 96 training, 16 development and three evaluation roots of 16 camps each.",
    )


def fig_models_cells(reg: Registry, geo: dict) -> str:
    W, H = 952, 300
    b: list[str] = []
    desc = {
        "zero_innovation": "predicts no change",
        "training_constant": "training average per cell",
        "ridge_full": f"linear on all {reg('features.source')} predictors",
        "structured_full": f"built on {reg('mode.fast')} h / {reg('mode.slow')} h decays",
    }
    b.append(text(0, 26, "4 reference models", "labb"))
    for i, model in enumerate(MODELS):
        y = 46 + i * 62
        b.append(rect(0, y, 426, 54, PANEL, RULE, 1.5))
        b.append(rect(0, y, 10, 54, MODEL_COLOR[model]))
        b.append(text(24, y + 24, MODEL_LABEL[model], "lab-s"))
        b.append(text(24, y + 47, desc[model], "ax-xs"))
    x0 = 470
    b.append(text(x0, 26, "× 6 scored cells", "labb"))
    cx0, cw, chh = x0 + 112, 118, 84
    for j, h in enumerate(HORIZONS):
        b.append(text(cx0 + j * cw + (cw - 12) / 2, 74, f"H{h}", "mono-s", "middle", COBALT))
    for i, (sym, unit) in enumerate((("ΔF", "N/kg"), ("ΔJ", "m/s"))):
        y = 92 + i * (chh + 12)
        b.append(text(x0, y + 38, sym, "labb"))
        b.append(text(x0, y + 66, unit, "ax-xs"))
        for j in range(3):
            b.append(rect(cx0 + j * cw, y, cw - 12, chh, COBALT_WASH, COBALT, 1.5))
            b.append(
                text(
                    cx0 + j * cw + (cw - 12) / 2,
                    y + 50,
                    "NRMSE",
                    "mono-xs",
                    "middle",
                    COBALT,
                    halo=False,
                )
            )
    b.append(text(x0, 294, "score = mean of the 6 cells", "ax-xs"))
    return svg(
        W,
        H,
        b,
        "Four evaluated reference models crossed with six scored cells: two outcomes by three horizons.",
    )


def fig_results(reg: Registry, geo: dict) -> str:
    var = geo["var"]
    W, H = 952, 420
    L, R, top, rowh = 250, 900, 52, 71
    sx = Scale(0, 2.6, L, R)
    b: list[str] = [rect(0, 0, W, H, PANEL, RULE, 1.5)]
    axis_y = top + 4 * rowh + 6
    for v in (0, 0.5, 1.0, 1.5, 2.0, 2.5):
        b.append(line(sx(v), top - 8, sx(v), axis_y, GRID, 1.2))
        b.append(text(sx(v), axis_y + 30, f"{v:g}", "ax", "middle"))
    b.append(line(sx(1.0), 20, sx(1.0), axis_y, MUTED, 2, "7 5"))
    b.append(text(sx(1.0) - 12, 36, "1 = error as large as the true spread", "ax-xs", "end", MUTED))
    for i, model in enumerate(MODELS):
        y = top + i * rowh + 26
        color = MODEL_COLOR[model]
        mean = var[model]["root_mean_nrmse"]
        first, *rest = MODEL_LABEL[model].split(" ")
        b.append(text(28, y - 2, first, "labb"))
        b.append(text(28, y + 26, " ".join(rest), "ax-s"))
        b.append(rect(L, y - 16, sx(mean) - L, 32, color))
        roots = " · ".join(f"{root} {reg(f'{model}.root{root}')}" for root in ROOTS)
        b.append(text(L, y + 40, f"roots {roots}", "ax-xs"))
        if model == "zero_innovation":
            b.append(
                text(sx(mean) - 14, y + 9, reg(f"{model}.mean"), "mono-b", "end", PANEL, halo=False)
            )
        else:
            b.append(text(sx(mean) + 14, y + 9, reg(f"{model}.mean"), "mono-b", "start", INK))
    b.append(line(L, axis_y, R, axis_y, MUTED, 1.5))
    b.append(text(L, H - 12, "mean NRMSE over 6 cells and 3 roots", "ax-xs"))
    return svg(
        W,
        H,
        b,
        "Six-cell mean NRMSE for four reference models: "
        + ", ".join(f"{MODEL_LABEL[m]} {reg(f'{m}.mean')}" for m in MODELS)
        + ".",
    )


def fig_heatmap(reg: Registry, geo: dict) -> str:
    var = geo["var"]
    W, H = 952, 272
    L, cw, rh, top = 220, 118, 46, 60
    short_label = {
        "zero_innovation": "Zero",
        "training_constant": "Training mean",
        "ridge_full": "Ridge",
        "structured_full": "Structured",
    }
    b: list[str] = []
    for j, (_, short, h) in enumerate(CELLS):
        cx = L + j * cw + cw / 2
        b.append(text(cx, 24, f"{'ΔF' if short == 'F' else 'ΔJ'}", "lab-s", "middle"))
        b.append(text(cx, 50, f"H{h}", "mono-xs", "middle", COBALT))
    for i, model in enumerate(MODELS):
        y = top + i * rh
        b.append(rect(0, y + 12, 8, rh - 24, MODEL_COLOR[model]))
        b.append(text(20, y + 31, short_label[model], "lab-s"))
        for j, (cell, short, h) in enumerate(CELLS):
            v = var[model]["cell_nrmse_across_roots"][cell]["root_mean_nrmse"]
            if v <= 1.0:
                fill = mix(PANEL, "#9fb5e3", min(1.0, (1.0 - v) / 0.45))
            else:
                fill = mix(PANEL, "#e3a796", min(1.0, (v - 1.0) / 2.2))
            b.append(rect(L + j * cw + 2, y + 2, cw - 4, rh - 4, fill))
            b.append(
                text(
                    L + j * cw + cw / 2,
                    y + 31,
                    reg(f"{model}.{short}{h}"),
                    "mono-s",
                    "middle",
                    INK,
                    halo=False,
                )
            )
    b.append(text(0, H - 6, "per-cell NRMSE, mean of 3 roots · blue below 1, red above 1", "ax-xs"))
    return svg(W, H, b, "NRMSE for each model in each of the six outcome-by-horizon cells.")


def mix(a: str, b_: str, k: float) -> str:
    ca = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b_[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * k):02x}" for x, y in zip(ca, cb, strict=True))


def fig_evidence(reg: Registry, geo: dict) -> str:
    var = geo["var"]
    intervals = geo["intervals"]
    W, H = 952, 600
    b: list[str] = [rect(0, 0, W, H, PANEL, RULE, 1.5)]
    # (a) Recorded intervals.
    b.append(text(28, 40, "a", "panel"))
    b.append(text(60, 40, "Recorded 95% camp-bootstrap intervals", "labb"))
    L, R = 120, 920
    sx = Scale(0.72, 0.79, L, R)
    for v in (0.72, 0.74, 0.76, 0.78):
        b.append(line(sx(v), 62, sx(v), 196, GRID, 1.2))
        b.append(text(sx(v), 222, f"{v:.2f}", "ax-xs", "middle"))
    for i, root in enumerate(ROOTS):
        y = 80 + i * 40
        b.append(text(60, y + 14, root, "labb"))
        for k, model in enumerate(("ridge_full", "structured_full")):
            lo, hi = intervals[(root, model)]
            yy = y + k * 16
            reg(f"{model}.ci{root}")
            b.append(line(sx(lo), yy, sx(hi), yy, MODEL_COLOR[model], 7))
    for k, (label, color) in enumerate((("ridge", COBALT), ("structured", VERMILION))):
        b.append(line(690 + k * 108, 32, 714 + k * 108, 32, color, 7))
        b.append(text(720 + k * 108, 40, label, "ax-xs"))
    # (b) Ablations.
    y0 = 258
    b.append(line(24, y0 - 20, W - 24, y0 - 20, RULE, 1.2))
    b.append(text(28, y0 + 16, "b", "panel"))
    b.append(text(60, y0 + 16, "Ablations: NRMSE change when inputs are removed", "labb"))
    rows = [
        ("ridge_no_current_exposure", "ridge − current exposure", COBALT),
        ("ridge_no_prior_history", "ridge − prior history", COBALT),
        ("ridge_no_participant_context", "ridge − participant context", COBALT),
        ("structured_no_prior_history", "structured − prior history", VERMILION),
    ]
    bx = Scale(0, 0.14, 420, 780)
    for i, (key, label, color) in enumerate(rows):
        y = y0 + 52 + i * 40
        b.append(text(60, y + 9, label, "lab-s"))
        delta = (
            var[key]["root_mean_nrmse"]
            - var["ridge_full" if key.startswith("ridge") else "structured_full"]["root_mean_nrmse"]
        )
        b.append(rect(bx(0), y - 12, max(bx(delta) - bx(0), 3), 24, color))
        b.append(text(max(bx(delta), bx(0) + 3) + 12, y + 9, reg(f"{key}.delta"), "mono-s"))
    # (c) Nested camps.
    y1 = 500
    b.append(line(24, y1 - 22, W - 24, y1 - 22, RULE, 1.2))
    b.append(text(28, y1 + 14, "c", "panel"))
    b.append(text(60, y1 + 14, "Training camps 24 → 48 → 96", "labb"))
    b.append(
        text(
            60,
            y1 + 52,
            f"ridge {reg('ridge_n24')} → {reg('ridge_n48')} → {reg('ridge_n96')}",
            "mono-s",
            fill=COBALT,
        )
    )
    b.append(
        text(
            60,
            y1 + 84,
            f"structured {reg('structured_n24')} → {reg('structured_n48')} → {reg('structured_n96')}",
            "mono-s",
            fill=VERMILION,
        )
    )
    return svg(
        W,
        H,
        b,
        "Recorded bootstrap intervals by root, ablation changes in NRMSE, and nested training-camp diagnostics.",
    )


FIGURES: dict[str, Callable[[Registry, dict], str]] = {
    "cover": fig_cover,
    "force_time": fig_force_time,
    "trials": fig_trials,
    "response": fig_response,
    "architectures": fig_architectures,
    "design": fig_design,
    "models_cells": fig_models_cells,
    "results": fig_results,
    "heatmap": fig_heatmap,
    "evidence": fig_evidence,
}


# ----------------------------------------------------------------------------- render

PAGE_RE = re.compile(r'(<section class="page[^"]*" data-page="(\d+)".*?</section>)', re.S)
SLOT_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.:]+)\s*\}\}")


def render() -> tuple[str, Registry]:
    reg, geo = build_registry()
    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count("<section") != 8:
        raise SystemExit("pages must not contain nested <section> elements")
    pages = PAGE_RE.findall(template)
    if [int(n) for _, n in pages] != list(range(1, 9)):
        raise SystemExit("template must contain pages 1..8 in order")

    def fill(match: re.Match[str]) -> str:
        name = match.group(1)
        if name.startswith("fig:"):
            return FIGURES[name[4:]](reg, geo)
        if name == "page":
            return f"{reg.page:02d}"
        if name not in reg.tokens:
            raise SystemExit(f"unknown token {name} on page {reg.page}")
        return esc(reg(name))

    out = template
    for block, number in pages:
        reg.page = int(number)
        out = out.replace(block, SLOT_RE.sub(fill, block), 1)
    reg.page = 0
    out = SLOT_RE.sub(fill, out)  # head/title tokens
    return out, reg


def write_ledger(reg: Registry) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "page",
            "token",
            "displayed",
            "unit",
            "evidence_class",
            "claim_id",
            "source",
            "key",
            "source_sha256",
        ]
    )
    digests: dict[str, str] = {}
    for page, name in sorted(reg.used, key=lambda pn: (pn[0], pn[1])):
        tok = reg.tokens[name]
        if tok.source not in digests:
            digests[tok.source] = sha256(tok.source) if (REPO / tok.source).is_file() else ""
        writer.writerow(
            [
                page,
                name,
                tok.text,
                tok.unit,
                tok.kind,
                tok.claim,
                tok.source,
                tok.key,
                digests[tok.source],
            ]
        )
    return buffer.getvalue()


def main() -> None:
    out, reg = render()
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(out, encoding="utf-8")
    LEDGER.write_text(write_ledger(reg), encoding="utf-8")
    unused = sorted(set(reg.tokens) - {n for _, n in reg.used})
    print(
        f"wrote {OUTPUT_HTML.relative_to(REPO)} and {LEDGER.relative_to(REPO)} ({len(reg.used)} value uses)"
    )
    if unused:
        print("tokens defined but not displayed:", ", ".join(unused))


if __name__ == "__main__":
    main()
