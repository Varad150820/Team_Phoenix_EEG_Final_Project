from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "milestone5" / "reports" / "pipeline_flow_infographic.png"


def add_box(ax, xy, width, height, color, text, fontsize=16, radius=0.03):
    x, y = xy
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        linewidth=1.5,
        edgecolor=(0, 0, 0, 0.2),
        facecolor=color,
    )
    ax.add_patch(box)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color="white",
        fontsize=fontsize,
        fontweight="bold",
        linespacing=1.4,
        family="DejaVu Sans",
    )


def add_arrow(ax, start, end, color="#5f6e7a", lw=2.5, rad=0.0):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(
            arrowstyle="->",
            color=color,
            lw=lw,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=2,
            shrinkB=2,
        ),
    )


def main() -> None:
    fig, ax = plt.subplots(figsize=(16, 9), dpi=160)
    fig.patch.set_facecolor("#eceff3")
    ax.set_facecolor("#eceff3")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    add_box(
        ax,
        (0.35, 0.88),
        0.30,
        0.10,
        "#355b7e",
        "INPUT\nRaw BIDS EEG\n64 ch · 1000 Hz · 19 subjects",
        fontsize=19,
        radius=0.05,
    )

    add_box(
        ax,
        (0.23, 0.68),
        0.54,
        0.15,
        "#123f66",
        "PHASE 1: PREPROCESSING\n"
        "Bandpass Filter (5–20 Hz) + Resample (250 Hz)\n"
        "Bad-Channel Detection (robust z-score) + Interpolation\n"
        "ICA Artifact Removal (Infomax, 12 components)",
        fontsize=17,
        radius=0.03,
    )

    add_box(
        ax,
        (0.23, 0.52),
        0.54,
        0.13,
        "#20737c",
        "PHASE 2: SIGNAL CONDITIONING\n"
        "Average Reference (64-electrode mean)\n"
        "Epoch Extraction (−100 to +1000 ms) + Baseline Correction",
        fontsize=17,
        radius=0.03,
    )

    add_box(
        ax,
        (0.23, 0.34),
        0.54,
        0.15,
        "#188050",
        "PHASE 3: QUALITY CONTROL\n"
        "Automatic Epoch Rejection (AutoReject / 150 µV fallback)\n"
        "Per-subject Quality Metrics (drop rate, RMS, trial counts)\n"
        "Noisy Subject Exclusion (robust outlier detection)",
        fontsize=17,
        radius=0.03,
    )

    add_box(
        ax,
        (0.23, 0.18),
        0.54,
        0.12,
        "#b77708",
        "PHASE 4: GROUP ANALYSIS & OUTPUT\n"
        "Grand-Average ERPs (2 events × 3 conditions = 6 ERPs)\n"
        "Reports: Topomaps, Waveforms, HTML, CSV/JSON",
        fontsize=17,
        radius=0.03,
    )

    add_box(
        ax,
        (0.32, 0.03),
        0.36,
        0.11,
        "#b44a2e",
        "OUTPUT\nClean ERP Dataset\n18 subjects · 59 recordings · 6 grand averages",
        fontsize=19,
        radius=0.05,
    )

    add_arrow(ax, (0.50, 0.88), (0.50, 0.83))
    add_arrow(ax, (0.50, 0.68), (0.50, 0.65))
    add_arrow(ax, (0.50, 0.52), (0.50, 0.49))
    add_arrow(ax, (0.50, 0.34), (0.50, 0.30))
    add_arrow(ax, (0.50, 0.18), (0.50, 0.14))

    add_arrow(ax, (0.77, 0.76), (0.88, 0.76), lw=1.8)
    ax.text(0.89, 0.76, "53/60 recordings\nhad bad channels\n(repaired)", fontsize=14, va="center", color="#222")

    add_arrow(ax, (0.77, 0.41), (0.88, 0.41), lw=1.8)
    ax.text(0.89, 0.41, "1 noisy subject\nexcluded", fontsize=14, va="center", color="#222")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
