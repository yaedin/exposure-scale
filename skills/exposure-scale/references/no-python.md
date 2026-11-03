# Without Python

Use this only when `python3`, `python` and `py` all fail, or there is no shell. Tell the user the flow is less exact this way and nothing is saved between sessions.

1. Read `assets/content.json`. Ask `questions` in file order, one per message, with options numbered as listed.
2. Skip a question when its `showIf` isn't met. Conditions: `equals` or `notEquals` compare the answer's `value`; `minCount` counts selected options that aren't `exclusive`.
3. After each answer, show the option's `note` if it has one.
4. Build the plan: for each answered question in order, every step in `add` becomes "to do" unless already "in place"; every step in `done` becomes "in place". Apply `effects` too when their `if` holds.
5. Group "to do" steps: `withOthers` → With others; otherwise 10 minutes or less → Minutes, longer → An evening. Within a group: higher `impact` first, then fewer `minutes`.
6. For each step, show its `links` (with `showIf` met) and the `how` and `phone` text from `assets/assist.json`.
