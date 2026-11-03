# Exposure Scale

A guided check of your cybersecurity and AI exposure. One question at a time, it builds a plan sorted by effort: minutes, an evening, or bigger.

**Live:** https://yaedin.github.io/exposure-scale/

## How it works
- One self-contained page: `index.html`. No build step, no dependencies.
- Answers are stored only in the visitor's browser (`localStorage`). Nothing is sent anywhere.
- Fonts are self-hosted in `fonts/` (SIL Open Font License, see the license files there).

## Content
Questions and steps live in two arrays near the top of the script in `index.html`: `QS` (questions) and `STEPS` (actions with time, impact and links). Each answer option can add steps to the plan or mark them as already in place.

## Status
Prototype. Several settings links were written from memory and still need checking.
