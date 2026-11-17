# 04 — New Reference Style: Toy-3D Storytelling (the "Clever Hans" Short)

This is the target look and feel for our Shorts. It replaces the paper-diorama look from Short #001.

**Source:** a 67-second, 9:16 Short the user uploaded about *Clever Hans*, the "maths horse" of Berlin in 1904. It runs at 30 fps.
**Same rule as always:** copy the *craft* (rendering, camera, pacing, overlays, story shape). Never copy its characters, sets, script or jokes.

---

## 1. Look: real 3D, "vinyl toy" figures

| Element | What it does |
| :--- | :--- |
| **Render** | True 3D, Blender-style. It uses soft shadows, ambient occlusion, real perspective, depth-of-field background blur and motion blur. It is not 2D layers faking depth. |
| **Characters** | Toy-figure proportions: a big sphere head, a small capsule body and thin peg limbs with ball feet. Faces are simple: dot or round eyes with heavy expressive lids and brows, small mouths, and blush or freckle details. The material is smooth matte-satin plastic. |
| **Acting** | It comes from the eyelids and brows: smug half-lids, wide shocked eyes, a narrowed suspicious squint. Emoji-style props float over heads: `?`, `!`, hearts, sweat drops and a lightbulb. |
| **Sets** | One main hero set that is reused all video: a town square with cobblestones, pastel facades, coloured shutters, flower boxes, bunting and readable shop signs. There are only 1–2 secondary sets, such as a dark green committee room and a warm amber study. |
| **Props with text** | The text is big, simple and readable in-world: blackboards with `2 + 3 = ?`, a shop banner, a corkboard of clue notes, newspapers that fly in with headlines, and a stamped report reading `NO TRICK`. |
| **Lighting as story** | Warm daylight while the setup is "innocent". A night/purple grade for the reveal (the tension section). Warm amber lamp light for the detective. A change of mood equals a change of lighting. |

## 2. Camera and editing

- **About 30 hard cuts in 67 s** (about one every 2.2 s), plus **whip pans with heavy motion blur** as transitions. Roughly 1 in 8 frames sampled is a blur transition.
- **Shot variety:** extreme close-ups (hoof tapping, eyes, a sweat drop), low angles from under the horse, slow push-ins on faces at key words, over-the-shoulder shots, high-angle crowd shots, and a wide establishing shot of the square.
- **The camera never stops.** Every shot drifts, pushes or orbits slightly. Shallow depth of field keeps the subject sharp and the background soft.
- **The visual gag matches the spoken word.** "Tapping his hoof" cuts to an extreme close-up of the hoof. "Rolled their eyes" cuts to three faces rolling their eyes in sync.

## 3. Motion-graphics layer (on top of the 3D)

- **Title pops:** large yellow 3D-bevel words for the key facts (`1904`, `HANS`, `GENIUS`, `MATH`, `CLEVER HANS EFFECT`).
- **Tag labels:** a yellow label with an arrow pointing at a character (`RETIRED MATH TEACHER`) or a place (`BERLIN`).
- **Counters:** a circular badge counts each hoof tap. Its colour carries meaning: yellow is neutral, green is correct, red is wrong, purple is in the "tension" section.
- **Meters:** a vertical `TENSION` thermometer fills green, then yellow, then red as the hoof nears the answer, and drops back on the final tap. This turns an invisible idea into something you can see.
- **Cards and stamps:** a `MEANWHILE...` purple title card, a red `X` for wrong, a green tick for right, and a red rubber-stamp `NO TRICK`.

## 4. Captions

- **1–2 words at a time**, centred about 58–60% down the frame, with an extra-bold rounded sans (Montserrat ExtraBold style), white fill and a soft dark shadow.
- **Key words turn yellow:** names, numbers and punch words (`Hans`, `1904`, `math`, `strangers`, `genius`, `blind`).
- They are smaller than the title pops, so the two layers never compete.

## 5. Story shape: the "mystery" arc

Reconstructed narration, read from the on-screen captions (about 200 words, roughly 3.0 words per second):

> In 1904, a horse in Berlin could do math better than schoolchildren. His name was Hans, and he answered by tapping his hoof. Two plus three? *(5 taps)* The square root of sixteen? Four taps, proud snort. His owner, a retired math teacher, swore he taught him everything himself. Scientists rolled their eyes and came to expose the trick. They searched for hidden signals, secret helpers… Nothing. Then they sent the owner away and let strangers ask the questions. Hans still got them right. Meanwhile, a young student named Oskar noticed something strange. When the person asking didn't know the answer, Hans got it wrong. And when Hans wore blinders, his genius vanished completely. You see, Hans couldn't count at all. He was counting on us. As his hoof got close to the right number, everyone watching tensed up without realizing it. On the final tap, they relaxed, heads lifted a tiny bit, and Hans stopped. Even Oskar, who knew the secret, couldn't stop himself from doing it. Scientists still call it the Clever Hans effect, and it's why experiments today are run blind. So Hans was a genius after all. Just not at math. He was a genius at reading people. And we were so easy to read, the whole world believed…

| Beat | Time | What happens |
| :--- | :--- | :--- |
| 1. Absurd claim | 0–8 s | A date and place, then an impossible claim ("a horse could do math"). |
| 2. Proof | 8–16 s | We watch it work, twice, with numbers on screen. |
| 3. Skeptics fail | 16–28 s | Experts try to debunk it and find nothing. The test is made harder and it *still* works. |
| 4. The detective | 28–38 s | "Meanwhile…" A new character notices one strange pattern, and two clues land. |
| 5. Mechanism | 38–50 s | "You see…" The mood and lighting flip, and the hidden mechanism is shown with a visual meter. |
| 6. Legacy + term | 50–57 s | The real-world name for it ("the Clever Hans effect") and why it matters today (blind experiments). |
| 7. Reframe + loop | 57–67 s | The punchline flips the premise ("a genius at reading *people*"). The last line is cut off mid-sentence ("the whole world believed…") so it loops back into "In 1904". |

**Differences from our current formula (`CLAUDE.md`):**
- The story is in third person with a named historical hero, not "You…" plus "Congratulations". Both work. This one suits history and mystery topics, while "You…" suits schemes.
- Pacing is slightly slower (about 3.0 words per second against our 3.5–3.8). The extra air goes to visual beats like tap counts and reaction shots.
- The **loop ending** (cutting off mid-sentence into the first line) is new, and worth adopting for re-watches.
- The real term is still taught *after* the mechanism is shown, which matches Rule 2.

## 6. What this means for our pipeline

Our current renderer (`render/engine.py`) draws 2D shapes with Cairo and fakes depth with parallax. **It cannot reach this look.** Real perspective, soft shadows, depth of field, glossy toy materials and motion-blurred whip pans need a real 3D renderer.

The free option that fits our cloud setup is **Blender, driven by Python scripts, rendering on GitHub Actions**. We keep the audio, captions and assembly steps we already have and swap out only the picture.
