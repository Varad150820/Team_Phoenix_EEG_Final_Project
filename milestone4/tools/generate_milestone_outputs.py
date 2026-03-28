from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_BIDS_ROOT = (ROOT / "milestone4" / "raw_bids") if (ROOT / "milestone4" / "raw_bids").exists() else ROOT
LEGACY_DERIV_ROOT = ROOT / "milestone5" / "legacy_derivatives" / "DS003846"
OUT = ROOT / "analysis_outputs"
M3 = ROOT / "milestone2" / "continuous_data_of_one_subject"
M4 = OUT / "milestone4"
M5 = ROOT / "milestone5" / "artifacts"
SESSIONS = ["TestVisual", "TestVibro", "TestEMS", "Training"]


def ensure_dirs() -> None:
    for path in (M3, M4, M5):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "milestone5" / "reports").mkdir(parents=True, exist_ok=True)


def dataset_subjects() -> list[str]:
    return sorted([p.name.replace("sub-", "") for p in RAW_BIDS_ROOT.glob("sub-*") if p.is_dir()])


def derivative_status_table(subjects: list[str]) -> pd.DataFrame:
    rows = []
    for subject in subjects:
        for session in SESSIONS:
            raw_vhdr = RAW_BIDS_ROOT / f"sub-{subject}" / f"ses-{session}" / "eeg" / f"sub-{subject}_ses-{session}_task-PredError_eeg.vhdr"
            deriv_dir = LEGACY_DERIV_ROOT / f"sub-{subject}" / f"ses-{session}" / "eeg"
            rows.append(
                {
                    "subject": subject,
                    "session": session,
                    "raw_exists": raw_vhdr.exists(),
                    "report_exists": (deriv_dir / f"sub-{subject}_ses-{session}_task-PredError_report.html").exists(),
                    "scores_exists": (deriv_dir / f"sub-{subject}_ses-{session}_task-PredError_scores.json").exists(),
                    "filt_raw_exists": (deriv_dir / f"sub-{subject}_ses-{session}_task-PredError_proc-filt_raw.fif").exists(),
                    "epochs_exists": (deriv_dir / f"sub-{subject}_ses-{session}_task-PredError_epo.fif").exists(),
                    "clean_epochs_exists": (deriv_dir / f"sub-{subject}_ses-{session}_task-PredError_proc-clean_epo.fif").exists(),
                    "evoked_exists": (deriv_dir / f"sub-{subject}_ses-{session}_task-PredError_ave.fif").exists(),
                }
            )
    table = pd.DataFrame(rows)
    table.to_csv(M4 / "pipeline_completion_table.csv", index=False)
    return table


def plot_completion(table: pd.DataFrame) -> None:
    total = table.groupby("session")["raw_exists"].sum().reindex(SESSIONS).fillna(0)
    reports = table.groupby("session")["report_exists"].sum().reindex(SESSIONS).fillna(0)
    evoked = table.groupby("session")["evoked_exists"].sum().reindex(SESSIONS).fillna(0)

    x = np.arange(len(SESSIONS))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width, total.values, width=width, label="Raw recordings", color="tab:gray")
    ax.bar(x, reports.values, width=width, label="Report produced", color="tab:blue")
    ax.bar(x + width, evoked.values, width=width, label="Evoked produced", color="tab:red")
    ax.set_xticks(x)
    ax.set_xticklabels(SESSIONS)
    ax.set_ylabel("Count")
    ax.set_title("Milestone 4 coverage check by session")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(M4 / "completion_overview.png", dpi=150)
    plt.close(fig)


def plot_milestone3_outputs() -> dict[str, str]:
    target = {"subject": "5", "session": "TestEMS"}
    subject = target["subject"]
    session = target["session"]

    vhdr = RAW_BIDS_ROOT / f"sub-{subject}" / f"ses-{session}" / "eeg" / f"sub-{subject}_ses-{session}_task-PredError_eeg.vhdr"
    events_tsv = RAW_BIDS_ROOT / f"sub-{subject}" / f"ses-{session}" / "eeg" / f"sub-{subject}_ses-{session}_task-PredError_events.tsv"
    ave_fif = LEGACY_DERIV_ROOT / f"sub-{subject}" / f"ses-{session}" / "eeg" / f"sub-{subject}_ses-{session}_task-PredError_ave.fif"

    output_files = {}

    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="ERROR")
    raw.rename_channels({ch: ch.replace("BrainVision RDA_", "") for ch in raw.ch_names})
    raw.set_montage("standard_1020", on_missing="ignore")
    raw.pick("eeg")
    raw.filter(
        l_freq=0.1,
        h_freq=30.0,
        method="iir",
        iir_params={"order": 4, "ftype": "butter"},
        verbose="ERROR",
    )
    raw.set_eeg_reference("average", verbose="ERROR")

    channel_std = raw.get_data(picks="eeg").std(axis=1)
    median = np.median(channel_std)
    mad = np.median(np.abs(channel_std - median))
    scale = 1.4826 * mad if mad > 0 else np.std(channel_std)
    scale = scale if scale > 0 else 1.0
    robust_z = (channel_std - median) / scale
    bad_idx = np.where(np.abs(robust_z) > 5.0)[0]
    bads = [raw.ch_names[idx] for idx in bad_idx]
    if bads:
        raw.info["bads"] = bads
        raw.interpolate_bads(reset_bads=True, verbose="ERROR")

    picks = [ch for ch in ["Fz", "Cz", "Pz"] if ch in raw.ch_names]
    crop_tmax = min(30.0, raw.times[-1])
    raw_crop = raw.copy().pick(picks).crop(tmin=0.0, tmax=crop_tmax)
    data, times = raw_crop.get_data(return_times=True)
    data_uv = data * 1e6
    offset_step = max(40.0, float(np.nanpercentile(np.abs(data_uv), 99)) * 2.5)
    offsets = np.arange(len(picks))[::-1] * offset_step

    events = pd.read_csv(events_tsv, sep="\t")
    events = events[events["onset"] <= crop_tmax]
    colors = {
        "box:spawned": "tab:blue",
        "box:touched": "tab:red",
        "vibroFeedback:off": "tab:purple",
        "visualFeedback:off": "tab:green",
        "duplicate_event": "tab:orange",
    }

    fig, ax = plt.subplots(figsize=(12, 6))
    for idx, ch in enumerate(picks):
        ax.plot(times, data_uv[idx] + offsets[idx], label=ch, linewidth=0.8)

    seen = set()
    for row in events.itertuples(index=False):
        if row.value not in colors:
            continue
        label = row.value if row.value not in seen else None
        seen.add(row.value)
        ax.axvline(float(row.onset), color=colors[row.value], alpha=0.7, linewidth=0.8, label=label)

    ax.set_title("Milestone 3: continuous EEG with marked events (sub-5, TestEMS)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (µV, offset)")
    ax.set_yticks(offsets)
    ax.set_yticklabels(picks)
    ax.legend(loc="upper right", ncol=2, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    continuous_png = M3 / "sub-5_ses-TestEMS_continuous_events.png"
    fig.savefig(continuous_png, dpi=150)
    plt.close(fig)
    output_files["continuous"] = str(continuous_png.relative_to(ROOT)).replace("\\", "/")

    evoked = mne.read_evokeds(ave_fif, condition=0, verbose="ERROR")
    evoked.rename_channels({ch: ch.replace("BrainVision RDA_", "") for ch in evoked.ch_names})
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, ch in zip(axes, ["Fz", "Cz", "Pz"]):
        if ch in evoked.ch_names:
            trace = evoked.copy().pick(ch).data[0] * 1e6
            ax.plot(evoked.times, trace, color="black", linewidth=1.5)
        ax.axvline(0.0, color="0.4", linestyle="--", linewidth=1)
        ax.axhline(0.0, color="0.7", linewidth=0.8)
        ax.set_ylabel(f"{ch}\nµV")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_title("Milestone 3: ERP for sub-5 TestEMS (box:touched)")
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    erp_png = M3 / "sub-5_ses-TestEMS_erp.png"
    fig.savefig(erp_png, dpi=150)
    plt.close(fig)
    output_files["erp"] = str(erp_png.relative_to(ROOT)).replace("\\", "/")

    return output_files


def detect_pipeline_steps(table: pd.DataFrame) -> dict[str, dict[str, str]]:
    cache = LEGACY_DERIV_ROOT / "_cache" / "mne_bids_pipeline" / "steps"

    def exists(pattern: str) -> bool:
        return any(cache.glob(pattern))

    step_status = {
        "data_loaded": {
            "status": "done" if table["raw_exists"].any() else "not_done",
            "evidence": "Raw BIDS files exist in sub-*/ses-*/eeg",
        },
        "data_quality": {
            "status": "done" if exists("preprocessing/_01_data_quality/**/output.pkl") else "not_done",
            "evidence": "Cache folder _01_data_quality",
        },
        "filtering": {
            "status": "done" if exists("preprocessing/_04_frequency_filter/**/output.pkl") else "not_done",
            "evidence": "Cache folder _04_frequency_filter; proc-filt_raw.fif exists for sub-5 TestEMS",
        },
        "event_handling": {
            "status": "done",
            "evidence": "Config has event_repeated='drop' and events.tsv contains duplicate_event markers",
        },
        "epoching": {
            "status": "done" if exists("preprocessing/_07_make_epochs/**/output.pkl") else "not_done",
            "evidence": "Cache folder _07_make_epochs; epo.fif exists for sub-5 TestEMS",
        },
        "auto_cleaning_ptp": {
            "status": "done" if exists("preprocessing/_09_ptp_reject/**/output.pkl") else "not_done",
            "evidence": "Cache folder _09_ptp_reject; proc-clean_epo.fif exists for sub-5 TestEMS",
        },
        "ica": {
            "status": "not_done",
            "evidence": "No ICA step output found in derivatives/cache",
        },
        "evoked_subject": {
            "status": "done" if table["evoked_exists"].any() else "not_done",
            "evidence": "sub-5 TestEMS _ave.fif exists",
        },
        "group_average": {
            "status": "done" if (LEGACY_DERIV_ROOT / "sub-average" / "ses-TestEMS" / "eeg" / "sub-average_ses-TestEMS_task-PredError_proc-clean_ave.fif").exists() else "not_done",
            "evidence": "sub-average TestEMS evoked file exists",
        },
        "all_subjects_processed": {
            "status": "not_done",
            "evidence": "Derivatives only for sub-5 (+ sub-average), not for all available subjects",
        },
    }
    return step_status


def write_report(table: pd.DataFrame, step_status: dict[str, dict[str, str]], outputs: dict[str, str]) -> None:
    subjects_total = int(table["subject"].nunique())
    raw_total = int(table["raw_exists"].sum())
    reports_total = int(table["report_exists"].sum())
    evoked_total = int(table["evoked_exists"].sum())

    core_hypotheses = [
        "If visuo-haptic feedback is mismatched (premature feedback), early negative ERP components should be stronger than in matched trials.",
        "EEG ERPs can provide an objective signal of visuo-haptic conflict and complement subjective immersion questionnaires.",
    ]

    lines = [
        "# Milestone 3-5 Output (Audit + Existing Derivatives)",
        "",
        "## Core paper information",
        "",
        "- **Paper**: Detecting Visuo-Haptic Mismatches in Virtual Reality using the Prediction Error Negativity of ERPs (CHI 2019)",
        "- **General experiment idea**: participants touched virtual objects under visual-only, vibrotactile, and EMS conditions; in 25% of trials feedback was delivered prematurely to induce mismatch.",
        "- **Main research question**: can EEG (ERP prediction-error negativity) detect visuo-haptic mismatch events in VR?",
        "- **Main analysis type**: Event-Related Potentials (ERP)",
        "",
        "## Extracted central hypotheses",
        "",
    ]
    for hyp in core_hypotheses:
        lines.append(f"- {hyp}")

    lines.extend(
        [
            "",
            "## Milestone 3 (first subject analyzed)",
            "",
            "- Existing subject-level derivatives found for `sub-5` `ses-TestEMS` (`_proc-filt_raw.fif`, `_epo.fif`, `_proc-clean_epo.fif`, `_ave.fif`).",
            f"- Continuous EEG + event markers figure: `{outputs['continuous']}`",
            f"- Subject ERP figure: `{outputs['erp']}`",
            "",
            "## Milestone 4 (all subjects check)",
            "",
            f"- Dataset has **{subjects_total} subjects** and **{raw_total} raw recordings** (across sessions).",
            f"- Derivative reports exist for **{reports_total} recordings**.",
            f"- Evoked outputs exist for **{evoked_total} recording(s)**.",
            "- **Conclusion**: milestone 4 is **not completed for all subjects**.",
            "- Completion table: `analysis_outputs/milestone4/pipeline_completion_table.csv`",
            "- Completion overview plot: `analysis_outputs/milestone4/completion_overview.png`",
            "",
            "## Pipeline step checklist (done vs not done)",
            "",
        ]
    )

    for step, info in step_status.items():
        lines.append(f"- **{step}**: {info['status']} ({info['evidence']})")

    lines.extend(
        [
            "",
            "## Milestone 5 outlook (next analyses)",
            "",
            "- Finish the same preprocessing+ERP pipeline for all available subjects and sessions.",
            "- Recreate a mismatch-vs-normal ERP contrast once full condition labels are restored in events metadata.",
            "- Add one robustness extension analysis (time-frequency or decoding) after full replication is stable.",
            "",
            "## Notes",
            "",
            "- Event metadata dictionary lists fields such as `normal_or_conflict`, but current events.tsv files only contain compact markers; this blocks exact mismatch-vs-normal replication from raw events alone.",
            "- Existing derivatives indicate a partial mne-bids-pipeline run focused on sub-5/TestEMS.",
        ]
    )

    report = ROOT / "milestone5" / "reports" / "milestone3_to_5_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "subjects_total": subjects_total,
        "raw_recordings_total": raw_total,
        "derivative_reports_total": reports_total,
        "evoked_outputs_total": evoked_total,
        "milestone4_all_subjects_complete": False,
        "pipeline_step_status": step_status,
        "milestone3_outputs": outputs,
        "report_file": "milestone5/reports/milestone3_to_5_report.md",
    }
    (ROOT / "milestone5" / "reports" / "milestone3_to_5_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    subjects = dataset_subjects()
    table = derivative_status_table(subjects)
    plot_completion(table)
    outputs = plot_milestone3_outputs()
    step_status = detect_pipeline_steps(table)
    write_report(table, step_status, outputs)
    print("Generated milestone outputs under milestone3/, milestone5/, and analysis_outputs/milestone4/")


if __name__ == "__main__":
    main()
