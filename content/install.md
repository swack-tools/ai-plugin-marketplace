## Install in the Claude apps

Open **Customize → Plugins → Add → Add marketplace → Add from GitHub**, then enter:

```text
swack-tools/ai-plugin-marketplace
```

Install **Vale**, **Trakt MCP**, or **Token Max**. Claude.ai uses the same account-level plugin manager when marketplace plugins are available to your plan/organization. Organization admins may need to approve plugins or connectors.

## Install with the Claude command-line tool

```sh
claude plugin marketplace add swack-tools/ai-plugin-marketplace
claude plugin install vale@swack-tools-community
claude plugin install trakt-mcp@swack-tools-community
claude plugin install token-max@swack-tools-community
```

Install only the plugins you want. Start a new session after installing. For a project installation, add `--scope project` to the plugin install command.

## Codex installation

Add the marketplace from a terminal:

```sh
codex plugin marketplace add https://github.com/swack-tools/ai-plugin-marketplace.git --sparse .agents/plugins
```

Then install from the Codex app's **Plugins** screen, or use the command-line tool:

```sh
codex plugin add vale@swack-tools-community
codex plugin add trakt-mcp@swack-tools-community
codex plugin add token-max@swack-tools-community
```

Restart or start a new Codex chat after installation. Codex Desktop and command-line tool use the same marketplace catalog.

## Upload a plugin archive

Open a plugin page and choose its verified release download for your client. A release becomes available here after both client archives pass verification.

- **Claude web or Desktop.** Open **Customize → Plugins** and use the custom plugin upload option. Upload the plugin's Claude ZIP. Plugins are available on paid Claude plans; see [Claude's plugin guide](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).
- **ChatGPT web.** Open `Admin → Plugins → Add → Upload plugin` and select the plugin's Codex ZIP. This option requires upload access or eligible workspace owner or administrator permissions and may not be available in every workspace. See [OpenAI's plugin instructions](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt-and-codex).

For Codex Desktop and command-line tool, use the marketplace installation steps in this guide. Workspace plugin availability and upload permissions depend on your account and organization settings.

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


## Import a marketplace in an eligible workspace

ChatGPT workspace administrators can import a GitHub marketplace when the workspace provides that option. Follow [OpenAI's marketplace import guide](https://help.openai.com/articles/20001504) for repository access and sync requirements. Availability and plugin runtime support depend on the workspace. A plugin marked **Desktop only** cannot run in the web app. Uploading a ZIP does not complete authorization for its included apps.
