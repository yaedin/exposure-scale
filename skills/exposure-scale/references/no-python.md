# Without Python

Use this only when `python3`, `python` and `py` all fail, or there is no shell. Tell the user the flow is less exact this way and nothing is saved between sessions.

1. Read `assets/content.json`. Ask `questions` in file order, one per message, with options numbered as listed.
2. Skip a question when its `showIf` isn't met. Conditions: `equals` or `notEquals` compare the answer's `value`; `minCount` counts selected options that aren't `exclusive`; `minLevel` compares with the reach in step 4. A question with `optionsFrom` offers the options picked in that question (not exclusive ones), then its own.
3. After each answer, show the option's `note` if it has one.
4. Place the user: each option of a question with `place` has a `level`. "tried" is the highest level picked in the `tried` question, "habit" the level of the `habit` answer. Their level is habit (or tried until habit is answered), at least 1; reach is the higher of the two. Tell them the level and the matching entry in `levels`, and how it compares with their `self` answer.
5. Build the plan: first, every step in `guards` of each level up to the reach, and every step in `climb` of the next level, becomes "to do". Then, for each answered question in order, every step in `add` becomes "to do" unless already "in place"; every step in `done` becomes "in place". Apply `effects` too when their `if` holds.
6. Group "to do" steps: `withOthers` → With others; otherwise 10 minutes or less → Minutes, longer → An evening. Within a group: higher `impact` first, then fewer `minutes`.
7. For each step, show its `links` (with `showIf` met) and the `how` and `phone` text from `assets/assist.json`.
