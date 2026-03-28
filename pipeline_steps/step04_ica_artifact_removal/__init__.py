from __future__ import annotations

import mne
import numpy as np
from scipy.stats import kurtosis


def fit_apply_ica(raw: mne.io.BaseRaw) -> tuple[mne.io.BaseRaw, int]:
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
    return cleaned, len(ica.exclude)
