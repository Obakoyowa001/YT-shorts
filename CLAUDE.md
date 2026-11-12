# CLAUDE.md — Wobbly Business YouTube Shorts Automation & Script/Storyboard Engine

This repository contains a complete reverse-engineering and video analysis of the viral YouTube Shorts channel **Wobbly Business** (`@wobblybusiness`), designed so you (Claude) can help generate high-retention scripts, shot-by-shot 3D animation storyboards, voiceover directions, and sound design cues in our own unique spin on this format.

---

## 1. Repository Structure

- [`README.md`](./README.md) — Project overview, performance benchmarks of the 3 reference Shorts, and workflow guide.
- [`analysis/01_channel_formula_and_blueprint.md`](./analysis/01_channel_formula_and_blueprint.md) — Deep-dive breakdown of the narrative formula, pacing metrics, visual/3D aesthetic, typography, and audio engineering.
- [`analysis/02_video_breakdowns.md`](./analysis/02_video_breakdowns.md) — Second-by-second, shot-by-shot visual, audio, and script breakdown of all three analyzed Shorts:
  1. **From Illegal Casino To Real Business** (`uiIKhYWuO50` — 68s, 1.10M views, 31.8K likes)
  2. **How Cheap Phone Shops Earn Money** (`NrVzNpmNZ3s` — 53s, 661K views, 11.6K likes)
  3. **How Money Gets Cleaned** (`IdSsAquESBE` — 61s, 1.71M views, 53.6K likes)
- [`analysis/03_performance_insights_and_strategy.md`](./analysis/03_performance_insights_and_strategy.md) — Verified metrics, which topics perform best, originality guardrails, topic backlog, and the production/automation pipeline.
- [`transcripts/`](./transcripts/) — Clean full-text scripts, word-level timing stats, and raw `.vtt` caption files.

---

## 2. Core Formula When Writing New Videos

Whenever asked to brainstorm topics, write a script, or build a storyboard/prompt list for a new Short, strictly adhere to these **7 Golden Rules** derived from the data:

### Rule 1: The "You + Absurd Premise + Congratulations" Hook (0.0s – 8.0s)
Every video opens in **second person ("You")** throwing the viewer straight into a shady, grey-area, or counter-intuitive business operation, punctuated by a deadpan **"Congratulations."**
- *Pattern A (Illicit/Grey Hustle):* `"If you [do shady/clever business move], congratulations—you're in the [X] business."`
- *Pattern B (Sudden Windfall Problem):* `"You just made $100,000 in cash in a gym bag from a job we're not going to talk about. Congratulations. You can't spend a cent of it."`
- Immediately follow with the **Core Conflict / Paradox** (why the obvious move fails or how the hidden margin actually works).

### Rule 2: Relentless Pacing & Reading Level (50–68 Seconds, ~3.5–3.8 Words/Sec)
- **Target Word Count:** 190 to 240 words (for a 53–68 second Short; ~210–230 WPM).
- **Reading Grade:** 4th–5th grade vocabulary. Zero jargon without an immediate physical joke explaining it.
- **Sentence Length:** Short, punchy declarative sentences (6–12 words average).
- **Named Business Concepts:** Always teach 1 to 3 real economic/financial terms (`placement`, `layering`, `integration`, `gray import`, `loss leader`), introduced *after* showing the physical action:
  > *"Every night, you slip casino cash into the register, making it look like it came from washing socks. Timmy washes the actual socks for free. **This is called placement.**"*

### Rule 3: The Recurring Character Cast
Use a consistent cast of recurring toy-like characters so viewers build parasocial familiarity across episodes:
1. **The Boss ("You"):** Grey suit, neat grey/brown hair, calm, calculating entrepreneur/hustler who executes the scheme.
2. **Timmy (The Naive Customer / Fall Guy):** Orange curly hair, round black glasses, yellow-and-navy horizontal striped polo shirt. He happily overpays for plastic phone cases, gets made "Director" of an offshore shell company thinking it's a promotion, or leaves a 5-star review ("very relaxing") after his car comes out dirtier than it went in.
3. **Tony (The Shady Middleman / Dealer):** Tracksuit or bakery/dealership owner, tinted glasses, pencil mustache—asks pointed questions or helps bounce cash.
4. **The Inspector / Government / Banker:** Bowler hat & monocle/glasses (Tax Man) or stern police/inspector who "does the math."

### Rule 4: Visual Gags & Diegetic Props (Show, Don't Just Tell)
Hard-cut to a new shot roughly every 2.5 seconds (22–25 shots per Short), and keep the camera moving / new props or text popping in every ~1.5–2 seconds within each shot, so every beat lands on a new physical gag or close-up prop with **huge, readable in-world text**:
- Never show complex spreadsheets. Show a whiteboard where a hand physically sticks a green `0` onto `$5,000` to make `$50,000`.
- Show a literal yellow sponge wiping a phone screen to "wipe" a trade-in phone.
- Show a bubble machine with its power cord lying unplugged next to a wall outlet (`"The bubble machine isn't even plugged in."`).
- Show stacks of cash sitting next to a literal appointment card that says `DENTIST - Tue 3:00` (`"Now the money is clean. It has receipts. It has a dentist."`).

### Rule 5: The Twist / Ironic Payoff Ending (48s – 65s)
End with a humorous escalation featuring Timmy and a signature closing one-liner:
- *"The cheap phone was never the product. Timmy was. And that's basically how every phone shop works."*
- *"That's the only real money this place made all year. And that's basically how every money laundering scheme works."*
- *"The inspector does the math. So do the 12 police cars outside Timmy's house."*

### Rule 6: On-Screen Caption Specification
- **Style:** Single-word (1 word at a time) karaoke pop-in at the center/lower-middle of the 9:16 frame (`align: center`, ~55%–60% down from top).
- **Font:** Extra-bold rounded sans-serif (e.g., Montserrat Black / Rubik Mono / Komika Axis), white fill with thick black outline + subtle drop shadow.
- **Color Emphasis:** Switch word color to **Bright Yellow/Gold (`#FFD700`)** on dollar amounts (`$100,000`, `$200`, `$0.50`, `$30`, `$8`), key nouns (`Cash`, `Gym`, `Charger`), or punchwords (`Cheaper`).

### Rule 7: Output Format When Generating New Videos
When the user asks you to create a new video, provide:
1. **3 High-CTR Title Options** (4–6 words, Title Case, curiosity gap around how a business/scheme works).
2. **Full Voiceover Script** with word count, estimated duration, and `[emphasis/pause]` markers.
3. **Shot-by-Shot Storyboard Table** (Timestamp | Shot Duration | Spoken Line | 3D Visual Scene & Camera Move | In-World Prop Text | SFXCue).
4. **AI Video / 3D Scene Generation Prompts** (ready to paste into image/video generators or Blender/3D pipelines).

