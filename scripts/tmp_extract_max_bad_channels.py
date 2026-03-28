from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline_steps.step01_load import build_input_paths, load_raw_eeg
from pipeline_steps.step02_filter_and_resample import bandpass_filter, resample_raw, apply_average_reference
from pipeline_steps.step03_bad_channels import robust_bad_channels

PER = ROOT / "milestone5" / "final_pipeline" / "per_recording"


def main() -> None:
    records: list[tuple[str, str, str]] = []
    for metric_path in sorted(PER.glob("*_metrics.json")):
        metric = json.loads(metric_path.read_text(encoding="utf-8"))
        if metric.get("status") == "ok" and int(metric.get("n_bad_channels", 0)) == 8:
            records.append((str(metric["subject"]), str(metric["session"]), str(metric["recording"])))

    print(f"recordings_with_8_bad_channels={len(records)}")
    for subject, session, recording in records:
        vhdr, _ = build_input_paths(subject, session)
        raw = load_raw_eeg(vhdr)
        bandpass_filter(raw)
        resample_raw(raw)
        apply_average_reference(raw)
        bads = robust_bad_channels(raw)
        print(f"{recording}: {len(bads)} -> {bads}")


if __name__ == "__main__":
    main()
