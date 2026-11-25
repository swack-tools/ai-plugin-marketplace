# Colab Pilot reference

## MCP tools

The bundled `pilot` MCP server exposes 10 tools. See the [complete technical reference](https://colab.ai.swacktech.com/reference.html) for input parameters, return schemas, and architecture details.

| Tool | Title | Description |
| :--- | :--- | :--- |
| `colab_dashboard` | Open Colab Pilot dashboard | Open the interactive dashboard showing Compute Unit balance, burn rate, active sessions, and detached jobs. |
| `colab_allocate_cascade` | Allocate GPU cascade | Try GPU tiers in priority order, verify BF16 support, and probe VRAM and system RAM. |
| `colab_mount_rclone` | Mount Google Drive with rclone | Configure rclone and mount Google Drive headlessly with workload-tuned VFS flags. |
| `colab_smart_transfer` | Transfer files safely | Transfer files using direct upload for small files and Drive staging or chunking for large archives. |
| `colab_launch_detached` | Launch detached job | Launch a Python script detached with nohup and 10-second GPU heartbeat status. |
| `colab_poll_job` | Poll detached job | Poll a detached Colab job over the REST Contents API without opening a WebSocket. |
| `colab_reset_vram` | Reset zombie VRAM | Clear tracebacks, IPython caches, and CUDA memory after a failed cell. |
| `colab_keep_warm` | Register keep-warm lease | Register or clear a timed keep-warm lease for an active Colab session. |
| `colab_stop_all` | Stop Colab sessions | Stop one named session or all active sessions and return verified Compute Unit usage. |
| `colab_wakeup_alarm` | Control wakeup alarm | Start, stop, inspect, or test the escalating macOS wakeup alarm. |

## Lifecycle hooks

- **SessionStart**: Summarizes active Colab sessions and Compute Unit burn rate when sessions exist.
- **PreToolUse**: Blocks interactive TTY `colab` commands, unrecognized `--gpu` tiers, and direct `colab upload` calls larger than 30 MiB.
- **Stop**: Prevents ending a turn while an unleased Colab VM remains allocated with no running detached job.
