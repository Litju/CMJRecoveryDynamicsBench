"""Regenerate the V3 scientific figures from frozen, public-safe evidence."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "evidence" / "release_sources"
AUDIT = ROOT / "evidence" / "v2_audit"
OUT = ROOT / "figures"

INK = "#18232d"
BLUE = "#286090"
TEAL = "#147d78"
VERMILION = "#b54234"
GOLD = "#b57a18"
PURPLE = "#6b5a8d"
MID = "#626c75"
PALE_BLUE = "#e6eef5"
PALE_TEAL = "#e4f0ed"
PALE_RED = "#f5e7e4"
PALE_GOLD = "#f5efdf"
PALE_GRAY = "#eef0f2"

MODEL_ORDER = ["zero_innovation", "training_constant", "ridge_full", "structured_full"]
MODEL_LABELS = {
    "zero_innovation": "Zero innovation",
    "training_constant": "Training mean",
    "ridge_full": "Ridge regression",
    "structured_full": "Structured comparator",
}
MODEL_COLORS = {
    "zero_innovation": MID,
    "training_constant": GOLD,
    "ridge_full": BLUE,
    "structured_full": VERMILION,
}
ROOT_KEYS = [("A", "root_a", "^"), ("B", "root_b", "o"), ("C", "root_c", "s")]
ROOT_ORDER = ["A", "B", "C"]

plt.rcParams.update(
    {
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "font.size": 8.5,
        "axes.labelsize": 8.5,
        "axes.titlesize": 9,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.3,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": MID,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "grid.color": "#aab2b9",
        "grid.alpha": 0.24,
        "grid.linewidth": 0.55,
        "svg.hashsalt": "cmj-recovery-scientific-figures",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def arrow(ax, start, end, *, color=INK, lw=0.9, connection="arc3"):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            transform=ax.transAxes,
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=lw,
            color=color,
            connectionstyle=connection,
            zorder=2,
        )
    )


def save_figure(fig, stem: str):
    OUT.mkdir(parents=True, exist_ok=True)
    figure_number = int(stem.removeprefix("figure").split("_", 1)[0])
    journal_stem = f"Fig{figure_number}"
    pdf = OUT / f"{journal_stem}.pdf"
    svg = OUT / f"{journal_stem}.svg"
    png = OUT / f"{journal_stem}.png"
    tif = OUT / f"{journal_stem}.tif"
    fig.savefig(
        pdf,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.06,
        metadata={
            "Creator": "Matplotlib",
            "Title": f"Figure {figure_number}: {stem.split('_', 1)[1].replace('_', ' ')}",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    fig.savefig(
        svg,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.06,
        metadata={"Creator": "Matplotlib", "Date": None},
    )
    # Matplotlib uses trailing spaces for SVG path line continuation; they are unnecessary in XML.
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    fig.savefig(
        png,
        format="png",
        dpi=450,
        bbox_inches="tight",
        pad_inches=0.06,
        metadata={"Software": "Matplotlib 3.11.2"},
    )
    fig.savefig(
        tif,
        format="tiff",
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.06,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    with Image.open(tif) as exported:
        rgb = exported.convert("RGB")
    rgb.save(tif, format="TIFF", dpi=(600, 600), compression="tiff_lzw")
    rgb.close()
    with Image.open(tif) as checked:
        if (
            checked.mode != "RGB"
            or checked.info.get("dpi") != (600.0, 600.0)
            or checked.info.get("compression") != "tiff_lzw"
        ):
            raise RuntimeError(f"{tif.name} must be flattened RGB at 600 dpi with LZW compression")
    plt.close(fig)


def plot_genealogy(lineage, formulation_methods):
    fig, ax = plt.subplots(figsize=(6.3, 4.85))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(
        0.5,
        0.97,
        "Recorded formulation ancestry; unresolved links remain open",
        ha="center",
        va="top",
        fontsize=10,
        fontweight="bold",
        color=INK,
        transform=ax.transAxes,
    )
    ax.text(
        0.50,
        0.91,
        "CAMP / HISTORY TASKS",
        ha="center",
        fontsize=7.2,
        fontweight="bold",
        color=MID,
        transform=ax.transAxes,
    )
    ax.text(
        0.50,
        0.46,
        "EPISODE RESPONSE TASKS",
        ha="center",
        fontsize=7.2,
        fontweight="bold",
        color=MID,
        transform=ax.transAxes,
    )

    status_colors = {
        "SUPERSEDED": MID,
        "RETIRED": VERMILION,
        "PROPOSED": GOLD,
        "ACTIVE_CANDIDATE": TEAL,
    }
    positions = {
        "initial_preseason_camp_recovery": (0.08, 0.70),
        "canonical_preseason_camp_recovery": (0.35, 0.70),
        "rich_history_camp_recovery": (0.68, 0.70),
        "preliminary_post_exposure_recovery": (0.08, 0.23),
        "phase_consistent_post_exposure_recovery": (0.31, 0.23),
        "correlated_exposure_recovery": (0.54, 0.23),
        "threshold_response_recovery": (0.78, 0.47),
        "fixed_mode_discrepancy_recovery": (0.78, 0.02),
    }
    width, height = 0.20, 0.185
    label_wrap = {
        "Initial preseason": "Initial\npreseason",
        "Canonical preseason": "Canonical\npreseason",
        "Rich-history camp": "Rich-history\ncamp",
        "Preliminary post-exposure": "Preliminary\npost-exposure",
        "Phase-consistent": "Phase-consistent\npost-exposure",
        "Correlated exposure": "Correlated\nexposure",
        "Threshold response": "Threshold\nresponse",
        "Fixed-mode discrepancy": "Fixed-mode\ndiscrepancy",
    }
    method_by_id = formulation_methods

    # Draw only authenticated parent edges, before nodes.
    for child in lineage:
        parent = child.get("parent")
        if not parent:
            continue
        px, py = positions[parent]
        cx, cy = positions[child["id"]]
        arrow(ax, (px + width, py + height * 0.5), (cx, cy + height * 0.5))

    for item in lineage:
        x, y = positions[item["id"]]
        status = item["status"]
        color = status_colors.get(status, MID)
        methods = method_by_id[item["id"]]
        horizon = "H72 / D7" if "D7" in methods["task"] else "H24 / H48 / H72"
        world = methods["world"].replace("_", " ")
        short_world = {
            "event time adaptation recovery": "event-time adaptation",
            "fitness fatigue impulse response": "fitness-fatigue response",
            "biexponential episode response": "biexponential episode",
            "correlated exposure response": "correlated exposure",
            "threshold response": "threshold response",
            "fixed mode discrepancy response": "fixed-mode discrepancy",
        }.get(world, world)
        label = label_wrap.get(item["label"], item["label"])
        face = {
            "ACTIVE_CANDIDATE": PALE_TEAL,
            "PROPOSED": PALE_GOLD,
            "RETIRED": PALE_RED,
            "SUPERSEDED": PALE_GRAY,
        }.get(status, "white")
        patch = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.01,rounding_size=0.018",
            facecolor=face,
            edgecolor=color,
            linewidth=1.15,
            transform=ax.transAxes,
            zorder=4,
        )
        ax.add_patch(patch)
        ax.text(
            x + width / 2,
            y + height * 0.76,
            label,
            ha="center",
            va="center",
            fontsize=7.1,
            fontweight="bold",
            color=INK,
            transform=ax.transAxes,
            zorder=5,
            linespacing=1.05,
        )
        ax.text(
            x + width / 2,
            y + height * 0.39,
            status.replace("_", " ").lower(),
            ha="center",
            va="center",
            fontsize=6.8,
            color=color,
            transform=ax.transAxes,
            zorder=5,
        )
        ax.text(
            x + width / 2,
            y + height * 0.12,
            f"{short_world}\n{horizon}",
            ha="center",
            va="center",
            fontsize=6.5,
            color=INK,
            transform=ax.transAxes,
            zorder=5,
            linespacing=1.0,
        )

    ax.text(
        0.02,
        0.045,
        "No parent record = unknown ancestry; arrows are not a timeline.",
        fontsize=7.1,
        color=MID,
        transform=ax.transAxes,
    )
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.03)
    save_figure(fig, "figure01_formulation_genealogy")


def plot_sample_design(study_results):
    data = study_results["data"]
    training, development = data["training"], data["development"]
    root_data = study_results["independent_test_roots"][0]["data"]
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    columns = [0.04, 0.46, 0.64, 0.82]
    ax.text(columns[0], 0.87, "Split", fontweight="bold", fontsize=8.6, va="center")
    for x, label in zip(columns[1:], ["Camps", "Episodes", "Horizon rows"], strict=True):
        ax.text(x, 0.87, label, fontweight="bold", fontsize=8.6, ha="center", va="center")
    rows = [
        ("Training", training),
        ("Development", development),
        ("Evaluation root*", root_data),
    ]
    for idx, (label, split) in enumerate(rows):
        y = 0.65 - idx * 0.19
        ax.plot([0.03, 0.97], [y + 0.075, y + 0.075], color="#c9cdd1", lw=0.55)
        ax.text(columns[0], y, label, fontsize=8.4, va="center")
        values = [split["camps"], split["episodes"], split["rows"]]
        for x, value in zip(columns[1:], values, strict=True):
            ax.text(x, y, f"{value:,}", fontsize=8.4, ha="center", va="center")
    ax.plot([0.03, 0.97], [0.075, 0.075], color=INK, lw=0.8)
    ax.text(
        0.04,
        0.005,
        "*Three fixed evaluation roots (A–C) from one generator. Each episode contributes grouped H24, H48, and H72 queries.",
        fontsize=7.4,
        color=MID,
        va="bottom",
    )
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.02)
    save_figure(fig, "figure02_synthetic_sample_structure")


def plot_architecture(architectures):
    fig = plt.figure(figsize=(6.3, 5.8))
    gs = fig.add_gridspec(4, 1, height_ratios=[0.75, 1.0, 1.05, 2.15], hspace=0.20)
    model_params = {r["model"]: int(r["parameters"]) for r in architectures}

    ax1 = fig.add_subplot(gs[0])
    ax1.set_axis_off()
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.text(0.01, 0.95, "A  Raw-feature feedforward backbones", fontsize=8.2, fontweight="bold", va="top")
    for y, model, layers in [(0.63, "M0", "39 → 32 → 2"), (0.40, "M1", "39 → 64 → 2"), (0.17, "M2", "39 → 64 → 64 → 2")]:
        ax1.text(0.04, y, model, fontweight="bold", fontsize=7.8, va="center")
        ax1.text(0.20, y, layers + "  (exact GELU hidden layers)", fontsize=7.8, va="center")
        ax1.text(0.96, y, f"{model_params[model]:,} parameters", fontsize=7.5, ha="right", va="center")

    ax2 = fig.add_subplot(gs[1])
    ax2.set_axis_off()
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.text(0.01, 0.98, "B  History encoding", fontsize=8.2, fontweight="bold", va="top")
    ax2.text(0.04, 0.67, "Family", fontsize=7.3, fontweight="bold")
    ax2.text(0.22, 0.67, "History branch (four records × four values)", fontsize=7.3, fontweight="bold")
    ax2.text(0.63, 0.67, "Pooling and output", fontsize=7.3, fontweight="bold")
    for y, model, encoder in [(0.43, "M3", "pointwise encoder"), (0.18, "M4", "gated recurrent unit, 4 → 32")]:
        ax2.text(0.04, y, model, fontweight="bold", fontsize=7.8, va="center")
        ax2.text(0.22, y, encoder, fontsize=7.6, va="center")
        ax2.text(0.63, y, "mean/latest pool + raw branch → 128 → 2 head", fontsize=7.1, va="center")
    ax2.plot([0.03, 0.97], [0.57, 0.57], color="#c9cdd1", lw=0.55)
    ax2.plot([0.03, 0.97], [0.055, 0.055], color="#c9cdd1", lw=0.55)

    ax3 = fig.add_subplot(gs[2])
    ax3.set_axis_off()
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)
    ax3.text(0.01, 0.98, "C  Horizon and schedule-basis additions", fontsize=8.2, fontweight="bold", va="top")
    additions = [
        ("M5", "M4 + two-entry, eight-dimensional horizon embedding"),
        ("M6", "M5 + first two of five basis values projected to 16"),
        ("M7", "M5 + all five basis values projected to 16"),
        ("M8", "M7 + bias-free linear basis head (5 → 2), added to output"),
    ]
    for idx, (model, description) in enumerate(additions):
        y = 0.73 - idx * 0.19
        ax3.text(0.04, y, model, fontweight="bold", fontsize=7.7, va="center")
        ax3.text(0.20, y, description, fontsize=7.5, va="center")

    ax4 = fig.add_subplot(gs[3])
    ax4.set_title("D  Recorded trainable parameter counts", loc="left", fontsize=8.2, fontweight="bold", pad=3)
    family_order = [f"M{i}" for i in range(9)]
    values = [model_params[m] for m in family_order]
    y = list(range(len(family_order)))
    colors = [BLUE, BLUE, BLUE, TEAL, TEAL, GOLD, PURPLE, PURPLE, VERMILION]
    ax4.barh(y, values, color=colors, edgecolor="white", linewidth=0.5, height=0.62)
    ax4.set_yticks(y, [f"{m}  (r0, r1)" for m in family_order])
    ax4.invert_yaxis()
    ax4.set_xlim(0, 11800)
    ax4.set_xlabel("Trainable parameters")
    ax4.grid(axis="x", zorder=0)
    ax4.set_axisbelow(True)
    for yi, value in zip(y, values, strict=True):
        ax4.text(value + 110, yi, f"{value:,}", va="center", fontsize=7.0)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.985, bottom=0.06)
    save_figure(fig, "figure03_architecture_comparison")


def plot_numerical(routes):
    fig, ax = plt.subplots(figsize=(6.3, 5.35))
    ax.set_xlim(-0.10, 1.0)
    ax.set_ylim(-2.65, len(routes) + 1.0)
    ax.invert_yaxis()
    ax.axis("off")
    cuda_pass = sum(route["saved_cuda"].lower() == "pass" for route in routes)
    ax.text(0.015, -2.34, f"Recovered CPU: {len(routes)}/{len(routes)} exact   |   Archived GPU outputs: {cuda_pass}/{len(routes)} pass, {len(routes) - cuda_pass}/{len(routes)} fail", fontsize=8.1, fontweight="bold", va="center")
    ax.text(0.18, -1.37, "Reference\nCPU output", ha="center", va="center", fontsize=7.4, fontweight="bold")
    ax.text(0.40, -1.37, "Archived\nGPU output", ha="center", va="center", fontsize=7.4, fontweight="bold")
    ax.text(0.68, -1.37, "Maximum absolute\ndifference (mixed units)", ha="center", va="center", fontsize=7.0, fontweight="bold")
    ax.text(0.93, -1.37, "Failing elements\n(of 1,024)", ha="center", va="center", fontsize=7.2, fontweight="bold")

    for i, route in enumerate(routes):
        y = i
        model, repeat = route["route"].split("-")
        if repeat == "r0":
            ax.plot([0.0, 0.98], [y - 0.42, y - 0.42], color="#d6dbe0", lw=0.45, zorder=0)
        ax.text(0.015, y, f"{model}-{repeat}", ha="left", va="center", fontsize=7.5, fontweight="bold" if repeat == "r0" else "normal")
        ax.text(0.18, y, "Exact", ha="center", va="center", fontsize=7.4, fontweight="bold", color=INK)
        cuda = route["saved_cuda"].upper()
        pass_cuda = cuda == "PASS"
        color = INK if pass_cuda else VERMILION
        ax.text(0.40, y, "Pass" if pass_cuda else "Fail", ha="center", va="center", fontsize=7.4, fontweight="bold", color=color)
        error = float(route["max_absolute_error"])
        ax.text(0.68, y, f"{error:.3e}", ha="center", va="center", fontsize=7.2)
        fail = route["failing_elements"]
        ax.text(0.93, y, fail if fail != "not tabulated" else "—", ha="center", va="center", fontsize=7.2)

    ax.text(
        0.015,
        len(routes) + 0.42,
        r"Archived-output criterion: $|a-b|\leq10^{-5}+10^{-4}|b|$. A dash marks an unreported failure count.",
        ha="left",
        va="top",
        fontsize=7.0,
        color=MID,
    )
    fig.subplots_adjust(left=0.015, right=0.985, top=0.96, bottom=0.06)
    save_figure(fig, "figure04_numerical_qualification")


def plot_chronology():
    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    ax.set_xlim(-260, 190)
    ax.set_ylim(-0.1, 2.65)
    ax.set_yticks([1.95, 0.68], ["Native measurement", "Public synthetic queries"])
    ax.tick_params(axis="y", length=0, pad=8)
    ax.set_xlabel("Hours relative to index exposure")
    ax.set_xticks([-240, -168, -120, -72, -24, 0, 24, 48, 72, 120, 168])
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    # Native baseline search window; no event times are fabricated.
    ax.barh(2.0, 216, left=-240, height=0.32, color=PALE_BLUE, edgecolor=BLUE, linewidth=0.9, hatch="///")
    ax.text(-132, 2.0, "Pre-origin baseline search: −240 to −24 h\nselect the two latest qualifying assessments",
            ha="center", va="center", fontsize=7.4, color=INK)
    ax.axvline(0, color=VERMILION, lw=1.2, ls="--", zorder=3)
    ax.scatter([0], [2.0], marker="D", s=40, color=VERMILION, edgecolor="white", zorder=4)
    ax.text(0, 2.32, "Index exposure", ha="center", va="bottom", fontsize=7.4, color=VERMILION)
    ax.barh(1.58, 12, left=66, height=0.24, color=PALE_TEAL, edgecolor=TEAL, linewidth=0.9)
    ax.annotate(
        "H72 window\n66–78 h",
        xy=(72, 1.71),
        xytext=(83, 1.82),
        textcoords="data",
        ha="left",
        va="center",
        fontsize=7.0,
        color=TEAL,
        arrowprops={"arrowstyle": "-", "color": TEAL, "lw": 0.65},
    )
    ax.barh(1.58, 24, left=156, height=0.24, color=PALE_GOLD, edgecolor=GOLD, linewidth=0.9)
    ax.annotate(
        "D7 window\n156–180 h",
        xy=(168, 1.71),
        xytext=(176, 1.82),
        textcoords="data",
        ha="left",
        va="center",
        fontsize=7.0,
        color=GOLD,
        arrowprops={"arrowstyle": "-", "color": GOLD, "lw": 0.65},
    )
    ax.text(-250, 2.40, "3 valid trials per assessment", ha="left", va="center", fontsize=7.2,
            bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#b4bdc4", "lw": 0.6})

    ax.axhline(1.12, color="#b5bcc2", lw=0.6)
    ax.scatter([24, 48, 72], [0.68, 0.68, 0.68], marker="o", s=37, color=BLUE, edgecolor="white", zorder=4)
    for x, label in [(24, "H24"), (48, "H48"), (72, "H72")]:
        ax.text(x, 0.38, label, ha="center", va="top", fontsize=7.4, color=BLUE, fontweight="bold")
    ax.set_yticklabels(["Native measurement", "Public synthetic queries"])
    fig.subplots_adjust(left=0.19, right=0.98, top=0.91, bottom=0.16)
    save_figure(fig, "figure05_horizon_chronology")


def analytical_force(t, mass=70.0, gravity=9.80665, amplitude=1000.0, peak=0.22, duration=0.55):
    if t <= peak:
        return mass * gravity + amplitude * math.sin(math.pi * t / (2 * peak))
    peak_force = mass * gravity + amplitude
    return peak_force * (1 - (t - peak) / (duration - peak))


def plot_mechanics():
    mass, gravity, amplitude, peak, duration = 70.0, 9.80665, 1000.0, 0.22, 0.55
    times = np.linspace(0, duration, 361)
    forces = np.array([analytical_force(float(t), mass, gravity, amplitude, peak, duration) for t in times])
    bodyweight = mass * gravity
    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    ax.fill_between(times, 0, forces, color=PALE_BLUE, alpha=0.86, label="Gross force area")
    ax.fill_between(times, bodyweight, forces, where=forces >= bodyweight, color=PALE_TEAL, alpha=0.88, hatch="///", label="Net impulse: above body weight")
    ax.fill_between(times, bodyweight, forces, where=forces < bodyweight, color=PALE_RED, alpha=0.95, hatch="\\\\", label="Net impulse: below body weight")
    ax.plot(times, forces, color=BLUE, lw=2.0, label=r"$F_z(t)$")
    ax.axhline(bodyweight, color=MID, lw=1.0, ls="--", label=r"$mg$")
    ax.axvline(0, color=TEAL, lw=1.0, ls=":")
    ax.axvline(duration, color=VERMILION, lw=1.0, ls=":")
    ax.scatter([0, duration], [forces[0], forces[-1]], color=[TEAL, VERMILION], s=28, zorder=5)
    ax.annotate("Concentric onset", (0, forces[0]), xytext=(0.07, bodyweight + 650), textcoords="data",
                arrowprops={"arrowstyle": "->", "color": TEAL, "lw": 0.8}, fontsize=7.1, color=TEAL)
    ax.annotate("Takeoff", (duration, forces[-1]), xytext=(0.43, 330), textcoords="data",
                arrowprops={"arrowstyle": "->", "color": VERMILION, "lw": 0.8}, fontsize=7.1, color=VERMILION)
    ax.set_xlim(-0.02, 0.59)
    ax.set_ylim(0, 1850)
    ax.set_xlabel("Time, t (s)")
    ax.set_ylabel(r"Vertical force, $F_z$ (N)")
    ax.grid(alpha=0.20)
    ax.legend(loc="upper right", frameon=False, ncol=2, fontsize=6.8)
    fig.subplots_adjust(left=0.13, right=0.98, top=0.97, bottom=0.15)
    save_figure(fig, "figure06_force_time_mechanics")


def plot_public_performance(six_cells):
    data = {}
    for row in six_cells:
        data[(row["model"], row["cell"])] = row
    horizons = ["H24", "H48", "H72"]
    outcome_names = [
        "relative_peak_mean_force_innovation",
        "net_impulse_innovation",
    ]
    outcome_labels = [
        "Peak mean-force innovation\n(N/kg target)",
        "Net-impulse innovation (m/s target)",
    ]
    fig, axes = plt.subplots(3, 2, figsize=(6.3, 7.2), sharey=True)
    x = np.arange(len(MODEL_ORDER))
    jitter = {"A": -0.18, "B": 0.0, "C": 0.18}
    for col, label in enumerate(outcome_labels):
                axes[0, col].set_title(label, fontsize=8.1, fontweight="bold", pad=5)
    for row_idx, horizon in enumerate(horizons):
        for col_idx, outcome in enumerate(outcome_names):
            ax = axes[row_idx, col_idx]
            cell = f"{horizon}/{outcome}"
            for model_idx, model in enumerate(MODEL_ORDER):
                entry = data[(model, cell)]
                vals = {name: float(entry[key]) for name, key, _ in ROOT_KEYS}
                mean = float(entry["mean"])
                for root, _, marker in ROOT_KEYS:
                    ax.scatter(
                        model_idx + jitter[root],
                        vals[root],
                        marker=marker,
                        s=22,
                        color=MODEL_COLORS[model],
                        edgecolor="white",
                        linewidth=0.45,
                        zorder=3,
                    )
                ax.plot(
                    [model_idx - 0.22, model_idx + 0.22],
                    [mean, mean],
                    color=INK,
                    lw=1.2,
                    solid_capstyle="round",
                    zorder=4,
                )
            ax.set_xlim(-0.5, 3.5)
            ax.set_ylim(0, 3.35)
            ax.grid(axis="y")
            ax.set_axisbelow(True)
            if row_idx == 2:
                ax.set_xticks(x, ["Zero\ninnovation", "Training\nmean", "Ridge\nregression", "Structured\ncomparator"])
            else:
                ax.set_xticks(x, [""] * 4)
            if col_idx == 0:
                ax.set_ylabel(f"{horizon}\nNRMSE")
            else:
                ax.set_ylabel("")
    model_handles = [
        Line2D([0], [0], color=MODEL_COLORS[m], marker="o", linestyle="none", label=MODEL_LABELS[m], markersize=4)
        for m in MODEL_ORDER
    ]
    root_handles = [
        Line2D([0], [0], color=INK, marker=marker, linestyle="none", label=f"Root {root}", markersize=4)
        for root, _, marker in ROOT_KEYS
    ]
    fig.legend(handles=model_handles + root_handles, loc="lower center", ncol=7, frameon=False, bbox_to_anchor=(0.5, -0.005))
    fig.text(0.02, 0.985, "Points: fixed evaluation roots   |   horizontal mark: mean across roots", ha="left", va="top", fontsize=7.1, color=MID)
    fig.subplots_adjust(left=0.11, right=0.99, top=0.93, bottom=0.13, hspace=0.18, wspace=0.18)
    save_figure(fig, "figure07_public_benchmark")


def plot_bootstrap(uncertainty, study_results):
    root_index = {letter: i for i, letter in enumerate(ROOT_ORDER)}
    model_markers = {"ridge_full": "o", "structured_full": "s"}
    model_styles = {"ridge_full": "-", "structured_full": "--"}
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 4.3))
    ax0, ax1 = axes
    y_positions = {}
    y = 0
    for root in ROOT_ORDER:
        for model in ["ridge_full", "structured_full"]:
            y_positions[(root, model)] = y
            y += 1
        y += 0.65

    for row in uncertainty:
        root = row["root"]
        model = row["model"]
        yy = y_positions[(root, model)]
        color = MODEL_COLORS[model]
        score_key = "ridge_full" if model == "ridge_full" else "structured_full"
        estimate = float(study_results["across_root_variability"][score_key]["root_values"][root_index[root]])
        lo, hi = float(row["nrmse_lower"]), float(row["nrmse_upper"])
        ax0.plot([lo, hi], [yy, yy], color=color, lw=2.1, ls=model_styles[model], solid_capstyle="round")
        ax0.scatter([estimate], [yy], marker=model_markers[model], color=color, edgecolor="white", linewidth=0.5, s=28, zorder=3)
        d = float(study_results["across_root_variability"][score_key]["root_deltas_vs_zero"][root_index[root]])
        dlo, dhi = float(row["paired_delta_vs_zero_lower"]), float(row["paired_delta_vs_zero_upper"])
        ax1.plot([dlo, dhi], [yy, yy], color=color, lw=2.1, ls=model_styles[model], solid_capstyle="round")
        ax1.scatter([d], [yy], marker=model_markers[model], color=color, edgecolor="white", linewidth=0.5, s=28, zorder=3)

    for ax in axes:
        ax.set_yticks([y_positions[(r, "ridge_full")] + 0.5 for r in ROOT_ORDER], [f"Root {r}" for r in ROOT_ORDER])
        ax.invert_yaxis()
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
    ax0.set_xlim(0.70, 0.81)
    ax0.set_xlabel("Mean six-cell NRMSE")
    ax0.set_title("Stored 95% bootstrap interval", fontsize=8.0, fontweight="bold")
    ax1.axvline(0, color=INK, lw=0.8, ls="--")
    ax1.set_xlim(-1.88, 0.12)
    ax1.set_xlabel("Δ NRMSE (model − zero innovation)")
    ax1.set_title("Paired interval vs zero", fontsize=8.0, fontweight="bold")
    handles = [
        Line2D([0], [0], color=MODEL_COLORS["ridge_full"], marker="o", lw=2, ls="-", label="Ridge regression"),
        Line2D([0], [0], color=MODEL_COLORS["structured_full"], marker="s", lw=2, ls="--", label="Structured comparator"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.015))
    fig.text(
        0.02,
        0.99,
        "95% percentile intervals: 5,000 paired camp resamples; 16 camps/root; 250 episodes/camp × 3 horizons",
        ha="left",
        va="top",
        fontsize=7.4,
        color=MID,
    )
    fig.subplots_adjust(left=0.11, right=0.99, top=0.89, bottom=0.15, wspace=0.30)
    save_figure(fig, "figure08_bootstrap_uncertainty")


def plot_ablation_sample_size(study_results):
    result = study_results["across_root_variability"]
    fig, axes = plt.subplots(2, 1, figsize=(6.3, 6.5), gridspec_kw={"height_ratios": [1.1, 1.0]})
    ax0, ax1 = axes
    ablations = [
        ("ridge_full", "Full ridge regression", BLUE),
        ("ridge_no_prior_history", "Ridge without prior history", TEAL),
        ("ridge_no_current_exposure", "Ridge without current exposure", VERMILION),
        ("ridge_no_participant_context", "Ridge without participant context", GOLD),
        ("structured_no_prior_history", "Structured comparator without prior history", PURPLE),
    ]
    y_positions = list(range(len(ablations)))
    for yi, (key, label, color) in zip(y_positions, ablations, strict=True):
        values = result[key]["root_values"]
        mean = float(result[key]["root_mean_nrmse"])
        ax0.plot([mean, mean], [yi - 0.25, yi + 0.25], color=INK, lw=1.2, zorder=2)
        for idx, (root, _, marker) in enumerate(ROOT_KEYS):
            ax0.scatter(values[idx], yi, marker=marker, s=27, color=color, edgecolor="white", linewidth=0.5, zorder=3)
        ax0.text(mean + 0.004, yi - 0.17, f"{mean:.4f}", fontsize=7.1, color=INK)
    ax0.set_yticks(y_positions, [label for _, label, _ in ablations])
    ax0.invert_yaxis()
    ax0.set_xlim(0.70, 0.91)
    ax0.set_xlabel("Mean six-cell NRMSE")
    ax0.set_title("A  Recorded full-model and ablation diagnostics", loc="left", fontsize=8.3, fontweight="bold")
    ax0.grid(axis="x")
    ax0.set_axisbelow(True)

    camp_counts = [24, 48, 96]
    root_markers = {"A": "^", "B": "o", "C": "s"}
    for model, color, linestyle in [("ridge", BLUE, "-"), ("structured", VERMILION, "--")]:
        for root_idx, root in enumerate(ROOT_ORDER):
            yvals = [result[f"{model}_n{n}"]["root_values"][root_idx] for n in camp_counts]
            ax1.plot(
                camp_counts,
                yvals,
                color=color,
                linestyle=linestyle,
                linewidth=0.9,
                alpha=0.72,
                marker=root_markers[root],
                markersize=4.2,
                markerfacecolor=color,
                markeredgecolor="white",
                markeredgewidth=0.4,
            )
    ax1.set_xticks(camp_counts)
    ax1.set_xlim(18, 102)
    ax1.set_ylim(0.72, 0.79)
    ax1.set_xlabel("Training camps")
    ax1.set_ylabel("Six-cell NRMSE")
    ax1.set_title("B  Nested camp-size diagnostic (regularization fixed)", loc="left", fontsize=8.3, fontweight="bold")
    ax1.grid(alpha=0.22)
    ax1.set_axisbelow(True)
    handles = [
        Line2D([0], [0], color=BLUE, lw=1.8, label="Ridge"),
        Line2D([0], [0], color=VERMILION, lw=1.8, ls="--", label="Structured"),
    ] + [
        Line2D([0], [0], color=INK, marker=root_markers[root], linestyle="none", label=f"Root {root}", markersize=4)
        for root in ROOT_ORDER
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.005))
    fig.text(0.02, 0.985, "Points show evaluation-root values; vertical marks show three-root means. No causal effect is inferred.", fontsize=7.4, color=MID, va="top")
    fig.subplots_adjust(left=0.31, right=0.98, top=0.93, bottom=0.13, hspace=0.55)
    save_figure(fig, "figure09_ablation_sample_efficiency")


def plot_reconstruction_rows(reproduction_receipts):
    runs = [
        run for run in reproduction_receipts["runs"]
        if run["kind"] == "public_split_generation"
        and run["run_spec"]["benchmark"] == "rich_history_camp_recovery"
    ]
    by_split = {run["run_spec"]["split"]: run["dataset_output"] for run in runs}
    splits = [("training", "Training"), ("public_validation", "Validation")]
    differences = [
        by_split[split]["row_count"] - by_split[split]["m2_historical_row_count"]
        for split, _ in splits
    ]
    fig, ax = plt.subplots(figsize=(6.3, 2.7))
    y = np.arange(len(splits))
    ax.axvline(0, color=INK, lw=0.8, zorder=1)
    for yi, ((split, _), difference) in enumerate(zip(splits, differences, strict=True)):
        color = BLUE if split == "training" else VERMILION
        ax.hlines(yi, 0, difference, color=color, lw=2.0, zorder=2)
        ax.scatter([difference], [yi], color=color, edgecolor="white", linewidth=0.5, s=32, zorder=3)
        offset = (-7, 0) if difference < 0 else (7, 0)
        alignment = "right" if difference < 0 else "left"
        ax.annotate(f"{difference:+,} rows", (difference, yi), xytext=offset, textcoords="offset points", ha=alignment, va="center", fontsize=7.5)
    ax.set_yticks(y, [label for _, label in splits])
    ax.set_ylim(-0.55, 1.55)
    ax.set_xlim(-60, 60)
    ax.set_xlabel("Difference in horizon rows\n(public reconstruction − historical record)")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.20, right=0.98, top=0.95, bottom=0.23)
    save_figure(fig, "figure10_rich_history_row_counts")


def validate_inputs(lineage, architecture, routes, six_cells, uncertainty, study_results):
    assert len(lineage) == 8
    assert len(architecture) == 18
    assert len(routes) == 18
    assert len(six_cells) == 24
    assert len(uncertainty) == 6
    assert set(study_results["protocol"]["registered_cells"]) == {
        "H24/relative_peak_mean_force_innovation",
        "H24/net_impulse_innovation",
        "H48/relative_peak_mean_force_innovation",
        "H48/net_impulse_innovation",
        "H72/relative_peak_mean_force_innovation",
        "H72/net_impulse_innovation",
    }
    assert {row["model"] for row in architecture} == {f"M{i}" for i in range(9)}
    assert all(row["inference_rerun"] == "False" for row in routes)
    assert all(int(row["valid_replicates"]) == 5000 for row in uncertainty)
    assert all(len(study_results["across_root_variability"][m]["root_values"]) == 3 for m in MODEL_ORDER)
    assert (study_results["data"]["training"]["camps"], study_results["data"]["training"]["episodes"], study_results["data"]["training"]["rows"]) == (96, 24000, 72000)
    assert (study_results["data"]["development"]["camps"], study_results["data"]["development"]["episodes"], study_results["data"]["development"]["rows"]) == (16, 4000, 12000)
    assert all((root["data"]["camps"], root["data"]["episodes"], root["data"]["rows"]) == (16, 4000, 12000) for root in study_results["independent_test_roots"])


def main():
    lineage = read_json(RELEASE / "S17_lineage.json")
    formulation_methods = read_json(RELEASE / "S18_formulation-methods.json")
    architecture = read_csv(AUDIT / "architecture_qualification.csv")
    routes = read_csv(AUDIT / "model_identity_sanitized.csv")
    six_cells = read_csv(AUDIT / "six_cell_results.csv")
    uncertainty = read_csv(AUDIT / "recorded_uncertainty.csv")
    study_results = read_json(RELEASE / "S01_M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json")
    reproduction_receipts = read_json(RELEASE / "S04_M8_PUBLIC_REPRODUCTION_RECEIPTS.json")

    validate_inputs(lineage, architecture, routes, six_cells, uncertainty, study_results)
    plot_genealogy(lineage, formulation_methods)
    plot_sample_design(study_results)
    plot_architecture(architecture)
    plot_numerical(routes)
    plot_chronology()
    plot_mechanics()
    plot_public_performance(six_cells)
    plot_bootstrap(uncertainty, study_results)
    plot_ablation_sample_size(study_results)
    plot_reconstruction_rows(reproduction_receipts)
    files = sorted(OUT.glob("Fig*.pdf"))
    assert len(files) == 10, f"Expected 10 PDF figures, found {len(files)}"
    for stem in files:
        for suffix in [".svg", ".png", ".tif"]:
            assert stem.with_suffix(suffix).is_file(), f"Missing export for {stem.stem}{suffix}"
    print(f"Generated {len(files)} figures as PDF, SVG, PNG, and 600 dpi TIFF.")


if __name__ == "__main__":
    main()
