import mne
from pathlib import Path

# Path to the raw BrainVision file
vhdr_file = "sub-5/ses-TestEMS/eeg/sub-5_ses-TestEMS_task-PredError_eeg.vhdr"

print(f"Reading {vhdr_file}...")
raw = mne.io.read_raw_brainvision(vhdr_file, preload=True)

# Fix the corrupted date
print("Fixing measurement date...")
raw.set_meas_date(None)  # Remove invalid date

# Save back as BrainVision format (overwrites original)
print("Saving fixed file...")
mne.export.export_raw(
    vhdr_file.replace('.vhdr', '_fixed.vhdr'),
    raw,
    fmt='brainvision',
    overwrite=True
)

print("✅ Done! Created fixed file: sub-5_ses-TestEMS_task-PredError_eeg_fixed.vhdr")
