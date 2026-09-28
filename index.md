# Swack Tools AI Plugin Marketplace

Plugins from [swack-tools](https://github.com/swack-tools) for Claude and Codex. Add the marketplace once, then choose a plugin:

| Plugin | What it does | Source |
| --- | --- | --- |
| **Vale** | Checks technical prose with Vale and Google style rules. | [Repository](https://github.com/swack-tools/vale-ai-plugin) · [Guide](https://vale.swacktech.com/) |
| **Trakt MCP** | Connects your Trakt account for movie and TV discovery, watch history, calendars, lists, and requested library changes. | [Repository](https://github.com/swack-tools/trakt-ai-plugin) · [Guide](https://trakt.swacktech.com/) |
| **Token Max** | Produces an in-chat, report-only token usage audit. | [Repository](https://github.com/swack-tools/token-max-ai-plugin) · [Guide](https://token-max.swacktech.com/) |

These are community plugins installed from GitHub repositories. Review each repository and its permissions before installing. Trakt requires you to connect your own account.

## Claude Desktop and Claude.ai

Open **Customize → Plugins → Add → Add marketplace → Add from GitHub**, then enter:

```text
swack-tools/ai-plugin-marketplace
```

Install **Vale**, **Trakt MCP**, or **Token Max**. Claude.ai uses the same account-level plugin manager when marketplace plugins are available to your plan/organization. Organization admins may need to approve plugins or connectors.

## Claude Code CLI

```sh
claude plugin marketplace add swack-tools/ai-plugin-marketplace
claude plugin install vale@swack-tools-community
claude plugin install trakt-mcp@swack-tools-community
claude plugin install token-max@swack-tools-community
```

Install only the plugin(s) you want. Start a new session after installing. For project-only setup, add `--scope project` to the marketplace and install commands.

## Codex Desktop and Codex CLI

Add the marketplace from a terminal:

```sh
codex plugin marketplace add https://github.com/swack-tools/ai-plugin-marketplace.git --sparse .agents/plugins
```

Then install from the Codex app's **Plugins** screen, or use the CLI:

```sh
codex plugin add vale@swack-tools-community
codex plugin add trakt-mcp@swack-tools-community
codex plugin add token-max@swack-tools-community
```

Restart or start a new Codex chat after installation. Codex Desktop and CLI use the same marketplace catalog.

## ChatGPT web

ChatGPT web does not currently provide a user-facing flow to add community plugin marketplaces from GitHub. Install these in Codex Desktop or Codex CLI instead. ChatGPT does not automatically inherit local Codex plugins.

## Update or remove

Update from the client’s **Plugins** settings, or run:

```sh
# Claude Code
claude plugin marketplace update swack-tools-community
claude plugin update vale@swack-tools-community
claude plugin uninstall vale@swack-tools-community --scope user

# Codex
codex plugin marketplace upgrade swack-tools-community
codex plugin add vale@swack-tools-community
codex plugin remove vale@swack-tools-community
```

Replace `vale` with `trakt-mcp` or `token-max` as needed. Review each plugin repository for its permissions and connection requirements.

## Official format references

- [OpenAI/Codex plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Claude marketplace creation](https://code.claude.com/docs/en/plugins/create-marketplace)
