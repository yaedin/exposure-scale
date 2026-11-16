# Exposure Scale

Do your guardrails keep up with how you use AI? Exposure Scale works on five levels, from asking AI a question to letting it run your work: **Ask, Work with, Delegate, Automate, Hand over**. You pick your level, then answer a few questions about what you do at each level up to it. The result shows which levels are covered, which are open and what to fix first, and what the next level needs before you move up. An optional part covers what other people's AI can do to you: voice-clone scams, deepfakes, training on what you post, and automated decisions.

**Live:** https://yaedin.github.io/exposure-scale/

## How it works
- One page, `index.html`, with content in `content.json`. No build step, no dependencies.
- To run it locally: `python3 -m http.server`, then open http://localhost:8000. Opening the file directly won't load the content.
- Answers are stored only in the visitor's browser (`localStorage`). Nothing is sent anywhere.
- The font is self-hosted in `fonts/` (SIL Open Font License, see the license file there).

## The scale
The levels follow how much you lead and how much the AI does. The same idea appears in research on AI autonomy levels ([Feng, McDonald & Zhang, 2025](https://arxiv.org/abs/2506.12469)) and in Microsoft's three phases, from AI as an assistant to agents running whole processes ([Work Trend Index 2025](https://www.microsoft.com/en-us/worklab/work-trend-index/2025-the-year-the-frontier-firm-is-born)). Anthropic's own staff span the same range, from interactive sessions to agents that triage email and act as a chief of staff ([2026](https://www.anthropic.com/research/employment-at-anthropic)).

Two questions place you: what you do most weeks, and whether you went further last month. Your level is what you do most weeks. What you tried counts too, because its risks start the first time. The first version asked for a guess and then checked it; in tests most people guessed right, so this version takes the level as given and asks about the guardrails instead.

Risk grows with what you hand over ([Mitchell et al., 2025](https://arxiv.org/abs/2502.02649)). People also loosen oversight as they get used to agents: full auto-approve goes from about 20% to over 40% of sessions ([Anthropic, 2026](https://www.anthropic.com/research/measuring-agent-autonomy)). Each level has a few essential guardrails, and one question per guardrail asks what you actually do. A level counts as covered when its essential guardrails are in place, partly covered when some are, and open when none is. Which guardrail belongs to which level is a reading of the evidence, not a measurement.

Every number and incident on the page links to its source. The list is under "What this is based on" on the result screen and in `sources` in `content.json`.

## Content
Everything lives in `content.json`: `levels` (what each looks like, its risk, one sourced case, its guardrail and level-up steps), `questions`, `steps` (actions with time, impact and links) and `sources`. Each answer option can add steps to the plan or mark them as already in place. Steps with `agentHelp` point to the skill below. `python3 tools/check_content.py` checks ids, sources and links.

General cybersecurity (passwords, sign-in, updates, credit freezes, data brokers) was cut in November 2026 to keep the check on AI. It's in the git history before that date.

## In your own AI chat
The start screen has a "Use your AI" link. It opens a short panel that says in three lines what the prompt does, lets you read the full prompt, and offers ChatGPT, Claude, Gemini and Copy prompt. Each one copies the prompt and opens the app (ChatGPT also gets it prefilled). The prompt is built in the page from `content.json` (`buildPrompt()` in `index.html`), so it never drifts from the site. It starts with a short part meant for you to read, followed by the reference the AI scores with.

In the chat, the model asks only for your level, then answers the rest from what it already knows about you (memory and past chats), with the evidence for each answer. It shows which levels are covered, the step to do first and the next few, and ends with a few numbered questions for what it couldn't tell. Without memory it says so and asks those in one batch. `node tools/check_prompt.mjs` checks that the prompt covers every level, question, step and link and stays under its size limit; `--print` shows it.

## Agent skill
`skills/exposure-scale/` is an [Agent Skill](https://agentskills.io) with the same levels, questions and result, plus help doing the steps: reviewing what your AI agents and plugins can reach, opening the right settings page, drafting a brief for handing work to AI, family messages and requests about automated decisions, and adding AI-crawler rules to your own website. It never changes settings for you. Needs Python 3.8+; answers stay in `~/.exposure-scale/`.

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
Prototype. Links last checked 16 November 2026; settings pages behind a sign-in still need a signed-in check.
