---
name: colab-pilot
description: >-
  Open the Colab Pilot live Compute Unit dashboard, audit active sessions and
  one-fifth AI Ultra monthly budget, manage headless rclone/ADC auth, and sweep
  orphaned VMs. Use when the user invokes /colab-pilot or asks about Colab CU
  usage, sessions, or auth.
---

# Colab Pilot Overview & Control

Use this skill to inspect live Google Colab Compute Unit (CU) usage, open the interactive **Colab Pilot** MCP App dashboard, or clean up orphaned VMs.

## Quick Actions

1. **Open Interactive Dashboard (`colab_dashboard`)**:
   - Call MCP tool `colab_dashboard` (optionally passing `ultra_monthly_cu` and `budget_fraction`, default `25000` and `0.20` for the one-fifth monthly guardrail).
   - Both the interactive UI and the text response list live CU balance, burn rate, per-session hardware, GPU/VRAM/RAM/CPU telemetry, leases, and active jobs, replacing manual `colab usage && colab sessions` calls.

2. **Bounded One-Shot Commands & Cleanup (`colab_exec`)**:
   - Call `colab_exec(session="<name>", command="..." | python_code="...", cwd="...", kill_pattern="...", clean_globs=[...], timeout_seconds=60)` for quick shell/Python inspection, `pip install`, or safe PID cleanup without TTY hangs or blocking behind busy Jupyter kernels.

2. **Sweep Orphaned VMs (`colab_stop_all`)**:
   - Call `colab_stop_all` (omit `session` to stop all active VMs, or pass `session` for one).
   - Verify `Active assignments: 0` and `Usage rate: 0.00/hr` in the response.

3. **Intentional Keep-Warm Lease (`colab_keep_warm`)**:
   - The `Stop` hook blocks ending a turn if an unleased Colab VM is still running without a detached job.
   - If you intentionally want to keep a VM warm for the user, call `colab_keep_warm(session="<name>", minutes=30, reason="...")`.

4. **Authentication Reference**:
   - **CLI auth (`oauth2` vs 4-scope `adc`)**: Verify with `colab sessions` or `colab whoami`. If `adc` 401s, re-mint with `openid`, `cloud-platform`, `userinfo.email`, and `colaboratory` scopes.
   - **Headless Drive access**: Never call `colab drivemount` (blocks on TTY). Use `colab_mount_rclone` instead.
