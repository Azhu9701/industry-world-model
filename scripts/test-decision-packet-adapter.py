#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "examples" / "robotics" / "viabot-series-a-decision-packet.json"
EXPECTED = (
    ROOT
    / "contributions"
    / "robotics"
    / "2026-09-17-viabot-series-a"
    / "contribution.json"
)
CONVERTER = ROOT / "scripts" / "decision-packet-to-contribution.py"


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(CONVERTER), str(INPUT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    actual = json.loads(result.stdout)
    expected = json.loads(EXPECTED.read_text())
    if actual != expected:
        print(
            "Decision Packet adapter output drifted from the committed Viabot contribution.",
            file=sys.stderr,
        )
        return 1

    print("ok decision-packet adapter: Viabot Series A fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
