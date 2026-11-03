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

## Status
Prototype. Links last checked 3 November 2026; settings pages behind a sign-in still need a signed-in check.
