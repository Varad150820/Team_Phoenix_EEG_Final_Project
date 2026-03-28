# Milestone 4 — All Subjects

## Goals to be reached
- Your pipeline worked for all subjects ✅
- Further outliers / problems identified ✅

## All-subject processing status (final pipeline route)
Based on `milestone5/final_pipeline/summary.json`:
- Recordings attempted: **60**
- Recordings processed successfully: **60**
- Subjects processed: **19**
- Noisy subjects identified/removed for clean grand-average: **sub-3**, **sub-15**

## Raw dataset location for this milestone
To keep repository flow readable, the full BIDS raw dataset is grouped under:
- `milestone4/raw_bids/`

This folder now contains:
- `sub-1` to `sub-19`
- `dataset_description.json`
- `participants.tsv`
- `participants.json`
- `task-PredError_events.json`

All main scripts were updated to auto-detect this location.

## Further outliers / problems identified
1. **Noisy-subject outliers**:
   - `sub-3`
   - `sub-15`
   - handled by clean grand-average exclusion logic in final aggregation.

2. **Earlier milestone route issue**:
   - Duplicate event sample timing in milestone scripts caused repeated failures
   - error seen in `analysis_outputs/milestone4/preprocessing_summary.csv`:
     - `Event time samples were not unique`
   - mitigation used in improved route:
     - explicit duplicate-event handling (`event_repeated='drop'` pattern)
     - robust per-recording processing + aggregation in final pipeline scripts.

## Evidence files
- `milestone5/final_pipeline/summary.json`
- `analysis_outputs/milestone4/pipeline_completion_table.csv`
- `analysis_outputs/milestone4/preprocessing_summary.csv`
- `analysis_outputs/milestone4/completion_overview.png`
- `analysis_outputs/milestone4/group_erp_by_session.png`

## Interpretation
- Milestone 4 goals are satisfied by the **final pipeline path** (all subjects processed).
- The milestone route outputs are still useful as a diagnostics trail showing what failed before stabilization.
