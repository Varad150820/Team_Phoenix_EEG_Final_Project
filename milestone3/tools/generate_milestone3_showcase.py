from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
from scipy.stats import kurtosis

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline_steps.step01_load import build_input_paths, load_raw_eeg
from pipeline_steps.step02_filter_and_resample import apply_average_reference, bandpass_filter, resample_raw
from pipeline_steps.step03_bad_channels import mark_and_interpolate_bads
from pipeline_steps.step05_events_and_trials import build_spawn_touch_events, load_trials
from pipeline_steps.step06_epoch_and_reject import drop_bad_epochs, make_epochs

OUT = ROOT / "milestone3" / "sub-1-outputs"
SUBJECT = "1"
SESSION = "TestVibro"
PREFERRED_CHANNELS = ("Oz", "Cz", "Pz", "Fz")


def fit_ica_with_object(raw: mne.io.BaseRaw) -> tuple[mne.preprocessing.ICA, mne.io.BaseRaw, int]:
    fit_tmax = min(90.0, float(raw.times[-1]))
    ica_raw = raw.copy().crop(tmin=0.0, tmax=fit_tmax)
    ica = mne.preprocessing.ICA(n_components=12, method="infomax", random_state=97, max_iter=100)
    ica.fit(ica_raw, picks="eeg", decim=30, verbose="ERROR")

    exclude: set[int] = set()
    try:
        muscle_idx, _ = ica.find_bads_muscle(ica_raw, threshold=0.8)
        exclude.update(muscle_idx)
    except Exception:
        pass

    try:
        src = ica.get_sources(ica_raw).get_data()
        kurts = kurtosis(src, axis=1, fisher=False, bias=False)
        k_med = np.median(kurts)
        k_mad = np.median(np.abs(kurts - k_med))
        scale = 1.4826 * k_mad if k_mad > 0 else np.std(kurts)
        scale = scale if scale > 0 else 1.0
        z = (kurts - k_med) / scale
        exclude.update(np.where(np.abs(z) > 5.0)[0].tolist())
    except Exception:
        pass

    ica.exclude = sorted(exclude)[:5]
    cleaned = raw.copy()
    ica.apply(cleaned)
    return ica, cleaned, len(ica.exclude)


def choose_channel(ch_names: list[str]) -> str:
    for ch in PREFERRED_CHANNELS:
        if ch in ch_names:
            return ch
    return ch_names[0]


def save_ica_topographies(ica: mne.preprocessing.ICA, raw: mne.io.BaseRaw, out_file: Path) -> None:
    components = ica.get_components()
    n_comp = min(components.shape[1], 12)
    n_cols = 4
    n_rows = int(np.ceil(n_comp / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 3.2 * n_rows))
    axes = np.atleast_1d(axes).ravel()
    info = raw.copy().pick("eeg").info

    for idx, ax in enumerate(axes):
        if idx < n_comp:
            mne.viz.plot_topomap(components[:, idx], info, axes=ax, show=False, contours=5)
            ax.set_title(f"ICA{idx:02d}", fontsize=10)
        else:
            ax.axis("off")

    fig.suptitle("Milestone 3 showcase: ICA topographies", fontsize=16)
    fig.tight_layout()
    fig.savefig(out_file, dpi=180)
    plt.close(fig)


def save_processed_vs_unprocessed(raw_before: mne.io.BaseRaw, raw_after: mne.io.BaseRaw, out_file: Path) -> str:
    channel = choose_channel(raw_after.ch_names)
    tmax = min(5.0, float(raw_after.times[-1]), float(raw_before.times[-1]))
    before = raw_before.copy().pick(channel).crop(0.0, tmax)
    after = raw_after.copy().pick(channel).crop(0.0, tmax)
    data_before, times = before.get_data(return_times=True)
    data_after = after.get_data()

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(times, data_before[0] * 1e6, color="0.35", linewidth=0.8, label="Unprocessed")
    ax.plot(times, data_after[0] * 1e6, color="tab:red", linewidth=1.2, label="Processed")
    ax.set_title(f"Processed vs unprocessed ({channel})")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (µV)")
    ax.legend(loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_file, dpi=180)
    plt.close(fig)
    return channel


def save_butterfly(evoked: mne.Evoked, out_file: Path) -> None:
    fig = evoked.plot(spatial_colors=False, gfp=True, show=False, time_unit="s")
    fig.axes[0].set_title("Milestone 3 showcase: butterfly ERP (box:touched)")
    fig.savefig(out_file, dpi=180)
    plt.close(fig)


def save_psd(raw_before: mne.io.BaseRaw, raw_after: mne.io.BaseRaw, out_file: Path) -> None:
    psd_before = raw_before.compute_psd(fmin=0.5, fmax=60.0, verbose="ERROR")
    before_data, freqs = psd_before.get_data(return_freqs=True)
    psd_after = raw_after.compute_psd(fmin=0.5, fmax=60.0, verbose="ERROR")
    after_data, _ = psd_after.get_data(return_freqs=True)

    before_db = 10 * np.log10(np.maximum(before_data, np.finfo(float).tiny))
    after_db = 10 * np.log10(np.maximum(after_data, np.finfo(float).tiny))

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(freqs, before_db.mean(axis=0), color="0.45", linewidth=1.2, label="Unprocessed")
    ax.fill_between(freqs, before_db.mean(axis=0) - before_db.std(axis=0), before_db.mean(axis=0) + before_db.std(axis=0), color="0.6", alpha=0.25)
    ax.plot(freqs, after_db.mean(axis=0), color="tab:red", linewidth=1.4, label="Processed")
    ax.fill_between(freqs, after_db.mean(axis=0) - after_db.std(axis=0), after_db.mean(axis=0) + after_db.std(axis=0), color="tab:red", alpha=0.18)
    ax.set_title("Milestone 3 showcase: source power spectrum / PSD")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (dB)")
    ax.legend(loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_file, dpi=180)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    vhdr, events_tsv = build_input_paths(SUBJECT, SESSION)

    raw_base = load_raw_eeg(vhdr)
    raw_unprocessed = raw_base.copy()
    resample_raw(raw_unprocessed)

    raw_processed = raw_base.copy()
    bandpass_filter(raw_processed)
    resample_raw(raw_processed)
    apply_average_reference(raw_processed)
    raw_processed, bads = mark_and_interpolate_bads(raw_processed)
    ica, raw_clean, n_ica = fit_ica_with_object(raw_processed)

    trials = load_trials(events_tsv)
    events = build_spawn_touch_events(raw_clean, trials)
    epochs = make_epochs(raw_clean, events)
    epochs, before_epochs, after_epochs = drop_bad_epochs(epochs)
    evoked_touch = epochs["box:touched"].average()

    ica_png = OUT / f"sub-{SUBJECT}_ses-{SESSION}_ica_topographies.png"
    compare_png = OUT / f"sub-{SUBJECT}_ses-{SESSION}_processed_vs_unprocessed.png"
    butterfly_png = OUT / f"sub-{SUBJECT}_ses-{SESSION}_butterfly.png"
    psd_png = OUT / f"sub-{SUBJECT}_ses-{SESSION}_psd.png"

    save_ica_topographies(ica, raw_processed, ica_png)
    compare_channel = save_processed_vs_unprocessed(raw_unprocessed, raw_clean, compare_png)
    save_butterfly(evoked_touch, butterfly_png)
    save_psd(raw_unprocessed, raw_clean, psd_png)

    summary = {
        "subject": SUBJECT,
        "session": SESSION,
        "compare_channel": compare_channel,
        "n_bad_channels": len(bads),
        "n_ica_excluded": n_ica,
        "n_epochs_before": before_epochs,
        "n_epochs_after": after_epochs,
        "files": {
            "ica_topographies": str(ica_png.relative_to(ROOT)).replace("\\", "/"),
            "processed_vs_unprocessed": str(compare_png.relative_to(ROOT)).replace("\\", "/"),
            "butterfly": str(butterfly_png.relative_to(ROOT)).replace("\\", "/"),
            "psd": str(psd_png.relative_to(ROOT)).replace("\\", "/"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
