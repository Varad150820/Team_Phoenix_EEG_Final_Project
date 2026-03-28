from __future__ import annotations

import mne
import numpy as np
import pandas as pd


def load_trials(events_tsv) -> pd.DataFrame:
    events = pd.read_csv(events_tsv, sep="\t")
    spawned = events[events["value"] == "box:spawned"].reset_index(drop=True)
    touched = events[events["value"] == "box:touched"].reset_index(drop=True)
    n = min(len(spawned), len(touched))
    if n == 0:
        return pd.DataFrame()
    trials = pd.DataFrame(
        {
            "spawn_onset": spawned.loc[: n - 1, "onset"].to_numpy(float),
            "touch_onset": touched.loc[: n - 1, "onset"].to_numpy(float),
        }
    )
    trials["rt"] = trials["touch_onset"] - trials["spawn_onset"]
    return trials


def make_mne_events(raw: mne.io.BaseRaw, onsets: list[float], event_code: int) -> np.ndarray:
    samples = np.array(raw.time_as_index(onsets), dtype=int)
    if samples.size == 0:
        return np.empty((0, 3), dtype=int)
    _, first_idx = np.unique(samples, return_index=True)
    unique_samples = samples[np.sort(first_idx)]
    return np.column_stack(
        [
            unique_samples,
            np.zeros(len(unique_samples), dtype=int),
            np.full(len(unique_samples), event_code, dtype=int),
        ]
    )


def build_spawn_touch_events(raw: mne.io.BaseRaw, trials: pd.DataFrame) -> np.ndarray:
    events_touch = make_mne_events(raw, trials["touch_onset"].to_list(), event_code=2)
    events_spawn = make_mne_events(raw, trials["spawn_onset"].to_list(), event_code=1)
    events = np.vstack([events_spawn, events_touch])
    return events[np.argsort(events[:, 0])]
