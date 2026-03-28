from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline_steps.config import MIN_CONDITION_EPOCHS, PER_RECORDING_OUT
from pipeline_steps.step01_load import build_input_paths, load_raw_eeg
from pipeline_steps.step02_filter_and_resample import apply_average_reference, bandpass_filter, resample_raw
from pipeline_steps.step03_bad_channels import mark_and_interpolate_bads
from pipeline_steps.step04_ica_artifact_removal import fit_apply_ica
from pipeline_steps.step05_events_and_trials import build_spawn_touch_events, load_trials
from pipeline_steps.step06_epoch_and_reject import drop_bad_epochs, has_minimum_condition_epochs, make_epochs
from pipeline_steps.step07_evoked_and_metrics import compute_recording_metrics, save_condition_evokeds, write_metrics



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--session", required=True)
    args = parser.parse_args()

    subject = args.subject
    session = args.session
    label = f"sub-{subject}_ses-{session}"

    PER_RECORDING_OUT.mkdir(parents=True, exist_ok=True)
    metric_path = PER_RECORDING_OUT / f"{label}_metrics.json"
    evoked_path = PER_RECORDING_OUT / f"{label}_evoked-ave.fif"
    vhdr, events_tsv = build_input_paths(subject, session)

    metric: dict[str, object] = {
        "recording": label,
        "subject": subject,
        "session": session,
        "status": "failed",
    }

    try:
        raw = load_raw_eeg(vhdr)
        bandpass_filter(raw)
        resample_raw(raw)
        apply_average_reference(raw)
        raw, bads = mark_and_interpolate_bads(raw)
        raw_clean, n_ica = fit_apply_ica(raw)

        trials = load_trials(events_tsv)
        if trials.empty:
            metric["status"] = "failed_no_trials"
            write_metrics(metric_path, metric)
            return

        events = build_spawn_touch_events(raw_clean, trials)

        if len(events) == 0:
            metric["status"] = "failed_no_mne_events"
            write_metrics(metric_path, metric)
            return

        epochs = make_epochs(raw_clean, events)
        epochs, before, after = drop_bad_epochs(epochs)

        if after < MIN_CONDITION_EPOCHS:
            metric.update(
                {
                    "status": "failed_too_few_epochs",
                    "n_epochs_before": before,
                    "n_epochs_after": after,
                    "n_ica_excluded": n_ica,
                    "n_bad_channels": len(bads),
                }
            )
            write_metrics(metric_path, metric)
            return

        touch_epochs = epochs["box:touched"]
        spawn_epochs = epochs["box:spawned"]
        if not has_minimum_condition_epochs(epochs):
            metric.update(
                {
                    "status": "failed_too_few_condition_epochs",
                    "n_touch_epochs": int(len(touch_epochs)),
                    "n_spawn_epochs": int(len(spawn_epochs)),
                }
            )
            write_metrics(metric_path, metric)
            return

        _, evoked_touch = save_condition_evokeds(evoked_path, spawn_epochs, touch_epochs)
        metric.update(compute_recording_metrics(evoked_touch, before, after, spawn_epochs, touch_epochs, n_ica, bads, evoked_path))
    except Exception as exc:
        metric["status"] = f"failed_exception: {exc}"

    write_metrics(metric_path, metric)


if __name__ == "__main__":
    main()
