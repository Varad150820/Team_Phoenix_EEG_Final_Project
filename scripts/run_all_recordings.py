from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BIDS_ROOT = (ROOT / "milestone4" / "raw_bids") if (ROOT / "milestone4" / "raw_bids").exists() else ROOT
SESSIONS = ("TestVisual", "TestVibro", "TestEMS", "Training")


def discover() -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for sub_dir in sorted(BIDS_ROOT.glob("sub-*")):
        subject = sub_dir.name.replace("sub-", "")
        for session in SESSIONS:
            vhdr = sub_dir / f"ses-{session}" / "eeg" / f"sub-{subject}_ses-{session}_task-PredError_eeg.vhdr"
            events = sub_dir / f"ses-{session}" / "eeg" / f"sub-{subject}_ses-{session}_task-PredError_events.tsv"
            if vhdr.exists() and events.exists():
                items.append((subject, session))
    return items


def run() -> int:
    py = sys.executable
    tasks = discover()
    print(f"Found {len(tasks)} recordings")

    for idx, (subject, session) in enumerate(tasks, start=1):
        label = f"sub-{subject}_ses-{session}"
        print(f"[{idx}/{len(tasks)}] Processing {label}")
        cmd = [
            py,
            str(ROOT / "scripts" / "process_one_recording.py"),
            "--subject",
            subject,
            "--session",
            session,
        ]
        proc = subprocess.run(cmd, cwd=ROOT)
        if proc.returncode != 0:
            print(f"  WARNING: process failed with return code {proc.returncode}")

    print("Aggregating final report...")
    agg = subprocess.run([py, str(ROOT / "scripts" / "aggregate_final_pipeline.py")], cwd=ROOT)
    print(f"Aggregation return code: {agg.returncode}")
    return agg.returncode


if __name__ == "__main__":
    raise SystemExit(run())
