# YouTube Shorts Automation — Channel Analysis (`@wobblybusiness`)

This repository contains transcripts, metadata, and a complete reverse-engineered production bible for the viral YouTube Shorts channel **Wobbly Business** (`@wobblybusiness`), prepared for **Claude** to help script, storyboard, and produce original videos in our own variation of this style.

---

## Analyzed Reference Shorts

1. **[From Illegal Casino To Real Business](https://youtube.com/shorts/uiIKhYWuO50)** (`uiIKhYWuO50`)
   - **Stats:** 1,096,452 views | 31,849 likes | 68 seconds | 237 words (3.49 words/sec)
2. **[How Cheap Phone Shops Earn Money](https://youtube.com/shorts/NrVzNpmNZ3s)** (`NrVzNpmNZ3s`)
   - **Stats:** 661,385 views | 11,566 likes | 53 seconds | 193 words (3.64 words/sec)
3. **[How Money Gets Cleaned](https://youtube.com/shorts/IdSsAquESBE)** (`IdSsAquESBE`)
   - **Stats:** 1,706,317 views | 53,584 likes | 61 seconds | 231 words (3.79 words/sec)

---

## Repository Contents

| File / Folder | Description |
| :--- | :--- |
| [`CLAUDE.md`](./CLAUDE.md) | **Start Here for Claude:** System instructions, 7 Golden Rules, recurring character bible, caption rules, and output templates for generating new scripts and storyboards. |
| [`analysis/01_channel_formula_and_blueprint.md`](./analysis/01_channel_formula_and_blueprint.md) | Deep-dive analysis of the 5-Act narrative formula, hook mechanics, 3D "toy/clay" visual style, camera pacing, diegetic prop labels, and sound design. |
| [`analysis/02_video_breakdowns.md`](./analysis/02_video_breakdowns.md) | Second-by-second, shot-by-shot visual, audio, and script breakdowns of all 3 Shorts. |
| [`analysis/03_performance_insights_and_strategy.md`](./analysis/03_performance_insights_and_strategy.md) | Independent metric verification, topic-performance insights (shady topics ~2x views), originality guardrails, topic backlog, and automation pipeline. |
| [`transcripts/transcripts_clean.md`](./transcripts/transcripts_clean.md) | Clean, full-text transcripts with exact word counts and speaking-rate (WPS/WPM) metrics. |
| [`analysis/04_reference_style_3d.md`](./analysis/04_reference_style_3d.md) | The target 3D visual style: toy figures, camera and editing, graphics layer and story arc. |
| [`render3d/`](./render3d/) | The 3D renderer (Blender on GitHub Actions). Push to get a preview; start the commit message with `[final]` for the full render. See [`render3d/README.md`](./render3d/README.md). |

---

## How to Use With Claude

1. Open this repository in **Claude Code** or attach [`CLAUDE.md`](./CLAUDE.md), [`analysis/01_channel_formula_and_blueprint.md`](./analysis/01_channel_formula_and_blueprint.md), and [`analysis/02_video_breakdowns.md`](./analysis/02_video_breakdowns.md) to a **Claude Project**.
2. Prompt Claude with any business, street-hustle, or economics topic, for example:
   - *"Using CLAUDE.md, write a 60-second script and shot-by-shot 3D storyboard on 'How Mattress Stores Stay Open With Zero Customers'."*
   - *"Give me 10 viral video concepts in our own spin on the Wobbly Business format, complete with hooks and the business terms they teach."*
