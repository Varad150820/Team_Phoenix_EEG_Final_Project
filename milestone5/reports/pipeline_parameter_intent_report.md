# EEG Pipeline Parameter & Intent Report

## 1) Purpose of this report
This document explains:
- why the current preprocessing and aggregation parameters were selected,
- what intent each stage has,
- why filtering and cleaning are done in this order,
- and what output each stage produces.

It is based on the current implementation in:
- `pipeline_steps/config.py`
- `pipeline_steps/step01_load/` to `pipeline_steps/step07_evoked_and_metrics/`
- `scripts/process_one_recording.py`
- `scripts/run_all_recordings.py`
- `scripts/aggregate_final_pipeline.py`

---

## 2) Overall design intent
The pipeline is designed to be:
1. **Robust in batch mode** (many recordings, partial failures allowed).
2. **Conservative for EEG quality** (multiple artifact controls: filtering, bad channels, ICA, epoch rejection).
3. **Reproducible** (fixed random seed in ICA, deterministic session discovery order).
4. **Practical for milestone delivery** (per-recording outputs first, then group-level aggregation/reporting).

In short: the project first stabilizes each recording, then computes condition evokeds, then creates final all-subject summaries.

---

## 3) Why these parameters were selected

## 3.1 Global configuration (`pipeline_steps/config.py`)

- **`TMIN = -0.1`, `TMAX = 1.0`**
  - **Intent:** keep a short pre-stimulus baseline and a full post-stimulus response window.
  - **Why:** enough pre-time for baseline correction and enough post-time to capture main ERP morphology and late activity.

- **`BASELINE = (-0.1, 0.0)`**
  - **Intent:** normalize each epoch to pre-event voltage.
  - **Why:** reduces DC shifts and improves comparability across trials/subjects.

- **`TARGET_SFREQ = 250.0`**
  - **Intent:** reduce computational load while preserving ERP timing content.
  - **Why:** 250 Hz is a common practical ERP rate and is sufficient for the chosen analysis bandwidth.

- **`FILT_L_FREQ = 5.0`, `FILT_H_FREQ = 20.0`**
  - **Intent:** keep mid-band EEG activity and suppress slow drifts + high-frequency contamination.
  - **Why:** this narrower passband produces stable, cleaner waveforms for this milestone pipeline and reduces sensitivity to EMG/high-frequency noise.

- **`FILTER_METHOD = "iir"`, `FILTER_KWARGS = {"order": 4, "ftype": "butter"}`**
  - **Intent:** use efficient, smooth, low-order filtering suitable for batch processing.
  - **Why:** 4th-order Butterworth is a balanced choice (reasonable roll-off without excessive complexity).

- **`MIN_CONDITION_EPOCHS = 10`**
  - **Intent:** enforce minimum per-condition sample support before accepting a recording.
  - **Why:** protects against unstable evoked estimates from too few trials.

## 3.2 Bad-channel detection (`step03_bad_channels`)

- **Robust z-score threshold `|z| > 5.0` on channel standard deviation (MAD-based scaling).**
  - **Intent:** detect extreme outlier channels conservatively.
  - **Why:** robust statistics (median/MAD) reduce sensitivity to non-Gaussian distributions and avoid over-flagging.

## 3.3 ICA settings (`step04_ica_artifact_removal`)

- **`n_components = 12`, `method = "infomax"`, `random_state = 97`, `max_iter = 100`, `decim = 30`**
  - **Intent:** keep ICA fast and stable for many files while still removing major artifacts.
  - **Why:** limited components and decimation reduce runtime; fixed seed improves reproducibility.

- **Fit window: up to first 90 seconds (`fit_tmax = min(90, raw_end)`)**
  - **Intent:** avoid fitting ICA on entire long recordings.
  - **Why:** speeds up processing and usually captures enough artifact patterns for decomposition.

- **Artifact criteria:**
  - muscle components from `find_bads_muscle(..., threshold=0.8)`
  - plus robust kurtosis outliers (`|z| > 5.0`)
  - **cap exclusion to first 5 components**
  - **Intent:** remove strongest artifact sources conservatively, avoid over-cleaning.

## 3.4 Epoch rejection (`step06_epoch_and_reject`)

- **Primary threshold:** `autoreject.get_rejection_threshold(...)`
- **Fallback threshold:** `{'eeg': 150e-6}`
  - **Intent:** use data-driven rejection when possible, but never block pipeline if autoreject fails.
  - **Why:** keeps batch run resilient and prevents complete loss of outputs.

## 3.5 Group-level noisy-subject handling (`aggregate_final_pipeline.py`)

- **Robust threshold rule:** `median + k * robust_scale`, with **`k = 2.5`**
  - applied to `mean_drop_fraction` and `mean_rms_uv`
  - **Intent:** down-weight extreme outlier subjects before clean grand averages.
  - **Why:** robust rule is less affected by skewed distributions than plain mean/std cutoffs.

---

## 4) Flow of the pipeline, step-by-step

## Step 0: Recording discovery and orchestration
**File:** `scripts/run_all_recordings.py`

What it does:
- Finds all valid `sub-*/ses-*` recordings containing both `.vhdr` and `_events.tsv`.
- Calls `scripts/process_one_recording.py` for each recording.
- Calls `scripts/aggregate_final_pipeline.py` at the end.

Why this exists:
- ensures complete, repeatable all-recordings execution.

Output:
- all per-recording derivatives + final group report artifacts.

## Step 1: Load and standardize EEG input
**File:** `pipeline_steps/step01_load/__init__.py`

What it does:
- Reads BrainVision raw.
- Normalizes channel names.
- Applies `standard_1020` montage.
- Keeps EEG channels only.

Why:
- creates consistent channel space and valid sensor geometry for later interpolation/ICA.

Output:
- loaded MNE `Raw` ready for preprocessing.

## Step 2: Filter, resample, and re-reference
**File:** `pipeline_steps/step02_filter_and_resample/__init__.py`

What it does:
1. band-pass filter (5–20 Hz),
2. resample to 250 Hz,
3. average reference.

Why in this order:
- filtering early suppresses major noise before later algorithms,
- resampling then reduces data size and runtime,
- average reference stabilizes scalp-level comparability.

Output:
- denoised and normalized `Raw`.

## Step 3: Bad channel detection and interpolation
**File:** `pipeline_steps/step03_bad_channels/__init__.py`

What it does:
- identifies outlier channels via robust dispersion,
- interpolates flagged channels.

Why:
- protects ICA/epoching from localized sensor failures.

Output:
- cleaned `Raw` + list of interpolated channels.

## Step 4: ICA artifact removal
**File:** `pipeline_steps/step04_ica_artifact_removal/__init__.py`

What it does:
- fits ICA on a cropped/decimated copy,
- marks likely muscle and extreme kurtosis components,
- applies ICA to full raw.

Why:
- removes structured artifacts not fully handled by filtering/referencing.

Output:
- artifact-reduced `Raw` + count of excluded ICA components.

## Step 5: Event pairing and trial construction
**File:** `pipeline_steps/step05_events_and_trials/__init__.py`

What it does:
- reads events TSV,
- extracts `box:spawned` and `box:touched`,
- pairs them into trials and computes reaction time,
- converts onsets into MNE event arrays.

Why:
- transforms timestamp logs into analysis-ready trial structure.

Output:
- trial table + MNE-compatible event matrix.

## Step 6: Epoching and bad-epoch rejection
**File:** `pipeline_steps/step06_epoch_and_reject/__init__.py`

What it does:
- builds epochs for both event types,
- baseline-corrects,
- rejects noisy epochs,
- enforces minimum condition count.

Why:
- only sufficiently clean and adequately sampled recordings should contribute to evoked summaries.

Output:
- accepted `Epochs` + before/after epoch counts.

## Step 7: Evoked generation and recording-level metrics
**File:** `pipeline_steps/step07_evoked_and_metrics/__init__.py`

What it does:
- computes condition-average evokeds (`spawn`, `touch`),
- writes FIF file,
- computes QC and signal metrics.

Why:
- creates standardized per-recording products needed for group aggregation.

Output:
- `milestone5/final_pipeline/per_recording/sub-*_ses-*_evoked-ave.fif`
- `milestone5/final_pipeline/per_recording/sub-*_ses-*_metrics.json`

---

## 5) What filtering/cleaning achieves for outputs

- **Filtering (5–20 Hz):** improves waveform stability, reduces very slow drifts and high-frequency contamination in evokeds.
- **Resampling (250 Hz):** accelerates processing without losing relevant timing detail for this analysis range.
- **Average reference:** reduces dependence on any single reference electrode.
- **Bad-channel interpolation:** avoids single-channel artifacts distorting averages.
- **ICA exclusion:** removes dominant structured artifacts (muscle/outlier components).
- **Epoch rejection:** drops high-amplitude/noisy trials before averaging.

Together, these steps improve reliability of:
- condition evoked waveforms,
- per-recording QC metrics,
- final subject-level and grand-average summaries.

---

## 6) Recording-level failure handling (intent)
`scripts/process_one_recording.py` explicitly writes failure status instead of crashing global execution.

Possible statuses include:
- `failed_no_trials`
- `failed_no_mne_events`
- `failed_too_few_epochs`
- `failed_too_few_condition_epochs`
- `failed_exception: ...`

Why:
- preserves traceability and allows the batch pipeline to continue processing other recordings.

---

## 7) Group aggregation intent and outputs
**File:** `scripts/aggregate_final_pipeline.py`

What it does:
- reads all per-recording metrics,
- builds recording and subject tables,
- detects noisy subjects using robust thresholds,
- computes grand averages and figures,
- generates final HTML and MNE-style reports.

Why:
- produce interpretable final artifacts for milestone completion and reporting.

Key outputs:
- `milestone5/final_pipeline/recording_metrics.csv`
- `milestone5/final_pipeline/subject_metrics.csv`
- `milestone5/final_pipeline/summary.json`
- `milestone5/final_pipeline/grand_average_report_cleaned_mne.html`
- plus related PNG/FIF aggregate artifacts in `milestone5/final_pipeline/`

---

## 8) Practical summary
The selected parameters reflect a **stability-first milestone pipeline**:
- moderate band-pass,
- robust outlier handling,
- conservative ICA,
- epoch-count quality gates,
- robust subject-level outlier removal before final grand-average reporting.

This combination prioritizes reproducibility and end-to-end completion over highly customized per-subject tuning.