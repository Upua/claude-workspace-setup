# Hardware & Embedded Reference

## Board Identification
- Always run `ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null` before flashing
- Cross-reference detected ports with the project's CLAUDE.md board table
- Never assume port mapping — USB enumeration order can change

## ESP32-S3 Strapping Pins
- GPIO 0, 3, 45, 46 are strapping pins — do not use for general I/O
- GPIO 19, 20 are USB D-/D+ — reserved for USB communication
- Always check pin assignments before wiring suggestions

## Flash Diagnosis
On flash failure, check in this order (do NOT just retry):
1. USB cable (try different cable/port)
2. `dmesg | tail -10` for USB errors
3. Hold BOOT button during flash
4. Check baud rate in platformio.ini

Max 3 flash retries, then STOP and present a diagnostic summary.

## Pi Deployment
- WiFi first: `192.168.2.174`, ethernet fallback: `192.168.100.10`
- Check `.claude-state.json` before re-deploying (avoids clobbering in-progress changes)
- Use `rsync` not `scp` (incremental, preserves permissions)
- Always run remote tests after deploy — never assume success
