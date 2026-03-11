---
name: autonomous-flash
description: Flash all detected embedded boards sequentially with automatic probe, identify, build, flash, and verify stages. Supports --dry-run and --skip-verify.
disable-model-invocation: true
requires:
  bins:
    - pio  # PlatformIO CLI
install: "pip install platformio"
# Context cost: ~67 lines (~1.5K tokens). References: references/pipeline-stages.md
---

# Autonomous Flash

Full pipeline that discovers and flashes all connected embedded boards without manual intervention.

## Pipeline Stages

6 stages: Probe, Identify, Build, Flash (sequential), Verify, Report.
See `references/pipeline-stages.md` for detailed steps per stage.

## Flags

- `--dry-run`: Execute stages 1-2 only (probe and identify), report what WOULD be flashed
- `--skip-verify`: Skip stage 5 (serial verification)
- `--env <name>`: Flash only the specified environment, skip others

## Safety

- Never flash a board that cannot be positively identified
- Never flash two boards simultaneously
- Stop after 3 failed attempts per board — do not brute-force
- Check strapping pins (ESP32-S3: GPIO 0, 3, 45, 46) and warn if used in project

## Usage

```
/hardware:flash-all
/hardware:flash-all --dry-run
/hardware:flash-all --skip-verify
/hardware:flash-all --env client_board
```
