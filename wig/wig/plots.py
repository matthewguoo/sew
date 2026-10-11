"""Matplotlib styling: thin marks, recessive grid, fixed categorical palette (dataviz skill defaults)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
STATUS = dict(good="#008300", warning="#eda100", serious="#eb6834", critical="#e34948")
TEXT, TEXT2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"

def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": TEXT2, "xtick.color": TEXT2, "ytick.color": TEXT2,
        "text.color": TEXT, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
        "lines.markersize": 6, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
        "legend.frameon": False, "figure.dpi": 130, "axes.prop_cycle": matplotlib.cycler(color=PALETTE),
    })

def finish(fig, path, note=None):
    if note:
        fig.text(0.01, 0.005, note, fontsize=7.5, color=TEXT2, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.03 if note else 0, 1, 1))
    fig.savefig(path)
    plt.close(fig)
