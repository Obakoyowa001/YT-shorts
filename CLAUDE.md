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
- [`analysis/04_reference_style_3d.md`](./analysis/04_reference_style_3d.md) — **The target visual style**: real 3D toy-figure animation, camera and editing rhythm, motion-graphics layer, captions and the "mystery" story arc, taken from a reference Short the user supplied.
- [`render3d/`](./render3d/) — **The 3D renderer** (Blender `bpy` + Cycles on GitHub Actions). Each Short is a Python file in `render3d/shorts/`. See [`render3d/README.md`](./render3d/README.md).
- `render/` — The old 2D renderer, now retired. Its `audio.py` and `sfx/` are still used by the 3D renderer.

---

## 2. Core Formula When Writing New Videos

Whenever asked to brainstorm topics, write a script, or build a storyboard/prompt list for a new Short, strictly adhere to these **7 Golden Rules** derived from the data:

> **Originality first (see [`analysis/03_performance_insights_and_strategy.md`](./analysis/03_performance_insights_and_strategy.md), Section 3):** reuse the *formula*, never the channel's *assets*. Every script, gag, character design, and name must be our own. Quoted lines below come from the reference channel and are there to show the pattern. Never reuse them verbatim or lightly reworded.

### Rule 1: The "You + Absurd Premise + Congratulations" Hook (0.0s – 8.0s)
Every video opens in **second person ("You")** throwing the viewer straight into a shady, grey-area, or counter-intuitive business operation, punctuated by a deadpan **"Congratulations."**
- *Pattern A (Illicit/Grey Hustle):* `"If you [do shady/clever business move], congratulations—you're in the [X] business."`
- *Pattern B (Sudden Windfall Problem):* `"You just made $100,000 in cash in a gym bag from a job we're not going to talk about. Congratulations. You can't spend a cent of it."`
- Immediately follow with the **Core Conflict / Paradox** (why the obvious move fails or how the hidden margin actually works).
- **Topic choice:** prefer "secret/shady money" topics. They pulled ~2x the views of legal-retail topics. Frame them as explanation, never as instructions. When a video over-performs, re-run the same topic 1–3 weeks later with a new setting/metaphor (doc 03, Sections 2.2–2.3 and topic backlog in Section 4).

### Rule 2: Relentless Pacing & Reading Level (50–68 Seconds, ~3.5–3.8 Words/Sec)
- **Target Word Count:** 190 to 240 words (for a 53–68 second Short; ~210–230 WPM).
- **Reading Grade:** 4th–5th grade vocabulary. Zero jargon without an immediate physical joke explaining it.
- **Sentence Length:** Short, punchy declarative sentences (6–12 words average).
- **Named Business Concepts:** Always teach 1 to 3 real economic/financial terms (`placement`, `layering`, `integration`, `gray import`, `loss leader`), introduced *after* showing the physical action:
  > *"Every night, you slip casino cash into the register, making it look like it came from washing socks. Timmy washes the actual socks for free. **This is called placement.**"*

### Rule 3: The Recurring Character Cast (Our Own Characters, Same Four Roles)
Use a consistent cast of recurring characters so viewers build parasocial familiarity across episodes. Keep the four **roles** that make the reference channel work, but use **our own names and visual designs**. Do **not** reproduce the reference channel's characters (Timmy, Tony, the bowler-hat Tax Man) or their looks.

| Role | What the role does | Our character |
| :--- | :--- | :--- |
| **1. The Boss ("You")** | Calm, calculating operator who runs the scheme; stands in for the viewer. | *TBD: our own name & design* |
| **2. The Fall Guy** | Lovable, naive customer/accomplice who gets used and never notices. Delivers the comedic payoff in Act IV and appears in every episode. | *TBD: our own name & design* |
| **3. The Middleman** | Shady dealer/partner who asks pointed questions or helps move the money. | *TBD: our own name & design* |
| **4. The Authority** | Inspector/tax man/banker who "does the math" and catches the scheme. | *TBD: our own name & design* |

Design guidance: pick a visual style and silhouettes clearly different from the reference channel's (different art style, palette, proportions, signature outfits). Once the cast is defined, replace the *TBD* cells and use those names in every script.

### Rule 4: Visual Gags & Diegetic Props (Show, Don't Just Tell)
Hard-cut to a new shot roughly every 2.5 seconds (22–25 shots per Short), and keep the camera moving / new props or text popping in every ~1.5–2 seconds within each shot, so every beat lands on a new physical gag or close-up prop with **huge, readable in-world text**:
- Never show complex spreadsheets. Show a whiteboard where a hand physically sticks a green `0` onto `$5,000` to make `$50,000`.
- Show a literal yellow sponge wiping a phone screen to "wipe" a trade-in phone.
- Show a bubble machine with its power cord lying unplugged next to a wall outlet (`"The bubble machine isn't even plugged in."`).
- Show stacks of cash sitting next to a literal appointment card that says `DENTIST - Tue 3:00` (`"Now the money is clean. It has receipts. It has a dentist."`).

### Rule 5: The Twist / Ironic Payoff Ending (48s – 65s)
End with a humorous escalation featuring **our Fall Guy** (Rule 3), then the signature closing line *"And that's basically how every ___ works."* It generalizes the lesson and loops cleanly back to the hook. Reference-channel examples of the pattern (do not reuse):
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

---

## 3. Producing the Video (3D)

Every new Short is produced as **real 3D animation** in [`render3d/`](./render3d/), in the style of [`analysis/04_reference_style_3d.md`](./analysis/04_reference_style_3d.md). The old 2D/2.5D look is retired.
- Write the Short as `render3d/shorts/sNNN.py`, one `SHOTS` entry per ~2–2.5 s of narration (about 22–28 shots per minute). Use the kit's cast, sets and props, and add new props to `kit.py` when they will be reused.
- Every shot needs a moving camera (`cam.at` keys plus `cam.drift`), at least one character reaction or prop action keyed to a spoken word (`c.w("word")`), and usually one graphics beat (`pop`, `tag`, `icon`, `badge`, `meter`, `stamp`, `card`).
- Use lighting to mark story mood: `light_day` for setup, `light_night` for tension or reveals, `light_amber` for interiors and detectives.
- Push to get a cheap preview render. Put `[final]` in the commit message only when the preview is approved, because final renders use a lot of the private repo's GitHub Actions minutes.

