from __future__ import annotations

import mne
from autoreject import get_rejection_threshold

from pipeline_steps.config import BASELINE, MIN_CONDITION_EPOCHS, TMAX, TMIN


def make_epochs(raw: mne.io.BaseRaw, events) -> mne.Epochs:
    return mne.Epochs(
        raw,
        events,
        event_id={"box:spawned": 1, "box:touched": 2},
        tmin=TMIN,
        tmax=TMAX,
        baseline=BASELINE,
        preload=True,
        detrend=1,
        event_repeated="drop",
        reject_by_annotation=False,
        verbose="ERROR",
    )


def drop_bad_epochs(epochs: mne.Epochs) -> tuple[mne.Epochs, int, int]:
    try:
        reject = get_rejection_threshold(epochs.copy().pick("eeg"), ch_types="eeg")
    except Exception:
        reject = {"eeg": 150e-6}

    before = len(epochs)
    epochs.drop_bad(reject=reject)
    after = len(epochs)
    return epochs, before, after


def has_minimum_condition_epochs(epochs: mne.Epochs, minimum: int = MIN_CONDITION_EPOCHS) -> bool:
    return len(epochs["box:touched"]) >= minimum and len(epochs["box:spawned"]) >= minimum
