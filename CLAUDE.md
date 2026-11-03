# Exposure Scale

A guided self-check of a person's cybersecurity and AI exposure. It asks one question at a time and builds a plan sorted by effort. Live at https://yaedin.github.io/exposure-scale/ (GitHub Pages, from `main`, root).

Goal of this stage: show that the idea works (adaptive onboarding, a quick sense of what's easy vs. hard), not full coverage.

## Ground rules
- **One file, no build step.** Everything lives in `index.html`; fonts in `fonts/`. Keep it that way unless there is a clear reason.
- **No outside requests.** No CDNs, analytics, embeds or Google Fonts. Answers stay in `localStorage` only. The footer's privacy note depends on this; update it if anything changes.
- **Lean copy.** Short, plain sentences. No defensive caveats, no filler. The owner explicitly dislikes verbose text.
- **Comfort first.** One question per screen, number-key shortcuts, instant feedback after each answer.
- Light and dark themes come from CSS tokens at the top of the style block. Use the tokens, not literal colors.

## How it works
- `QS`: questions. Each option can `add` step ids to the plan or mark them `done`. `when` hides a question, `many` makes it multi-select, `x` marks an exclusive option ("None").
- `STEPS`: actions with `min` (minutes), `imp` (impact 1–3), `tier` (1 baseline, 2 recommended, 3 advanced), `k` (`c` cyber, `a` AI), `m` (how a full build could check it: auto/link/self), and `L` (links; can depend on answers).
- Effort lanes come from `min`: ≤10 min "Minutes", ≤60 "An evening", else "Bigger" (or when `proj` is set).
- Tabs: Check (onboarding), Plan (lanes + time to baseline), All steps (catalog with filters).
- Nine areas: accounts, devices, data already out there, money, voice & likeness, family & habits, data you give AI, AI acting for you, response. Organized by what's being protected; each step is tagged cyber, AI or both.

## Open issues
1. **Links not verified.** Several settings URLs were written from memory. Check each one.
2. **No sources per step.** Plan: add a source URL and a "last checked" date to each step, plus a link check that runs on a schedule (GitHub Action).
3. **Impressum.** Not added. Depends on the owner's country of residence (not Germany). Ask before adding anything.
4. Content is US/EU-focused; other regions only get generic steps.
5. Possible later step: move `QS`/`STEPS` into a JSON file so content can be edited without touching code.

## Research behind the content (as of Oct–Nov 2026)
- Mozilla Monitor Plus (broker removal) shut down 17 Dec 2025; the free breach monitoring continues.
- Data broker removal services vary in quality (a 2024 Consumer Reports study found DeleteMe removed 27% of listings in 3 months); Onerep's founder ran people-search sites.
- LinkedIn trains on user data by default (setting: Data privacy → Data for Generative AI Improvement). GitHub opted personal Copilot accounts into training in April 2026.
- Voice cloning: a few seconds of audio can be enough; bank voice ID has been beaten by clones; family safe word + callback is the main defense. Voice "cloaking" tools (AntiFake) can be stripped by purification (De-AntiFake, ICML 2025), so they're not recommended.
- YouTube likeness detection is open to all creators 18+ since May 2026 (face only, flags but doesn't remove). Loti offers free likeness monitoring.
- US TAKE IT DOWN Act: platforms must remove nonconsensual intimate images, including deepfakes, within 48 hours; FTC enforcement since 19 May 2026 (TakeItDown.ftc.gov).
- Prompt injection is the main risk of AI agents acting in logged-in sessions; no complete defense exists.
- Prior art: Consumer Reports Security Planner, EFF Surveillance Self-Defense. Neither covers AI exposure much; that's this tool's gap.
