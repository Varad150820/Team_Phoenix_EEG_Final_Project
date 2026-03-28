# Milestone 3 — First Subject Analyzed

## Goals to be reached
- Implemented a preprocessing pipeline ✅
- One single subject is analyzed ✅
- The table with the authors and your improved pipeline (highlight changes) ✅
- First results of one subject (ERP/TRF or similar) ✅

## Subject analyzed
- Subject: `sub-5`
- Session: `TestEMS`

## Pipeline used for this milestone (single-subject route)
1. Load BrainVision EEG (`.vhdr`)
2. Channel rename + montage assignment
3. Filtering (band-pass)
4. Resampling
5. Average reference
6. Bad-channel detection + interpolation
7. Event pairing (`box:spawned` / `box:touched`)
8. Epoching + baseline correction
9. Bad-epoch rejection
10. Evoked (ERP) computation and export

## First subject results (evidence)
Expected milestone 3 visual outputs in this folder:
- one continuous EEG preview image with event markers
- one ERP image for the first analyzed subject
- one clean single-subject output set for presentation use

- Continuous EEG with event markers:
  - `milestone2/continuous_data_of_one_subject/sub-5_ses-TestEMS_continuous_events.png`
- Subject ERP figure:
  - `milestone2/continuous_data_of_one_subject/sub-5_ses-TestEMS_erp.png`

## Presentation-style single-subject outputs
To match milestone 3 presentation needs, a clean output set was added for one strong recording:

- Selected recording: `sub-1` / `TestVibro`
- ICA topographies:
  - `milestone3/sub-1-outputs/sub-1_ses-TestVibro_ica_topographies.png`
- Processed vs unprocessed comparison:
  - `milestone3/sub-1-outputs/sub-1_ses-TestVibro_processed_vs_unprocessed.png`
- Butterfly plot:
  - `milestone3/sub-1-outputs/sub-1_ses-TestVibro_butterfly.png`
- PSD plot:
  - `milestone3/sub-1-outputs/sub-1_ses-TestVibro_psd.png`
- Summary metadata:
  - `milestone3/sub-1-outputs/summary.json`

## Authors vs improved pipeline (changes highlighted)

| Paper / context | Authors | Original processing focus | Improved pipeline in this repo (**highlighted changes**) |
|---|---|---|---|
| CHI 2019 prediction-error EEG study | Lukas Gehrke; Sezen Akman; Pedro Lopes; Albert Chen; Avinash Kumar Singh; Hsiang-Ting Chen; Chin-Teng Lin; Klaus Gramann | ERP mismatch detection in VR with visual / vibro / EMS feedback | **Explicit stage-wise modular pipeline**, **robust bad-channel interpolation**, **ICA artifact-removal stage**, **automated epoch rejection**, **single-command reproducibility path**, and **structured milestone artifacts** |

## Notes
- This milestone demonstrates the first reproducible single-subject ERP output.
- The pipeline is now split into root-level stage folders at `pipeline_steps/` for readability and reusability.
