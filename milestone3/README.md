# Milestone 3 — One Subject Output

## Goals to be reached
- Implemented a preprocessing pipeline ✅
- One single subject is analyzed ✅
- The table with the authors and your improved pipeline (highlight changes) ✅
- First results of one subject (ERP/TRF or similar) ✅

## Subject analyzed
- Subject: `sub-1`
- Session: `TestVibro`

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
Expected milestone 3 visual outputs are in this folder:
- one clean single-subject output set for presentation use
- topography figure
- processed vs unprocessed comparison
- butterfly view
- PSD view

## Presentation-style one-subject output
To match milestone 3 presentation needs, a clean output set was created for one recording:

- Selected recording: `sub-1` / `TestVibro`
- ICA topographies:
  - `milestone3/one-subject-output/sub-1_ses-TestVibro_ica_topographies.png`
- Processed vs unprocessed comparison:
  - `milestone3/one-subject-output/sub-1_ses-TestVibro_processed_vs_unprocessed.png`
- Butterfly plot:
  - `milestone3/one-subject-output/sub-1_ses-TestVibro_butterfly.png`
- PSD plot:
  - `milestone3/one-subject-output/sub-1_ses-TestVibro_psd.png`
- Summary metadata:
  - `milestone3/one-subject-output/summary.json`

## Authors vs improved pipeline (changes highlighted)

| Paper / context | Authors | Original processing focus | Improved pipeline in this repo (**highlighted changes**) |
|---|---|---|---|
| CHI 2019 prediction-error EEG study | Lukas Gehrke; Sezen Akman; Pedro Lopes; Albert Chen; Avinash Kumar Singh; Hsiang-Ting Chen; Chin-Teng Lin; Klaus Gramann | ERP mismatch detection in VR with visual / vibro / EMS feedback | **Explicit stage-wise modular pipeline**, **robust bad-channel interpolation**, **ICA artifact-removal stage**, **automated epoch rejection**, **single-command reproducibility path**, and **structured milestone artifacts** |

## Notes
- This milestone demonstrates the first reproducible single-subject ERP output.
- The pipeline is now split into root-level stage folders at `pipeline_steps/` for readability and reusability.
