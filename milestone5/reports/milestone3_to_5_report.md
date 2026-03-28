# Milestone 3-5 Output (Audit + Existing Derivatives)

## Core paper information

- **Paper**: Detecting Visuo-Haptic Mismatches in Virtual Reality using the Prediction Error Negativity of ERPs (CHI 2019)
- **General experiment idea**: participants touched virtual objects under visual-only, vibrotactile, and EMS conditions; in 25% of trials feedback was delivered prematurely to induce mismatch.
- **Main research question**: can EEG (ERP prediction-error negativity) detect visuo-haptic mismatch events in VR?
- **Main analysis type**: Event-Related Potentials (ERP)

## Extracted central hypotheses

- If visuo-haptic feedback is mismatched (premature feedback), early negative ERP components should be stronger than in matched trials.
- EEG ERPs can provide an objective signal of visuo-haptic conflict and complement subjective immersion questionnaires.

## Milestone 3 (first subject analyzed)

- Existing subject-level derivatives found for `sub-5` `ses-TestEMS` (`_proc-filt_raw.fif`, `_epo.fif`, `_proc-clean_epo.fif`, `_ave.fif`).
- Continuous EEG + event markers figure: `milestone2/continuous_data_of_one_subject/sub-5_ses-TestEMS_continuous_events.png`
- Subject ERP figure: `milestone2/continuous_data_of_one_subject/sub-5_ses-TestEMS_erp.png`

## Milestone 4 (all subjects check)

- Dataset has **19 subjects** and **60 raw recordings** (across sessions).
- Derivative reports exist for **4 recordings**.
- Evoked outputs exist for **1 recording(s)**.
- **Conclusion**: milestone 4 is **not completed for all subjects**.
- Completion table: `analysis_outputs/milestone4/pipeline_completion_table.csv`
- Completion overview plot: `analysis_outputs/milestone4/completion_overview.png`

## Pipeline step checklist (done vs not done)

- **data_loaded**: done (Raw BIDS files exist in sub-*/ses-*/eeg)
- **data_quality**: done (Cache folder _01_data_quality)
- **filtering**: done (Cache folder _04_frequency_filter; proc-filt_raw.fif exists for sub-5 TestEMS)
- **event_handling**: done (Config has event_repeated='drop' and events.tsv contains duplicate_event markers)
- **epoching**: done (Cache folder _07_make_epochs; epo.fif exists for sub-5 TestEMS)
- **auto_cleaning_ptp**: done (Cache folder _09_ptp_reject; proc-clean_epo.fif exists for sub-5 TestEMS)
- **ica**: not_done (No ICA step output found in derivatives/cache)
- **evoked_subject**: done (sub-5 TestEMS _ave.fif exists)
- **group_average**: done (sub-average TestEMS evoked file exists)
- **all_subjects_processed**: not_done (Derivatives only for sub-5 (+ sub-average), not for all available subjects)

## Milestone 5 outlook (next analyses)

- Finish the same preprocessing+ERP pipeline for all available subjects and sessions.
- Recreate a mismatch-vs-normal ERP contrast once full condition labels are restored in events metadata.
- Add one robustness extension analysis (time-frequency or decoding) after full replication is stable.

## Notes

- Event metadata dictionary lists fields such as `normal_or_conflict`, but current events.tsv files only contain compact markers; this blocks exact mismatch-vs-normal replication from raw events alone.
- Existing derivatives indicate a partial mne-bids-pipeline run focused on sub-5/TestEMS.