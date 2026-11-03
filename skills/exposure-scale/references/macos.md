# macOS notes

## What `detect` and `check` read
All read-only, no admin rights, no network.
- **AI tools:** apps in `/Applications`; `~/.claude/settings.json`, `~/.claude.json`, `~/.codex/config.toml`, `~/.gemini/settings.json`, `~/.cursor/mcp.json`. Only tool names and permission modes are printed, never keys, tokens or environment values.

## Opening pages
`exposure.py open ID` uses `open` with the step's web link. The user changes the setting; run `check ID` afterwards where one exists.

## Limits
- Checks cover this Mac only. Phone and web-account steps need the user's word.
