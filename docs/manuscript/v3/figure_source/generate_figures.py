"""Regenerate the V3 scientific figures from frozen, public-safe evidence (RES-585 design system).

No training, fitting, checkpoint inference or scoring is performed. Every plotted
quantity is read from the pinned release sources or the sanitized public summaries.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

import figstyle as S
import matplotlib.pyplot as plt
import numpy as np
from figstyle import (
    COBALT,
    INK,
    MID,
    MODEL_COLORS,
    MODEL_LABELS,
    MODEL_ORDER,
    MODEL_SHORT,
    OCHRE,
    PALE_COBALT,
    PALE_GRAY,
    PALE_OCHRE,
    PALE_TEAL,
    PALE_VERMILION,
    ROOT_KEYS,
    ROOT_MARKERS,
    ROOT_ORDER,
    RULE,
    SLATE,
    SOFT,
    TEAL,
    VERMILION,
    axmm,
    canvas,
    new_figure,
    panel_label,
    save_figure,
    tidy_axis,
)
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "evidence" / "release_sources"
AUDIT = ROOT / "evidence" / "v2_audit"

FORCE_CELL = "relative_peak_mean_force_innovation"  # legacy registered score-cell identifier
IMPULSE_CELL = "net_impulse_innovation"
HORIZONS = ["H24", "H48", "H72"]
CELL_ORDER = [f"{h}/{o}" for o in (FORCE_CELL, IMPULSE_CELL) for h in HORIZONS]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def arrow(ax, start, end, *, color=INK, lw=0.8, style="-|>", ls="-", rad=0.0, scale=7):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=scale,
            linewidth=lw,
            color=color,
            linestyle=ls,
            connectionstyle=f"arc3,rad={rad}",
            zorder=2,
            shrinkA=0,
            shrinkB=0,
        )
    )


# ---------------------------------------------------------------------------
# Figure 1 - formulation genealogy
# ---------------------------------------------------------------------------
def plot_genealogy(lineage, methods):
    fig = new_figure(180, 108)
    ax = canvas(fig)
    status_color = {"SUPERSEDED": SLATE, "RETIRED": VERMILION, "PROPOSED": OCHRE, "ACTIVE_CANDIDATE": TEAL}
    status_face = {"SUPERSEDED": PALE_GRAY, "RETIRED": PALE_VERMILION, "PROPOSED": PALE_OCHRE, "ACTIVE_CANDIDATE": PALE_TEAL}
    status_name = {"SUPERSEDED": "superseded", "RETIRED": "retired", "PROPOSED": "proposed", "ACTIVE_CANDIDATE": "active candidate"}
    world_name = {
        "event_time_adaptation_recovery": "event-time adaptation",
        "fitness_fatigue_impulse_response": "fitness–fatigue response",
        "biexponential_episode_response": "biexponential episode response",
        "correlated_exposure_response": "correlated exposure response",
        "threshold_response": "threshold response",
        "fixed_mode_discrepancy_response": "fixed-mode discrepancy",
    }
    obs_name = {
        "camp_history": "camp-history observations",
        "rich_monitoring": "rich-monitoring observations",
        "episode_summary": "paired-trial summaries",
        "phase_consistent_force_impulse": "phase-consistent force trace",
    }
    cw, ch = 36.0, 20.0
    pos = {
        "initial_preseason_camp_recovery": (8.0, 80.0),
        "canonical_preseason_camp_recovery": (54.0, 80.0),
        "rich_history_camp_recovery": (8.0, 50.0),
        "preliminary_post_exposure_recovery": (8.0, 12.0),
        "phase_consistent_post_exposure_recovery": (54.0, 12.0),
        "correlated_exposure_recovery": (100.0, 12.0),
        "threshold_response_recovery": (140.0, 25.0),
        "fixed_mode_discrepancy_recovery": (140.0, 1.0),
    }
    cards = {item["id"]: item for item in lineage}

    ax.add_patch(Rectangle((0, 74), 180, 34, facecolor="#f7f9fb", edgecolor="none", zorder=0))
    ax.add_patch(Rectangle((0, 0), 180, 47, facecolor="#f7f9fb", edgecolor="none", zorder=0))
    ax.text(2, 106, "Camp-state tasks · H72 and D7 targets", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    ax.text(2, 45, "Episode-response tasks · H24, H48 and H72 targets", fontsize=S.FS_TITLE, fontweight="bold", va="top")

    for item in lineage:
        parent = item["parent"]
        if not parent:
            continue
        px, py = pos[parent]
        cx, cy = pos[item["id"]]
        start = (px + cw, py + ch / 2)
        end = (cx, cy + ch / 2)
        if abs(start[1] - end[1]) < 0.01:
            arrow(ax, start, end)
        else:
            arrow(ax, start, end, rad=-0.25 if end[1] > start[1] else 0.25)

    for node_id in ("initial_preseason_camp_recovery", "rich_history_camp_recovery", "preliminary_post_exposure_recovery"):
        x, y = pos[node_id]
        ax.plot([x - 5, x], [y + ch / 2] * 2, color=VERMILION, lw=0.9, ls=(0, (2, 1.6)))
        ax.text(x - 5, y + ch / 2 + 1.0, "?", fontsize=7, color=VERMILION, fontweight="bold", ha="left", va="bottom")

    for node_id, (x, y) in pos.items():
        item = cards[node_id]
        meth = methods[node_id]
        status = item["status"]
        col = status_color[status]
        ax.add_patch(
            FancyBboxPatch((x, y), cw, ch, boxstyle="round,pad=0,rounding_size=1.2", facecolor=status_face[status], edgecolor=col, linewidth=0.9, zorder=3)
        )
        ax.add_patch(Rectangle((x, y + 1.2), 1.6, ch - 2.4, facecolor=col, edgecolor="none", zorder=4))
        ax.text(x + 3.6, y + ch - 2.3, item["label"], fontsize=6.6, fontweight="bold", va="top", zorder=5)
        ax.text(x + 3.6, y + ch - 7.0, status_name[status].upper(), fontsize=5.6, color=col, fontweight="bold", va="top", zorder=5)
        ax.text(x + 3.6, y + ch - 10.4, world_name[meth["world"]], fontsize=5.9, va="top", zorder=5, color=INK)
        ax.text(x + 3.6, y + ch - 13.6, obs_name[meth["observation"]], fontsize=5.9, va="top", zorder=5, color=MID)
        native = "D7" in meth["task"]
        labels = ["H72", "D7"] if native else HORIZONS
        for k, lab in enumerate(labels):
            px = x + 3.9 + k * 8.2
            ax.add_patch(plt.Circle((px, y + 2.7), 1.15, facecolor=col, edgecolor="none", zorder=5))
            ax.text(px + 1.8, y + 2.7, lab, fontsize=5.4, va="center", zorder=5, color=INK)

    ax.text(101, 66, "Solid arrows: direct parent links recorded in the published\nlineage (5 of 8). They are not a calendar timeline.\n? and dashed stubs: direct scientific parent not recorded (3 of 8).",
            fontsize=6.0, color=MID, ha="left", va="top", linespacing=1.4)
    kx = 101
    for k, key in enumerate(["SUPERSEDED", "RETIRED", "PROPOSED", "ACTIVE_CANDIDATE"]):
        ax.add_patch(Rectangle((kx + k * 20, 100.2), 2.4, 2.4, facecolor=status_color[key], edgecolor="none"))
        ax.text(kx + k * 20 + 3.4, 101.4, status_name[key].replace("active candidate", "active"), fontsize=5.8, va="center")
    ax.text(101, 97.0, "Status of each formulation in the archive", fontsize=5.8, color=MID, va="center")
    save_figure(fig, 1, "Formulation genealogy")


# ---------------------------------------------------------------------------
# Figure 2 - synthetic study design
# ---------------------------------------------------------------------------
def plot_sample_design(study):
    data = study["data"]
    roots = study["independent_test_roots"]
    fig = new_figure(180, 102)
    ax = canvas(fig)
    panel_label(fig, "a", 1, 101)
    ax.text(7, 101, "Camps are the unit of separation (one square = 1 camp = 250 episodes = 750 horizon rows)", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    s, g = 4.0, 0.6

    def waffle(x0, y0, count, cols, color):
        for k in range(count):
            r, c = divmod(k, cols)
            ax.add_patch(Rectangle((x0 + c * (s + g), y0 - r * (s + g) - s), s, s, facecolor=color, edgecolor="white", linewidth=0.3))
        rows = math.ceil(count / cols)
        return cols * (s + g) - g, rows * (s + g) - g

    top = 90
    tw, th = waffle(5, top, data["training"]["camps"], 12, COBALT)
    ax.text(5, top + 2.0, f"Training · {data['training']['camps']} camps", fontsize=S.FS_LABEL, fontweight="bold", color=COBALT, va="bottom")
    dx = 5 + tw + 12
    dw, _ = waffle(dx, top, data["development"]["camps"], 8, OCHRE)
    ax.text(dx, top + 2.0, f"Development · {data['development']['camps']}", fontsize=S.FS_LABEL, fontweight="bold", color=OCHRE, va="bottom")
    rx = dx + dw + 10
    shades = {"A": "#c4452e", "B": "#d77a67", "C": "#e6aa9d"}
    ry = top
    for letter in ROOT_ORDER:
        waffle(rx, ry, 16, 8, shades[letter])
        ax.text(rx + dw + 2.0, ry - s - 0.3, f"Root {letter}", fontsize=S.FS_TEXT, va="center", color=INK)
        ry -= 2 * (s + g) + 3.0
    ax.text(rx, top + 2.0, "Evaluation roots · 16 each", fontsize=S.FS_LABEL, fontweight="bold", color=VERMILION, va="bottom")
    ax.text(5, top - th - 2.0, "Three fixed evaluation roots share one generator and differ only by public seed;\nthey are not independent human cohorts.",
            fontsize=S.FS_TEXT - 0.2, color=MID, va="top", linespacing=1.35)

    panel_label(fig, "b", 1, 41)
    ax.text(7, 41, "Rows per split (3 rows per episode)", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    bx = axmm(fig, 36, 5, 66, 28)
    entries = [("Training", data["training"], COBALT), ("Development", data["development"], OCHRE)]
    entries += [(f"Evaluation root {letter}", r["data"], shades[letter]) for letter, r in zip(ROOT_ORDER, roots, strict=True)]
    ypos = np.arange(len(entries))[::-1]
    for y, (_, rec, color) in zip(ypos, entries, strict=True):
        bx.barh(y, rec["rows"], color=color, height=0.62, edgecolor="none")
        bx.text(rec["rows"] + 1200, y, f"{rec['rows']:,} rows · {rec['episodes']:,} episodes", va="center", fontsize=S.FS_TEXT - 0.4)
    bx.set_yticks(ypos, [e[0] for e in entries])
    bx.set_xlim(0, 130000)
    bx.set_xticks([0, 24000, 48000, 72000], ["0", "24k", "48k", "72k"])
    tidy_axis(bx, "x")

    panel_label(fig, "c", 108, 41)
    cx = 108
    ax.text(cx + 6, 41, "One episode: three queries, one split", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    for k, h in enumerate(HORIZONS):
        y = 28 - k * 8.5
        ax.add_patch(FancyBboxPatch((cx + 6, y), 29, 6.4, boxstyle="round,pad=0,rounding_size=0.8", facecolor=PALE_COBALT, edgecolor=COBALT, linewidth=0.6))
        ax.text(cx + 8.2, y + 3.2, f"query {h} · 2 targets", fontsize=S.FS_TEXT - 0.2, va="center")
    ax.plot([cx + 4, cx + 4], [9.5, 34.4], color=INK, lw=0.9)
    ax.text(cx + 1.8, 22, "kept together", rotation=90, fontsize=S.FS_TEXT, ha="center", va="center", color=INK)
    ax.text(cx + 6, 3.4, "Predictors: 82 source fields → 84 numeric columns", fontsize=S.FS_TEXT - 0.2, va="center", color=MID)
    ax.text(cx + 40, 33, "Checked for separation", fontsize=S.FS_TEXT, fontweight="bold", va="center")
    ax.text(cx + 40, 28.4, "participant · episode ·\nquery · camp ids", fontsize=S.FS_TEXT - 0.2, va="center", color=INK, linespacing=1.3)
    ax.text(cx + 40, 20.4, "Excluded predictors", fontsize=S.FS_TEXT, fontweight="bold", color=VERMILION, va="center")
    ax.text(cx + 40, 14.4, "group keys · target labels ·\nfuture-time fields · hidden\neffects, oracle states", fontsize=S.FS_TEXT - 0.2, va="center", color=INK, linespacing=1.3)
    save_figure(fig, 2, "Synthetic study design and separation")


# ---------------------------------------------------------------------------
# Figure 3 - neural architectures and complexity
# ---------------------------------------------------------------------------
def box(ax, x, y, w, h, text, face, edge, *, fs=6.2, bold=False, color=INK, lw=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.9", facecolor=face, edgecolor=edge, linewidth=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=color, zorder=4, linespacing=1.25)


def plot_architecture(architectures):
    params = {r["model"]: int(r["parameters"]) for r in architectures}
    fig = new_figure(180, 144)
    ax = canvas(fig, 0, 16, 180, 128)
    cb = canvas(fig)
    panel_label(fig, "a", 1, 143)
    ax.text(7, 127, "Computational graph of the largest family (M8); each module is labelled with its first family", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    purple = "#6b5a8d"
    ix, iw, ih = 3, 30, 10
    rows = {"raw": 100, "hist": 82, "hor": 64, "basis": 46}
    box(ax, ix, rows["raw"], iw, ih, "39 standardized\nraw predictors", PALE_GRAY, SLATE)
    box(ax, ix, rows["hist"], iw, ih, "history\n4 records × 4 values", PALE_GRAY, SLATE)
    box(ax, ix, rows["hor"], iw, ih, "horizon index\n(2 entries)", PALE_GRAY, SLATE)
    box(ax, ix, rows["basis"], iw, ih, "schedule basis\n5 values", PALE_GRAY, SLATE)

    ex, ew = 48, 40
    box(ax, ex, rows["raw"], ew, ih, "raw backbone\nM0 39→32 · M1 39→64 · M2 39→64→64", PALE_COBALT, COBALT, fs=5.7)
    box(ax, ex, rows["hist"] + 5.2, ew, 5.6, "pointwise encoder (M3)", PALE_TEAL, TEAL, fs=5.9)
    box(ax, ex, rows["hist"] - 0.8, ew, 5.6, "GRU 4→32 replaces encoder (M4)", PALE_TEAL, TEAL, fs=5.9)
    box(ax, ex, rows["hor"], ew, ih, "embedding\n2 entries × 8 dims (M5)", PALE_OCHRE, OCHRE)
    box(ax, ex, rows["basis"] + 5.2, ew, 5.6, "first 2 values → 16 (M6)", "#e7e2f1", purple, fs=5.9)
    box(ax, ex, rows["basis"] - 0.8, ew, 5.6, "all 5 values → 16 (M7, M8)", "#e7e2f1", purple, fs=5.9)
    box(ax, 100, rows["hist"] - 0.8, 24, 11.6, "mean ⊕ latest\npooling", PALE_TEAL, TEAL, fs=5.9)
    box(ax, 131, 62, 20, 36, "concatenate\n\nwidth\nM3, M4: 128\nM5: 136\nM6–M8: 152", "white", INK, fs=5.9, lw=0.9)
    box(ax, 157, 74, 20, 12, "linear head\n→ 2 outputs", PALE_COBALT, COBALT, fs=6.0, lw=0.9)
    box(ax, 120, 38, 57, 10, "bias-free linear basis head 5 → 2 (M8)\nadded to the output", PALE_VERMILION, VERMILION, fs=5.7)
    ax.text(167, 88, "additive innovations:\nforce, net impulse", fontsize=5.7, color=MID, ha="center", va="bottom", linespacing=1.25)

    def link(p0, p1):
        arrow(ax, p0, p1, color=MID, lw=0.6, scale=5)

    link((ix + iw, rows["raw"] + ih / 2), (ex, rows["raw"] + ih / 2))
    link((ix + iw, rows["hist"] + 5), (ex, rows["hist"] + 8))
    link((ix + iw, rows["hist"] + 5), (ex, rows["hist"] + 2))
    link((ix + iw, rows["hor"] + ih / 2), (ex, rows["hor"] + ih / 2))
    link((ix + iw, rows["basis"] + 5), (ex, rows["basis"] + 8))
    link((ix + iw, rows["basis"] + 5), (ex, rows["basis"] + 2))
    link((ex + ew, rows["raw"] + ih / 2), (131, 92))
    link((ex + ew, rows["hist"] + 8), (100, rows["hist"] + 6.5))
    link((ex + ew, rows["hist"] + 2), (100, rows["hist"] + 4.0))
    link((124, rows["hist"] + 5), (131, 82))
    link((ex + ew, rows["hor"] + ih / 2), (131, 72))
    link((ex + ew, rows["basis"] + 8), (131, 66))
    link((ex + ew, rows["basis"] + 2), (131, 64.5))
    link((151, 80), (157, 80))
    ax.plot([ix + iw + 2, ix + iw + 2, 119], [rows["basis"] + 5, 43, 43], color=MID, lw=0.6)
    link((119, 43), (120, 43))
    link((160, 48), (167, 74))
    ax.text(3, 33.5, "Outputs differ in unit: force innovation (N/kg) and net-impulse innovation (m/s) occupy separate columns. M0–M2 use only the raw branch.",
            fontsize=5.8, color=MID, va="top")

    panel_label(fig, "b", 1, 35)
    cb.text(7, 35, "Components per family (r0 and r1 share each topology)", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    cols = ["Raw MLP", "History\nencoder", "GRU", "Horizon\nembedding", "Basis\nprojection", "Basis\nlinear head"]
    comp = {
        "M0": [1, 0, 0, 0, 0, 0],
        "M1": [1, 0, 0, 0, 0, 0],
        "M2": [1, 0, 0, 0, 0, 0],
        "M3": [1, 1, 0, 0, 0, 0],
        "M4": [1, 0, 1, 0, 0, 0],
        "M5": [1, 0, 1, 1, 0, 0],
        "M6": [1, 0, 1, 1, 1, 0],
        "M7": [1, 0, 1, 1, 1, 0],
        "M8": [1, 0, 1, 1, 1, 1],
    }
    families = [f"M{i}" for i in range(9)]
    mx = axmm(fig, 16, 1.5, 98, 25)
    mx.set_xlim(-0.5, len(cols) - 0.5)
    mx.set_ylim(len(families) - 0.5, -0.5)
    mx.set_xticks(range(len(cols)), cols, fontsize=5.6)
    mx.xaxis.tick_top()
    mx.set_yticks(range(len(families)), families, fontsize=6.2)
    mx.tick_params(length=0, pad=2)
    for sp in mx.spines.values():
        sp.set_visible(False)
    for r, fam in enumerate(families):
        for c, v in enumerate(comp[fam]):
            if v:
                mx.plot([c], [r], marker="o", markersize=4.4, color=INK)
            else:
                mx.plot([c], [r], marker=".", color=RULE, markersize=2.5)
    for r, note in ((6, "2 of 5"), (7, "5 of 5"), (8, "5 of 5")):
        mx.text(4.42, r, note, fontsize=5.4, color=MID, va="center", ha="left")

    bx = axmm(fig, 128, 1.5, 48, 25)
    vals = [params[f] for f in families]
    colors = [COBALT] * 3 + [TEAL] * 2 + [OCHRE] + [purple] * 2 + [VERMILION]
    bx.barh(range(9), vals, color=colors, height=0.66)
    bx.set_ylim(8.5, -0.5)
    bx.set_yticks([])
    bx.set_xlim(0, 13500)
    bx.set_xticks([0, 5000, 10000], ["0", "5k", "10k"], fontsize=5.8)
    bx.tick_params(length=2, pad=1.5)
    for r, v in enumerate(vals):
        bx.text(v + 250, r, f"{v:,}", va="center", fontsize=5.6)
    bx.spines["left"].set_visible(False)
    bx.xaxis.tick_top()
    bx.spines["bottom"].set_visible(False)
    bx.spines["top"].set_visible(True)
    cb.text(128, 35, "Trainable parameters", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    save_figure(fig, 3, "Neural architectures and parameter counts")


# ---------------------------------------------------------------------------
# Figure 4 - 18-route qualification matrix
# ---------------------------------------------------------------------------
def plot_numerical(routes):
    fig = new_figure(180, 118)
    n = len(routes)
    gap = 0.38
    ypos = [i + gap * (i // 2) for i in range(n)]
    ymax = ypos[-1] + 0.7
    top, bottom = 94.0, 22.0
    cuda_pass = sum(r["saved_cuda"].lower() == "pass" for r in routes)
    panel_label(fig, "a", 1, 117.5)
    fig.text(7 / 180, 117.0 / 118, "Route-level qualification: nine families × two repeats", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    fig.text(
        7 / 180,
        111.8 / 118,
        f"Recovered CPU vs original CPU: {n}/{n} exactly equal   ·   Recovered CPU vs archived GPU arrays: {cuda_pass}/{n} within tolerance, {n - cuda_pass}/{n} outside",
        fontsize=S.FS_TEXT,
        va="top",
    )
    mx = axmm(fig, 0, bottom, 100, top - bottom)
    mx.set_xlim(0, 100)
    mx.set_ylim(ymax, -0.8)
    mx.axis("off")
    for x, label in [(9, "Route"), (36, "Recovered CPU =\noriginal CPU"), (78, "Archived GPU\ncomparison")]:
        mx.text(x, -1.05, label, fontsize=S.FS_TEXT, fontweight="bold", ha="center", va="bottom", linespacing=1.15)
    for i, route in enumerate(routes):
        y = ypos[i]
        model, rep = route["route"].split("-")
        passed = route["saved_cuda"].lower() == "pass"
        if (i // 2) % 2 == 0:
            mx.add_patch(Rectangle((0, y - 0.55 - (0 if i % 2 == 0 else 1.0)), 100, 0.0, facecolor="none"))
        mx.text(9, y, f"{model} · {rep}", fontsize=S.FS_TEXT, ha="center", va="center", fontweight="bold" if rep == "r0" else "normal")
        mx.plot([30], [y], marker="s", markersize=4.0, color=INK)
        mx.text(34, y, "exact", fontsize=S.FS_TEXT - 0.3, va="center")
        if passed:
            mx.plot([70], [y], marker="o", markersize=4.4, markerfacecolor="white", markeredgecolor=COBALT, markeredgewidth=1.0)
            mx.text(75, y, "within tolerance", fontsize=S.FS_TEXT - 0.3, va="center", color=COBALT)
        else:
            mx.plot([70], [y], marker="X", markersize=4.8, color=VERMILION)
            mx.text(75, y, "outside tolerance", fontsize=S.FS_TEXT - 0.3, va="center", color=VERMILION, fontweight="bold")
    for k in range(1, 9):
        yy = ypos[2 * k] - (gap + 1) / 2 + 0.31
        mx.plot([2, 99], [yy, yy], color=RULE, lw=0.4)

    panel_label(fig, "b", 104, 100)
    lx = axmm(fig, 108, bottom, 34, top - bottom)
    lx.set_ylim(ymax, -0.8)
    lx.set_xscale("log")
    lx.set_xlim(5e-7, 1e-3)
    lx.set_yticks([])
    lx.spines["left"].set_visible(False)
    lx.axvline(1e-5, color=MID, lw=0.7, ls=(0, (3, 2)))
    for i, route in enumerate(routes):
        passed = route["saved_cuda"].lower() == "pass"
        v = float(route["max_absolute_error"])
        lx.hlines(ypos[i], 5e-7, v, color=RULE, lw=0.6, zorder=1)
        lx.plot([v], [ypos[i]], marker="o" if passed else "X", markersize=3.8, markerfacecolor="white" if passed else VERMILION,
                markeredgecolor=COBALT if passed else VERMILION, markeredgewidth=0.9, zorder=3, linestyle="none")
    lx.set_xlabel("Maximum |difference|\n(mixed N/kg and m/s outputs)", fontsize=S.FS_TEXT, labelpad=2)
    lx.set_xticks([1e-6, 1e-5, 1e-4, 1e-3], ["10⁻⁶", "10⁻⁵", "10⁻⁴", "10⁻³"])
    lx.minorticks_off()
    lx.tick_params(labelsize=5.8, length=2)
    lx.grid(axis="x")
    lx.set_axisbelow(True)
    lx.text(1.2e-5, -0.55, "atol", fontsize=5.4, color=MID, va="bottom", ha="left")
    fig.text(126 / 180, 97.5 / 118, "Largest difference", fontsize=S.FS_TEXT, fontweight="bold", ha="center", va="bottom")

    panel_label(fig, "c", 147, 100)
    fx = axmm(fig, 152, bottom, 24, top - bottom)
    fx.set_ylim(ymax, -0.8)
    fx.set_xlim(0, 1024)
    fx.set_yticks([])
    fx.spines["left"].set_visible(False)
    for i, route in enumerate(routes):
        fail = route["failing_elements"]
        y = ypos[i]
        if fail == "not tabulated":
            fx.text(18, y, "n/t", fontsize=5.4, color=SOFT, va="center")
            continue
        count = int(fail)
        if count:
            fx.barh(y, count, height=0.62, color=VERMILION)
            fx.text(count + 24, y, f"{count}", fontsize=5.6, va="center")
        else:
            fx.plot([8], [y], marker="o", markersize=3, markerfacecolor="white", markeredgecolor=COBALT)
            fx.text(60, y, "0", fontsize=5.6, va="center")
    fx.set_xticks([0, 512, 1024], ["0", "512", "1k"], fontsize=5.8)
    fx.set_xlabel("Elements outside\ntolerance (of 1,024)", fontsize=S.FS_TEXT, labelpad=2)
    fx.tick_params(length=2)
    fig.text(165.5 / 180, 97.5 / 118, "Failing elements", fontsize=S.FS_TEXT, fontweight="bold", ha="center", va="bottom")
    fig.text(7 / 180, 7.0 / 118, "Criterion per element: |a − b| ≤ 10⁻⁵ + 10⁻⁴|b| (a replayed, b archived). A difference ≤ atol = 10⁻⁵ (dashed) always passes.\nn/t: failure count not tabulated. Recorded private comparison summarized publicly; no GPU replay or new inference was run for this article.",
             fontsize=5.6, color=MID, va="bottom")
    save_figure(fig, 4, "Eighteen-route numerical qualification")


# ---------------------------------------------------------------------------
# Figure 5 - biomechanics and assessment chronology
# ---------------------------------------------------------------------------
MASS, GRAV, AMP, T_PEAK, DUR = 70.0, 9.80665, 1000.0, 0.22, 0.55


def analytical_force(t):
    t = np.asarray(t, dtype=float)
    rising = MASS * GRAV + AMP * np.sin(np.pi * t / (2 * T_PEAK))
    falling = (MASS * GRAV + AMP) * (1 - (t - T_PEAK) / (DUR - T_PEAK))
    return np.where(t <= T_PEAK, rising, falling)


def analytic_quantities():
    t = np.linspace(0, DUR, 5501)
    f = analytical_force(t)
    gross_area = float(np.trapezoid(f, t))
    mean_force_n = gross_area / DUR
    net = float(np.trapezoid(f - MASS * GRAV, t))
    return {
        "mean_force_n_per_kg": mean_force_n / MASS,
        "mean_force_n": mean_force_n,
        "peak_force_n": float(f.max()),
        "peak_force_n_per_kg": float(f.max()) / MASS,
        "net_impulse_m_per_s": net / MASS,
        "gross_area_ns": gross_area,
    }


def plot_biomechanics():
    q = analytic_quantities()
    assert math.isclose(q["net_impulse_m_per_s"], 2.739850606012398, abs_tol=2e-5)
    fig = new_figure(180, 128)
    ax = canvas(fig)
    bw = MASS * GRAV
    t = np.linspace(0, DUR, 551)
    f = analytical_force(t)
    panel_label(fig, "a", 1, 127)
    ax.text(7, 127, "Concentric-phase force–time curve (analytical, not athlete data)", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    fx = axmm(fig, 13, 62, 92, 58)
    fx.fill_between(t, 0, f, color=PALE_COBALT, lw=0, zorder=1)
    fx.fill_between(t, bw, f, where=f >= bw, facecolor="none", edgecolor=VERMILION, hatch="////", lw=0, zorder=2)
    fx.fill_between(t, bw, f, where=f < bw, facecolor="none", edgecolor=SLATE, hatch="....", lw=0, zorder=2)
    fx.plot(t, f, color=COBALT, lw=1.6, zorder=4)
    fx.axhline(bw, color=MID, lw=0.8, ls=(0, (4, 2)), zorder=3)
    fx.hlines(q["mean_force_n"], 0, DUR, color=INK, lw=1.1, zorder=5)
    fx.axvline(0, color=TEAL, lw=0.9, ls=":")
    fx.axvline(DUR, color=VERMILION, lw=0.9, ls=":")
    fx.plot([T_PEAK], [q["peak_force_n"]], marker="v", color=INK, markersize=4, zorder=6)
    fx.set_xlim(-0.03, 0.6)
    fx.set_ylim(0, 1900)
    fx.set_xlabel("Time since concentric onset, t (s)")
    fx.set_ylabel(r"Vertical force, $F_z$ (N)")
    tidy_axis(fx, "y")
    sec = fx.secondary_yaxis("right", functions=(lambda v: v / MASS, lambda v: v * MASS))
    sec.set_ylabel(r"$F_z/m$ (N/kg)", fontsize=S.FS_LABEL)
    sec.tick_params(length=2.2, labelsize=S.FS_TEXT)
    fx.text(0.006, 1880, "onset (t = 0)", color=TEAL, fontsize=S.FS_TEXT, va="top", ha="left")
    fx.text(0.594, 1880, "takeoff (t = T)", color=VERMILION, fontsize=S.FS_TEXT, va="top", ha="right")
    fx.annotate(f"peak force (not scored)\n{q['peak_force_n']:.0f} N = {q['peak_force_n_per_kg']:.2f} N/kg", xy=(T_PEAK, q["peak_force_n"]),
                xytext=(0.40, 1700), fontsize=S.FS_TEXT, va="center", ha="center", arrowprops={"arrowstyle": "-", "lw": 0.6, "color": MID})
    fx.text(0.505, 870, f"gross mean force\n{q['mean_force_n_per_kg']:.2f} N/kg (black line)", fontsize=S.FS_TEXT, ha="center", va="center", fontweight="bold", linespacing=1.2)
    fx.text(0.255, bw - 40, rf"body weight $mg$ = {bw:.0f} N ({GRAV:.2f} N/kg)", fontsize=S.FS_TEXT, ha="center", va="top", color=MID, bbox={"fc": "#dfe8f6", "ec": "none", "pad": 0.5})
    fx.text(0.115, 150, "gross force integral\n(area under $F_z$)", fontsize=S.FS_TEXT, color=COBALT, ha="center", va="bottom", linespacing=1.25)
    fx.annotate("net impulse: signed\narea relative to $mg$", xy=(0.30, 1000), xytext=(0.435, 1330), fontsize=S.FS_TEXT - 0.2, color=VERMILION, va="center",
                arrowprops={"arrowstyle": "-", "lw": 0.5, "color": VERMILION}, linespacing=1.2)

    panel_label(fig, "b", 118, 127)
    ax.text(124, 127, "Three distinct quantities", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    ledger = [
        (r"$Y_F=\dfrac{1}{mT}\int_{0}^{T}F_z\,dt$", f"{q['mean_force_n_per_kg']:.2f}", "N/kg", "Gross mean concentric force", "Basis of the scored force target", COBALT),
        (r"$\max F_z\,/\,m$", f"{q['peak_force_n_per_kg']:.2f}", "N/kg", "Peak force", "Not the scored target", SLATE),
        (r"$Y_J=\dfrac{1}{m}\int_{0}^{T}(F_z-mg)\,dt$", f"{q['net_impulse_m_per_s']:.2f}", "m/s", "Gravity-adjusted net impulse", "Separate scored outcome", VERMILION),
    ]
    y = 118
    for eq, val, unit, name, note, color in ledger:
        ax.add_patch(Rectangle((118, y - 16.0), 1.4, 15.5, facecolor=color, edgecolor="none"))
        ax.text(122, y - 0.8, name, fontsize=S.FS_TEXT, fontweight="bold", va="top")
        ax.text(122, y - 14.6, note, fontsize=5.7, color=MID, va="bottom")
        ax.text(122, y - 8.2, eq, fontsize=8.6, va="center")
        ax.text(177, y - 7.0, val, fontsize=11, fontweight="bold", color=color, ha="right", va="center")
        ax.text(177, y - 12.0, unit, fontsize=S.FS_TEXT, color=MID, ha="right", va="center")
        y -= 20.0
    ax.text(118, 59.2, f"Illustrative: m = {MASS:.0f} kg, g = {GRAV:.5f} m s⁻², A = {AMP:.0f} N,\nt_p = {T_PEAK:.2f} s, T = {DUR:.2f} s.\nt ≤ t_p: F = mg + A sin(πt / 2t_p)\nt > t_p: F = (mg + A)[1 − (t − t_p)/(T − t_p)]",
            fontsize=5.5, color=MID, va="top", linespacing=1.3)

    panel_label(fig, "c", 1, 49)
    ax.text(7, 49, "Assessment chronology relative to the index exposure (native contract and public synthetic task are separate)", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    tx = axmm(fig, 36, 12, 138, 24)
    tx.set_xlim(-255, 195)
    tx.set_ylim(-0.2, 3.2)
    tx.set_yticks([])
    for side in ("left", "right"):
        tx.spines[side].set_visible(False)
    tx.set_xticks([-240, -168, -96, -24, 0, 24, 48, 72, 120, 168])
    tx.set_xlabel("Hours relative to index exposure")
    tx.grid(axis="x")
    tx.set_axisbelow(True)
    tx.barh(2.55, 216, left=-240, height=0.42, color=PALE_COBALT, edgecolor=COBALT, linewidth=0.8)
    tx.text(-132, 2.55, "baseline search: 24–240 h before origin", ha="center", va="center", fontsize=S.FS_TEXT)
    tx.barh(1.75, 12, left=66, height=0.42, color=PALE_TEAL, edgecolor=TEAL, linewidth=0.8)
    tx.barh(1.75, 24, left=156, height=0.42, color=PALE_OCHRE, edgecolor=OCHRE, linewidth=0.8)
    tx.text(60, 1.75, "H72 target\n66–78 h", ha="right", va="center", fontsize=S.FS_TEXT, color=TEAL, linespacing=1.15)
    tx.text(150, 1.75, "D7 target\n156–180 h", ha="right", va="center", fontsize=S.FS_TEXT, color=OCHRE, linespacing=1.15)
    tx.axvline(0, color=VERMILION, lw=1.0, ls="--", ymin=0.02, ymax=0.97)
    tx.text(3, 3.15, "index exposure (origin)", fontsize=S.FS_TEXT, color=VERMILION, va="top", ha="left")
    tx.axhline(1.05, color=RULE, lw=0.6)
    for h, x in zip(HORIZONS, (24, 48, 72), strict=True):
        tx.plot([x], [0.45], marker="o", markersize=4.6, color=COBALT, markeredgecolor="white")
        tx.text(x, 0.12, h, fontsize=S.FS_TEXT, ha="center", va="top", color=COBALT, fontweight="bold")
    ax.text(3, 31, "Native\nmeasurement\ncontract", fontsize=S.FS_TEXT, fontweight="bold", va="center", linespacing=1.15)
    ax.text(3, 19, "Public\nsynthetic\nqueries", fontsize=S.FS_TEXT, fontweight="bold", va="center", linespacing=1.15)
    ax.text(7, 44.5, "Assessment = mean of 3 valid trials · baseline = mean of the 2 latest valid assessments · no athlete data plotted",
            fontsize=5.6, color=MID, ha="left", va="top")
    save_figure(fig, 5, "Biomechanical definitions and assessment chronology")


# ---------------------------------------------------------------------------
# Figure 6 - six-cell performance small multiples
# ---------------------------------------------------------------------------
def cell_lookup(six):
    return {(r["model"], r["cell"]): r for r in six}


def plot_public_performance(six):
    data = cell_lookup(six)
    fig = new_figure(180, 150)
    left, right, bottom, top = 12, 2, 18, 9
    gap_x, gap_y = 10, 7
    pw = (180 - left - right - gap_x) / 2
    ph = (150 - bottom - top - 2 * gap_y) / 3
    titles = ["Mean concentric-force innovation (N/kg)", "Net-impulse innovation (m/s)"]
    cell_names = [FORCE_CELL, IMPULSE_CELL]
    for r, horizon in enumerate(HORIZONS):
        for c, cell_name in enumerate(cell_names):
            x0 = left + c * (pw + gap_x)
            y0 = 150 - top - (r + 1) * ph - r * gap_y
            ax = axmm(fig, x0, y0, pw, ph)
            cell = f"{horizon}/{cell_name}"
            for m, model in enumerate(MODEL_ORDER):
                entry = data[(model, cell)]
                mean = float(entry["mean"])
                for k, root in enumerate(ROOT_ORDER):
                    ax.plot([m + (k - 1) * 0.16], [float(entry[ROOT_KEYS[root]])], marker=ROOT_MARKERS[root], markersize=3.6,
                            color=MODEL_COLORS[model], markeredgecolor="white", markeredgewidth=0.35, linestyle="none", zorder=3)
                ax.hlines(mean, m - 0.30, m + 0.30, color=INK, lw=1.1, zorder=4)
                ax.text(m, mean + 0.17, f"{mean:.3f}", ha="center", va="bottom", fontsize=5.8)
            ax.axhline(1.0, color=SOFT, lw=0.6, ls=(0, (3, 2)), zorder=1)
            ax.set_xlim(-0.55, 3.55)
            ax.set_ylim(0, 3.45)
            ax.set_yticks([0, 1, 2, 3])
            tidy_axis(ax, "y")
            ax.set_xticks(range(4), [MODEL_SHORT[m] if r == 2 else "" for m in MODEL_ORDER], fontsize=S.FS_TEXT)
            if c == 0:
                ax.set_ylabel(f"{horizon}\nNRMSE", fontsize=S.FS_LABEL, fontweight="bold")
            else:
                ax.tick_params(labelleft=False)
            if r == 0:
                ax.set_title(titles[c], fontsize=S.FS_TITLE, fontweight="bold", pad=4)
            if r == 0 and c == 0:
                ax.text(3.5, 1.07, "NRMSE = 1", fontsize=5.4, color=MID, ha="right", va="bottom")
    panel_label(fig, "a", 1, 149)
    handles = [Line2D([0], [0], marker=ROOT_MARKERS[k], color=INK, linestyle="none", markersize=3.8, label=f"root {k}") for k in ROOT_ORDER]
    handles.append(Line2D([0], [0], color=INK, lw=1.2, label="mean of 3 roots"))
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(left / 180, 1.0 / 150), ncol=4, fontsize=S.FS_TEXT, columnspacing=1.6, handletextpad=0.5)
    fig.text(178 / 180, 3.6 / 150, "colour = reference model · marker = evaluation root", fontsize=S.FS_TEXT, color=MID, ha="right", va="center")
    save_figure(fig, 6, "Six-cell public synthetic benchmark performance")


# ---------------------------------------------------------------------------
# Figure 7 - model by cell heatmap
# ---------------------------------------------------------------------------
def plot_heatmap(six, study):
    data = cell_lookup(six)
    fig = new_figure(180, 100)
    cmap = LinearSegmentedColormap.from_list("cmj_div", [COBALT, "#7f9fd1", "#f2f4f7", "#e7a395", VERMILION])
    norm = TwoSlopeNorm(vmin=0.45, vcenter=1.0, vmax=3.2)
    ncell, nmodel = len(CELL_ORDER), len(MODEL_ORDER)
    nrow = ncell + 1
    summary = study["across_root_variability"]
    values = np.array([[float(data[(m, c)]["mean"]) for m in MODEL_ORDER] for c in CELL_ORDER])
    means = np.array([[float(summary[m]["root_mean_nrmse"]) for m in MODEL_ORDER]])
    allv = np.vstack([values, means])
    ax_x, ax_y, ax_w, ax_h = 46, 17, 80, 62
    row_h = ax_h / nrow
    ax = axmm(fig, ax_x, ax_y, ax_w, ax_h)
    ax.imshow(allv, cmap=cmap, norm=norm, aspect="auto", extent=(-0.5, nmodel - 0.5, nrow - 0.5, -0.5))
    for i in range(nrow):
        best = int(allv[i].argmin())
        for j in range(nmodel):
            v = allv[i, j]
            dark = v < 0.78 or v > 2.2
            ax.text(j, i, f"{v:.4f}" if i == ncell else f"{v:.3f}", ha="center", va="center", fontsize=6.8, color="white" if dark else INK, fontweight="bold" if j == best else "normal")
        ax.add_patch(Rectangle((best - 0.5, i - 0.5), 1, 1, fill=False, edgecolor=INK, linewidth=1.3))
    ax.set_xticks(range(nmodel), [MODEL_SHORT[m] for m in MODEL_ORDER], fontsize=S.FS_TEXT)
    ax.xaxis.tick_top()
    ax.set_yticks(range(nrow), [c.split("/")[0] for c in CELL_ORDER] + ["Mean"], fontsize=S.FS_LABEL)
    ax.tick_params(length=0, pad=3)
    for sp in ax.spines.values():
        sp.set_visible(False)
    for k in range(1, nmodel):
        ax.axvline(k - 0.5, color="white", lw=1.0)
    for k in range(1, nrow):
        ax.axhline(k - 0.5, color="white", lw=1.0 if k not in (3, 6) else 2.6)
    cx = canvas(fig)
    top_y = ax_y + ax_h
    cx.text(15, top_y - row_h * 1.5, "Mean concentric-\nforce innovation\n(N/kg)", fontsize=S.FS_TEXT, fontweight="bold", ha="center", va="center", linespacing=1.2)
    cx.text(15, top_y - row_h * 4.5, "Net-impulse\ninnovation\n(m/s)", fontsize=S.FS_TEXT, fontweight="bold", ha="center", va="center", linespacing=1.2)
    cx.text(15, top_y - row_h * 6.5, "Six-cell mean", fontsize=S.FS_TEXT, fontweight="bold", ha="center", va="center")
    for r0, r1 in ((0, 3), (3, 6)):
        cx.plot([36.5, 36.5], [top_y - row_h * r1 + 1, top_y - row_h * r0 - 1], color=INK, lw=0.8)
    panel_label(fig, "a", 1, 99)
    cx.text(46, 99, "Mean NRMSE across three roots (lower is better)", fontsize=S.FS_TITLE, fontweight="bold", va="top", ha="left")
    panel_label(fig, "b", 134, 99)
    cx.text(140, 99, "Ridge vs structured", fontsize=S.FS_TITLE, fontweight="bold", va="top", ha="left")
    bx = axmm(fig, 143, ax_y + row_h, 33, ax_h - row_h)
    bx.set_ylim(ncell - 0.5, -0.5)
    bx.set_xlim(-0.01, 0.065)
    bx.axvline(0, color=INK, lw=0.8)
    for i, c in enumerate(CELL_ORDER):
        diffs = [float(data[("structured_full", c)][ROOT_KEYS[r]]) - float(data[("ridge_full", c)][ROOT_KEYS[r]]) for r in ROOT_ORDER]
        for r, d in zip(ROOT_ORDER, diffs, strict=True):
            bx.plot([d], [i], marker=ROOT_MARKERS[r], markersize=3.4, color=VERMILION, markeredgecolor="white", markeredgewidth=0.3, linestyle="none")
        bx.hlines(i, 0, statistics.mean(diffs), color=RULE, lw=0.7, zorder=0)
    bx.axhline(2.5, color=RULE, lw=0.6)
    bx.set_yticks([])
    bx.spines["left"].set_visible(False)
    bx.set_xticks([0, 0.02, 0.04, 0.06])
    bx.set_xlabel("Structured − ridge NRMSE\n(each root; descriptive)", fontsize=S.FS_TEXT)
    tidy_axis(bx, "x")
    kx = axmm(fig, 46, 7, 80, 3)
    grad = np.linspace(0.45, 3.2, 256)[None, :]
    kx.imshow(grad, aspect="auto", cmap=cmap, norm=norm, extent=(0.45, 3.2, 0, 1))
    kx.set_yticks([])
    kx.set_xticks([0.5, 1.0, 2.0, 3.0])
    kx.tick_params(labelsize=5.8, length=2, pad=1)
    for sp in kx.spines.values():
        sp.set_visible(False)
    cx.text(22, 8.5, "NRMSE colour scale\ncentred at 1.0", fontsize=S.FS_TEXT, color=MID, ha="center", va="center", linespacing=1.2)
    cx.text(46, 1.5, "Outlined: lowest NRMSE in the row. Blue (< 1) beats the test-set cell mean; red (> 1) is worse.", fontsize=5.6, color=MID, ha="left", va="center")
    save_figure(fig, 7, "Model-by-cell NRMSE heatmap")


# ---------------------------------------------------------------------------
# Figure 8 - forest plot of recorded bootstrap intervals
# ---------------------------------------------------------------------------
def plot_bootstrap(uncertainty, study):
    fig = new_figure(180, 84)
    cx = canvas(fig)
    panel_label(fig, "a", 1, 83)
    panel_label(fig, "b", 94, 83)
    cx.text(7, 83, "Mean six-cell NRMSE, 95% interval", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    cx.text(100, 83, "Paired change vs zero innovation", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    cx.text(7, 78.0, "Resampling unit: camp (16 per root, each keeping its 250 episodes × 3 horizons) · 5,000 paired replicates · PCG64 seed 49,505,000\nPercentile intervals, conditional on each fixed root; markers show the root estimate.",
            fontsize=5.5, color=MID, va="top")
    ypos = {}
    y = 0.0
    for root in ROOT_ORDER:
        for model in ("ridge_full", "structured_full"):
            ypos[(root, model)] = y
            y += 1.0
        y += 0.8
    ymax = y - 0.8
    axa = axmm(fig, 20, 14, 62, 57)
    axb = axmm(fig, 108, 14, 66, 57)
    markers = {"ridge_full": "o", "structured_full": "s"}
    for ax in (axa, axb):
        ax.set_ylim(ymax + 0.6, -0.6)
        tidy_axis(ax, "x")
        ax.tick_params(axis="y", length=0)
    for row in uncertainty:
        root, model = row["root"], row["model"]
        yy = ypos[(root, model)]
        color = MODEL_COLORS[model]
        idx = ROOT_ORDER.index(root)
        est = float(study["across_root_variability"][model]["root_values"][idx])
        delta = float(study["across_root_variability"][model]["root_deltas_vs_zero"][idx])
        lo, hi = float(row["nrmse_lower"]), float(row["nrmse_upper"])
        dlo, dhi = float(row["paired_delta_vs_zero_lower"]), float(row["paired_delta_vs_zero_upper"])
        axa.hlines(yy, lo, hi, color=color, lw=2.0)
        axa.plot([est], [yy], marker=markers[model], markersize=4.4, color=color, markeredgecolor="white", markeredgewidth=0.5, zorder=3)
        axa.text(hi + 0.0035, yy, f"{lo:.3f}–{hi:.3f}", fontsize=5.6, va="center")
        axb.hlines(yy, dlo, dhi, color=color, lw=2.0)
        axb.plot([delta], [yy], marker=markers[model], markersize=4.4, color=color, markeredgecolor="white", markeredgewidth=0.5, zorder=3)
        axb.text(dhi + 0.04, yy, f"{dlo:.3f} to {dhi:.3f}", fontsize=5.6, va="center")
    for ax in (axa, axb):
        ax.set_yticks([(ypos[(r, "ridge_full")] + ypos[(r, "structured_full")]) / 2 for r in ROOT_ORDER], [f"Root {r}" for r in ROOT_ORDER], fontsize=S.FS_LABEL)
    axa.set_xlim(0.715, 0.835)
    axa.set_xticks([0.72, 0.74, 0.76, 0.78, 0.80])
    axa.set_xlabel("Mean six-cell NRMSE")
    axb.set_xlim(-1.90, 0.0)
    axb.axvline(0, color=INK, lw=0.9, ls=(0, (3, 2)))
    axb.set_xlabel(r"$\Delta$NRMSE (model − zero innovation)")
    axb.text(-1.88, ymax + 0.55, "negative favours the model", fontsize=5.4, color=MID, va="bottom")
    for k in (1, 2):
        sep = (ypos[(ROOT_ORDER[k - 1], "structured_full")] + ypos[(ROOT_ORDER[k], "ridge_full")]) / 2
        for ax in (axa, axb):
            ax.axhline(sep, color=RULE, lw=0.5)
    handles = [Line2D([0], [0], color=MODEL_COLORS[m], marker=markers[m], lw=2, markersize=4.2, label=MODEL_LABELS[m]) for m in ("ridge_full", "structured_full")]
    fig.legend(handles=handles, loc="lower left", ncol=2, bbox_to_anchor=(20 / 180, 0.0), fontsize=S.FS_TEXT)
    fig.text(178 / 180, 1.4 / 84, "No ridge-versus-structured interval was recorded.", fontsize=5.6, color=MID, ha="right", va="bottom")
    save_figure(fig, 8, "Recorded camp-bootstrap intervals")


# ---------------------------------------------------------------------------
# Figure 9 - ablations and sample efficiency
# ---------------------------------------------------------------------------
def plot_ablation_sample_size(study):
    result = study["across_root_variability"]
    fig = new_figure(180, 86)
    cx = canvas(fig)
    panel_label(fig, "a", 1, 85)
    panel_label(fig, "b", 104, 85)
    cx.text(7, 85, "Recorded ablations (mean six-cell NRMSE)", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    cx.text(110, 85, "Nested training-camp results", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    ablations = [
        ("ridge_full", "Full ridge", COBALT),
        ("ridge_no_prior_history", "Ridge − prior history", COBALT),
        ("ridge_no_current_exposure", "Ridge − current exposure", COBALT),
        ("ridge_no_participant_context", "Ridge − participant context", COBALT),
        ("structured_no_prior_history", "Structured − prior history", VERMILION),
    ]
    ax = axmm(fig, 40, 14, 58, 61)
    ax.set_ylim(len(ablations) - 0.4, -0.7)
    full = float(result["ridge_full"]["root_mean_nrmse"])
    ax.axvline(full, color=SOFT, lw=0.7, ls=(0, (3, 2)), zorder=1)
    for i, (key, _, color) in enumerate(ablations):
        vals = [float(v) for v in result[key]["root_values"]]
        mean = float(result[key]["root_mean_nrmse"])
        ax.hlines(i, min(vals), max(vals), color=color, lw=1.2, alpha=0.5)
        for r, v in zip(ROOT_ORDER, vals, strict=True):
            ax.plot([v], [i], marker=ROOT_MARKERS[r], markersize=3.8, color=color, markeredgecolor="white", markeredgewidth=0.35, linestyle="none", zorder=3)
        ax.plot([mean, mean], [i - 0.3, i + 0.3], color=INK, lw=1.3, zorder=4)
        txt = f"{mean:.4f}"
        if key.startswith("ridge") and key != "ridge_full":
            txt += f" ({mean - full:+.4f})"
        ax.text(max(vals) + 0.006, i, txt, fontsize=5.6, va="center")
    ax.set_yticks(range(len(ablations)), [a[1] for a in ablations], fontsize=S.FS_TEXT)
    ax.set_xlim(0.725, 0.935)
    ax.set_xticks([0.74, 0.78, 0.82, 0.86, 0.90])
    ax.set_xlabel("Mean six-cell NRMSE")
    tidy_axis(ax, "x")
    ax.tick_params(axis="y", length=0)
    ax.text(0.7275, len(ablations) - 0.45, "dashed: full ridge; parentheses: change from full ridge", fontsize=5.4, color=MID, va="bottom")

    bx = axmm(fig, 112, 14, 64, 61)
    camps = [24, 48, 96]
    for model, color, ls in (("ridge", COBALT, "-"), ("structured", VERMILION, "--")):
        for r, root in enumerate(ROOT_ORDER):
            yvals = [float(result[f"{model}_n{n}"]["root_values"][r]) for n in camps]
            bx.plot(camps, yvals, color=color, ls=ls, lw=0.8, alpha=0.7, marker=ROOT_MARKERS[root], markersize=3.6, markeredgecolor="white", markeredgewidth=0.3)
        means = [float(result[f"{model}_n{n}"]["root_mean_nrmse"]) for n in camps]
        bx.plot(camps, means, color=INK, lw=1.2, ls=ls, zorder=5)
        bx.text(98.5, means[-1], f"{means[-1]:.4f}", fontsize=5.6, va="center", ha="left")
        bx.text(22.5, means[0], f"{means[0]:.4f}", fontsize=5.6, va="center", ha="right")
    bx.set_xticks(camps)
    bx.set_xlim(2, 116)
    bx.set_ylim(0.728, 0.782)
    bx.set_xlabel("Training camps (regularization held at its full-data value)")
    bx.set_ylabel("Mean six-cell NRMSE")
    tidy_axis(bx, "y")
    bx.text(60, 0.7775, "structured comparator", fontsize=S.FS_TEXT, color=VERMILION, ha="center")
    bx.text(60, 0.7415, "ridge regression", fontsize=S.FS_TEXT, color=COBALT, ha="center")
    handles = [Line2D([0], [0], marker=ROOT_MARKERS[k], color=INK, linestyle="none", markersize=3.8, label=f"root {k}") for k in ROOT_ORDER]
    handles.append(Line2D([0], [0], color=INK, lw=1.2, label="mean"))
    fig.legend(handles=handles, loc="lower right", ncol=4, bbox_to_anchor=(0.995, 0.0), fontsize=S.FS_TEXT, columnspacing=1.2, handletextpad=0.4)
    fig.text(7 / 180, 2.0 / 86, "Descriptive diagnostics under the existing protocol; no interval or causal feature effect is implied.", fontsize=5.6, color=MID, va="bottom")
    save_figure(fig, 9, "Ablations and nested training-camp results")


# ---------------------------------------------------------------------------
# Figure 10 - historical reproducibility gaps
# ---------------------------------------------------------------------------
def plot_reconstruction_rows(reproduction):
    runs = [r for r in reproduction["runs"] if r["kind"] == "public_split_generation" and r["run_spec"]["benchmark"] == "rich_history_camp_recovery"]
    by_split = {r["run_spec"]["split"]: r["dataset_output"] for r in runs}
    fig = new_figure(180, 88)
    cx = canvas(fig)
    panel_label(fig, "a", 1, 87)
    cx.text(7, 87, "Rich-history materialization", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    ax = axmm(fig, 22, 38, 55, 38)
    splits = [("training", "Training"), ("public_validation", "Validation")]
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_ylim(1.7, -0.7)
    for i, (key, _) in enumerate(splits):
        clean, hist = by_split[key]["row_count"], by_split[key]["m2_historical_row_count"]
        d = clean - hist
        color = COBALT if d < 0 else VERMILION
        ax.hlines(i, 0, d, color=color, lw=2.2)
        ax.plot([d], [i], marker="o", markersize=5, color=color, markeredgecolor="white")
        ax.text(d / 2 if d < 0 else d + 4, i - 0.22 if d < 0 else i, f"{d:+d} rows", fontsize=7.0, fontweight="bold", color=color, ha="center" if d < 0 else "left", va="center")
        ax.text(0, i + 0.46, f"public {clean:,} vs historical {hist:,}", fontsize=5.6, color=MID, ha="center", va="center")
    ax.set_yticks([0, 1], ["Training", "Validation"], fontsize=S.FS_LABEL)
    ax.set_xlim(-60, 40)
    ax.set_xlabel("Public reconstruction − historical record\n(horizon rows)")
    tidy_axis(ax, "x")
    ax.tick_params(axis="y", length=0)
    cx.text(7, 22, "Membership differences in preserved splits;\nnot response effects or uncertainty intervals.", fontsize=5.6, color=MID, va="top", linespacing=1.3)

    panel_label(fig, "b", 84, 87)
    cx.text(90, 87, "Evidence boundary: what each result rests on", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    classes = ["Public\nsource", "Public\nregenerable", "Private\nsummary", "Not\nestablished"]
    class_color = [COBALT, TEAL, OCHRE, VERMILION]
    rows = [
        ("Eight formulations; 5 parent links", [1, 0, 0, 0]),
        ("Architecture topology, M0–M8", [1, 0, 0, 0]),
        ("Parameter counts, 18 routes", [0, 0, 1, 0]),
        ("Source-CPU equality, 18/18 routes", [0, 0, 1, 0]),
        ("Archived-GPU comparison, 8 pass / 10 fail", [0, 0, 1, 0]),
        ("Six-cell benchmark, bootstrap, ablations", [0, 1, 0, 0]),
        ("Rich-history row counts (−48, +4)", [0, 1, 0, 0]),
        ("Historical split identity; GPU-difference cause", [0, 0, 0, 1]),
        ("Rerun of private checkpoints from public files", [0, 0, 0, 1]),
        ("Athlete validity, transport, clinical use", [0, 0, 0, 1]),
    ]
    cell_x0, cw = 128.0, 12.5
    row_h = 66 / len(rows)
    for j, name in enumerate(classes):
        cx.text(cell_x0 + (j + 0.5) * cw, 77.5, name, fontsize=5.6, ha="center", va="bottom", color=class_color[j], fontweight="bold", linespacing=1.15)
    for i, (label, flags) in enumerate(rows):
        y = 72 - (i + 0.5) * row_h
        if i % 2 == 0:
            cx.add_patch(Rectangle((84, y - row_h / 2), 94, row_h, facecolor="#f4f6f8", edgecolor="none", zorder=0))
        cx.text(86, y, label, fontsize=5.9, va="center")
        for j, f in enumerate(flags):
            xx = cell_x0 + (j + 0.5) * cw
            if f:
                cx.add_patch(plt.Circle((xx, y), 1.7, facecolor=class_color[j], edgecolor="none"))
            else:
                cx.plot([xx], [y], marker=".", color=RULE, markersize=2.5)
    save_figure(fig, 10, "Historical reproducibility gaps")


def validate_inputs(lineage, architecture, routes, six_cells, uncertainty, study):
    assert len(lineage) == 8
    assert len(architecture) == 18
    assert len(routes) == 18
    assert len(six_cells) == 24
    assert len(uncertainty) == 6
    assert set(study["protocol"]["registered_cells"]) == set(CELL_ORDER)
    assert {row["model"] for row in architecture} == {f"M{i}" for i in range(9)}
    assert all(row["inference_rerun"] == "False" for row in routes)
    assert all(int(row["valid_replicates"]) == 5000 for row in uncertainty)
    assert all(len(study["across_root_variability"][m]["root_values"]) == 3 for m in MODEL_ORDER)
    train, dev = study["data"]["training"], study["data"]["development"]
    assert (train["camps"], train["episodes"], train["rows"]) == (96, 24000, 72000)
    assert (dev["camps"], dev["episodes"], dev["rows"]) == (16, 4000, 12000)
    assert all((r["data"]["camps"], r["data"]["episodes"], r["data"]["rows"]) == (16, 4000, 12000) for r in study["independent_test_roots"])
    assert all("label.relative_mean_concentric_force_innovation" in r["data"]["labels"] for r in study["independent_test_roots"])


def main():
    lineage = read_json(RELEASE / "S17_lineage.json")
    methods = read_json(RELEASE / "S18_formulation-methods.json")
    architecture = read_csv(AUDIT / "architecture_qualification.csv")
    routes = read_csv(AUDIT / "model_identity_sanitized.csv")
    six_cells = read_csv(AUDIT / "six_cell_results.csv")
    uncertainty = read_csv(AUDIT / "recorded_uncertainty.csv")
    study = read_json(RELEASE / "S01_M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json")
    reproduction = read_json(RELEASE / "S04_M8_PUBLIC_REPRODUCTION_RECEIPTS.json")
    validate_inputs(lineage, architecture, routes, six_cells, uncertainty, study)
    plot_genealogy(lineage, methods)
    plot_sample_design(study)
    plot_architecture(architecture)
    plot_numerical(routes)
    plot_biomechanics()
    plot_public_performance(six_cells)
    plot_heatmap(six_cells, study)
    plot_bootstrap(uncertainty, study)
    plot_ablation_sample_size(study)
    plot_reconstruction_rows(reproduction)
    files = sorted(S.OUT.glob("Fig*.pdf"))
    assert len(files) == 10, f"Expected 10 PDF figures, found {len(files)}"
    for pdf in files:
        for suffix in (".svg", ".png", ".tif"):
            assert pdf.with_suffix(suffix).is_file(), f"Missing export for {pdf.stem}{suffix}"
    print(f"Generated {len(files)} figures as PDF, SVG, PNG, and 600 dpi TIFF.")


if __name__ == "__main__":
    main()
