# macOS notes

## What `detect` and `check` read
All read-only, no admin rights, no network.
- **Password manager:** names of apps in `/Applications` and `~/Applications`.
- **Automatic updates:** `defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates` (1 = on).
- **Screen lock:** `sysadminctl -screenLock status`.
- **Lockdown Mode:** `defaults read .GlobalPreferences LDMGlobalEnabled` (1 = on, not set = off).
- **AI tools:** apps in `/Applications`; `~/.claude/settings.json`, `~/.claude.json`, `~/.codex/config.toml`, `~/.gemini/settings.json`, `~/.cursor/mcp.json`. Only tool names and permission modes are printed, never keys, tokens or environment values.

## Opening settings
`exposure.py open ID` uses `open` with a System Settings link (Software Update, Lock Screen, Privacy & Security) or the step's web link. The user changes the setting; run `check ID` afterwards where one exists.

## Limits
- Checks cover this Mac only. Phone steps (updates, screen lock, voicemail) need the user's word.
- FileVault, firewall and Gatekeeper aren't part of the plan. If the user asks, `fdesetup status` and `spctl --status` are read-only; changing them is for the user in System Settings.
