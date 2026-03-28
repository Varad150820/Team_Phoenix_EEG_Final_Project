from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PER = ROOT / "milestone5" / "final_pipeline" / "per_recording"
OUT_DIR = ROOT / "milestone5" / "reports"
OUT_PNG = OUT_DIR / "paper_style_erp_match_mismatch.png"

SESSION_ORDER = ["TestVisual", "TestVibro", "TestEMS"]
SESSION_LABEL = {
    "TestVisual": "Visual",
    "TestVibro": "Vibro",
    "TestEMS": "EMS",
}
SESSION_COLOR = {
    "TestVisual": "#5aa7de",
    "TestVibro": "#e47e5c",
    "TestEMS": "#e6b84b",
}

# To match the figure style requested:
# A = match trials, B = mismatch trials, and right panel = A-B.
MATCH_CONDITION = "box:touched"
MISMATCH_CONDITION = "box:spawned"


def harmonize_evokeds(evokeds: list[mne.Evoked]) -> list[mne.Evoked]:
    if len(evokeds) <= 1:
        return evokeds

    tmin = max(float(ev.times[0]) for ev in evokeds)
    tmax = min(float(ev.times[-1]) for ev in evokeds)
    prepared = [ev.copy().crop(tmin=tmin, tmax=tmax) for ev in evokeds]
    mne.equalize_channels(prepared, copy=False)

    target_n_times = min(len(ev.times) for ev in prepared)
    target_times = np.linspace(tmin, tmax, target_n_times)
    target_sfreq = float((target_n_times - 1) / (tmax - tmin)) if target_n_times > 1 else float(prepared[0].info["sfreq"])

    aligned: list[mne.Evoked] = []
    for ev in prepared:
        data_interp = np.vstack([np.interp(target_times, ev.times, ch_data) for ch_data in ev.data])
        info = ev.info.copy()
        with info._unlock():
            info["sfreq"] = target_sfreq
        ev_interp = mne.EvokedArray(
            data_interp,
            info,
            tmin=float(target_times[0]),
            comment=ev.comment,
            nave=ev.nave,
            baseline=ev.baseline,
        )
        aligned.append(ev_interp)

    return aligned


def collect_evokeds() -> tuple[dict[tuple[str, str], list[mne.Evoked]], str]:
    metric_files = sorted(PER.glob("*_metrics.json"))
    if not metric_files:
        raise RuntimeError("No per-recording metrics found.")

    rows = [pd.read_json(path, typ="series") for path in metric_files]
    rec_df = pd.DataFrame(rows)
    ok_df = rec_df[rec_df["status"] == "ok"].copy()
    if ok_df.empty:
        raise RuntimeError("No successful recordings found.")

    grouped: dict[tuple[str, str], list[mne.Evoked]] = {}
    candidate_channel_names: set[str] = set()

    for row in ok_df.itertuples(index=False):
        session = str(row.session)
        if session not in SESSION_ORDER:
            continue

        evoked_file = PER / str(row.evoked_file)
        if not evoked_file.exists():
            continue

        evokeds = mne.read_evokeds(evoked_file, verbose="ERROR")
        by_comment = {ev.comment: ev for ev in evokeds}

        for cond in (MATCH_CONDITION, MISMATCH_CONDITION):
            ev = by_comment.get(cond)
            if ev is None:
                continue
            ev = ev.copy()
            ev.apply_baseline((-0.1, 0.0))
            grouped.setdefault((session, cond), []).append(ev)
            candidate_channel_names.update(ev.ch_names)

    if not grouped:
        raise RuntimeError("No grouped evoked data found.")

    channel = "FCz" if "FCz" in candidate_channel_names else ("Cz" if "Cz" in candidate_channel_names else sorted(candidate_channel_names)[0])
    return grouped, channel


def summarize_condition(evokeds: list[mne.Evoked], channel: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    aligned = harmonize_evokeds(evokeds)
    times = aligned[0].times
    values = []
    for ev in aligned:
        idx = ev.ch_names.index(channel)
        values.append(ev.data[idx] * 1e6)
    arr = np.array(values, dtype=float)
    mean = arr.mean(axis=0)
    sem = arr.std(axis=0, ddof=1) / np.sqrt(arr.shape[0]) if arr.shape[0] > 1 else np.zeros(arr.shape[1])
    return times, mean, sem


def build_figure() -> None:
    grouped, channel = collect_evokeds()

    series: dict[str, dict[str, np.ndarray]] = {}
    for session in SESSION_ORDER:
        match_evs = grouped.get((session, MATCH_CONDITION), [])
        mismatch_evs = grouped.get((session, MISMATCH_CONDITION), [])
        n = min(len(match_evs), len(mismatch_evs))
        if n == 0:
            continue
        match_evs = match_evs[:n]
        mismatch_evs = mismatch_evs[:n]

        t_match, m_match, s_match = summarize_condition(match_evs, channel)
        t_mismatch, m_mismatch, s_mismatch = summarize_condition(mismatch_evs, channel)

        n_time = min(len(t_match), len(t_mismatch))
        t = t_match[:n_time]
        m_match = m_match[:n_time]
        s_match = s_match[:n_time]
        m_mismatch = m_mismatch[:n_time]
        s_mismatch = s_mismatch[:n_time]

        diff_mean = m_match - m_mismatch
        diff_sem = np.sqrt(s_match**2 + s_mismatch**2)

        series[session] = {
            "t": t,
            "match_mean": m_match,
            "match_sem": s_match,
            "mismatch_mean": m_mismatch,
            "mismatch_sem": s_mismatch,
            "diff_mean": diff_mean,
            "diff_sem": diff_sem,
        }

    if not series:
        raise RuntimeError("No session had both match and mismatch conditions.")

    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor("#efefef")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1.2], height_ratios=[1, 1], wspace=0.25, hspace=0.35)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[1, 0], sharex=ax_a, sharey=ax_a)
    ax_diff = fig.add_subplot(gs[:, 1], sharex=ax_a)

    for ax in (ax_a, ax_b, ax_diff):
        ax.set_facecolor("#efefef")
        ax.axhline(0.0, color="#888888", linewidth=1.1)
        ax.axvline(0.0, color="#888888", linewidth=1.1)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    for session in SESSION_ORDER:
        if session not in series:
            continue
        label = SESSION_LABEL[session]
        color = SESSION_COLOR[session]
        t = series[session]["t"]

        mm = series[session]["match_mean"]
        ms = series[session]["match_sem"]
        xm = series[session]["mismatch_mean"]
        xs = series[session]["mismatch_sem"]
        dm = series[session]["diff_mean"]
        ds = series[session]["diff_sem"]

        ax_a.plot(t, mm, color=color, linewidth=2.4, label=label)
        ax_a.fill_between(t, mm - ms, mm + ms, color=color, alpha=0.25)

        ax_b.plot(t, xm, color=color, linewidth=2.4, label=label)
        ax_b.fill_between(t, xm - xs, xm + xs, color=color, alpha=0.25)

        ax_diff.plot(t, dm, color=color, linewidth=2.4, label=label)
        ax_diff.fill_between(t, dm - ds, dm + ds, color=color, alpha=0.25)

    ax_a.set_title("A. match trials", fontsize=18, fontweight="bold", loc="left")
    ax_b.set_title("B. mismatch trials", fontsize=18, fontweight="bold", loc="left")
    ax_diff.set_title("ERP difference (A - B)", fontsize=17)

    ax_a.set_ylabel(f"{channel} (µV)", fontsize=12)
    ax_b.set_ylabel(f"{channel} (µV)", fontsize=12)
    ax_b.set_xlabel("Time (s)", fontsize=12)
    ax_diff.set_ylabel(f"{channel} (µV)", fontsize=12)
    ax_diff.set_xlabel("Time (s)", fontsize=12)

    for ax in (ax_a, ax_b, ax_diff):
        ax.tick_params(labelsize=10)

    ax_a.legend(loc="upper right", framealpha=0.9)
    ax_diff.legend(loc="upper right", framealpha=0.9)

    # Zoom all panels to requested window
    for ax in (ax_a, ax_b, ax_diff):
        ax.set_xlim(0.0, 0.4)

    # Annotation bracket for prediction-error window (visual style cue)
    x1, x2 = 0.10, 0.30

    y_annot_b = ax_b.get_ylim()[0] + 0.6
    ax_b.plot([x1, x2], [y_annot_b, y_annot_b], color="black", linewidth=1.8)
    ax_b.plot([x1, x1], [y_annot_b - 0.15, y_annot_b], color="black", linewidth=1.8)
    ax_b.plot([x2, x2], [y_annot_b - 0.15, y_annot_b], color="black", linewidth=1.8)
    ax_b.text((x1 + x2) / 2, y_annot_b - 0.2, "prediction error", ha="center", va="top", fontsize=11)

    y_annot_d = ax_diff.get_ylim()[0] + 0.7
    ax_diff.plot([x1, x2], [y_annot_d, y_annot_d], color="black", linewidth=1.8)
    ax_diff.plot([x1, x1], [y_annot_d - 0.15, y_annot_d], color="black", linewidth=1.8)
    ax_diff.plot([x2, x2], [y_annot_d - 0.15, y_annot_d], color="black", linewidth=1.8)
    ax_diff.text((x1 + x2) / 2, y_annot_d - 0.2, "prediction error", ha="center", va="top", fontsize=11)

    fig.suptitle("Paper-style ERP visualization from pipeline data", fontsize=16, y=0.98)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=220, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {OUT_PNG}")
    print(f"Channel used for plotting: {channel}")


if __name__ == "__main__":
    build_figure()