# Swack Tools AI Plugin Marketplace

Plugins from [swack-tools](https://github.com/swack-tools) for Claude and Codex. Add the marketplace once, then choose a plugin:

| Plugin | What it does | Source |
| --- | --- | --- |
| **Vale** | Checks technical prose with Vale and Google style rules. | [Repository](https://github.com/swack-tools/vale-ai-plugin) · [Guide](https://vale.swacktech.com/) |
| **Trakt MCP** | Connects your Trakt account for movie and TV discovery, watch history, calendars, lists, and requested library changes. | [Repository](https://github.com/swack-tools/trakt-ai-plugin) · [Guide](https://trakt.swacktech.com/) |
| **Token Max** | Produces an in-chat, report-only token usage audit. | [Repository](https://github.com/swack-tools/token-max-ai-plugin) · [Guide](https://token-max.swacktech.com/) · [Claude ZIP](https://github.com/swack-tools/token-max-ai-plugin/releases/download/v1.0.0/token-max-claude.zip) · [Codex ZIP](https://github.com/swack-tools/token-max-ai-plugin/releases/download/v1.0.0/token-max-codex.zip) |

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

## Upload Token Max in Claude or ChatGPT

Download the archive for the app you are using from the Token Max links above. These direct links point to the `v1.0.0` GitHub Release; [later releases](https://github.com/swack-tools/token-max-ai-plugin/releases) may contain newer versions.

- **Claude web or Desktop:** Open **Customize → Plugins** and use the custom plugin upload option. Select `token-max-claude.zip`. Plugins are available on paid Claude plans; see [Claude's plugin guide](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).
- **ChatGPT web:** Open **Admin → Plugins → Add → Upload plugin** and select `token-max-codex.zip`. This option requires upload access or eligible workspace owner/admin permissions and may not be available in every workspace. See [OpenAI's plugin ZIP instructions](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt-and-codex).

For Codex Desktop and CLI, use the marketplace installation steps above. Workspace plugin availability and upload permissions depend on your account and organization settings.

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
