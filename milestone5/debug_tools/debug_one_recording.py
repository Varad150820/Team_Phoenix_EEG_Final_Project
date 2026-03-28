from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import mne
from autoreject import get_rejection_threshold

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / 'milestone4' / 'raw_bids'

print('1')
raw = mne.io.read_raw_brainvision(
    DATA_ROOT / 'sub-5' / 'ses-TestEMS' / 'eeg' / 'sub-5_ses-TestEMS_task-PredError_eeg.vhdr',
    preload=True,
    verbose='ERROR',
)
print('2')
raw.rename_channels({ch: ch.replace('BrainVision RDA_', '') for ch in raw.ch_names})
raw.set_montage('standard_1020', on_missing='ignore')
raw.pick('eeg')
print('3')
raw.filter(
    l_freq=0.1,
    h_freq=30.0,
    method='iir',
    iir_params={'order': 4, 'ftype': 'butter'},
    verbose='ERROR',
)
print('4')
raw.resample(250, verbose='ERROR')
print('5')
raw.set_eeg_reference('average', verbose='ERROR')
print('6')
df = pd.read_csv(DATA_ROOT / 'sub-5' / 'ses-TestEMS' / 'eeg' / 'sub-5_ses-TestEMS_task-PredError_events.tsv', sep='\t')
touch = df[df['value'] == 'box:touched'].copy()
print('7', touch.shape)
samples = np.array(raw.time_as_index(touch['onset'].to_list()), dtype=int)
print('8', samples.shape, samples[:5])
events = np.column_stack([samples, np.zeros(len(samples), dtype=int), np.ones(len(samples), dtype=int)])
print('9', events.shape)
epochs = mne.Epochs(
    raw,
    events,
    event_id={'touch': 1},
    tmin=-0.2,
    tmax=0.6,
    baseline=(-0.1, 0.0),
    preload=True,
    detrend=1,
    reject_by_annotation=False,
    verbose='ERROR',
)
print('10', len(epochs))
reject = get_rejection_threshold(epochs.copy().pick('eeg'), ch_types='eeg')
print('11', reject)
epochs.drop_bad(reject=reject)
print('12', len(epochs))
