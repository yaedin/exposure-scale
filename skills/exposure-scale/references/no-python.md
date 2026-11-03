# Without Python

Use this only when `python3`, `python` and `py` all fail, or there is no shell. Tell the user the flow is less exact this way and nothing is saved between sessions.

1. Read `assets/content.json`. Ask `questions` in file order, one per message, with options numbered as listed.
2. Skip a question when its `showIf` isn't met. Conditions: `equals` or `notEquals` compare the answer's `value`; `minCount` counts selected options that aren't `exclusive`.
3. `main_email` takes its options from the user's `email_accounts` answer. If only one account was picked, that's the main email. In `email_sign_in`, replace `{mainEmail}` with the provider's `name` from `emailProviders`, or "your main email".
4. After each answer, show the option's `note` if it has one.
5. Build the plan: for each answered question in order, every step in `add` becomes "to do" unless already "in place"; every step in `done` becomes "in place". Apply `effects` too when their `if` holds.
6. Group "to do" steps by effort: 10 minutes or less → Minutes, up to 60 → An evening, more or with `effortLabel` → Bigger. Within a group: higher `impact` first, then fewer `minutes`.
7. For each step, show its `links` (with `showIf` met) and the `how`, `phone` and `computer` text from `assets/assist.json`.
