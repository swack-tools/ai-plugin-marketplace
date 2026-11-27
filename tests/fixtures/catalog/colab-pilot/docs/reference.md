# Colab Pilot reference

## MCP tools

The bundled `pilot` MCP server exposes 11 tools. See the [complete technical reference](https://colab.ai.swacktech.com/reference.html) for input parameters, return schemas, and architecture details.

| Tool | Title | Description |
| :--- | :--- | :--- |
| `colab_dashboard` | Open Colab Pilot dashboard | Open the interactive dashboard showing Compute Unit balance, burn rate, active sessions, live GPU, VRAM, system RAM, disk, and CPU telemetry, and detached jobs. |
| `colab_allocate_cascade` | Allocate GPU cascade | Try GPU tiers in priority order (supporting `prefer_gpus`, `high_mem`, and configurable per-tier timeouts) within a 145-second budget, skip unsupported accelerators immediately, verify BF16 support, and probe VRAM and system RAM. |
| `colab_mount_rclone` | Mount Google Drive with rclone | Configure rclone and mount Google Drive headlessly with workload-tuned VFS flags. |
| `colab_smart_transfer` | Transfer files safely | Transfer single or batch files with auto-mkdir direct upload, async Drive staging, `remote_glob` checkpoint downloads, and headless `drive_pull` archive extraction. |
| `colab_launch_detached` | Launch detached job | Launch a local or remote Python script detached with nohup, `cwd` and custom log mirroring, warm-chain cleanup, 10-second GPU heartbeat status, incremental Drive checkpoint mirroring, and runtime keepalive. |
| `colab_poll_job` | Poll detached job | Poll a detached Colab job, background Drive transfer, or ad-hoc process, log path, and artifacts directory without opening a WebSocket. |
| `colab_exec` | Run bounded remote command | Execute a bounded one-shot shell command or Python snippet on a Colab VM (auto-routing over SSH when the kernel is busy) with optional safe process and glob cleanup. |
| `colab_reset_vram` | Reset zombie VRAM | Clear tracebacks, IPython caches, and CUDA memory after a failed cell. |
| `colab_keep_warm` | Register keep-warm lease | Register or clear a timed keep-warm lease for an active Colab session. |
| `colab_stop_all` | Stop Colab sessions | Stop one named session or all active sessions and return verified Compute Unit usage. |
| `colab_wakeup_alarm` | Control wakeup alarm | Start, stop, inspect, or test the escalating macOS wakeup alarm. |

## Lifecycle hooks

- **SessionStart**: Summarizes active Colab sessions and Compute Unit burn rate when sessions exist.
- **PreToolUse**: Blocks interactive TTY `colab` commands, unrecognized `--gpu` tiers, and direct `colab upload` calls larger than 30 MiB.
- **Stop**: Prevents ending a turn while an unleased Colab VM remains allocated with no running detached job.
