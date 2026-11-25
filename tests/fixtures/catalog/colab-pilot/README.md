# Colab Pilot Plugin

Zero-waste Google Colab orchestration for Antigravity, Claude Code, and Codex: GPU cascade provisioning, 0-CU Google Drive pre-staging, WebSocket-proof detached jobs, Compute Unit leak guardrails, parallel CPU sharding, and an interactive MCP App dashboard.

[Documentation](https://colab.ai.swacktech.com/) · [Install guide](https://colab.ai.swacktech.com/install.html) · [Workflows](https://colab.ai.swacktech.com/workflows.html) · [Technical reference](https://colab.ai.swacktech.com/reference.html) · [Plugin marketplace](https://ai.swacktech.com/plugins/colab-pilot/)

## Install

From a GitHub release archive:

```sh
gh release download v1.2.0 --repo swack-tools/colab-pilot-plugin --pattern 'colab-pilot-*.zip' --dir /tmp/colab-pilot-release
unzip -q /tmp/colab-pilot-release/colab-pilot-*.zip -d /tmp/colab-pilot-release/colab-pilot
agy plugin install /tmp/colab-pilot-release/colab-pilot
agy plugin enable colab-pilot
```

From Claude Code or Codex using the Swack Tools marketplace:

```sh
# Claude Code
/plugin marketplace add swack-tools/ai-plugin-marketplace
/plugin install colab-pilot@swack-tools-community

# Codex
codex plugin marketplace add https://github.com/swack-tools/ai-plugin-marketplace.git
codex plugin add colab-pilot@swack-tools-community
```

Or directly from a local clone:

```sh
agy plugin install ./plugins/colab-pilot
```

## Components

- **MCP Server (`pilot`)** — 10 tools (`colab_dashboard`, `colab_allocate_cascade`, `colab_mount_rclone`, `colab_smart_transfer`, `colab_launch_detached`, `colab_poll_job`, `colab_reset_vram`, `colab_keep_warm`, `colab_stop_all`, `colab_wakeup_alarm`) + `ui://colab-pilot/dashboard.html` MCP App UI.
- **Custom Agent (`colab-operator`)** — Autonomous Colab SRE executing the 6-phase zero-waste protocol.
- **Lifecycle Hooks (`hooks.json`)** — `SessionStart`, `PreToolUse` (blocks TTY hangs, invalid `--gpu` tiers, and `>30 MiB` direct `colab upload`), and `Stop` (prevents orphaned CU burn).
- **Skills / Slash Commands** — `/colab-pilot`, `/colab-train`, `/colab-shard-cpu`, `/colab-watch`.
- **Always-On Rules (`rules/AGENTS.md`)** — Enforces 0-CU staging, `num_workers=0` for RAM-cached datasets, BF16 checks, and `0.00/hr` teardown.

## Local CI & Devcontainer Replay

```sh
devcontainer build --workspace-folder . --platform linux/amd64 --image-name localhost/colab-pilot-actions:amd64
act --trust-project-actrc --container-architecture linux/amd64 workflow_dispatch -W .github/workflows/checks.yml
act --trust-project-actrc --container-architecture linux/amd64 workflow_dispatch -W .github/workflows/release.yml
```
