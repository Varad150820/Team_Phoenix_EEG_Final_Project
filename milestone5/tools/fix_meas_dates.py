"""Fix invalid measurement dates in raw EEG files (BrainVision .vhdr).

This script searches the BIDS dataset for BrainVision files (*.vhdr),
tries to read them with MNE, and if the raw.info['meas_date'] value
is outside the 32-bit unix timestamp range it sets the measurement
date to None and writes a fixed copy with suffix `_fixed`.

Usage:
    python milestone5/tools/fix_meas_dates.py --bids-root .

Note: this requires MNE to be installed in the active Python environment.
"""
from pathlib import Path
import argparse
import sys

try:
    import mne
except Exception as e:
    print("ERROR: could not import mne. Make sure you run this script inside a Python environment with MNE installed.")
    raise


def is_timestamp_out_of_range(ts_seconds: int) -> bool:
    # MNE currently checks meas_date seconds fit in 32-bit signed range
    return ts_seconds < -2147483648 or ts_seconds > 2147483647


def fix_brainvision_file(vhdr_path: Path) -> None:
    print(f"Processing: {vhdr_path}")
    try:
        # Do not preload data to avoid reading full recordings into memory here.
        raw = mne.io.read_raw_brainvision(str(vhdr_path), preload=False, verbose=False)
    except Exception as exc:
        print(f"  Skipped (read error): {exc}")
        return

    meas = raw.info.get("meas_date", None)
    # meas_date is often a tuple (secs, usec) or a float/int or None
    if meas is None:
        print("  meas_date is already None — nothing to do.")
        return

    # Normalize to seconds integer if possible
    try:
        if isinstance(meas, (tuple, list)):
            secs = int(meas[0])
        elif isinstance(meas, float):
            secs = int(meas)
        elif isinstance(meas, int):
            secs = meas
        else:
            # unknown type — be conservative and skip
            print(f"  Unknown meas_date type: {type(meas)} — skipping")
            return
    except Exception:
        print("  Could not interpret meas_date — skipping")
        return

    if is_timestamp_out_of_range(secs):
        print(f"  meas_date ({secs}) out of range -> setting to None and writing fixed copy")
        raw.set_meas_date(None)
        out_vhdr = vhdr_path.with_name(vhdr_path.stem + "_fixed" + vhdr_path.suffix)
        try:
            mne.export.export_raw(str(out_vhdr), raw, fmt="brainvision", overwrite=True)
            print(f"  Wrote fixed file: {out_vhdr}")
        except Exception as exc:
            print(f"  Failed to write fixed file: {exc}")
    else:
        print(f"  meas_date ({secs}) within allowed range — nothing to do.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bids-root", default=".", help="BIDS root folder containing sub-*/ses-*/eeg/*.vhdr files")
    args = parser.parse_args()

    bids_root = Path(args.bids_root).resolve()
    if not bids_root.exists():
        print(f"BIDS root not found: {bids_root}")
        sys.exit(1)

    vhdr_files = list(bids_root.rglob("*.vhdr"))
    if not vhdr_files:
        print("No BrainVision (.vhdr) files found under BIDS root.")
        return

    print(f"Found {len(vhdr_files)} .vhdr files. Scanning for invalid meas_date values...")
    for vhdr in sorted(vhdr_files):
        fix_brainvision_file(vhdr)


if __name__ == "__main__":
    main()
