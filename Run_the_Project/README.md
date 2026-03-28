# Terminal Run Guide

This folder explains how to run the EEG project from the terminal.

## Main command to run the full project
This is the main workflow for all subjects and all available sessions:

```powershell
D:/EEG_Lecture/ds003846/mne/Scripts/python.exe scripts/run_all_recordings.py
```

What it does:
1. reads raw BIDS data from `milestone4/raw_bids/`
2. processes each available subject/session recording
3. prints progress in the terminal
4. runs final aggregation automatically
5. creates the main final report

## Main final report
After the run finishes, open:
- `final output/grand_average_report_cleaned_mne.html`

That entry opens the primary report:
- `final output/grand_average_report_cleaned_mne.html`

## Optional commands
Re-run only final aggregation:

```powershell
D:/EEG_Lecture/ds003846/mne/Scripts/python.exe scripts/aggregate_final_pipeline.py
```

Run only one recording:

```powershell
D:/EEG_Lecture/ds003846/mne/Scripts/python.exe scripts/process_one_recording.py --subject 5 --session TestEMS
```
