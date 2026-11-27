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
1. Call `colab_allocate_cascade(session="<name>", tiers=["A100-highmem", "A100", "G4", "L4"], require_bf16=True)` (or pass `prefer_gpus=["A100", "L4"]`, `high_mem=True`, and optional `per_tier_timeout_seconds`).
2. Respect the returned hardware probe:
   - Never run `torch.bfloat16` on `T4` (unsupported).
   - Set `DataLoader(num_workers=0)` whenever the dataset is preloaded in System RAM (prevents Linux fork OOM-killer).
   - On short runs, guard EMA decay with warmup: `decay = min(0.9995, (1 + step) / (10 + step))`.
3. Stage bundles onto the VM headlessly without FUSE staleness via `colab_smart_transfer(session="<name>", direction="drive_to_vm", mode="drive_pull", drive_source="gdrive_root:...", remote_path="/content/work", extract_archives=True)`, or mount Drive via `colab_mount_rclone(session="<name>", mode="streaming", forward_env_keys=["HF_TOKEN"])`. Use batch `files=[{"local_path": ..., "remote_path": ...}]` to sync local code files cleanly.

## Phase 3 — Detached Launch, Keepalive & Drive Checkpointing
1. Launch training via `colab_launch_detached(session="<name>", script_path="...", cwd="/content/work", log_path="/content/out/train.log", env={...}, auto_stop_vm=True, sync_dir="/content/out", drive_sync_dest="gdrive_root:Colab Notebooks/checkpoints/<run>", sync_include=["*.pt", "*.json"])` — `script_path` accepts both local scripts and already-staged `/content/...` scripts, and `kill_existing_pattern` / `clean_globs` enable zero-downtime warm-chaining between waves without deallocating the GPU.
2. Passing `sync_dir` + `drive_sync_dest` mirrors modified checkpoints and `job.log` incrementally to Drive on the 10-second heartbeat and on exit, while `colab_launch_detached` and `colab_keep_warm` automatically keep a `150s` runtime-proxy keepalive daemon running so Colab does not idle-reclaim the VM.
3. Monitor via `colab_poll_job` (supports `job_id`, background `drive_stage`/`drive_pull` transfers, or ad-hoc `session` + `log_path` / `process_pattern` / `artifacts_dir`), use `colab_exec` for bounded one-shot checks, or attach `/colab-watch` (`scripts/colab_watchdog.py --session <name> --job-id <id>`).
4. If a run hits CUDA OOM, call `colab_reset_vram(session="<name>")` to flush `sys.last_traceback` and IPython `Out` caches before retrying with a smaller micro-batch and larger `grad_accum`.

## Phase 4 — Verified Artifact Pull & Teardown
1. Pull trained weights, metrics JSON, and audit plots via `colab_smart_transfer(direction="download", remote_glob="/content/out/*.pt", local_path="weights/")` or single-file / batch `files` download.
2. Call `colab_stop_all(session="<name>")` and confirm `Active assignments: 0` (`0.00/hr`).
