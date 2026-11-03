# Exposure Scale

A guided self-check of a person's AI exposure. It asks one question at a time and builds a plan sorted by effort. Live at https://yaedin.github.io/exposure-scale/ (GitHub Pages, from `main`, root).

Goal of this stage: show that the idea works (adaptive onboarding, a quick sense of what's easy vs. hard), not full coverage.

**Scope: AI only.** General cybersecurity (passwords, sign-in, updates, credit freezes, data brokers) was cut in November 2026 after feedback that the start felt like standard privacy advice; it's in the git history. Don't add it back without asking. A step belongs here if AI creates or changes the risk.

## Ground rules
- **No build step.** Code and styles live in `index.html`, content in `content.json`, fonts in `fonts/`. The page fetches `content.json`, so preview it through a local server (`python3 -m http.server`), not by opening the file.
- **No outside requests.** No CDNs, analytics, embeds or Google Fonts. Answers stay in `localStorage` only. The footer's privacy note depends on this; update it if anything changes.
- **Lean copy.** Short, plain sentences. No defensive caveats, no filler. The owner explicitly dislikes verbose text.
- **Comfort first.** One question per screen, number-key shortcuts, instant feedback after each answer.
- Light and dark themes come from CSS tokens at the top of the style block. Use the tokens, not literal colors.

## How it works
- `content.json` holds all content: `intro` (the line above the first question), `areas`, `steps`, `questions`, and `linksChecked` (shown in the footer).
- `questions`: each option can `add` step ids to the plan or mark them `done`. `showIf` hides a question, `multi` makes it multi-select, `exclusive` marks an option like "None", `effects` add steps whenever the question is answered (optionally with `if`), `optionsFrom` reuses another question's selected options.
- `steps`: `minutes`, `impact` (1–3), `tier` (1 baseline, 2 recommended, 3 advanced), `checkMethod` (how a full build could check it: auto/link/self; not shown on the page), `withOthers` (needs family, a bank or a company; puts the step in "With others"), `links` (a step opens to show its links; steps without links or agent help don't open), `agentHelp` (one line on what the skill does for this step; shows an "Agent helps" tag and a link to the skill; `exposure.py validate` fails if the skill has no check, template or review for it). A link is `{label, url, showIf?}`.
- Conditions (`showIf`, `if`): `{question, equals | notEquals | minCount}`. `minCount` ignores exclusive options.
- Ids are stored in visitors' `localStorage` (key `exposure-scale-v2`). Renaming a question, option value or step id resets that answer for returning visitors.
- Plan lanes: `withOthers` → "With others"; otherwise ≤10 min "Minutes", longer "An evening". This replaced the old "Bigger" lane, which only held cyber steps. The three dots on each step are impact.
- Tabs: Check (onboarding), Plan (lanes + time to baseline), All steps (catalog with filters).
- Seven areas, in question order: people close to you, your voice and face, what you tell AI, AI acting for you, your work, decisions about you, if something happens. Ordered by how much is in the person's own hands: a family safe word is fully theirs, a company's automated decision is not. Questions follow that order; the plan sorts by effort.

## Agent skill
`skills/exposure-scale/` is a terminal version for coding agents (Agent Skills standard: `SKILL.md` plus `scripts/`, `assets/`, `references/`).
- `scripts/exposure.py` (Python 3.8+, standard library only) holds the logic: questions, plan, step help, read-only checks, state in `~/.exposure-scale/state.json`. The agent relays its output; `SKILL.md` sets the rules (never change settings, never handle secrets, follow the `Next:` line).
- `assets/content.json` is a copy of the site's `content.json`; `tools/check_content.py` fails if they differ. Terminal-only help per step (how-to text, phone instructions, templates) lives in `assets/assist.json`.
- `node tools/compare_logic.mjs` checks that the script and `index.html` give the same questions, plan and links on random answers. Run it after changing logic in either.
- `python3 skills/exposure-scale/scripts/exposure.py validate` checks `assist.json`, probes, templates and the `SKILL.md` header.
- `evals/exposure-scale.json` holds scenarios to rerun on several models after changing `SKILL.md`.
- `.claude/skills/`, `.agents/skills/` and `.gemini/skills/` hold relative symlinks to `skills/exposure-scale` so agents opened in this repo pick it up. Edit the real folder, not the links.
- Windows and Linux checks are untested.

## Checking content
`python3 tools/check_content.py` checks that every id in `content.json` resolves and that every link responds. Sites that block scripts (FTC consumer pages, Facebook, ICO) are listed for a browser check. Links behind a sign-in only prove the page exists; whether they land on the right setting needs a signed-in check. Update `linksChecked` after a full pass.

## Open issues
1. **Signed-in settings links unverified.** Reachable as of 2026-11-03, but not checked while signed in: Google connections, Gemini activity, Microsoft app access, YouTube Studio, GitHub Copilot, LinkedIn AI setting, X Grok setting, ChatGPT data controls and personalization, Claude privacy and preferences. The ICO page on automated decisions sits behind a bot check; its URL comes from a search result and hasn't been opened.
2. **No sources per step.** Plan: add a source URL to each step. A scheduled link check (GitHub Action running `tools/check_content.py`) is deferred.
3. **Impressum.** Deferred by the owner. Ask before adding anything.
4. Content is US/EU-focused; other regions only get generic steps.
5. **Candidates, not yet added** (narrowness first): AI meeting notetakers recording you, AI features reading your email (Gmail smart features), AI on by default in phones and laptops (Apple Intelligence, Windows Recall).

## Research behind the content (as of Oct–Nov 2026)
- LinkedIn trains on user data by default (setting: Data privacy → Data for Generative AI Improvement). GitHub opted personal Copilot accounts into training in April 2026.
- Voice cloning: a few seconds of audio can be enough; bank voice ID has been beaten by clones; family safe word + callback is the main defense. Voice "cloaking" tools (AntiFake) can be stripped by purification (De-AntiFake, ICML 2025), so they're not recommended.
- YouTube likeness detection is open to all creators 18+ since May 2026 (face only, flags but doesn't remove). Loti offers free likeness monitoring.
- US TAKE IT DOWN Act: platforms must remove nonconsensual intimate images, including deepfakes, within 48 hours; FTC enforcement since 19 May 2026 (TakeItDown.ftc.gov).
- Teens: 72% of US teens have used AI companions (Common Sense Media, Jul 2025). Character.AI ended open-ended chat for under-18s in Nov 2025; Meta paused teen access to AI characters in Jan 2026; ChatGPT parental controls link a parent and teen account but don't show chats; Snapchat lets parents disable My AI; Claude is 18+. California SB 243 (Jan 2026) and New York's companion law require disclosure and crisis protocols.
- Sycophancy: models back the user about 50% more often than people (Stanford, Science, Mar 2026). Instructions help but don't remove it; asking for the strongest case against works better than "don't flatter me" (UK AISI "Ask Don't Tell", 2026).
- AI training on creative work: DeviantArt and ArtStation opt out by default; X trains Grok on posts by default. Training crawlers (GPTBot, ClaudeBot, CCBot, Meta-ExternalAgent; Google-Extended and Applebot-Extended are control tokens) say they honour robots.txt; user-triggered fetchers often don't.
- Automated decisions: GDPR Art. 22 and 15(1)(h) give a right to human review and an explanation (CJEU C-203/22, Feb 2025). UK replaced Art. 22 with Arts. 22A–D from 5 Feb 2026. California ADMT rules apply from 1 Jan 2027; Colorado's replacement law from 1 Jan 2027. Whether EU AI Act Art. 86 applies from Aug 2026 or Dec 2027 is unclear.
- Face search engines (PimEyes, FaceCheck.ID) make faces searchable; PimEyes has an opt-out form.
- Prompt injection is the main risk of AI agents acting in logged-in sessions; no complete defense exists.
- Prior art: Consumer Reports Security Planner, EFF Surveillance Self-Defense. Neither covers AI exposure much; that's this tool's gap.
