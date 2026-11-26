# Install and use Colab Pilot

## Requirements

- Python 3.9 or later
- The `colab` command-line tool (`google-colab-cli`) authenticated with OAuth 2.0 or Application Default Credentials
- Optional `rclone` configuration for headless Google Drive staging

## Client usage

- **Antigravity**: Install with `agy plugin install https://github.com/swack-tools/colab-pilot-ai-plugin` and invoke `/colab-pilot`, `/colab-train`, `/colab-shard-cpu`, or `/colab-watch`.
- **Claude Code**: Add `swack-tools/ai-plugin-marketplace` and install `colab-pilot@swack-tools-community`. Invoke `/colab-pilot:colab-pilot` or ask Claude to manage your Colab run.
- **Codex**: Add `https://github.com/swack-tools/ai-plugin-marketplace.git` and install `colab-pilot@swack-tools-community`. Invoke `$colab-pilot` or `$colab-train` in chat.

See the [installation and client setup guide](https://colab.ai.swacktech.com/install.html) for detailed walkthroughs and headless Google Drive configuration.
