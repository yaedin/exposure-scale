# Exposure Scale

A guided self-check of where a person stands with AI. It places them on five levels (Ask, Work with, Delegate, Automate, Hand over) and shows how to reach the next level and the risks of each. It asks one question at a time and builds a plan sorted by effort. Live at https://yaedin.github.io/exposure-scale/ (GitHub Pages, from `main`, root).

Goal of this stage: show that the idea works (people learn where they stand, adaptive onboarding, a quick sense of what's easy vs. hard), not full coverage.

**Why levels (Nov 2026).** The owner's insight: people don't learn about themselves, and that's what makes them act. The scale answers three things: (a) where you are, (b) how to get to the next level, (c) the risks of each level and how to handle them. Level-up steps and guardrails sit in the same plan.

**Scope: AI only.** General cybersecurity (passwords, sign-in, updates, credit freezes, data brokers) was cut in November 2026 after feedback that the start felt like standard privacy advice; it's in the git history. Don't add it back without asking. A step belongs here if AI creates or changes the risk.

## Ground rules
- **No build step.** Code and styles live in `index.html`, content in `content.json`, fonts in `fonts/`. The page fetches `content.json`, so preview it through a local server (`python3 -m http.server`), not by opening the file.
- **No outside requests.** No CDNs, analytics, embeds or Google Fonts. Answers stay in `localStorage` only. The footer's privacy note depends on this; update it if anything changes.
- **Lean copy.** Short, plain sentences. No defensive caveats, no filler. The owner explicitly dislikes verbose text.
- **Comfort first.** One question per screen, number-key shortcuts, instant feedback after each answer.
- Light and dark themes come from CSS tokens at the top of the style block. Use the tokens, not literal colors.

## How it works
- `content.json` holds all content: `intro` (the line above the first question), `levels`, `around` (risks at every level), `sources` (shown on the Level tab), `parts` (Your level, Your risks, Around you), `steps`, `questions`, and `linksChecked` (shown in the footer).
- `levels`: `n`, `name`, `line` (what it looks like), `up` (how to get there), `risk` (what it adds), `guards` (steps added for every level up to the reach), `climb` (steps added when this is the next level).
- Placement: questions with `place` (`self` = the person's guess, `tried` = last month, `habit` = most weeks) have options with a `level`. Level = habit (or tried until that's answered), shown as at least 1. Reach = the higher of tried and habit; risks and risk questions use the reach. Logic is `placement()` in both `index.html` and `exposure.py`.
- `questions`: each option can `add` step ids to the plan or mark them `done`. `showIf` hides a question, `multi` makes it multi-select, `exclusive` marks an option like "None", `effects` add steps whenever the question is answered (optionally with `if`), `optionsFrom` reuses another question's selected options (its own `options` follow them). Every question has a `part`.
- `steps`: `level` (0 = around you, 1–5 = where the risk starts or, with `up`, the level the step gets you to), `up` (a level-up step; tagged "Level up"), `minutes`, `impact` (1–3), `tier` (1 baseline, 2 recommended, 3 advanced), `checkMethod` (how a full build could check it: auto/link/self; not shown on the page), `withOthers` (needs family, a bank or a company; puts the step in "With others"), `links` (a step opens to show its links; steps without links or agent help don't open), `agentHelp` (one line on what the skill does for this step; shows an "Agent helps" tag and a link to the skill; `exposure.py validate` fails if the skill has no check, template or review for it). A link is `{label, url, showIf?}`.
- Conditions (`showIf`, `if`): `{question, equals | notEquals | minCount}` or `{minLevel}` (reach at least n). `minCount` ignores exclusive options. Placement questions can't use `minLevel`.
- Ids are stored in visitors' `localStorage` (key `exposure-scale-v2`). Renaming a question, option value or step id resets that answer for returning visitors.
- Plan lanes: `withOthers` → "With others"; otherwise ≤10 min "Minutes", longer "An evening". This replaced the old "Bigger" lane, which only held cyber steps. The three dots on each step are impact.
- Tabs: Check (onboarding; the level shows as soon as the three placement questions are answered), Level (ladder, next level with its steps, risks up to the reach, sources), Plan (lanes + time to baseline), All steps (catalog grouped by level, Around you last).
- Question order: your level first (the payoff comes early), then risks gated by level, then around you (voice clones, teens, likeness, posts, decisions). Up steps are tier 2, so "time to baseline" stays about guardrails.

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
5. **The level mapping is a reading, not a measurement.** No study measures risk per level for individuals. A future version could weight placement (e.g. frequency per behavior) or validate it against usage data.
6. **Candidates, not yet added** (narrowness first): AI meeting notetakers recording you, AI features reading your email (Gmail smart features), AI on by default in phones and laptops (Apple Intelligence, Windows Recall).

## Research behind the content (as of Oct–Nov 2026)
- Levels: Feng, McDonald & Zhang, "Levels of Autonomy for AI Agents" (2025): operator, collaborator, consultant, approver, observer. DeepMind "Levels of AGI" autonomy levels (tool → agent). Microsoft Work Trend Index 2025: three phases (assistant; agents as digital colleagues at human direction; agents run whole processes, humans check in). Dan Shapiro's five levels for coding (Jan 2026) are a social signal for the same ladder.
- Anthropic internal use ("How employment is changing at Anthropic", Oct 2026): agents passed human work hours in March 2026; standing agent instructions went from a few hundred to 8,500 in a year; an EA built an assistant agent and moved to chief-of-staff work; 20% describe shifting from doing work to managing Claudes.
- Risk rises with autonomy: Mitchell et al. (Hugging Face, 2025). Anthropic "Measuring AI agent autonomy in practice" (Feb 2026): full auto-approve rises from ~20% (new) to 40%+ (750+ sessions) of Claude Code sessions; 0.8% of API agent actions look irreversible.
- Level 2: two in three office workers have used AI they believed their employer prohibits (PagerDuty 2026). Higher trust in AI goes with less critical thinking (Lee et al., CHI 2025).
- Level 3: about 2,000 court cases with AI-invented citations (Charlotin database, Aug 2026: 1,981). METR (2025): developers felt 20% faster while measured 19% slower; self-assessment is unreliable, which is why placement asks about behavior.
- Level 4: the lethal trifecta (Willison, 2025): private data + untrusted content + a way to send. Scheduled tasks exist in Claude Cowork, ChatGPT and Gemini.
- Level 5: Replit's agent deleted a production database during a code freeze (Jul 2025). OpenClaw (Jan–Feb 2026): tens of thousands of exposed instances and hundreds of malicious skills on ClawHub.
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
