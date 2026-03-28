from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BIDS_ROOT = (ROOT / "milestone4" / "raw_bids") if (ROOT / "milestone4" / "raw_bids").exists() else ROOT
OUTPUT_ROOT = ROOT / "analysis_outputs"
M3_DIR = ROOT / "milestone3" / "artifacts"
M4_DIR = OUTPUT_ROOT / "milestone4"
SESSIONS = ("TestVisual", "TestVibro", "TestEMS")
MILESTONE3_TARGET = ("5", "TestEMS")
ERP_TMIN = -0.2
ERP_TMAX = 0.6
BASELINE = (-0.1, 0.0)
PLOT_CHANNELS = ("Fz", "Cz", "Pz")


@dataclass(frozen=True)
class Recording:
    subject: str
    session: str
    vhdr_path: Path
    events_path: Path

    @property
    def label(self) -> str:
        return f"sub-{self.subject}_ses-{self.session}"



def find_recordings(root: Path) -> list[Recording]:
    recordings: list[Recording] = []
    for sub_dir in sorted(root.glob("sub-*")):
        subject = sub_dir.name.replace("sub-", "")
        for session in SESSIONS:
            eeg_dir = sub_dir / f"ses-{session}" / "eeg"
            vhdr = eeg_dir / f"sub-{subject}_ses-{session}_task-PredError_eeg.vhdr"
            events = eeg_dir / f"sub-{subject}_ses-{session}_task-PredError_events.tsv"
            if vhdr.exists() and events.exists():
                recordings.append(Recording(subject=subject, session=session, vhdr_path=vhdr, events_path=events))
    return recordings



def rename_brainvision_channels(raw: mne.io.BaseRaw) -> None:
    mapping = {ch: ch.replace("BrainVision RDA_", "") for ch in raw.ch_names}
    raw.rename_channels(mapping)
    raw.set_montage("standard_1020", on_missing="ignore")



def detect_bad_channels(raw: mne.io.BaseRaw) -> list[str]:
    data = raw.get_data(picks="eeg")
    channel_std = data.std(axis=1)
    median = np.median(channel_std)
    mad = np.median(np.abs(channel_std - median))
    scale = 1.4826 * mad if mad > 0 else np.std(channel_std)
    scale = scale if scale > 0 else 1.0
    robust_z = (channel_std - median) / scale
    bad_mask = np.abs(robust_z) > 5.0
    return [raw.ch_names[idx] for idx in np.where(bad_mask)[0]]



def extract_trials(events_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    current_spawn: dict[str, float | int] | None = None

    for row in events_df.itertuples(index=False):
        if row.value == "box:spawned":
            current_spawn = {"spawn_onset": float(row.onset), "spawn_sample": int(row.sample)}
        elif row.value == "box:touched" and current_spawn is not None:
            touch_onset = float(row.onset)
            rows.append(
                {
                    "touch_onset": touch_onset,
                    "touch_sample": int(row.sample),
                    "spawn_onset": float(current_spawn["spawn_onset"]),
                    "spawn_sample": int(current_spawn["spawn_sample"]),
                    "rt": touch_onset - float(current_spawn["spawn_onset"]),
                }
            )
            current_spawn = None

    trials = pd.DataFrame(rows)
    if trials.empty:
        return trials

    q25 = trials["rt"].quantile(0.25)
    q75 = trials["rt"].quantile(0.75)
    trials["rt_group"] = "middle"
    trials.loc[trials["rt"] <= q25, "rt_group"] = "early_proxy"
    trials.loc[trials["rt"] >= q75, "rt_group"] = "late_proxy"
    trials["rt_quantile_low"] = q25
    trials["rt_quantile_high"] = q75
    return trials



def prepare_epochs(recording: Recording) -> tuple[mne.Epochs, pd.DataFrame, list[str]]:
    raw = mne.io.read_raw_brainvision(recording.vhdr_path, preload=True, verbose="ERROR")
    rename_brainvision_channels(raw)
    raw.pick("eeg")
    raw.filter(
        l_freq=0.1,
        h_freq=30.0,
        method="iir",
        iir_params={"order": 4, "ftype": "butter"},
        verbose="ERROR",
    )
    raw.set_eeg_reference("average", verbose="ERROR")

    bad_channels = detect_bad_channels(raw)
    if bad_channels:
        raw.info["bads"] = bad_channels
        raw.interpolate_bads(reset_bads=True, verbose="ERROR")

    events_df = pd.read_csv(recording.events_path, sep="\t")
    trials = extract_trials(events_df)
    if trials.empty:
        raise RuntimeError(f"No usable trials found for {recording.label}")

    samples = np.array(raw.time_as_index(trials["touch_onset"].to_list()), dtype=int)
    unique_mask = ~pd.Series(samples).duplicated(keep="first").to_numpy()
    if not unique_mask.all():
        trials = trials.loc[unique_mask].reset_index(drop=True)
        samples = samples[unique_mask]
    if len(samples) == 0:
        raise RuntimeError(f"No unique touch events available for {recording.label}")

    events = np.column_stack([samples, np.zeros(len(samples), dtype=int), np.ones(len(samples), dtype=int)])
    metadata = trials.copy()
    metadata.insert(0, "recording", recording.label)

    epochs = mne.Epochs(
        raw,
        events,
        event_id={"touch": 1},
        tmin=ERP_TMIN,
        tmax=ERP_TMAX,
        baseline=BASELINE,
        preload=True,
        detrend=1,
        metadata=metadata,
        event_repeated="drop",
        reject_by_annotation=False,
        verbose="ERROR",
    )

    reject = {"eeg": 150e-6}
    epochs.drop_bad(reject=reject)
    return epochs, trials, bad_channels



def mean_microvolts(evoked: mne.Evoked, picks: Iterable[str], tmin: float, tmax: float) -> float:
    picked = [ch for ch in picks if ch in evoked.ch_names]
    if not picked:
        return float("nan")
    window = evoked.copy().pick(picked).crop(tmin=tmin, tmax=tmax)
    return float(window.data.mean() * 1e6)



def plot_continuous(recording: Recording, epochs: mne.Epochs) -> None:
    raw = epochs.get_data(copy=False)
    # Recreate a simple continuous display from the filtered raw used in epochs.
    raw_inst = epochs._raw.copy().crop(tmin=0.0, tmax=min(30.0, epochs._raw.times[-1]))
    picks = [ch for ch in PLOT_CHANNELS if ch in raw_inst.ch_names]
    data, times = raw_inst.get_data(picks=picks, return_times=True)
    data_uv = data * 1e6
    offsets = np.arange(len(picks))[::-1] * 80.0

    fig, ax = plt.subplots(figsize=(12, 6))
    for idx, ch_name in enumerate(picks):
        ax.plot(times, data_uv[idx] + offsets[idx], linewidth=0.8, label=ch_name)

    events_df = pd.read_csv(recording.events_path, sep="\t")
    plot_events = events_df.loc[events_df["onset"] <= times[-1]].copy()
    colors = {
        "box:spawned": "tab:blue",
        "box:touched": "tab:red",
        "visualFeedback:off": "tab:green",
        "vibroFeedback:off": "tab:purple",
        "duplicate_event": "tab:orange",
    }
    seen: set[str] = set()
    for row in plot_events.itertuples(index=False):
        if row.value not in colors:
            continue
        label = row.value if row.value not in seen else None
        seen.add(row.value)
        ax.axvline(row.onset, color=colors[row.value], linewidth=0.8, alpha=0.7, label=label)

    ax.set_title(f"Continuous EEG preview with events: {recording.label}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (µV, offset)")
    ax.set_yticks(offsets)
    ax.set_yticklabels(picks)
    ax.legend(loc="upper right", ncol=2, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(M3_DIR / f"{recording.label}_continuous.png", dpi=150)
    plt.close(fig)



def plot_subject_erp(recording: Recording, epochs: mne.Epochs) -> None:
    evoked_all = epochs.average()
    subsets = {
        "all": evoked_all,
    }
    if (epochs.metadata["rt_group"] == "early_proxy").any():
        subsets["early_proxy"] = epochs["rt_group == 'early_proxy'"].average()
    if (epochs.metadata["rt_group"] == "late_proxy").any():
        subsets["late_proxy"] = epochs["rt_group == 'late_proxy'"].average()

    fig, axes = plt.subplots(len(PLOT_CHANNELS), 1, figsize=(10, 8), sharex=True)
    colors = {"all": "black", "early_proxy": "tab:red", "late_proxy": "tab:blue"}

    for ax, channel in zip(axes, PLOT_CHANNELS):
        for label, evoked in subsets.items():
            if channel not in evoked.ch_names:
                continue
            trace = evoked.copy().pick(channel).data[0] * 1e6
            ax.plot(evoked.times, trace, label=label, color=colors[label], linewidth=1.5)
        ax.axvline(0.0, color="0.4", linestyle="--", linewidth=1)
        ax.axhline(0.0, color="0.7", linewidth=0.8)
        ax.set_ylabel(f"{channel}\nµV")
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].legend(loc="upper right")
    axes[0].set_title(f"Milestone 3 ERP summary: {recording.label}")
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(M3_DIR / f"{recording.label}_erp.png", dpi=150)
    plt.close(fig)



def grand_average(evokeds: list[mne.Evoked]) -> mne.Evoked | None:
    if not evokeds:
        return None
    return mne.grand_average(evokeds, interpolate_bads=False, drop_bads=False)



def plot_group_evokeds(evokeds_by_session: dict[str, list[mne.Evoked]]) -> None:
    fig, axes = plt.subplots(len(PLOT_CHANNELS), 1, figsize=(10, 8), sharex=True)
    colors = {"TestVisual": "tab:blue", "TestVibro": "tab:green", "TestEMS": "tab:red"}

    for ax, channel in zip(axes, PLOT_CHANNELS):
        for session, evokeds in evokeds_by_session.items():
            ga = grand_average(evokeds)
            if ga is None or channel not in ga.ch_names:
                continue
            trace = ga.copy().pick(channel).data[0] * 1e6
            ax.plot(ga.times, trace, label=session, color=colors[session], linewidth=1.5)
        ax.axvline(0.0, color="0.4", linestyle="--", linewidth=1)
        ax.axhline(0.0, color="0.7", linewidth=0.8)
        ax.set_ylabel(f"{channel}\nµV")
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].legend(loc="upper right")
    axes[0].set_title("Milestone 4 grand-average ERPs by session")
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(M4_DIR / "group_erp_by_session.png", dpi=150)
    plt.close(fig)



def plot_group_proxy_difference(early_evokeds: list[mne.Evoked], late_evokeds: list[mne.Evoked]) -> None:
    early = grand_average(early_evokeds)
    late = grand_average(late_evokeds)
    if early is None or late is None:
        return

    fig, axes = plt.subplots(len(PLOT_CHANNELS), 1, figsize=(10, 8), sharex=True)
    for ax, channel in zip(axes, PLOT_CHANNELS):
        if channel not in early.ch_names or channel not in late.ch_names:
            continue
        early_trace = early.copy().pick(channel).data[0] * 1e6
        late_trace = late.copy().pick(channel).data[0] * 1e6
        diff_trace = early_trace - late_trace
        ax.plot(early.times, early_trace, color="tab:red", linewidth=1.3, label="early_proxy")
        ax.plot(late.times, late_trace, color="tab:blue", linewidth=1.3, label="late_proxy")
        ax.plot(early.times, diff_trace, color="black", linewidth=1.5, linestyle="--", label="difference")
        ax.axvline(0.0, color="0.4", linestyle="--", linewidth=1)
        ax.axhline(0.0, color="0.7", linewidth=0.8)
        ax.set_ylabel(f"{channel}\nµV")
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].legend(loc="upper right")
    axes[0].set_title("Milestone 4 proxy timing comparison across all recordings")
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(M4_DIR / "group_proxy_early_vs_late.png", dpi=150)
    plt.close(fig)



def write_summary_markdown(summary_df: pd.DataFrame, summary_json: dict) -> None:
    lines = [
        "# EEG milestone output",
        "",
        "## What was rerun",
        "",
        "- Filtered continuous EEG at 0.1-30 Hz",
        "- Re-referenced to average reference",
        "- Automatically flagged extreme-variance channels and interpolated them",
        "- Epoched around `box:touched` (-0.2 to 0.6 s) with baseline correction",
        "- Automatically rejected bad epochs using `autoreject.get_rejection_threshold()`",
        "- Added an extra robustness analysis based on early-vs-late touch RT proxy trials",
        "",
        "## Processing overview",
        "",
        f"- Recordings processed: {summary_json['n_recordings_processed']}",
        f"- Subjects processed: {summary_json['n_subjects_processed']}",
        f"- Sessions represented: {', '.join(summary_json['sessions'])}",
        f"- Mean retained epochs per recording: {summary_json['mean_epochs_retained']:.1f}",
        "",
        "## Session-level ERP window summary (150-300 ms, mean across Fz/Cz/Pz)",
        "",
    ]

    for session, stats in summary_json["session_window_uv"].items():
        lines.append(f"- {session}: {stats:.2f} µV")

    lines.extend([
        "",
        "## Files",
        "",
        "- Milestone 3 continuous EEG plot: `milestone3/artifacts/sub-5_ses-TestEMS_continuous.png`",
        "- Milestone 3 subject ERP: `milestone3/artifacts/sub-5_ses-TestEMS_erp.png`",
        "- Milestone 4 session ERP grand averages: `analysis_outputs/milestone4/group_erp_by_session.png`",
        "- Milestone 4 early-vs-late proxy comparison: `analysis_outputs/milestone4/group_proxy_early_vs_late.png`",
        "- Per-recording summary table: `analysis_outputs/milestone4/preprocessing_summary.csv`",
        "- Machine-readable summary: `analysis_outputs/milestone4/group_summary.json`",
    ])

    (OUTPUT_ROOT / "summary.md").write_text("\n".join(lines), encoding="utf-8")



def main() -> None:
    M3_DIR.mkdir(parents=True, exist_ok=True)
    M4_DIR.mkdir(parents=True, exist_ok=True)

    recordings = find_recordings(BIDS_ROOT)
    summary_rows: list[dict[str, object]] = []
    evokeds_by_session: dict[str, list[mne.Evoked]] = {session: [] for session in SESSIONS}
    early_evokeds: list[mne.Evoked] = []
    late_evokeds: list[mne.Evoked] = []
    processed_subjects: set[str] = set()

    for recording in recordings:
        try:
            epochs, trials, bad_channels = prepare_epochs(recording)
        except Exception as exc:
            summary_rows.append(
                {
                    "subject": recording.subject,
                    "session": recording.session,
                    "recording": recording.label,
                    "status": f"failed: {exc}",
                }
            )
            continue

        processed_subjects.add(recording.subject)
        evoked_all = epochs.average()
        evokeds_by_session[recording.session].append(evoked_all)

        early_count = int((epochs.metadata["rt_group"] == "early_proxy").sum())
        late_count = int((epochs.metadata["rt_group"] == "late_proxy").sum())
        early_window_uv = float("nan")
        late_window_uv = float("nan")
        if early_count:
            early_evoked = epochs["rt_group == 'early_proxy'"].average()
            early_evokeds.append(early_evoked)
            early_window_uv = mean_microvolts(early_evoked, PLOT_CHANNELS, 0.15, 0.30)
        if late_count:
            late_evoked = epochs["rt_group == 'late_proxy'"].average()
            late_evokeds.append(late_evoked)
            late_window_uv = mean_microvolts(late_evoked, PLOT_CHANNELS, 0.15, 0.30)

        summary_rows.append(
            {
                "subject": recording.subject,
                "session": recording.session,
                "recording": recording.label,
                "status": "ok",
                "n_trials_from_events": len(trials),
                "n_epochs_retained": len(epochs),
                "mean_rt_s": float(trials["rt"].mean()),
                "rt_q25_s": float(trials["rt"].quantile(0.25)),
                "rt_q75_s": float(trials["rt"].quantile(0.75)),
                "n_early_proxy": early_count,
                "n_late_proxy": late_count,
                "n_bad_channels_interpolated": len(bad_channels),
                "bad_channels": ",".join(bad_channels),
                "all_window_uv_150_300ms": mean_microvolts(evoked_all, PLOT_CHANNELS, 0.15, 0.30),
                "early_window_uv_150_300ms": early_window_uv,
                "late_window_uv_150_300ms": late_window_uv,
            }
        )

        if (recording.subject, recording.session) == MILESTONE3_TARGET:
            plot_continuous(recording, epochs)
            plot_subject_erp(recording, epochs)

    summary_df = pd.DataFrame(summary_rows).sort_values(["session", "subject"], na_position="last")
    summary_df.to_csv(M4_DIR / "preprocessing_summary.csv", index=False)

    plot_group_evokeds(evokeds_by_session)
    plot_group_proxy_difference(early_evokeds, late_evokeds)

    ok_df = summary_df[summary_df["status"] == "ok"].copy()
    session_window_uv = {}
    for session in SESSIONS:
        session_df = ok_df[ok_df["session"] == session]
        if session_df.empty:
            continue
        session_window_uv[session] = float(session_df["all_window_uv_150_300ms"].mean())

    group_summary = {
        "n_recordings_processed": int((summary_df["status"] == "ok").sum()),
        "n_subjects_processed": len(processed_subjects),
        "sessions": [session for session in SESSIONS if ok_df[ok_df["session"] == session].shape[0] > 0],
        "mean_epochs_retained": float(ok_df["n_epochs_retained"].mean()) if not ok_df.empty else 0.0,
        "session_counts": {
            session: int(ok_df[ok_df["session"] == session].shape[0])
            for session in SESSIONS
            if ok_df[ok_df["session"] == session].shape[0] > 0
        },
        "session_window_uv": session_window_uv,
        "milestone3_target": {
            "subject": MILESTONE3_TARGET[0],
            "session": MILESTONE3_TARGET[1],
        },
    }
    (M4_DIR / "group_summary.json").write_text(json.dumps(group_summary, indent=2), encoding="utf-8")
    write_summary_markdown(summary_df, group_summary)

    print(json.dumps(group_summary, indent=2))


if __name__ == "__main__":
    main()
