---
name: colab-train
description: >-
  Zero-waste end-to-end GPU training runbook on Google Colab: local 0-CU gate,
  0-CU Drive pre-staging, BF16 GPU cascade allocation, detached WebSocket-proof
  launch, OOM recovery, and verified teardown. Use when the user invokes
  /colab-train or wants to train a model on Colab.
---

# Zero-Waste Colab GPU Training

Follow this 5-phase protocol to eliminate wasted Compute Units (CUs), OOM crashes, and WebSocket disconnects.

## Phase 0 — Local 0-CU Gate
1. Run local unit tests (`pytest`) and verify dataset archives/manifests locally **before** touching Colab (`0.00 CU`).
2. Never rent a GPU VM to run `ffmpeg` frame extraction; use `/colab-shard-cpu` first if extraction must run on Colab.

## Phase 1 — 0-CU Drive Pre-Staging
1. For archives or weights `>24 MiB`, call `colab_smart_transfer` with `direction="upload"`, `mode="drive_stage"`, and **no** `session` so `rclone` uploads to Drive at `0.00 CU`.
2. Never use direct `colab upload` for files `>30 MiB` (triggers Jupyter `/api/contents` `500` errors and bills GPU time).

## Phase 2 — BF16 GPU Cascade & Hardware Sizing
1. Call `colab_allocate_cascade(session="<name>", tiers=["A100-highmem", "A100", "G4", "L4"], require_bf16=True)`.
2. Respect the returned hardware probe:
   - Never run `torch.bfloat16` on `T4` (unsupported).
   - Set `DataLoader(num_workers=0)` whenever the dataset is preloaded in System RAM (prevents Linux fork OOM-killer).
   - On short runs, guard EMA decay with warmup: `decay = min(0.9995, (1 + step) / (10 + step))`.
3. Call `colab_mount_rclone(session="<name>", mode="streaming", forward_env_keys=["HF_TOKEN"])` to pull pre-staged archives onto `/content/` and forward secrets without Drive OAuth popups.

## Phase 3 — Detached Launch & Watchdog
1. Launch training via `colab_launch_detached(session="<name>", script_path="...", env={...})` — never hold a `colab exec` WebSocket open for `>5` minutes.
2. Monitor via `colab_poll_job` or `/colab-watch` (`scripts/colab_watchdog.py --session <name> --job-id <id>`).
3. If a run hits CUDA OOM, call `colab_reset_vram(session="<name>")` to clear `sys.last_traceback` and IPython `Out` caches before retrying with a smaller micro-batch and larger `grad_accum`.

## Phase 4 — Verified Artifact Pull & Teardown
1. Pull trained weights, metrics JSON, and audit plots via `colab_smart_transfer(direction="download", ...)` (or `rclone` from Drive).
2. Call `colab_stop_all(session="<name>")` and confirm `Active assignments: 0` (`0.00/hr`).
