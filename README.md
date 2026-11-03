# Exposure Scale

A guided check of your cybersecurity and AI exposure. One question at a time, it builds a plan sorted by effort: minutes, an evening, or bigger.

**Live:** https://yaedin.github.io/exposure-scale/

## How it works
- One page, `index.html`, with content in `content.json`. No build step, no dependencies.
- To run it locally: `python3 -m http.server`, then open http://localhost:8000. Opening the file directly won't load the content.
- Answers are stored only in the visitor's browser (`localStorage`). Nothing is sent anywhere.
- Fonts are self-hosted in `fonts/` (SIL Open Font License, see the license files there).

## Content
Questions and steps live in `content.json`: `questions` and `steps` (actions with time, impact and links). Each answer option can add steps to the plan or mark them as already in place. `python3 tools/check_content.py` checks ids and links.

## In your terminal: the agent skill
`skills/exposure-scale/` is an [Agent Skill](https://agentskills.io) with the same questions and plan, plus help doing the steps: read-only checks on your computer, opening the right settings page, drafting letters and family messages, and reviewing what your AI agents can reach. It never changes settings for you. Needs Python 3.8+; answers stay in `~/.exposure-scale/`.

Working inside this repo, it's already installed: `.claude/skills/`, `.agents/skills/` and `.gemini/skills/` link to it, so Claude Code, Codex and Gemini CLI find it automatically. On Windows, clone with `git clone -c core.symlinks=true` (needs Developer Mode) or copy the folder instead.

To use it anywhere, copy the folder to where your agent looks for skills:

| Agent | Folder |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` (turn skills on in settings first) |
| Cursor | `~/.cursor/skills/` |
| GitHub Copilot | `~/.copilot/skills/` |

For example: `cp -R skills/exposure-scale ~/.claude/skills/`. Then ask your agent for an Exposure Scale check.

## Status
Prototype. Links last checked 3 November 2026; settings pages behind a sign-in still need a signed-in check.
