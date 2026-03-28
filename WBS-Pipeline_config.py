"""Optional external pipeline config.

This file is a settings file, not the main executable entry point for the
current repository workflow.

Current main workflow:
- scripts/run_all_recordings.py
- scripts/aggregate_final_pipeline.py
"""

bids_root = "milestone4/raw_bids"
deriv_root = "milestone5/legacy_derivatives/DS003846"
subjects_dir = "milestone5/legacy_derivatives/freesurfer"

subjects = [
	"1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
	"11", "12", "13", "14", "15", "16", "17", "18", "19",
]
sessions = ["TestVisual", "TestVibro", "TestEMS", "Training"]
task = "PredError"
ch_types = ["eeg"]
interactive = False

# Preprocessing
l_freq = 5.0
h_freq = 20.0
raw_resample_sfreq = 250.0

conditions = ["box:touched"]
contrasts = []

event_repeated = "drop"

interpolate_bads_grand_average = False
run_source_estimation = False
