# EEG Project Pipeline Flow

This file organizes the repository by **pipeline stage** so the project is easier to read, maintain, and reproduce.

It does **not move files physically**. Instead, it gives a clear stage-by-stage map of the files already present in the repository.

---

## 1. Dataset and BIDS input

These are the raw inputs and dataset-level metadata.

### Main files
- `dataset_description.json` — dataset metadata
- `participants.tsv` — participant table
- `participants.json` — participant column descriptions
- `task-PredError_events.json` — event metadata
- `sub-*/ses-*/eeg/*.vhdr` — raw EEG recordings
- `sub-*/ses-*/eeg/*_events.tsv` — event timing files

---

## 2. Configuration / pipeline settings

These files define preprocessing parameters and derivative roots.

### Main files
- `WBS-Pipeline_config.py`

### Typical settings found here
- filter range
- resampling frequency
- sessions / subjects to run
- event handling rules
- derivative output paths

---

## 3. Raw-file repair / metadata fixing

These scripts are for fixing BrainVision header issues before or during preprocessing.

### Main files
- `milestone5/debug_logs/fix_dates.py`
- `milestone5/tools/fix_meas_dates.py`

### Use when
- measurement dates are invalid
- BrainVision files need repair before loading into MNE

---

## 4. Per-recording preprocessing

This is the most important stage if someone wants to understand the actual EEG cleaning pipeline.

### Main file
- `scripts/process_one_recording.py`
- `pipeline_steps/README.md`

### Stage files
- `pipeline_steps/step01_load/`
- `pipeline_steps/step02_filter_and_resample/`
- `pipeline_steps/step03_bad_channels/`
- `pipeline_steps/step04_ica_artifact_removal/`
- `pipeline_steps/step05_events_and_trials/`
- `pipeline_steps/step06_epoch_and_reject/`
- `pipeline_steps/step07_evoked_and_metrics/`
- `pipeline_steps/config.py`

### Pipeline operations inside this script
1. Load BrainVision EEG
2. Rename BrainVision channel labels
3. Set montage
4. Pick EEG channels only
5. Band-pass filter
6. Resample
7. Re-reference to average
8. Detect bad channels
9. Interpolate bad channels
10. Run ICA / artifact removal
11. Build events for `box:spawned` and `box:touched`
12. Epoch the cleaned data
13. Drop bad epochs with autoreject thresholding
14. Save evoked outputs and metrics

### Outputs produced
- `milestone5/final_pipeline/per_recording/*_metrics.json`
- `milestone5/final_pipeline/per_recording/*_evoked-ave.fif`

---

## 5. Artifact removal / ICA

These files contain or demonstrate ICA-based cleaning.

### Main files
- `scripts/process_one_recording.py`
- `milestone5/tools/full_milestone_pipeline.py`

### ICA-related logic includes
- ICA fitting with `mne.preprocessing.ICA`
- muscle component detection
- kurtosis-based component rejection
- conservative exclusion of artifact components

---

## 6. Event pairing and trial construction

These files define how `box:spawned` and `box:touched` are paired and turned into trials.

### Main files
- `scripts/process_one_recording.py`
- `milestone4/tools/run_milestone_pipeline.py`
- `milestone5/tools/full_milestone_pipeline.py`

### Purpose
- read event TSV files
- pair spawned and touched events
- compute reaction time (`rt`)
- convert onsets to MNE event arrays

---

## 7. Epoching and rejection

These files handle epoch extraction, baseline correction, and bad-epoch rejection.

### Main files
- `scripts/process_one_recording.py`
- `milestone4/tools/run_milestone_pipeline.py`
- `milestone5/tools/full_milestone_pipeline.py`

### Typical operations
- define `tmin`, `tmax`, and baseline
- create `mne.Epochs`
- use `autoreject.get_rejection_threshold`
- drop bad epochs
- compute subject/session evokeds

---

## 8. Batch execution / orchestration

These scripts run the pipeline across many recordings.

### Main files
- `scripts/run_all_recordings.py`
- `milestone5/tools/full_milestone_pipeline.py`
- `milestone4/tools/run_milestone_pipeline.py`

### Role
- discover available recordings
- loop over subject/session combinations
- call per-recording processing
- trigger final aggregation/report generation

---

## 9. Aggregation and final reporting

These files build the final project-level summaries and grand averages.

### Main files
- `scripts/aggregate_final_pipeline.py`
- `milestone4/tools/generate_milestone_outputs.py`

### Role
- collect per-recording metrics
- identify noisy subjects
- compute grand averages
- save combined ERP plots
- generate HTML reports
- generate MNE-style interactive report(s)

### Important output folders
- `milestone5/final_pipeline/`
- `milestone2/continuous_data_of_one_subject/`
- `analysis_outputs/milestone4/`
- `milestone5/artifacts/`

---

## 10. Milestone-specific scripts

These scripts are useful when the project is read as milestone-based work instead of final-pipeline work.

### Main files
- `milestone4/tools/run_milestone_pipeline.py`
- `milestone4/tools/generate_milestone_outputs.py`
- `milestone5/tools/full_milestone_pipeline.py`

### Recommended interpretation
- `milestone4/tools/run_milestone_pipeline.py` — milestone-oriented preprocessing and review
- `milestone4/tools/generate_milestone_outputs.py` — milestone summaries and audit-style outputs
- `milestone5/tools/full_milestone_pipeline.py` — all-in-one milestone workflow variant

---

## 11. Debugging and inspection helpers

These are support files for troubleshooting individual recordings or pipeline stages.

### Main files
- `milestone5/debug_tools/debug_one_recording.py`

### Use when
- inspecting one subject/session manually
- checking event alignment
- checking epoch counts or intermediate preprocessing behavior

---

## 12. Derived outputs / reproducibility products

These are the products someone would inspect or reuse after rerunning the pipeline.

### Main folders
- `milestone5/final_pipeline/`
- `milestone5/final_pipeline/per_recording/`
- `milestone2/continuous_data_of_one_subject/`
- `analysis_outputs/milestone4/`
- `milestone5/artifacts/`
- `milestone5/legacy_derivatives/DS003846/`

### Important examples
- grand averages
- per-recording metrics
- evoked FIF files
- summary JSON files
- HTML reports

---

## 13. Recommended reading order for a new person

If someone wants to recreate the project, read files in this order:

1. `README`
2. `PIPELINE_FLOW.md`
3. `WBS-Pipeline_config.py`
4. `scripts/process_one_recording.py`
5. `scripts/run_all_recordings.py`
6. `scripts/aggregate_final_pipeline.py`
7. `milestone4/tools/run_milestone_pipeline.py`
8. `milestone4/tools/generate_milestone_outputs.py`
9. `milestone5/final_pipeline/summary.json` (if present)

---

## 14. Recommended execution order for reproduction

### Final pipeline route
1. Fix problematic BrainVision dates if needed
  - `milestone5/tools/fix_meas_dates.py`
2. Process all recordings
   - `scripts/run_all_recordings.py`
3. Aggregate final outputs
   - `scripts/aggregate_final_pipeline.py`

### Milestone route
1. Run milestone pipeline
  - `milestone4/tools/run_milestone_pipeline.py`
2. Generate milestone reports
  - `milestone4/tools/generate_milestone_outputs.py`

---

## 15. Suggested logical folder grouping (virtual organization)

If you want to mentally group the repo, use this structure:

- **00_dataset/**
  - raw BIDS data, dataset metadata
- **01_config/**
  - `WBS-Pipeline_config.py`
- **02_fixups/**
  - date and header repair scripts
- **03_preprocessing/**
  - filtering, resampling, referencing, bad-channel handling
- **04_artifact_removal/**
  - ICA-related logic
- **05_epoching/**
  - event conversion, epoch creation, rejection
- **06_batch_run/**
  - orchestration scripts
- **07_aggregation_reports/**
  - grand averages, summaries, HTML reports
- **08_milestones/**
  - milestone-specific pipeline and outputs
- **09_debug/**
  - debug scripts and logs

This is the cleanest way to explain the project flow without breaking existing code paths.
