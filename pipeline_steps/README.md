# Root-Level Pipeline Step Modules

These modules split the per-recording EEG preprocessing into explicit stages and are located at repository root (`pipeline_steps/`) as requested.

## Stage folders
1. `step01_load/` — load BrainVision EEG and basic channel preparation
2. `step02_filter_and_resample/` — filtering, resampling, average reference
3. `step03_bad_channels/` — robust bad-channel detection and interpolation
4. `step04_ica_artifact_removal/` — ICA-based artifact removal
5. `step05_events_and_trials/` — event pairing and MNE event creation
6. `step06_epoch_and_reject/` — epoching and bad-epoch rejection
7. `step07_evoked_and_metrics/` — evoked saving and metric generation

## Shared settings
- `config.py`

## Main entry point
- `scripts/process_one_recording.py`

The entry-point script links to these root-level modules so execution remains unchanged while repository readability improves.

## Git final report location
- Combined final HTML outputs are collected at: `final output/`
- Main required report file: `final output/grand_average_report_cleaned_mne.html`
