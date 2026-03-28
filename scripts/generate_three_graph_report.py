from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PER = ROOT / "milestone5" / "final_pipeline" / "per_recording"
REPORTS_OUT = ROOT / "milestone5" / "reports"
OUTPUT_PNG = REPORTS_OUT / "grand_average_match_mismatch_three_graphs.png"
OUTPUT_HTML = REPORTS_OUT / "grand_average_match_mismatch_report.html"
OUTPUT_MNE_HTML = REPORTS_OUT / "grand_average_match_mismatch_mne_report.html"
OUTPUT_JSON = REPORTS_OUT / "grand_average_match_mismatch_summary.json"

SESSION_ORDER = ["TestEMS", "TestVibro", "TestVisual"]
SESSION_LABEL = {"TestEMS": "EMS", "TestVibro": "Vibro", "TestVisual": "Visual"}
SESSION_COLOR = {
    "TestEMS": "#e6b84b",
    "TestVibro": "#e47e5c",
    "TestVisual": "#5aa7de",
}

MATCH_CONDITION = "box:spawned"
MISMATCH_CONDITION = "box:touched"
DIFFERENCE_LABEL = "B - A"


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


def choose_channel(candidate_names: list[str]) -> str:
    for preferred in ("FCz", "Fcz", "FCZ", "Cz", "Fz"):
        if preferred in candidate_names:
            return preferred
    return candidate_names[0]


def collect_evokeds() -> dict[tuple[str, str], list[mne.Evoked]]:
    metric_files = sorted(PER.glob("*_metrics.json"))
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in metric_files]
    if not rows:
        raise RuntimeError("No per-recording metrics found.")

    rec_df = pd.DataFrame(rows)
    ok_df = rec_df[rec_df["status"] == "ok"].copy()
    if ok_df.empty:
        raise RuntimeError("No successful recordings found.")

    grouped: dict[tuple[str, str], list[mne.Evoked]] = {}
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

    if not grouped:
        raise RuntimeError("No usable evoked data found for configured sessions/conditions.")
    return grouped


def mean_sem_from_evokeds(evokeds: list[mne.Evoked], channel: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    aligned = harmonize_evokeds(evokeds)
    times = aligned[0].times
    values = []
    for ev in aligned:
        pick = ev.ch_names.index(channel)
        values.append(ev.data[pick] * 1e6)
    arr = np.vstack(values)
    mean = arr.mean(axis=0)
    sem = arr.std(axis=0, ddof=1) / np.sqrt(arr.shape[0]) if arr.shape[0] > 1 else np.zeros(arr.shape[1])
    return times, mean, sem


def build_figure(series_data: dict[str, dict[str, np.ndarray]], channel: str) -> None:
    fig = plt.figure(figsize=(13, 8), constrained_layout=False)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.2, 1.0], height_ratios=[1, 1], wspace=0.3, hspace=0.35)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[1, 0], sharex=ax_a, sharey=ax_a)
    ax_diff = fig.add_subplot(gs[:, 1], sharex=ax_a)

    for axis in (ax_a, ax_b, ax_diff):
        axis.axvline(0.0, color="#666666", linestyle="-", linewidth=0.8, alpha=0.8)
        axis.axhline(0.0, color="#666666", linestyle="-", linewidth=0.8, alpha=0.8)
        axis.spines[["top", "right"]].set_visible(False)

    ax_a.set_title("A. Match trials")
    ax_b.set_title("B. Mismatch trials")
    ax_diff.set_title(f"ERP difference ({DIFFERENCE_LABEL})")

    for session in SESSION_ORDER:
        if session not in series_data:
            continue
        color = SESSION_COLOR[session]
        label = SESSION_LABEL[session]
        time = series_data[session]["time"]

        match_mean = series_data[session]["match_mean"]
        match_sem = series_data[session]["match_sem"]
        mismatch_mean = series_data[session]["mismatch_mean"]
        mismatch_sem = series_data[session]["mismatch_sem"]
        diff_mean = series_data[session]["diff_mean"]
        diff_sem = series_data[session]["diff_sem"]

        ax_a.plot(time, match_mean, color=color, linewidth=2.0, label=label)
        ax_a.fill_between(time, match_mean - match_sem, match_mean + match_sem, color=color, alpha=0.25)

        ax_b.plot(time, mismatch_mean, color=color, linewidth=2.0, label=label)
        ax_b.fill_between(time, mismatch_mean - mismatch_sem, mismatch_mean + mismatch_sem, color=color, alpha=0.25)

        ax_diff.plot(time, diff_mean, color=color, linewidth=2.0, label=label)
        ax_diff.fill_between(time, diff_mean - diff_sem, diff_mean + diff_sem, color=color, alpha=0.25)

    ax_b.set_xlabel("Time (s)")
    ax_diff.set_xlabel("Time (s)")
    ax_a.set_ylabel(f"{channel} (µV)")
    ax_b.set_ylabel(f"{channel} (µV)")
    ax_diff.set_ylabel(f"{channel} (µV)")

    ax_a.legend(loc="upper right", framealpha=0.9)
    ax_diff.legend(loc="upper right", framealpha=0.9)

    fig.suptitle(
        "Grand average across all subjects: Match, Mismatch, and Difference",
        fontsize=14,
        y=0.97,
    )
    fig.savefig(OUTPUT_PNG, dpi=180)
    plt.close(fig)


def build_single_panel_figure(
    series_data: dict[str, dict[str, np.ndarray]],
    channel: str,
    panel: str,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.axvline(0.0, color="#666666", linestyle="-", linewidth=0.8, alpha=0.8)
    ax.axhline(0.0, color="#666666", linestyle="-", linewidth=0.8, alpha=0.8)
    ax.spines[["top", "right"]].set_visible(False)

    if panel == "match":
        title = "A. Match trials"
        mean_key = "match_mean"
        sem_key = "match_sem"
    elif panel == "mismatch":
        title = "B. Mismatch trials"
        mean_key = "mismatch_mean"
        sem_key = "mismatch_sem"
    else:
        title = f"ERP difference ({DIFFERENCE_LABEL})"
        mean_key = "diff_mean"
        sem_key = "diff_sem"

    for session in SESSION_ORDER:
        if session not in series_data:
            continue
        color = SESSION_COLOR[session]
        label = SESSION_LABEL[session]
        time = series_data[session]["time"]
        mean = series_data[session][mean_key]
        sem = series_data[session][sem_key]
        ax.plot(time, mean, color=color, linewidth=2.0, label=label)
        ax.fill_between(time, mean - sem, mean + sem, color=color, alpha=0.25)

    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(f"{channel} (µV)")
    ax.legend(loc="upper right", framealpha=0.9)
    fig.tight_layout()
    return fig


def write_html(channel: str, n_subjects_by_session: dict[str, int]) -> None:
    lines = [
        "<html><head><meta charset='utf-8'><title>Grand Average Match/Mismatch Report</title>",
        "<style>body{font-family:Arial,Helvetica,sans-serif;margin:24px;} img{max-width:1200px;border:1px solid #ddd;} li{margin:4px 0;}</style>",
        "</head><body>",
        "<h1>Grand Average Match/Mismatch Report</h1>",
        "<p>This report reproduces the 3-graph layout you requested using all available subjects.</p>",
        "<ul>",
        f"<li>Match (A): <b>{MATCH_CONDITION}</b></li>",
        f"<li>Mismatch (B): <b>{MISMATCH_CONDITION}</b></li>",
        f"<li>Difference: <b>{DIFFERENCE_LABEL}</b></li>",
        f"<li>Plotted channel: <b>{channel}</b> (FCz preferred if present)</li>",
        "</ul>",
        "<h2>Three-graph figure</h2>",
        f"<img src='{OUTPUT_PNG.name}' alt='match mismatch difference grand average'>",
        "<h2>Included subjects by session</h2>",
        "<ul>",
    ]
    for session in SESSION_ORDER:
        label = SESSION_LABEL[session]
        lines.append(f"<li>{label}: <b>{n_subjects_by_session.get(session, 0)}</b> subjects</li>")
    lines.extend(["</ul>", "</body></html>"])
    OUTPUT_HTML.write_text("\n".join(lines), encoding="utf-8")


def write_mne_report(
    channel: str,
    n_subjects_by_session: dict[str, int],
    series_data: dict[str, dict[str, np.ndarray]],
) -> None:
    report = mne.Report(title="Grand Average Match/Mismatch (MNE Report)", image_format="png")
    report.add_html(
        f"""
        <h3>Grand-average ERP (All Subjects)</h3>
        <ul>
            <li>Match (A): <b>{MATCH_CONDITION}</b></li>
            <li>Mismatch (B): <b>{MISMATCH_CONDITION}</b></li>
            <li>Difference: <b>{DIFFERENCE_LABEL}</b></li>
            <li>Channel: <b>{channel}</b></li>
        </ul>
        """,
        title="EEG Analysis Explanation",
    )

    fig_match = build_single_panel_figure(series_data, channel, panel="match")
    report.add_figure(fig=fig_match, title="A. Match trials", tags=("custom-figure",))
    plt.close(fig_match)

    fig_mismatch = build_single_panel_figure(series_data, channel, panel="mismatch")
    report.add_figure(fig=fig_mismatch, title="B. Mismatch trials", tags=("custom-figure",))
    plt.close(fig_mismatch)

    fig_diff = build_single_panel_figure(series_data, channel, panel="difference")
    report.add_figure(fig=fig_diff, title=f"ERP difference ({DIFFERENCE_LABEL})", tags=("custom-figure",))
    plt.close(fig_diff)

    combined = plt.figure(figsize=(13, 8), constrained_layout=False)
    gs = combined.add_gridspec(2, 2, width_ratios=[1.2, 1.0], height_ratios=[1, 1], wspace=0.3, hspace=0.35)
    ax_a = combined.add_subplot(gs[0, 0])
    ax_b = combined.add_subplot(gs[1, 0], sharex=ax_a, sharey=ax_a)
    ax_diff = combined.add_subplot(gs[:, 1], sharex=ax_a)
    for axis in (ax_a, ax_b, ax_diff):
        axis.axvline(0.0, color="#666666", linestyle="-", linewidth=0.8, alpha=0.8)
        axis.axhline(0.0, color="#666666", linestyle="-", linewidth=0.8, alpha=0.8)
        axis.spines[["top", "right"]].set_visible(False)
    ax_a.set_title("A. Match trials")
    ax_b.set_title("B. Mismatch trials")
    ax_diff.set_title(f"ERP difference ({DIFFERENCE_LABEL})")
    for session in SESSION_ORDER:
        if session not in series_data:
            continue
        color = SESSION_COLOR[session]
        label = SESSION_LABEL[session]
        time = series_data[session]["time"]
        ax_a.plot(time, series_data[session]["match_mean"], color=color, linewidth=2.0, label=label)
        ax_a.fill_between(
            time,
            series_data[session]["match_mean"] - series_data[session]["match_sem"],
            series_data[session]["match_mean"] + series_data[session]["match_sem"],
            color=color,
            alpha=0.25,
        )
        ax_b.plot(time, series_data[session]["mismatch_mean"], color=color, linewidth=2.0, label=label)
        ax_b.fill_between(
            time,
            series_data[session]["mismatch_mean"] - series_data[session]["mismatch_sem"],
            series_data[session]["mismatch_mean"] + series_data[session]["mismatch_sem"],
            color=color,
            alpha=0.25,
        )
        ax_diff.plot(time, series_data[session]["diff_mean"], color=color, linewidth=2.0, label=label)
        ax_diff.fill_between(
            time,
            series_data[session]["diff_mean"] - series_data[session]["diff_sem"],
            series_data[session]["diff_mean"] + series_data[session]["diff_sem"],
            color=color,
            alpha=0.25,
        )
    ax_b.set_xlabel("Time (s)")
    ax_diff.set_xlabel("Time (s)")
    ax_a.set_ylabel(f"{channel} (µV)")
    ax_b.set_ylabel(f"{channel} (µV)")
    ax_diff.set_ylabel(f"{channel} (µV)")
    ax_a.legend(loc="upper right", framealpha=0.9)
    ax_diff.legend(loc="upper right", framealpha=0.9)
    combined.suptitle(
        f"Grand average across all subjects: Match, Mismatch, and Difference ({DIFFERENCE_LABEL})",
        fontsize=14,
        y=0.97,
    )
    report.add_figure(fig=combined, title="Combined 3-panel view", tags=("custom-figure",))
    plt.close(combined)

    details = "".join(
        [f"<li>{SESSION_LABEL[s]}: <b>{n_subjects_by_session.get(s, 0)}</b> subjects</li>" for s in SESSION_ORDER]
    )
    report.add_html(f"<h4>Included subjects by session</h4><ul>{details}</ul>", title="Session Coverage")
    report.save(OUTPUT_MNE_HTML, overwrite=True, open_browser=False)


def main() -> None:
    REPORTS_OUT.mkdir(parents=True, exist_ok=True)
    grouped = collect_evokeds()

    representative_key = next(iter(grouped.keys()))
    representative_ev = harmonize_evokeds(grouped[representative_key])[0]
    channel = choose_channel(representative_ev.ch_names)

    series_data: dict[str, dict[str, np.ndarray]] = {}
    n_subjects_by_session: dict[str, int] = {}

    for session in SESSION_ORDER:
        match_list = grouped.get((session, MATCH_CONDITION), [])
        mismatch_list = grouped.get((session, MISMATCH_CONDITION), [])
        n = min(len(match_list), len(mismatch_list))
        if n == 0:
            continue

        match_list = match_list[:n]
        mismatch_list = mismatch_list[:n]
        n_subjects_by_session[session] = n

        t_match, m_match, s_match = mean_sem_from_evokeds(match_list, channel)
        t_mismatch, m_mismatch, s_mismatch = mean_sem_from_evokeds(mismatch_list, channel)

        n_time = min(len(t_match), len(t_mismatch))
        time = t_match[:n_time]
        m_match = m_match[:n_time]
        s_match = s_match[:n_time]
        m_mismatch = m_mismatch[:n_time]
        s_mismatch = s_mismatch[:n_time]

        diff_mean = m_mismatch - m_match
        diff_sem = np.sqrt(s_match**2 + s_mismatch**2)

        series_data[session] = {
            "time": time,
            "match_mean": m_match,
            "match_sem": s_match,
            "mismatch_mean": m_mismatch,
            "mismatch_sem": s_mismatch,
            "diff_mean": diff_mean,
            "diff_sem": diff_sem,
        }

    if not series_data:
        raise RuntimeError("No session had both match and mismatch data available.")

    build_figure(series_data, channel)
    write_html(channel, n_subjects_by_session)
    write_mne_report(channel, n_subjects_by_session, series_data)

    summary = {
        "match_condition": MATCH_CONDITION,
        "mismatch_condition": MISMATCH_CONDITION,
        "difference": DIFFERENCE_LABEL,
        "channel": channel,
        "n_subjects_by_session": n_subjects_by_session,
        "figure_png": OUTPUT_PNG.name,
        "report_html": OUTPUT_HTML.name,
        "mne_report_html": OUTPUT_MNE_HTML.name,
    }
    OUTPUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Saved figure: {OUTPUT_PNG}")
    print(f"Saved report: {OUTPUT_HTML}")
    print(f"Saved MNE report: {OUTPUT_MNE_HTML}")
    print(f"Saved summary: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()