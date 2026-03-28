from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["figure.constrained_layout.use"] = False
import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "milestone5" / "final_pipeline"
PER = OUT / "per_recording"



def robust_thresh(series: pd.Series, k: float = 2.5) -> float:
    med = float(np.median(series))
    mad = float(np.median(np.abs(series - med)))
    scale = 1.4826 * mad if mad > 0 else float(np.std(series))
    scale = scale if scale > 0 else 1.0
    return med + k * scale


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


def patch_mne_report_slider_js(report_path: Path) -> None:
        html = report_path.read_text(encoding="utf-8")
    # The following pattern matches the slider event handler function in the HTML
        pattern = re.compile(
                r"const addSliderEventHandlers = \(\) => \{\n.*?\n\}",
                re.DOTALL,
        )
        replacement = """const addSliderEventHandlers = () => {
    const accordionElementsWithSlider = document.querySelectorAll('div.accordion-item.slider');
    accordionElementsWithSlider.forEach((el) => {
        const accordionElement = el.querySelector('div.accordion-body');
        if (!accordionElement) {
            return;
        }

        const slider = accordionElement.querySelector('input[type="range"]');
        const carousel = accordionElement.querySelector('div.carousel');
        const items = carousel ? carousel.querySelectorAll('div.carousel-item') : [];
        if (!slider || !carousel || !items.length) {
            return;
        }

        const setActiveItem = (index) => {
            const safeIndex = Math.max(0, Math.min(index, items.length - 1));
            slider.value = String(safeIndex);
            items.forEach((item, itemIndex) => {
                item.classList.toggle('active', itemIndex === safeIndex);
            });
            carousel.dataset.activeIndex = String(safeIndex);
        }

        const initialIndex = Array.from(items).findIndex((item) => item.classList.contains('active'));
        setActiveItem(initialIndex >= 0 ? initialIndex : parseInt(slider.value || '0', 10));

        const handleSliderValue = (value) => {
            const parsedValue = parseInt(value, 10);
            setActiveItem(Number.isNaN(parsedValue) ? 0 : parsedValue);
        }

        slider.addEventListener('input', (e) => {
            handleSliderValue(e.target.value);
        });
        slider.addEventListener('change', (e) => {
            handleSliderValue(e.target.value);
        });

        const focusSlider = () => {
            slider.focus({preventScroll: true});
        }

        slider.addEventListener('click', focusSlider);
        carousel.addEventListener('click', focusSlider);

        slider.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'Left') {
                e.preventDefault();
                handleSliderValue(String(parseInt(slider.value || '0', 10) - 1));
            }
            if (e.key === 'ArrowRight' || e.key === 'Right') {
                e.preventDefault();
                handleSliderValue(String(parseInt(slider.value || '0', 10) + 1));
            }
        });
    })
}"""
        updated_html, count = pattern.subn(replacement, html, count=1)
        if count != 1:
                raise RuntimeError("Could not patch slider handler in MNE report HTML.")
        report_path.write_text(updated_html, encoding="utf-8")



def plot_multiline_grand_average(
    lines: list[tuple[str, mne.Evoked]],
    title: str,
    out_png: Path,
    channel: str = "Cz",
) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_facecolor("#eaeaea")

    for label, evoked in lines:
        if channel not in evoked.ch_names:
            continue
        data_uv = evoked.copy().pick(channel).data[0] * 1e6
        time_ms = evoked.times * 1000.0
        ax.plot(time_ms, data_uv, linewidth=1.8, label=label)

    ax.axvline(0.0, color="black", linestyle="--", linewidth=1.5)
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1.5)
    ax.set_title(title)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplitude (µV)")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_png, dpi=160)
    plt.close(fig)



def write_html(
    rec_df: pd.DataFrame,
    subj_df: pd.DataFrame,
    noisy_subjects: list[str],
    all_png: Path,
    clean_png: Path,
    all_multiline_png: Path,
    clean_multiline_png: Path,
) -> None:
    html = []
    html.append("<html><head><meta charset='utf-8'><title>Final EEG Milestones Report</title>")
    html.append("<style>body{font-family:Arial,Helvetica,sans-serif;margin:24px;} table{border-collapse:collapse;} th,td{border:1px solid #ccc;padding:6px 8px;font-size:12px;} h1,h2{margin-top:28px;} .ok{color:#1b7f1b;} img{max-width:980px;border:1px solid #ddd;}</style>")
    html.append("</head><body>")
    html.append("<h1>Final Milestones Report (All Subjects)</h1>")

    html.append("<h2>Milestone status</h2>")
    html.append("<ul>")
    html.append("<li class='ok'>Milestone 1: done</li>")
    html.append("<li class='ok'>Milestone 2: done</li>")
    html.append("<li class='ok'>Milestone 3: done</li>")
    html.append("<li class='ok'>Milestone 4: done</li>")
    html.append("<li class='ok'>Milestone 5: done</li>")
    html.append("</ul>")

    ok_recs = int((rec_df["status"] == "ok").sum())
    total = len(rec_df)
    html.append("<h2>Processing summary</h2>")
    html.append("<ul>")
    html.append(f"<li>Total recordings attempted: <b>{total}</b></li>")
    html.append(f"<li>Successfully processed recordings: <b>{ok_recs}</b></li>")
    html.append(f"<li>Noisy subjects removed for final grand average: <b>{', '.join(noisy_subjects) if noisy_subjects else 'None'}</b></li>")
    html.append("</ul>")

    html.append("<h2>Grand average (all processed subjects)</h2>")
    html.append(f"<img src='{all_png.name}' alt='grand average all'>")

    html.append("<h2>Grand average (all processed subjects, multi-line like requested)</h2>")
    html.append(f"<img src='{all_multiline_png.name}' alt='grand average multiline all'>")

    html.append("<h2>Grand average (after noisy-subject removal)</h2>")
    html.append(f"<img src='{clean_png.name}' alt='grand average clean'>")

    html.append("<h2>Grand average (after noisy-subject removal, multi-line like requested)</h2>")
    html.append(f"<img src='{clean_multiline_png.name}' alt='grand average multiline clean'>")

    html.append("<h2>Subject quality table</h2>")
    show_subj = subj_df.copy()
    for col in ("mean_drop_fraction", "mean_rms_uv", "mean_ica_excluded"):
        if col in show_subj.columns:
            show_subj[col] = show_subj[col].round(3)
    html.append(show_subj.to_html(index=False))

    html.append("<h2>Recording-level table</h2>")
    show_rec = rec_df.copy()
    for col in ("drop_fraction", "mean_uv_120_300ms", "rms_uv"):
        if col in show_rec.columns:
            show_rec[col] = show_rec[col].round(3)
    html.append(show_rec.to_html(index=False))

    html.append("</body></html>")
    (OUT / "final_grand_average_report.html").write_text("\n".join(html), encoding="utf-8")


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
    nyq = float(evoked.info["sfreq"]) / 2.0
    fmax = min(124.0, nyq - 0.01)
    fig = evoked.compute_psd(fmin=1.0, fmax=fmax).plot(show=False)
    fig.set_size_inches(10, 5)
    fig.axes[0].set_title(title)
    fig.tight_layout()
    return fig


def write_sectioned_clean_html(section_rows: list[dict[str, str]], out_html: Path) -> None:
        toc_items = []
        body_items = []
        toc_items.append("<li><a href='#exp'>EEG Analysis Explanation</a></li>")
        body_items.append("<section id='exp'><h2>EEG Analysis Explanation</h2><p>Cleaned grand averages after noisy-subject removal.</p></section>")

        for row in section_rows:
                toc_items.append(f"<li><a href='#{row['id_evoked']}'>{row['title']}</a></li>")
                toc_items.append(f"<li><a href='#{row['id_psd']}'>PSD for {row['title']}</a></li>")
                body_items.append(
                        f"<section id='{row['id_evoked']}'><h2>{row['title']}</h2>"
                        f"<img src='{row['erp_png']}' alt='{row['title']} ERP'><br>"
                        f"<img src='{row['topo_png']}' alt='{row['title']} topomap'></section>"
                )
                body_items.append(
                        f"<section id='{row['id_psd']}'><h2>PSD for {row['title']}</h2>"
                        f"<img src='{row['psd_png']}' alt='PSD for {row['title']}'></section>"
                )

        toc_items.append("<li><a href='#combined'>Combined ERP Comparison</a></li>")
        combined_png = "combined_erp_comparison_clean.png"
        body_items.append(f"<section id='combined'><h2>Combined ERP Comparison</h2><img src='{combined_png}' alt='Combined ERP Comparison'></section>")

        html = f"""
<html>
<head>
    <meta charset='utf-8'>
    <title>Grand Average ERPs for All Subjects - Spawned and Touched (Cleaned)</title>
    <style>
        body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f3f3f3; }}
        .wrap {{ display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }}
        .toc {{ background: #efefef; border-right: 1px solid #d0d0d0; padding: 16px; position: sticky; top: 0; height: 100vh; overflow-y: auto; }}
        .toc h3 {{ margin-top: 0; }}
        .toc ul {{ list-style: none; padding: 0; margin: 0; }}
        .toc li {{ margin: 8px 0; }}
        .toc a {{ color: #1f5fbf; text-decoration: none; }}
        .main {{ padding: 18px 24px; }}
        section {{ background: #fff; border: 1px solid #d6d6d6; margin-bottom: 16px; padding: 12px; }}
        img {{ max-width: 100%; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class='wrap'>
        <aside class='toc'>
            <h3>Table of contents</h3>
            <ul>{''.join(toc_items)}</ul>
        </aside>
        <main class='main'>
            <h1>Grand Average ERPs for All Subjects - Spawned and Touched (Cleaned)</h1>
            {''.join(body_items)}
        </main>
    </div>
</body>
</html>
"""
        out_html.write_text(html, encoding="utf-8")


def write_mne_style_report(
    evokeds_by_session_condition: dict[tuple[str, str], list[mne.Evoked]],
    keep_subjects: set[str],
    ok_df: pd.DataFrame,
) -> None:
    report = mne.Report(title="Grand Average ERPs for All Subjects - Spawned and Touched")
    report.add_html(
        """
        <h3>EEG Grand Average ERP Analysis</h3>
        <p>This report presents the grand average Event-Related Potentials (ERPs) for the 'box:spawned' and 'box:touched' conditions across all subjects in the dataset. The ERPs are averaged across subjects for each session type (EMS, Vibro, Visual).</p>
        <ul>
          <li>ERP Plots: Time-series plots showing the average brain response (in µV) over time, locked to stimulus onset (t=0). The baseline is corrected from -100ms to 0ms.</li>
          <li>PSD Plots: Power Spectral Density plots showing the frequency content of the ERPs.</li>
          <li>Combined Plot: A comparison of all ERPs in one figure, with legends indicating session and condition.</li>
          <li>Sessions: EMS (Electrical Muscle Stimulation), Vibro (Vibrotactile), Visual (Visual feedback).</li>
        </ul>
        """,
        title="EEG Analysis Explanation",
    )

    session_order = ["TestEMS", "TestVibro", "TestVisual"]
    condition_order = ["box:spawned", "box:touched"]
    session_label = {"TestEMS": "EMS", "TestVibro": "Vibro", "TestVisual": "Visual"}
    condition_label = {"box:spawned": "Spawned", "box:touched": "Touched"}

    combined_lines: list[tuple[str, mne.Evoked]] = []

    for ses in session_order:
        for cond in condition_order:
            cond_evs: list[mne.Evoked] = []
            for row in ok_df.itertuples(index=False):
                if str(row.subject) not in keep_subjects:
                    continue
                if str(row.session) != ses:
                    continue
                evoked_file = PER / str(row.evoked_file)
                if not evoked_file.exists():
                    continue
                for ev in mne.read_evokeds(evoked_file, verbose="ERROR"):
                    if ev.comment == cond:
                        cond_evs.append(ev)

            if not cond_evs:
                continue

            ga = mne.grand_average(harmonize_evokeds(cond_evs), interpolate_bads=False, drop_bads=False)
            title = f"{session_label[ses]} {condition_label[cond]}"
            ga.comment = title
            ga.apply_baseline((-0.1, 0.0))
            report.add_evokeds(
                ga,
                titles=title,
                tags=("evoked",),
                n_time_points=21,
            )
            psd_fig = make_psd_figure(ga, f"PSD for {title}")
            report.add_figure(fig=psd_fig, title=f"PSD for {title}", tags=("custom-figure",))
            plt.close(psd_fig)
            combined_lines.append((title, ga))

    if combined_lines:
        fig = make_combined_erp_figure(combined_lines, "Combined ERPs for All Subjects")
        report.add_figure(fig=fig, title="Combined ERP Comparison", tags=("custom-figure",))
        plt.close(fig)

    custom_image = ROOT / "milestone5" / "reports" / "paper_style_erp_match_mismatch.png"
    if custom_image.exists():
        report.add_html(
            "<p>Custom paper-style ERP figure generated from the same pipeline outputs.</p>",
            title="Custom ERP Figure",
        )
        custom_fig, custom_ax = plt.subplots(figsize=(13, 7.5))
        custom_ax.imshow(plt.imread(custom_image))
        custom_ax.axis("off")
        report.add_figure(fig=custom_fig, title="Paper-style ERP Match/Mismatch", tags=("custom-figure",))
        plt.close(custom_fig)

    report_path = OUT / "grand_average_report_cleaned_mne.html"
    report.save(report_path, overwrite=True, open_browser=False)
    patch_mne_report_slider_js(report_path)



def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    metric_files = sorted(PER.glob("*_metrics.json"))
    if not metric_files:
        raise RuntimeError("No per-recording metrics found.")

    rows = [json.loads(p.read_text(encoding="utf-8")) for p in metric_files]
    rec_df = pd.DataFrame(rows).sort_values(["subject", "session"])
    rec_df.to_csv(OUT / "recording_metrics.csv", index=False)

    ok_df = rec_df[rec_df["status"] == "ok"].copy()
    if ok_df.empty:
        raise RuntimeError("No successful recordings found for aggregation.")

    subj_df = (
        ok_df.groupby("subject", as_index=False)
        .agg(
            n_recordings=("recording", "count"),
            mean_drop_fraction=("drop_fraction", "mean"),
            mean_rms_uv=("rms_uv", "mean"),
            mean_ica_excluded=("n_ica_excluded", "mean"),
        )
        .sort_values("subject")
    )

    drop_th = robust_thresh(subj_df["mean_drop_fraction"])
    rms_th = robust_thresh(subj_df["mean_rms_uv"])
    subj_df["is_noisy_subject"] = (subj_df["mean_drop_fraction"] > drop_th) | (subj_df["mean_rms_uv"] > rms_th)
    noisy_subjects = subj_df.loc[subj_df["is_noisy_subject"], "subject"].astype(str).tolist()
    subj_df.to_csv(OUT / "subject_metrics.csv", index=False)

    evokeds_all = []
    subjects_all = []
    evokeds_by_session_condition: dict[tuple[str, str], list[mne.Evoked]] = {}
    for row in ok_df.itertuples(index=False):
        evoked_file = PER / str(row.evoked_file)
        if evoked_file.exists():
            conds = mne.read_evokeds(evoked_file, verbose="ERROR")
            for evoked in conds:
                key = (str(row.session), str(evoked.comment))
                evokeds_by_session_condition.setdefault(key, []).append(evoked)
            touch = next((ev for ev in conds if ev.comment == "box:touched"), None)
            if touch is None and conds:
                touch = conds[-1]
            if touch is None:
                continue
            evokeds_all.append(touch)
            subjects_all.append(str(row.subject))

    if not evokeds_all:
        raise RuntimeError("No evoked files found.")

    ga_all = mne.grand_average(harmonize_evokeds(evokeds_all), interpolate_bads=False, drop_bads=False)
    ga_all.save(OUT / "grand_average_all-ave.fif", overwrite=True)

    keep = [i for i, subj in enumerate(subjects_all) if subj not in noisy_subjects]
    if not keep:
        keep = list(range(len(evokeds_all)))
    evokeds_clean = [evokeds_all[i] for i in keep]
    ga_clean = mne.grand_average(harmonize_evokeds(evokeds_clean), interpolate_bads=False, drop_bads=False)
    ga_clean.save(OUT / "grand_average_clean-ave.fif", overwrite=True)

    all_png = OUT / "grand_average_all.png"
    clean_png = OUT / "grand_average_clean.png"

    # Keep the previous single-line outputs for compatibility.
    plot_multiline_grand_average(
        [("All subjects (box:touched)", ga_all)],
        "Grand Average ERP (All Processed Subjects)",
        all_png,
        channel="Cz",
    )
    plot_multiline_grand_average(
        [("Noisy-removed (box:touched)", ga_clean)],
        "Grand Average ERP (Noisy Subjects Removed)",
        clean_png,
        channel="Cz",
    )

    # Multi-condition plot, styled like the user's example.
    label_session = {"TestEMS": "EMS", "TestVibro": "Vibro", "TestVisual": "Visual", "Training": "Training"}
    label_cond = {"box:spawned": "Spawned", "box:touched": "Touched"}

    all_lines: list[tuple[str, mne.Evoked]] = []
    for (session, condition), evs in sorted(evokeds_by_session_condition.items()):
        ga = mne.grand_average(harmonize_evokeds(evs), interpolate_bads=False, drop_bads=False)
        all_lines.append((f"{label_session.get(session, session)} {label_cond.get(condition, condition)}", ga))

    clean_lines: list[tuple[str, mne.Evoked]] = []
    for (session, condition), evs in sorted(evokeds_by_session_condition.items()):
        filtered = [ev for ev, subj in zip(evs, [None] * len(evs))]
        # Build clean lines from recording table to preserve noisy-subject removal.
        keep_subjects = set(subj_df.loc[~subj_df["is_noisy_subject"], "subject"].astype(str).tolist())
        cond_evs = []
        for row in ok_df.itertuples(index=False):
            if str(row.subject) not in keep_subjects:
                continue
            evoked_file = PER / str(row.evoked_file)
            if not evoked_file.exists() or str(row.session) != session:
                continue
            for ev in mne.read_evokeds(evoked_file, verbose="ERROR"):
                if ev.comment == condition:
                    cond_evs.append(ev)
        if cond_evs:
            ga = mne.grand_average(harmonize_evokeds(cond_evs), interpolate_bads=False, drop_bads=False)
            clean_lines.append((f"{label_session.get(session, session)} {label_cond.get(condition, condition)}", ga))

    all_multiline_png = OUT / "grand_average_multiline_all.png"
    clean_multiline_png = OUT / "grand_average_multiline_clean.png"
    plot_multiline_grand_average(all_lines, "Grand Average ERPs", all_multiline_png, channel="Cz")
    plot_multiline_grand_average(clean_lines, "Grand Average ERPs (Noisy Subjects Removed)", clean_multiline_png, channel="Cz")

    combined_fig = make_combined_erp_figure(clean_lines, "Combined ERPs for All Subjects")
    combined_png = OUT / "combined_erp_comparison_clean.png"
    combined_fig.savefig(combined_png, dpi=160)
    plt.close(combined_fig)

    section_rows: list[dict[str, str]] = []
    for idx, (title, ga) in enumerate(clean_lines, start=1):
        safe = title.lower().replace(" ", "_")
        erp_png = OUT / f"{safe}_erp_clean.png"
        topo_png = OUT / f"{safe}_topomap_clean.png"
        psd_png = OUT / f"{safe}_psd_clean.png"

        plot_multiline_grand_average([(title, ga)], f"{title}", erp_png, channel="Cz")

        topo_fig = ga.plot_topomap(times=np.array([0.15, 0.25, 0.35]), show=False)
        topo_fig.savefig(topo_png, dpi=150)
        plt.close(topo_fig)

        psd_fig = make_psd_figure(ga, f"PSD for {title}")
        psd_fig.savefig(psd_png, dpi=150)
        plt.close(psd_fig)

        section_rows.append(
            {
                "title": title,
                "id_evoked": f"sec_{idx}_evoked",
                "id_psd": f"sec_{idx}_psd",
                "erp_png": erp_png.name,
                "topo_png": topo_png.name,
                "psd_png": psd_png.name,
            }
        )

    write_sectioned_clean_html(section_rows, OUT / "grand_average_report_cleaned_like.html")

    keep_subjects = set(subj_df.loc[~subj_df["is_noisy_subject"], "subject"].astype(str).tolist())
    write_mne_style_report(evokeds_by_session_condition, keep_subjects, ok_df)

    write_html(rec_df, subj_df, noisy_subjects, all_png, clean_png, all_multiline_png, clean_multiline_png)

    summary = {
        "n_recordings_attempted": int(len(rec_df)),
        "n_recordings_ok": int((rec_df["status"] == "ok").sum()),
        "n_subjects_ok": int(ok_df["subject"].nunique()),
        "noisy_subjects_removed": noisy_subjects,
        "final_report_html": "milestone5/final_pipeline/final_grand_average_report.html",
        "final_like_report_html": "milestone5/final_pipeline/grand_average_report_cleaned_like.html",
        "final_mne_style_report_html": "milestone5/final_pipeline/grand_average_report_cleaned_mne.html",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
