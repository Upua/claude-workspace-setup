---
name: rpi-controller
description: Raspberry Pi 5 controller for Ladesaulen PoC - SSH operations, deployment, monitoring, camera, and dashboard control.
triggers:
  - rpi
  - raspberry
  - pi
  - deploy to pi
  - check pi
  - pi status
  - camera test
  - dashboard
requires:
  bins:
    - sshpass
    - ssh
    - ping
# Context cost: ~127 lines (~2.5K tokens)
---

# RPi Controller Skill

Controls the Raspberry Pi 5 used for the Ladesäulen (EV charging station) PoC.

## Hardware Context

| Component | Value |
|-----------|-------|
| **Model** | Raspberry Pi 5 (8GB) |
| **OS** | Debian Bookworm |
| **IP** | 192.168.100.10 (static, direct ethernet) |
| **User** | pi / ladesaule2026 |
| **Project Path** | ~/ladesaule-poc |
| **Camera** | Pi Camera v3 (IMX708) |

## Network Setup

The Pi connects via **direct ethernet** (no router):
- Pi: `192.168.100.10`
- Laptop: `192.168.100.1/24` on `enp0s31f6`

**IMPORTANT**: Laptop IP gets lost on cable disconnect. Run `/rpi:connect` to restore.

## Available Commands

| Command | Purpose |
|---------|---------|
| `/rpi:connect` | Set up network, verify Pi reachable |
| `/rpi:status` | Full system status (CPU, RAM, disk, services) |
| `/rpi:deploy [files]` | Deploy code changes to Pi |
| `/rpi:dashboard [start\|stop\|restart]` | Control dashboard service |
| `/rpi:monitor [start\|stop\|restart]` | Control PoC monitor |
| `/rpi:logs [dashboard\|monitor\|audit]` | Tail log files |
| `/rpi:camera [test\|status]` | Camera operations |
| `/rpi:test` | Run pytest on Pi |
| `/rpi:hardware` | Full hardware diagnostics (temp, fan, voltage) |
| `/rpi:research "issue"` | Search for Pi-specific solutions |
| `/rpi:explore "question"` | Multi-agent research team |

## Connection Pattern

All commands use this SSH pattern:
```bash
sshpass -p 'ladesaule2026' ssh -o StrictHostKeyChecking=no pi@192.168.100.10 "command"
```

For file transfer:
```bash
sshpass -p 'ladesaule2026' scp file.py pi@192.168.100.10:~/ladesaule-poc/
```

## State Tracking

A state file on the Pi tracks deployment info:
```
~/ladesaule-poc/.claude-state.json
```

This allows new Claude sessions to immediately understand:
- What was last deployed
- Current service status
- Recent errors

## Quick Reference

**Check if Pi is reachable:**
```bash
ping -c 1 192.168.100.10
```

**SSH to Pi:**
```bash
sshpass -p 'ladesaule2026' ssh pi@192.168.100.10
```

**Deploy a file:**
```bash
sshpass -p 'ladesaule2026' scp path/to/file.py pi@192.168.100.10:~/ladesaule-poc/
```

**Restart dashboard:**
```bash
sshpass -p 'ladesaule2026' ssh pi@192.168.100.10 "pkill -f uvicorn; cd ~/ladesaule-poc && source .venv/bin/activate && DASHBOARD_USER=norman DASHBOARD_PASS=ladesaule2026 nohup python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8080 > ~/dashboard.log 2>&1 &"
```

## Troubleshooting

### Pi not reachable
1. Check ethernet cable connected
2. Run `/rpi:connect` to set laptop IP
3. If still failing, Pi may need power cycle

### Dashboard not starting
1. Check logs: `/rpi:logs dashboard`
2. Verify venv: `source .venv/bin/activate && python -c "import fastapi"`
3. Check port in use: `ss -tlnp | grep 8080`

### Camera not working
1. Check connection: `libcamera-hello --list-cameras`
2. Check permissions: user must be in `video` group
3. Test capture: `libcamera-still -o test.jpg`

## Services

The PoC has two main services (manual start, no systemd):

| Service | Port | Start Command |
|---------|------|---------------|
| Dashboard | 8080 | `uvicorn dashboard.app:app --port 8080` |
| Monitor | - | `python poc_monitor.py` |

Both require the venv activated first.
