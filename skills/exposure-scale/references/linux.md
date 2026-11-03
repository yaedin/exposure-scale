# Linux notes

## What `detect` and `check` read
All read-only, no root, no network.
- **Password manager:** whether `bitwarden`, `keepassxc`, `1password`, `proton-pass` or `enpass` is on PATH. Flatpak and browser extensions aren't seen.
- **Automatic updates:** `/etc/apt/apt.conf.d/20auto-upgrades` (Debian, Ubuntu) or `systemctl is-enabled dnf-automatic*.timer` (Fedora).
- **Screen lock:** `gsettings get org.gnome.desktop.screensaver lock-enabled` (GNOME only).
- **AI tools:** `~/.claude`, `~/.codex`, `~/.gemini`, `~/.cursor` config files. Names and permission modes only.

## Opening settings
`exposure.py open ID` uses `xdg-open` for web links. There are no deep links into desktop settings; give the user the path from `step ID`.

## Limits
- Turning on automatic updates needs root. Show the user the command for their distribution; they run it.
- Without a desktop session, `open` can't work. Print the link instead.
