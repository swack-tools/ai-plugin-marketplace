---
name: colab-watch
description: >-
  Attach an active stall/error/VM-reachability watchdog and optional escalating
  multi-voice macOS TTS wakeup alarm to any running Colab job or log file. Use
  when the user invokes /colab-watch or wants unattended monitoring.
---

# Colab Watchdog & Escalating Wakeup Alarm

Monitor long-running Colab training or extraction jobs without polling in a loop or losing visibility on WebSocket drops.

## 1. Remote Detached Job Watchdog (Recommended)
For one-off status checks, call `colab_poll_job(session="<session-name>", job_id="<job-id>")` or ad-hoc `colab_poll_job(session="<session-name>", log_path="/content/out/train.log", process_pattern="train.py", artifacts_dir="/content/out")`. For unattended waiting, run `scripts/colab_watchdog.py` as a background `run_command` task so Antigravity wakes you up automatically when it exits:
```bash
python3 -B ~/.gemini/config/plugins/colab-pilot/scripts/colab_watchdog.py \
  --session <session-name> \
  --job-id <job-id> \
  --poll-sec 20 \
  --max-stall-sec 900 \
  --max-runtime-sec 3600 \
  --alarm-on-finish \
  --alarm-on-error
```

## 2. Local Runner Log Watchdog
If monitoring a local wrapper script log:
```bash
python3 -B ~/.gemini/config/plugins/colab-pilot/scripts/colab_watchdog.py \
  --log-file /path/to/runner.log \
  --session <session-name> \
  --done-marker "DONE:"
```

## 3. Controlling the Wakeup Alarm
- Use MCP tool `colab_wakeup_alarm(action="status" | "stop" | "start" | "self_test")`, or run:
  ```bash
  python3 -B ~/.gemini/config/plugins/colab-pilot/scripts/colab_wakeup_alarm.py --action stop
  ```
- Touching `/tmp/stop_wakeup_alarm` also silences the alarm immediately.
