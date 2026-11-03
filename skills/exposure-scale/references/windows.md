# Windows notes

## What `detect` and `check` read
All read-only, no admin rights, no network.
- **Password manager:** folder names in Program Files, Program Files (x86) and AppData\Local\Programs.
- **Automatic updates:** `reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU /v NoAutoUpdate`. Only a policy that turns updates off is detected; without one, Windows updates automatically.
- **AI tools:** `%USERPROFILE%\.claude`, `.codex`, `.gemini`, `.cursor` config files. Names and permission modes only.
- **Screen lock:** no check. Ask the user.

## Opening settings
`exposure.py open ID` uses `ms-settings:windowsupdate` or `ms-settings:signinoptions`, or the step's web link.

## Limits
- Use `python` or `py` if `python3` isn't found.
- The checks here are less tested than on macOS. If one fails or looks wrong, ask the user and mark the step by hand.
