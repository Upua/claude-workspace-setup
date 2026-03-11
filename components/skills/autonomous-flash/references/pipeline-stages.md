# Autonomous Flash - Pipeline Stage Details

## 1. Probe

- Scan `/dev/ttyUSB*` and `/dev/ttyACM*` for connected devices
- Parse `dmesg` for USB serial adapter identification (CH340, CP2102, FTDI, etc.)
- Build device map: port -> chip type -> USB path

## 2. Identify

- Read project `CLAUDE.md` and `platformio.ini` for board definitions
- Cross-reference detected ports with known board table
- Map each device to a PlatformIO environment
- If a device cannot be identified: skip it with a warning

## 3. Build

- For each identified board: `pio run -e <env>`
- Build all environments before flashing any (fail-fast on compile errors)
- Report build results: environment, binary size, warnings

## 4. Flash (Sequential)

- Flash boards ONE AT A TIME to avoid USB contention
- `pio run -e <env> -t upload`
- On failure: retry up to 3 times with increasing delay
- Between retries: check `dmesg` for USB disconnect/reconnect
- Suggest BOOT button hold for ESP32-S3 if repeated failures

## 5. Verify (unless --skip-verify)

- Open serial monitor for 10 seconds per board
- `pio device monitor -e <env> --filter time`
- Check for boot messages, firmware version strings, error-free startup
- Record first 20 lines of output

## 6. Report

- Summary table: board name, env, port, build, flash, verify status
- Total time elapsed
- Any warnings or skipped boards

## Safety

- Never flash a board that cannot be positively identified
- Never flash two boards simultaneously
- Stop after 3 failed attempts per board -- do not brute-force
- Check strapping pins (ESP32-S3: GPIO 0, 3, 45, 46) and warn if used in project
