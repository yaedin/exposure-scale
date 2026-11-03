# Exposure Scale

A guided self-check of a person's cybersecurity and AI exposure. It asks one question at a time and builds a plan sorted by effort. Live at https://yaedin.github.io/exposure-scale/ (GitHub Pages, from `main`, root).

Goal of this stage: show that the idea works (adaptive onboarding, a quick sense of what's easy vs. hard), not full coverage.

## Ground rules
- **No build step.** Code and styles live in `index.html`, content in `content.json`, fonts in `fonts/`. The page fetches `content.json`, so preview it through a local server (`python3 -m http.server`), not by opening the file.
- **No outside requests.** No CDNs, analytics, embeds or Google Fonts. Answers stay in `localStorage` only. The footer's privacy note depends on this; update it if anything changes.
- **Lean copy.** Short, plain sentences. No defensive caveats, no filler. The owner explicitly dislikes verbose text.
- **Comfort first.** One question per screen, number-key shortcuts, instant feedback after each answer.
- Light and dark themes come from CSS tokens at the top of the style block. Use the tokens, not literal colors.

## How it works
- `content.json` holds all content: `areas`, `emailProviders`, `steps`, `questions`, and `linksChecked` (shown in the footer).
- `questions`: each option can `add` step ids to the plan or mark them `done`. `showIf` hides a question, `multi` makes it multi-select, `exclusive` marks an option like "None", `effects` add steps whenever the question is answered (optionally with `if`), `optionsFrom` reuses another question's selected options. `{mainEmail}` in `text` becomes the main email provider's name.
- `steps`: `minutes`, `impact` (1–3), `tier` (1 baseline, 2 recommended, 3 advanced), `kind` (`cyber`, `ai`), `checkMethod` (how a full build could check it: auto/link/self; not shown on the page), `effortLabel` (replaces the time and forces "Bigger"), `links` (a step opens to show its links; steps without links don't open). A link is `{label, url, showIf?}` or `{emailProvider: "security" | "connectedApps"}` for the main email provider's page.
- Conditions (`showIf`, `if`): `{question, equals | notEquals | minCount}`. `minCount` ignores exclusive options.
- Ids are stored in visitors' `localStorage` (key `exposure-scale-v2`). Renaming a question, option value or step id resets that answer for returning visitors.
- Effort lanes come from `minutes`: ≤10 "Minutes", ≤60 "An evening", else "Bigger" (or when `effortLabel` is set). The three dots on each step are impact.
- Tabs: Check (onboarding), Plan (lanes + time to baseline), All steps (catalog with filters).
- Nine areas: accounts, devices, data already out there, money, voice & likeness, family & habits, data you give AI, AI acting for you, response. Organized by what's being protected; each step is tagged cyber, AI or both.

## Checking content
`python3 tools/check_content.py` checks that every id in `content.json` resolves and that every link responds. Sites that block scripts (FTC consumer pages, Facebook) are listed for a browser check. Links behind a sign-in only prove the page exists; whether they land on the right setting needs a signed-in check. Update `linksChecked` after a full pass.

## Open issues
1. **Signed-in settings links unverified.** Reachable as of 2026-11-03, but not checked while signed in: Google security/connections, Gemini activity, Microsoft security/app access, YouTube Studio, GitHub Copilot, LinkedIn AI setting, ChatGPT and Claude settings.
2. **No sources per step.** Plan: add a source URL to each step. A scheduled link check (GitHub Action running `tools/check_content.py`) is deferred.
3. **Impressum.** Deferred by the owner. Ask before adding anything.
4. Content is US/EU-focused; other regions only get generic steps.

## Research behind the content (as of Oct–Nov 2026)
- Mozilla Monitor Plus (broker removal) shut down 17 Dec 2025; the free breach monitoring continues.
- Data broker removal services vary in quality (a 2024 Consumer Reports study found DeleteMe removed 27% of listings in 3 months); Onerep's founder ran people-search sites.
- LinkedIn trains on user data by default (setting: Data privacy → Data for Generative AI Improvement). GitHub opted personal Copilot accounts into training in April 2026.
- Voice cloning: a few seconds of audio can be enough; bank voice ID has been beaten by clones; family safe word + callback is the main defense. Voice "cloaking" tools (AntiFake) can be stripped by purification (De-AntiFake, ICML 2025), so they're not recommended.
- YouTube likeness detection is open to all creators 18+ since May 2026 (face only, flags but doesn't remove). Loti offers free likeness monitoring.
- US TAKE IT DOWN Act: platforms must remove nonconsensual intimate images, including deepfakes, within 48 hours; FTC enforcement since 19 May 2026 (TakeItDown.ftc.gov).
- Prompt injection is the main risk of AI agents acting in logged-in sessions; no complete defense exists.
- Prior art: Consumer Reports Security Planner, EFF Surveillance Self-Defense. Neither covers AI exposure much; that's this tool's gap.
