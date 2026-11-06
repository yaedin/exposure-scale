# Exposure Scale

Where do you stand with AI? Exposure Scale places you on five levels, from asking AI a question to letting it run your work: **Ask, Work with, Delegate, Automate, Hand over**. It shows how to reach the next level and the risks that come with each one. Then it builds a plan sorted by effort: minutes, an evening, or steps that need someone else. It also covers what other people's AI can do to you: voice-clone scams, deepfakes, training on what you post, and automated decisions.

**Live:** https://yaedin.github.io/exposure-scale/

## How it works
- One page, `index.html`, with content in `content.json`. No build step, no dependencies.
- To run it locally: `python3 -m http.server`, then open http://localhost:8000. Opening the file directly won't load the content.
- Answers are stored only in the visitor's browser (`localStorage`). Nothing is sent anywhere.
- Fonts are self-hosted in `fonts/` (SIL Open Font License, see the license files there).

## The scale
The levels follow how much you lead and how much the AI does. The same idea appears in research on AI autonomy levels ([Feng, McDonald & Zhang, 2025](https://arxiv.org/abs/2506.12469)) and in Microsoft's three phases, from AI as an assistant to agents running whole processes ([Work Trend Index 2025](https://www.microsoft.com/en-us/worklab/work-trend-index/2025-the-year-the-frontier-firm-is-born)). Anthropic's own staff span the same range, from interactive sessions to agents that triage email and act as a chief of staff ([2026](https://www.anthropic.com/research/employment-at-anthropic)).

Three questions place you: your own guess, what you did with AI last month, and what you do most weeks. Your level is what you do most weeks, not what you tried once. The gap between your guess and your answers is part of the result.

Risk grows with what you hand over ([Mitchell et al., 2025](https://arxiv.org/abs/2502.02649)). People also loosen oversight as they get used to agents: full auto-approve goes from about 20% to over 40% of sessions ([Anthropic, 2026](https://www.anthropic.com/research/measuring-agent-autonomy)). Each level adds its own risks, and the plan adds the guardrails for every level up to the furthest one you've tried. Which risk sits at which level is our reading of the evidence, not a measurement.

## Content
Everything lives in `content.json`: `levels` (what each looks like, its risk, its guardrail and level-up steps), `questions` and `steps` (actions with time, impact and links). Each answer option can add steps to the plan or mark them as already in place. Steps with `agentHelp` are marked "Agent helps" on the site and point to the skill below. `python3 tools/check_content.py` checks ids and links.

General cybersecurity (passwords, sign-in, updates, credit freezes, data brokers) was cut in November 2026 to keep the check on AI. It's in the git history before that date.

## In your own AI chat
The start screen has a "Use your AI" row: ChatGPT, Claude, Gemini and Copy prompt. Each one copies a prompt and opens the app (ChatGPT also gets it prefilled), so it's tap, then send or paste. The prompt is built in the page from `content.json` (`buildPrompt()` in `index.html`), so it never drifts from the site.

In the chat, the model asks only for your guess, then answers the rest from what it already knows about you (memory and past chats), with the evidence for each answer. It shows your level, risks and top steps, and ends with a few numbered questions for what it couldn't tell. Without memory it says so and asks those in one batch. `node tools/check_prompt.mjs` checks that the prompt covers every level, question, step and link and stays under its size limit; `--print` shows it.

## Agent skill
`skills/exposure-scale/` is an [Agent Skill](https://agentskills.io) with the same levels, questions and plan, plus help doing the steps: reviewing what your AI agents and plugins can reach, opening the right settings page, drafting a brief for handing work to AI, family messages and requests about automated decisions, and adding AI-crawler rules to your own website. It never changes settings for you. Needs Python 3.8+; answers stay in `~/.exposure-scale/`.

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
Prototype. Links last checked 4 November 2026; settings pages behind a sign-in still need a signed-in check.
