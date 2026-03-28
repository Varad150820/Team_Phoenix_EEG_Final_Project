from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BIDS_ROOT = ROOT / "milestone4" / "raw_bids"
RAW_BIDS_ROOT = DEFAULT_BIDS_ROOT if DEFAULT_BIDS_ROOT.exists() else ROOT
PER_RECORDING_OUT = ROOT / "milestone5" / "final_pipeline" / "per_recording"

TMIN = -0.1
TMAX = 1.0
BASELINE = (-0.1, 0.0)
TARGET_SFREQ = 250.0
MIN_CONDITION_EPOCHS = 10
FILT_L_FREQ = 5.0
FILT_H_FREQ = 20.0
FILTER_METHOD = "iir"
FILTER_KWARGS = {"order": 4, "ftype": "butter"}
