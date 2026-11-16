# Without Python

Use this only when `python3`, `python` and `py` all fail, or there is no shell. Tell the user the flow is less exact this way and nothing is saved between sessions.

1. Read `assets/content.json`. Ask `questions` in file order, one per message, with options numbered as listed. Before the first question whose `part` is marked `optional` in `parts`, ask whether the user wants that part; if not, stop asking.
2. Skip a question when its `showIf` isn't met. Conditions: `equals` or `notEquals` compare the answer's `value`; `minCount` counts selected options that aren't `exclusive`; `minLevel` compares with the reach in step 4. A question with `above` leaves out the options whose `level` is at or below the level picked in the question it names (keep `exclusive` options).
3. After each answer, show the option's `note` if it has one, with the `url` of the entry in `sources` that its `src` names.
4. Place the user: each option of a question with `place` has a `level`. "habit" is the level of the `habit` answer, "tried" the highest level picked in the `tried` question. Their level is habit (or tried if habit was skipped), at least 1; reach is the higher of the two, at least 1. Tell them the level and the matching entry in `levels`.
5. Build the plan: first, every step in `guards` of each level up to the reach, and every step in `climb` of the level above theirs, becomes "to do". Then, for each answered question in order, every step in `add` becomes "to do" unless already "in place"; every step in `done` becomes "in place". Apply `effects` too when their `if` holds.
6. Cover: for each level up to the reach, take the steps of that `level` in the plan with `tier` 1 that aren't `up` steps. All "in place": the level is covered. Some: partly covered. None: open. Say how many levels are covered and show each level's state with its `risk` and `case`.
7. Name the step to do first: among "to do" steps at levels 1 to reach that aren't `up` steps, `tier` 1 before the rest, then higher `impact`, then the higher `level`, then fewer `minutes`. List the remaining steps level by level in the same order.
8. For each step, show its `why`, its `links` (with `showIf` met) and the `how` and `phone` text from `assets/assist.json`.
