from __future__ import annotations

from pathlib import Path

import mne

from pipeline_steps.config import RAW_BIDS_ROOT


def build_input_paths(subject: str, session: str) -> tuple[Path, Path]:
    base = RAW_BIDS_ROOT / f"sub-{subject}" / f"ses-{session}" / "eeg"
    stem = f"sub-{subject}_ses-{session}_task-PredError"
    vhdr = base / f"{stem}_eeg.vhdr"
    events_tsv = base / f"{stem}_events.tsv"
    return vhdr, events_tsv


def load_raw_eeg(vhdr: Path) -> mne.io.BaseRaw:
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="ERROR")
    raw.rename_channels({ch: ch.replace("BrainVision RDA_", "") for ch in raw.ch_names})
    raw.set_montage("standard_1020", on_missing="ignore")
    raw.pick("eeg")
    return raw
