from __future__ import annotations

import json
from pathlib import Path

import mne
import numpy as np


def save_condition_evokeds(evoked_path: Path, spawn_epochs: mne.Epochs, touch_epochs: mne.Epochs) -> tuple[mne.Evoked, mne.Evoked]:
    evoked_touch = touch_epochs.average()
    evoked_spawn = spawn_epochs.average()
    mne.write_evokeds(evoked_path, [evoked_spawn, evoked_touch], overwrite=True)
    return evoked_spawn, evoked_touch


def compute_recording_metrics(
    evoked_touch: mne.Evoked,
    before: int,
    after: int,
    spawn_epochs: mne.Epochs,
    touch_epochs: mne.Epochs,
    n_ica: int,
    bads: list[str],
    evoked_path: Path,
) -> dict[str, object]:
    picks = [ch for ch in ("Fz", "Cz", "Pz") if ch in evoked_touch.ch_names]
    window = evoked_touch.copy().pick(picks).crop(0.12, 0.30)
    return {
        "status": "ok",
        "n_epochs_before": before,
        "n_epochs_after": after,
        "n_spawn_epochs": int(len(spawn_epochs)),
        "n_touch_epochs": int(len(touch_epochs)),
        "drop_fraction": float((before - after) / before if before else 1.0),
        "n_ica_excluded": int(n_ica),
        "n_bad_channels": int(len(bads)),
        "mean_uv_120_300ms": float(window.data.mean() * 1e6),
        "rms_uv": float(np.sqrt(np.mean((evoked_touch.data * 1e6) ** 2))),
        "evoked_file": evoked_path.name,
    }


def write_metrics(metric_path: Path, metric: dict[str, object]) -> None:
    metric_path.write_text(json.dumps(metric, indent=2), encoding="utf-8")
