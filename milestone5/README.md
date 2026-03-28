# Milestone 5 — Consolidated Reporting & Reproducibility

## Purpose
This folder captures the project state after milestone 3 and 4 requirements are met, focusing on reproducibility and handoff.

## What is consolidated
- Root-level stage modules for preprocessing (`pipeline_steps/`)
- End-to-end final outputs in `milestone5/final_pipeline/`
- Interactive MNE-style report and clean grand-average exports

## Key final deliverables
- Main final report HTML (primary):
  - `milestone5/final_pipeline/grand_average_report_cleaned_mne.html`
- Secondary summary report HTML:
  - `milestone5/final_pipeline/final_grand_average_report.html`
- Clean-style report HTML:
  - `milestone5/final_pipeline/grand_average_report_cleaned_like.html`
- MNE-style interactive report HTML:
  - `milestone5/final_pipeline/grand_average_report_cleaned_mne.html`
- Final summary JSON:
  - `milestone5/final_pipeline/summary.json`

## Quick open from reports folder
- `milestone5/reports/main_final_report.html` (redirect entry to `grand_average_report_cleaned_mne.html`)

## Reproduction commands
From repository root:

1. Process all recordings + aggregate final report:
```powershell
D:/EEG_Lecture/ds003846/mne/Scripts/python.exe scripts/run_all_recordings.py
```

2. (Optional) Re-run only final aggregation:
```powershell
D:/EEG_Lecture/ds003846/mne/Scripts/python.exe scripts/aggregate_final_pipeline.py
```

## Acceptance checklist
- [x] Milestone 3 single-subject evidence available
- [x] Milestone 4 all-subject processing completed in final route
- [x] Outliers identified and handled
- [x] Stage-wise pipeline structure made readable from root view
