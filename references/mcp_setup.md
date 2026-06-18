# Adjust MCP Setup

Source: https://help.adjust.com/en/article/adjust-mcp

## Nature of the Adjust MCP

- **Early Access.** Exposes **aggregated data only**. All reasoning happens in the
  user's own AI environment — Adjust does not send data to an Adjust-hosted LLM.
- Underlying data goes through the Report Service API and can pull **Adjust KPI
  Service, SKAdNetwork, and Ad Spend** aggregates.
- **Units quirk:** ROAS / ROI display as percent in Datascape (e.g. `40%`) but the
  API returns **decimals** (e.g. `0.4`). Convert for display; note it in tooltips.

## Token

The user generates a token at:
`https://automate.adjust.com/ai-assistant-service/mcp_token`

## Server URL

`https://automate.adjust.com/ai-assistant-service/mcp/`

## Client config (Claude / Cursor)

The token lives in the **MCP client configuration**, not in a per-run prompt. So
the skill's "enter token" UI is a **first-run setup assistant**: detect whether
Adjust MCP tools are callable in the session; if not, generate this JSON with the
user's token filled in for them to paste into their client config.

```json
{
  "mcpServers": {
    "adjust-copilot": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://automate.adjust.com/ai-assistant-service/mcp/",
        "--header",
        "Authorization: Bearer << your token >>"
      ]
    }
  }
}
```

## Multi-account

Users with multiple accounts must add an `X-Account-ID` header to target a
specific account. Add a second `--header` arg:

```json
"--header", "X-Account-ID: << your account id >>"
```

## First-run assistant flow (skill behavior)

1. Detect whether the session can already call Adjust MCP tools (try to discover
   the tool list).
2. **If connected:** skip setup, go straight to the analysis configuration.
3. **If not connected:** guide the user to generate a token, then output the JSON
   above with their token (and `X-Account-ID` if multi-account) filled in for them
   to paste into their MCP client. Tell them to restart/reconnect the client.
4. **Security:** never persist the token; never write it into the dashboard or any
   log/file.

## Degradation

If SKAN metrics return empty (they may need Adjust TAM enablement), drop them,
continue the analysis, and note the degradation in the dashboard Appendix and
Data-Validation module.
