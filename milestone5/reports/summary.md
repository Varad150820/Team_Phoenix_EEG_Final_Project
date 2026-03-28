# EEG milestone output

## What was rerun

- Filtered continuous EEG at 0.1-30 Hz
- Re-referenced to average reference
- Automatically flagged extreme-variance channels and interpolated them
- Epoched around `box:touched` (-0.2 to 0.6 s) with baseline correction
- Automatically rejected bad epochs using `autoreject.get_rejection_threshold()`
- Added an extra robustness analysis based on early-vs-late touch RT proxy trials

## Processing overview

- Recordings processed: 0
- Subjects processed: 0
- Sessions represented: 
- Mean retained epochs per recording: 0.0

## Session-level ERP window summary (150-300 ms, mean across Fz/Cz/Pz)


## Files

- Milestone 3 continuous EEG plot: `milestone2/continuous_data_of_one_subject/sub-5_ses-TestEMS_continuous.png`
- Milestone 3 subject ERP: `milestone2/continuous_data_of_one_subject/sub-5_ses-TestEMS_erp.png`
- Milestone 4 session ERP grand averages: `analysis_outputs/milestone4/group_erp_by_session.png`
- Milestone 4 early-vs-late proxy comparison: `analysis_outputs/milestone4/group_proxy_early_vs_late.png`
- Per-recording summary table: `analysis_outputs/milestone4/preprocessing_summary.csv`
- Machine-readable summary: `analysis_outputs/milestone4/group_summary.json`