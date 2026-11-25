---
name: colab-shard-cpu
description: >-
  Fan out data extraction, mining, or preprocessing across N parallel CPU-only
  Google Colab VMs (~0.08 CU/hr each) with isolated session configs, random-seek
  rclone tuning, and guaranteed tar/manifest merge. Use when invoking
  /colab-shard-cpu or running parallel CPU Colab jobs.
---

# Parallel CPU Shard Runner

Never burn `1.94–10.05 CU/hr` on a GPU VM while `ffmpeg` or CPU preprocessing runs. Fan out across parallel CPU-only Colab VMs (`~0.08 CU/hr` per VM) using `scripts/colab_shard_runner.py`.

## Steps

1. **Prepare a shard-aware Python script**:
   - Read `SHARD_INDEX` (`0..N-1`) and `SHARD_TOTAL` (`N`) from `os.environ`.
   - If reading remote media from Google Drive via `rclone mount`, use **random-seek** flags (`--vfs-cache-mode off --vfs-read-chunk-size 8M --vfs-read-chunk-size-limit 256M --buffer-size 16M`) rather than `256M` full caching, which degrades `3x` under `ffmpeg -ss` seeks.
   - Write each shard's output archive (e.g. `/content/shard_out.tar` with `extract_manifest.json`).

2. **Run `colab_shard_runner.py`**:
   ```bash
   python3 -B ~/.gemini/config/plugins/colab-pilot/scripts/colab_shard_runner.py \
     --workers 5 \
     --prefix extract-shard \
     --script /path/to/worker.py \
     --rclone-conf ~/.config/rclone/colab_gdrive_root.conf \
     --remote-output /content/shard_out.tar \
     --out-dir /tmp/shards \
     --merge-tar /path/to/merged_pairs.tar
   ```
   - Each worker uses an isolated `--config /tmp/colab_shard_<run>_<i>.json` so concurrent `colab` calls never contend on `~/.config/colab-cli/sessions.json`.
   - A `try/finally` block guarantees every worker VM is stopped even on error, and prints the final `colab usage`.
