from __future__ import annotations

import mne

from pipeline_steps.config import FILTER_KWARGS, FILTER_METHOD, FILT_H_FREQ, FILT_L_FREQ, TARGET_SFREQ


def bandpass_filter(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    raw.filter(
        l_freq=FILT_L_FREQ,
        h_freq=FILT_H_FREQ,
        method=FILTER_METHOD,
        iir_params=FILTER_KWARGS,
        verbose="ERROR",
    )
    return raw


def resample_raw(raw: mne.io.BaseRaw, sfreq: float = TARGET_SFREQ) -> mne.io.BaseRaw:
    raw.resample(sfreq, npad="auto")
    return raw


def apply_average_reference(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    raw.set_eeg_reference("average", verbose="ERROR")
    return raw
