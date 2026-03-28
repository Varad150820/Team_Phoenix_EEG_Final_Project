from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne


ROOT = Path(__file__).resolve().parents[1]
PER_RECORDING_OUT = ROOT / "milestone5" / "final_pipeline" / "per_recording"
REPORTS_OUT = ROOT / "milestone5" / "reports"

PREFERRED_SESSION_ORDER = ["Training", "TestEMS", "TestVibro", "TestVisual"]
PREFERRED_CONDITION_ORDER = ["box:spawned", "box:touched"]


def make_combined_erp_figure(lines: list[tuple[str, mne.Evoked]], title: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_facecolor("#eaeaea")
    for label, evoked in lines:
        if "Cz" not in evoked.ch_names:
            continue
        data_uv = evoked.copy().pick("Cz").data[0] * 1e6
        ax.plot(evoked.times, data_uv, linewidth=1.5, label=label)

    ax.axvline(0.0, color="black", linestyle="--", linewidth=1.2)
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1.0)
    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("µV")
    ax.legend(loc="upper left", ncol=2, framealpha=0.9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def make_psd_figure(evoked: mne.Evoked, title: str) -> plt.Figure:
    nyquist = float(evoked.info["sfreq"]) / 2.0
    fmax = min(124.0, nyquist - 0.01)
    fig = evoked.compute_psd(fmin=1.0, fmax=fmax).plot(show=False)
    fig.set_size_inches(10, 5)
    fig.axes[0].set_title(title)
    fig.tight_layout()
    return fig


def parse_subject_session_from_name(name: str) -> tuple[str, str] | None:
    match = re.match(r"^(sub-[^_]+)_ses-([^_]+)_evoked-ave\.fif$", name)
    if not match:
        return None
    return match.group(1), match.group(2)


def session_sort_key(session: str) -> tuple[int, str]:
    if session in PREFERRED_SESSION_ORDER:
        return (PREFERRED_SESSION_ORDER.index(session), session)
    return (len(PREFERRED_SESSION_ORDER), session)


def condition_sort_key(condition: str) -> tuple[int, str]:
    if condition in PREFERRED_CONDITION_ORDER:
        return (PREFERRED_CONDITION_ORDER.index(condition), condition)
    return (len(PREFERRED_CONDITION_ORDER), condition)


def pretty_session(session: str) -> str:
    mapping = {
        "Training": "Training",
        "TestEMS": "EMS",
        "TestVibro": "Vibro",
        "TestVisual": "Visual",
    }
    return mapping.get(session, session)


def pretty_condition(condition: str) -> str:
    mapping = {
        "box:spawned": "Spawned",
        "box:touched": "Touched",
    }
    return mapping.get(condition, condition)


def build_reports() -> None:
    if not PER_RECORDING_OUT.exists():
        raise RuntimeError(f"Missing input folder: {PER_RECORDING_OUT}")

    REPORTS_OUT.mkdir(parents=True, exist_ok=True)
    evoked_files = sorted(PER_RECORDING_OUT.glob("*_evoked-ave.fif"))
    if not evoked_files:
        raise RuntimeError("No per-recording evoked files found.")

    by_subject: dict[str, dict[str, Path]] = {}
    for evoked_file in evoked_files:
        parsed = parse_subject_session_from_name(evoked_file.name)
        if parsed is None:
            continue
        subject, session = parsed
        by_subject.setdefault(subject, {})[session] = evoked_file

    if not by_subject:
        raise RuntimeError("No subject/session evoked files were recognized.")

    def subject_sort_key(value: str) -> tuple[int, str]:
        token = value.split("-", 1)[1] if "-" in value else value
        if token.isdigit():
            return (int(token), value)
        return (10_000, value)

    generated = 0
    for subject in sorted(by_subject.keys(), key=subject_sort_key):
        out_path = REPORTS_OUT / f"{subject}_mne_report.html"
        if out_path.exists():
            print(f"Skipping existing: {out_path}")
            continue

        session_to_file = by_subject[subject]
        sessions = sorted(session_to_file.keys(), key=session_sort_key)

        report = mne.Report(title=f"{subject} EEG Report", image_format="png")
        report.add_html(
            """
            <h3>Subject-wise EEG ERP Report</h3>
            <p>This report shows ERP and PSD plots for this subject, split by session and condition.</p>
            <ul>
              <li>ERP plots are baseline corrected from -100ms to 0ms.</li>
              <li>PSD plots summarize frequency content for each ERP.</li>
              <li>Combined plot overlays all available session-condition ERPs for quick comparison.</li>
            </ul>
            """,
            title="EEG Analysis Explanation",
        )

        combined_lines: list[tuple[str, mne.Evoked]] = []

        for session in sessions:
            evoked_file = session_to_file[session]
            evokeds = mne.read_evokeds(evoked_file, verbose="ERROR")
            evoked_by_condition = {ev.comment: ev for ev in evokeds}

            for condition in sorted(evoked_by_condition.keys(), key=condition_sort_key):
                evoked = evoked_by_condition[condition].copy()
                evoked.apply_baseline((-0.1, 0.0))

                title = f"{pretty_session(session)} {pretty_condition(condition)}"
                erp_fig = evoked.plot(show=False, spatial_colors=True, gfp=True)
                erp_fig.suptitle(title)
                report.add_figure(fig=erp_fig, title=title, tags=("evoked",))
                plt.close(erp_fig)
                psd_fig = make_psd_figure(evoked, f"PSD for {title}")
                report.add_figure(fig=psd_fig, title=f"PSD for {title}", tags=("custom-figure",))
                plt.close(psd_fig)
                combined_lines.append((title, evoked))

        if combined_lines:
            combined_fig = make_combined_erp_figure(combined_lines, f"Combined ERPs for {subject}")
            report.add_figure(fig=combined_fig, title="Combined ERP Comparison", tags=("custom-figure",))
            plt.close(combined_fig)

        report.save(out_path, overwrite=True, open_browser=False)
        generated += 1
        print(f"Generated: {out_path}")

    print(f"Done. Generated {generated} subject report(s) in {REPORTS_OUT}.")


def main() -> None:
    build_reports()


if __name__ == "__main__":
    main()