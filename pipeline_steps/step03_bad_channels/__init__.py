from __future__ import annotations

import mne
import numpy as np


def robust_bad_channels(raw: mne.io.BaseRaw) -> list[str]:
    data = raw.get_data(picks="eeg")
    channel_std = data.std(axis=1)
    median = np.median(channel_std)
    mad = np.median(np.abs(channel_std - median))
    scale = 1.4826 * mad if mad > 0 else np.std(channel_std)
    scale = scale if scale > 0 else 1.0
    z = (channel_std - median) / scale
    return [raw.ch_names[i] for i in np.where(np.abs(z) > 5.0)[0]]


def mark_and_interpolate_bads(raw: mne.io.BaseRaw) -> tuple[mne.io.BaseRaw, list[str]]:
    bads = robust_bad_channels(raw)
    if bads:
        raw.info["bads"] = bads
        raw.interpolate_bads(reset_bads=True, verbose="ERROR")
    return raw, bads
