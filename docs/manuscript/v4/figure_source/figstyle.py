"""Shared scientific figure design system for the science-first manuscript.

All figures are authored at their printed size: single column = 87 mm, double
column = 180 mm. Text is DejaVu Sans (bundled with Matplotlib, so the typeface is
reproducible) and mathematics uses the DejaVu Sans math set. Colour encodes the
model or evidence category, marker shape encodes the evaluation root, and no
colour scale is rainbow.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"

MM = 1 / 25.4
W1 = 87 * MM  # single column
W2 = 180 * MM  # double column

# Observatory palette: ink, cobalt and vermilion carry the argument; neutrals
# and one ochre accent separate categories that must remain distinguishable.
INK = "#17212b"
MID = "#5f6a74"
SOFT = "#97a1aa"
RULE = "#c9d0d6"
GRID = "#e6eaed"
PAPER = "#ffffff"
COBALT = "#1f4fa3"
VERMILION = "#c4452e"
OCHRE = "#b8862b"
TEAL = "#1d7f78"
SLATE = "#7b858f"
PALE_COBALT = "#dfe8f6"
PALE_VERMILION = "#f6e1dc"
PALE_OCHRE = "#f3ead7"
PALE_TEAL = "#dcefed"
PALE_GRAY = "#eef0f2"

MODEL_ORDER = ["zero_innovation", "training_constant", "ridge_full", "structured_full"]
MODEL_LABELS = {
    "zero_innovation": "Zero innovation",
    "training_constant": "Training mean",
    "ridge_full": "Ridge regression",
    "structured_full": "Structured comparator",
}
MODEL_SHORT = {
    "zero_innovation": "Zero\ninnovation",
    "training_constant": "Training\nmean",
    "ridge_full": "Ridge\nregression",
    "structured_full": "Structured\ncomparator",
}
MODEL_COLORS = {
    "zero_innovation": SLATE,
    "training_constant": OCHRE,
    "ridge_full": COBALT,
    "structured_full": VERMILION,
}
ROOT_ORDER = ["A", "B", "C"]
ROOT_MARKERS = {"A": "o", "B": "s", "C": "^"}
ROOT_KEYS = {"A": "root_a", "B": "root_b", "C": "root_c"}

FS_TEXT = 6.6
FS_LABEL = 7.0
FS_TITLE = 7.4
FS_PANEL = 9.0

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "mathtext.fontset": "dejavusans",
        "font.size": FS_TEXT,
        "axes.labelsize": FS_LABEL,
        "axes.titlesize": FS_TITLE,
        "xtick.labelsize": FS_TEXT,
        "ytick.labelsize": FS_TEXT,
        "legend.fontsize": FS_TEXT,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": MID,
        "axes.linewidth": 0.6,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.4,
        "ytick.major.size": 2.4,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "lines.linewidth": 1.0,
        "legend.frameon": False,
        "figure.facecolor": PAPER,
        "axes.facecolor": PAPER,
        "savefig.facecolor": PAPER,
        "svg.hashsalt": "cmj-recovery-scientific-figures",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def new_figure(width_mm: float, height_mm: float):
    return plt.figure(figsize=(width_mm * MM, height_mm * MM))


def axmm(fig, x, y, w, h, **kwargs):
    """Axes placed in millimetres from the lower-left corner of the figure."""
    fw, fh = fig.get_size_inches() / MM
    return fig.add_axes([x / fw, y / fh, w / fw, h / fh], **kwargs)


def canvas(fig, x=0, y=0, w=None, h=None):
    """Unitless drawing surface in millimetres (data coordinates equal millimetres)."""
    fw, fh = fig.get_size_inches() / MM
    w = fw if w is None else w
    h = fh if h is None else h
    ax = axmm(fig, x, y, w, h)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return ax


def panel_label(fig, letter, x_mm, y_mm):
    """Bold lowercase panel letter at an absolute position (mm from lower-left)."""
    fw, fh = fig.get_size_inches() / MM
    fig.text(
        x_mm / fw,
        y_mm / fh,
        letter,
        fontsize=FS_PANEL,
        fontweight="bold",
        color=INK,
        ha="left",
        va="top",
    )


def tidy_axis(ax, grid="y"):
    ax.tick_params(length=2.2, pad=1.8)
    if grid:
        ax.grid(axis=grid)
        ax.set_axisbelow(True)


def save_figure(fig, number: int, title: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    stem = f"Fig{number}"
    pdf, svg, png = (OUT / f"{stem}{ext}" for ext in (".pdf", ".svg", ".png"))
    if os.environ.get("FIG_PREVIEW"):  # fast iteration: PNG only
        fig.savefig(png, format="png", dpi=200)
        plt.close(fig)
        return
    fig.savefig(
        pdf,
        format="pdf",
        metadata={"Creator": "Matplotlib", "Title": f"Figure {number}: {title}", "CreationDate": None, "ModDate": None},
    )
    fig.savefig(svg, format="svg", metadata={"Creator": "Matplotlib", "Date": None})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    fig.savefig(png, format="png", dpi=300, metadata={"Software": f"Matplotlib {matplotlib.__version__}"})
    plt.close(fig)
