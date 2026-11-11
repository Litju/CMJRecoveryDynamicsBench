"""Regenerate the science-first paper figures from frozen, public-safe evidence.

No training, fitting, checkpoint inference or scoring is performed. Every plotted
quantity is read from the pinned release sources or the sanitized public summaries.
"""

from __future__ import annotations

import csv
import sys
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
REPO = ROOT.parents[2]
DOCS = REPO / "docs"
SUPPLEMENT = DOCS / "manuscript" / "supplement"

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
    save_figure(fig, 6, "Synthetic study design and separation")


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
    save_figure(fig, 5, "Neural architectures and parameter counts")


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
    save_figure(fig, 11, "Eighteen-route numerical qualification")


# ---------------------------------------------------------------------------
# Figure 5 - biomechanics and assessment chronology
# ---------------------------------------------------------------------------
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
    save_figure(fig, 7, "Six-cell public synthetic benchmark performance")


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
    save_figure(fig, 8, "Model-by-cell NRMSE heatmap")


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
    save_figure(fig, 9, "Recorded camp-bootstrap intervals")


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
    save_figure(fig, 10, "Ablations and nested training-camp results")


# ---------------------------------------------------------------------------
# Figure 10 - historical reproducibility gaps
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# New science-first figures (1-4). Closed-form or generator-computed; no scoring.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO / "src"))
from cmj_recovery_dynamics.dynamics.fixed_mode_discrepancy_response import (  # noqa: E402
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

ILLUSTRATIVE_FORCE = 20.0  # N/kg, inside the generator's support; not athlete data
ILLUSTRATIVE_IMPULSE = 2.7  # m/s
ILLUSTRATIVE_AMPLITUDES = (0.04, 0.03)  # fast, slow


def plot_study_map():
    fig = new_figure(180, 78)
    ax = canvas(fig)
    panel_label(fig, "a", 1, 77)
    ax.text(7, 77, "From jump measurement to a controlled synthetic benchmark", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    w, h = 31, 20
    xs = [3, 39, 75, 111, 147]
    top = 44
    labels = [
        ("1 Measure", "CMJ force–time:\nmean force (N/kg),\nnet impulse (m/s)", PALE_COBALT, COBALT),
        ("2 Expose", "training exposure,\nbaseline, time since\nexposure", PALE_COBALT, COBALT),
        ("3 Respond", "fixed 24 h / 84 h\nmathematical modes\n(synthetic assumption)", PALE_OCHRE, OCHRE),
        ("4 Simulate", "one generator:\ncamps, episodes,\nthree horizons", PALE_COBALT, COBALT),
        ("5 Forecast", "baseline-relative\ninnovations at\nH24 / H48 / H72", PALE_COBALT, COBALT),
    ]
    for x, (title, body, face, edge) in zip(xs, labels, strict=True):
        ax.text(x + w / 2, top + h + 2.2, title, fontsize=S.FS_LABEL, fontweight="bold", ha="center", color=edge)
        box(ax, x, top, w, h, body, face, edge, fs=5.9)
    for a, b in zip(xs, xs[1:], strict=False):
        arrow(ax, (a + w + 0.4, top + h / 2), (b - 0.4, top + h / 2), color=INK, lw=0.9)
    ax.text(3, 40.0, "Two separate bodies of work answer different questions", fontsize=S.FS_TEXT, fontweight="bold", color=MID, va="top")
    box(ax, 3, 6, 84, 27, "Original neural architectures M0–M8\n9 families × 2 repeats = 18 routes\nstructure, inputs, parameter counts, CPU/GPU\nnumerical qualification\nNO public predictive-performance comparison", PALE_GRAY, SLATE, fs=6.0)
    box(ax, 93, 6, 84, 27, "Public synthetic experiment\n4 evaluated reference models: zero innovation,\ntraining mean, ridge, structured fixed-mode\nsix-cell NRMSE · camp-bootstrap · ablations\nnested training camps · 3 same-generator roots", PALE_VERMILION, VERMILION, fs=6.0)
    arrow(ax, (45, 38), (45, 33.5), color=SLATE, lw=0.8)
    arrow(ax, (135, 38), (135, 33.5), color=VERMILION, lw=0.8)
    save_figure(fig, 1, "Study map")


def plot_force_time():
    trial = realize_concentric_trial(ILLUSTRATIVE_FORCE, ILLUSTRATIVE_IMPULSE)
    t = np.array(trial.time_seconds)
    f = np.array(trial.vertical_force_n_per_kg)
    duration = trial.concentric_duration_seconds
    peak = float(f.max())
    mean = trial.mean_force_n_per_kg
    net = trial.net_impulse_m_per_s
    assert math.isclose(mean, ILLUSTRATIVE_FORCE, abs_tol=1e-9)
    assert math.isclose(net, (mean - G) * duration, abs_tol=1e-9)
    assert math.isclose(peak, G + math.pi / 2 * (mean - G), rel_tol=2e-3)
    fig = new_figure(180, 82)
    panel_label(fig, "a", 1, 81)
    fig.text(7 / 180, 81 / 82, "One simulated concentric trial (analytical half-sine)", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    fx = axmm(fig, 14, 14, 96, 54)
    fx.fill_between(t, G, f, color=PALE_VERMILION, lw=0, zorder=1)
    fx.fill_between(t, 0, np.minimum(f, G), color=PALE_COBALT, lw=0, zorder=1)
    fx.plot(t, f, color=COBALT, lw=1.6, zorder=4)
    fx.axhline(G, color=MID, lw=0.8, ls=(0, (4, 2)), zorder=3)
    fx.hlines(mean, 0, duration, color=INK, lw=1.2, zorder=5)
    fx.plot([t[np.argmax(f)]], [peak], marker="v", color=INK, markersize=4, zorder=6)
    fx.set_xlim(-0.01, duration + 0.01)
    fx.set_ylim(0, 31)
    fx.set_xlabel("Time since concentric onset (s)")
    fx.set_ylabel(r"Vertical force per mass, $F_z/m$ (N/kg)")
    tidy_axis(fx, "y")
    fx.text(0.004, 1.2, "onset", color=TEAL, fontsize=S.FS_TEXT, va="bottom")
    fx.text(duration - 0.004, 1.2, "takeoff", color=VERMILION, fontsize=S.FS_TEXT, va="bottom", ha="right")
    fx.annotate(f"peak force (not scored)\n{peak:.2f} N/kg", xy=(t[np.argmax(f)], peak), xytext=(0.012, 28.2), fontsize=S.FS_TEXT, ha="left", va="center", arrowprops={"arrowstyle": "-", "lw": 0.6, "color": MID})
    fx.text(duration * 0.5, mean - 1.6, f"gross mean force {mean:.1f} N/kg", fontsize=S.FS_TEXT, ha="center", va="top", fontweight="bold", color=INK)
    fx.text(duration * 0.5, G - 1.0, f"body weight per mass g = {G:.5f} N/kg", fontsize=S.FS_TEXT, ha="center", va="top", color=MID)
    fx.text(duration * 0.5, 14.6, "net-impulse area\n(F − g integrated)", fontsize=S.FS_TEXT, ha="center", va="center", color=VERMILION, linespacing=1.2)
    ax = canvas(fig)
    panel_label(fig, "b", 118, 81)
    ax.text(124, 81, "Three distinct quantities", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    ledger = [
        (r"$\bar F=\dfrac{1}{mT}\int_{0}^{T}F_z\,dt$", f"{mean:.2f}", "N/kg", "Gross mean concentric force", "scored force target", COBALT),
        (r"$\max F_z\,/\,m$", f"{peak:.2f}", "N/kg", "Peak force", "not a scored target", SLATE),
        (r"$J=\dfrac{1}{m}\int_{0}^{T}(F_z-mg)\,dt$", f"{net:.2f}", "m/s", "Net concentric impulse", "scored impulse target", VERMILION),
    ]
    y = 73
    for eq, val, unit, name, note, color in ledger:
        ax.add_patch(Rectangle((118, y - 16.0), 1.4, 15.5, facecolor=color, edgecolor="none"))
        ax.text(122, y - 0.8, name, fontsize=S.FS_TEXT, fontweight="bold", va="top")
        ax.text(122, y - 14.6, note, fontsize=5.7, color=MID, va="bottom")
        ax.text(122, y - 8.2, eq, fontsize=8.4, va="center")
        ax.text(177, y - 7.0, val, fontsize=11, fontweight="bold", color=color, ha="right", va="center")
        ax.text(177, y - 12.0, unit, fontsize=S.FS_TEXT, color=MID, ha="right", va="center")
        y -= 20.0
    ax.text(118, 12.5, f"Illustrative: F̄ = {ILLUSTRATIVE_FORCE:.0f} N/kg, J = {ILLUSTRATIVE_IMPULSE} m/s ⇒ T = J/(F̄ − g) = {duration:.3f} s.\nPeak = g + (π/2)(F̄ − g) for this half-sine. Not athlete data.", fontsize=5.5, color=MID, va="top", linespacing=1.35)
    save_figure(fig, 2, "Force-time definitions in the synthetic measurement system")
    return {"duration_s": duration, "peak_n_per_kg": peak}


def plot_innovation():
    baseline_truth = ILLUSTRATIVE_FORCE
    r24 = fixed_mode_response(24.0, *ILLUSTRATIVE_AMPLITUDES)
    criterion_truth = baseline_truth * (1.0 + r24)
    streams = KeyedRandomStreams("manuscript-illustration")
    base = assessment_trials(baseline_truth, metric="force", streams=streams, assessment_key="baseline")
    crit = assessment_trials(criterion_truth, metric="force", streams=streams, assessment_key="criterion:H24")
    base_mean, crit_mean = sum(base) / 3, sum(crit) / 3
    innovation = crit_mean - base_mean
    fig = new_figure(87, 66)
    ax = axmm(fig, 17, 15, 66, 42)
    for k, (group, color, x0) in enumerate((("baseline", COBALT, 0), ("criterion (H24)", VERMILION, 1))):
        vals = base if k == 0 else crit
        mean = base_mean if k == 0 else crit_mean
        ax.plot([x0 - 0.18, x0, x0 + 0.18], vals, marker="o", linestyle="none", color=color, markersize=4, markeredgecolor="white")
        ax.hlines(mean, x0 - 0.3, x0 + 0.3, color=INK, lw=1.3)
        ax.text(x0, mean + 0.08, f"mean {mean:.2f}", ha="center", va="bottom", fontsize=S.FS_TEXT)
    ax.annotate("", xy=(1.42, crit_mean), xytext=(1.42, base_mean), arrowprops={"arrowstyle": "<->", "lw": 0.9, "color": INK})
    ax.text(1.5, (crit_mean + base_mean) / 2, f"innovation\n{innovation:+.2f} N/kg", fontsize=S.FS_TEXT, va="center", fontweight="bold")
    ax.set_xlim(-0.5, 2.3)
    lo, hi = min(*base, *crit) - 0.35, max(*base, *crit) + 0.5
    ax.set_ylim(lo, hi)
    ax.set_xticks([0, 1], ["baseline\n(≈2 h pre-exposure)", "criterion\n(24 h after)"])
    ax.set_ylabel("Mean concentric force (N/kg)")
    tidy_axis(ax, "y")
    fig.text(1 / 87, 65 / 66, "Trials → assessment mean → innovation", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    fig.text(1 / 87, 1.2 / 66, "Illustrative: truth 20 N/kg, a_f = 0.04, a_s = 0.03;\ntrial noise from the generator's measurement model.", fontsize=5.0, color=MID, va="bottom")
    save_figure(fig, 3, "Three-trial assessment and baseline-relative innovation")
    return {"baseline_trials": base, "criterion_trials": crit, "innovation": innovation}


def plot_response_modes():
    tau = np.linspace(0, 96, 481)
    a_f, a_s = ILLUSTRATIVE_AMPLITUDES
    fig = new_figure(180, 74)
    panel_label(fig, "a", 1, 73)
    fig.text(7 / 180, 73 / 74, "Fixed response modes (synthetic assumption)", fontsize=S.FS_TITLE, fontweight="bold", va="top")
    ax1 = axmm(fig, 16, 14, 70, 44)
    fast = np.array([-a_f * math.exp(-x / FAST_MODE_HOURS) for x in tau]) * 100
    slow = np.array([-a_s * math.exp(-x / SLOW_MODE_HOURS) for x in tau]) * 100
    total = np.array([fixed_mode_response(x, a_f, a_s) for x in tau]) * 100
    ax1.plot(tau, fast, color=OCHRE, lw=1.0, ls="--", label=f"fast mode, e-fold {FAST_MODE_HOURS:.0f} h")
    ax1.plot(tau, slow, color=TEAL, lw=1.0, ls="--", label=f"slow mode, e-fold {SLOW_MODE_HOURS:.0f} h")
    ax1.plot(tau, total, color=INK, lw=1.7, label=r"$r(\tau)$ (sum)")
    for h in (24, 48, 72):
        ax1.axvline(h, color=RULE, lw=0.7)
        ax1.text(h, 0.25, f"H{h}", ha="center", va="bottom", fontsize=S.FS_TEXT, color=COBALT, fontweight="bold")
    ax1.set_xlim(0, 96)
    ax1.set_ylim(-7.8, 1.3)
    ax1.set_xlabel(r"Time since exposure, $\tau$ (h)")
    ax1.set_ylabel("Relative change in true force (%)")
    ax1.legend(loc="lower right", fontsize=5.8)
    tidy_axis(ax1, "y")
    panel_label(fig, "b", 95, 73)
    ax2 = axmm(fig, 108, 14, 68, 44)
    lo = np.array([fixed_mode_response(x, 0.01, 0.0) for x in tau]) * 100
    hi = np.array([fixed_mode_response(x, 0.08, 0.08) for x in tau]) * 100
    ax2.fill_between(tau, hi, lo, color=PALE_OCHRE, lw=0, label="envelope of the amplitude support")
    ax2.plot(tau, lo, color=OCHRE, lw=0.8)
    ax2.plot(tau, hi, color=OCHRE, lw=0.8)
    ax2.plot(tau, total, color=INK, lw=1.5, label="panel a example")
    for h in (24, 48, 72):
        ax2.axvline(h, color=RULE, lw=0.7)
    ax2.set_xlim(0, 96)
    ax2.set_ylim(-17, 1.5)
    ax2.set_xlabel(r"Time since exposure, $\tau$ (h)")
    ax2.legend(loc="lower right", fontsize=5.8)
    tidy_axis(ax2, "y")
    fig.text(16 / 180, 1.5 / 74, "Amplitude support: a_f ∈ [0.01, 0.08], a_s ∈ [0, 0.08] (fraction of baseline). Plotted values are illustrative; the 24 h and 84 h constants are generator assumptions.", fontsize=5.0, color=MID, va="bottom")
    save_figure(fig, 4, "Fixed-mode response functions of the synthetic generator")


def validate_inputs(architecture, routes, six_cells, uncertainty, study):
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


def main():
    architecture = read_csv(SUPPLEMENT / "architecture_qualification.csv")
    routes = read_csv(SUPPLEMENT / "model_identity_sanitized.csv")
    six_cells = read_csv(SUPPLEMENT / "six_cell_results.csv")
    uncertainty = read_csv(SUPPLEMENT / "recorded_uncertainty.csv")
    study = read_json(DOCS / "M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json")
    validate_inputs(architecture, routes, six_cells, uncertainty, study)
    plot_study_map()
    plot_force_time()
    plot_innovation()
    plot_response_modes()
    plot_architecture(architecture)
    plot_sample_design(study)
    plot_public_performance(six_cells)
    plot_heatmap(six_cells, study)
    plot_bootstrap(uncertainty, study)
    plot_ablation_sample_size(study)
    plot_numerical(routes)
    files = sorted(S.OUT.glob("Fig*.pdf"))
    assert len(files) == 11, f"Expected 11 PDF figures, found {len(files)}"
    for pdf in files:
        for suffix in (".svg", ".png"):
            assert pdf.with_suffix(suffix).is_file(), f"Missing export for {pdf.stem}{suffix}"
    print(f"Generated {len(files)} figures as PDF, SVG and PNG.")


if __name__ == "__main__":
    main()
