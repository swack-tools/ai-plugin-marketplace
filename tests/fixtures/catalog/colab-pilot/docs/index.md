# Colab Pilot

Zero-waste Google Colab orchestration for Antigravity, Claude Code, and Codex. Stage large datasets to Google Drive at zero Compute Unit cost, provision BF16 GPU cascades, launch detached jobs resilient to WebSocket drops, and guard against orphaned sessions.

## Key features

- **GPU cascade provisioning**: Negotiate `A100-highmem`, `A100`, `G4`, and `L4` runtimes with automatic hardware probing.
- **Zero-cost Drive staging**: Stage large archives over `rclone` before renting a GPU VM.
- **WebSocket-proof detached jobs**: Run training with `nohup`, log normalization, and REST status polling.
- **Compute Unit leak guardrails**: Lifecycle hooks block interactive TTY hangs, large direct uploads, and unleased idle VMs.
