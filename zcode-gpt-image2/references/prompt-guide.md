# Prompt Guide for Project Visual Assets

Distilled from OpenAI's official GPT Image 2.5 prompting guide
(developers.openai.com/api/docs/guides/image-prompting) plus community practice.
English prompts work best. Write one self-contained prompt per asset; never chain
multiple assets into one prompt.

## Universal rules (apply to every asset)

1. **Define the result first**: name the deliverable (app icon, GitHub social
   preview, README illustration), the project's purpose, and the composition.
   For complex scenes organize as labeled sections: Scene / Subject / Details /
   Constraints.
2. **Describe what is visible**, not abstractions: materials, light source, colors,
   medium. Say "photorealistic" or "flat vector" explicitly — never rely on mood
   words alone. Camera/lens specs are appearance cues, not guarantees.
3. **Exact text**: put required wording in quotes, state where it goes and its
   typography, and say "render it exactly once, clearly and legibly". Spell unusual
   words letter by letter. Always add "no extra text". After generation, verify
   every character; small text or many chips may need a higher quality setting.
4. **Iterate deliberately**: regenerate only the failed asset; change one thing at
   a time; when editing, restate the constraints that must be preserved.
5. **State exclusions**: unwanted text, logos, watermarks. A drawn checkerboard is
   NOT transparency — real transparency comes only from an alpha channel.

## Style matching (pick color + aesthetic from tech stack)

| Tech stack | Color | Aesthetic keywords |
|---|---|---|
| AI / ML / LLM / agents | `#8b5cf6` | futuristic AI aesthetic, violet-to-indigo gradient glow, subtle neural mesh |
| Frontend / UI / web | `#06b6d4` | clean modern UI design language, bright flat style, glassy highlights |
| Backend / CLI / devtools | `#10b981` | solid engineering aesthetic, dark tech background, precise geometry |
| Blockchain / web3 | `#f59e0b` | cyberpunk gradient, geometric line art, amber accents |
| Computer vision | `#ec4899` | lens and pixel motifs, visual-tech feel |
| Anything else | `#3b82f6` | modern tech minimalist, flat vector, gentle blue gradient |

If the user gave a primary color, use their color with the matching aesthetic row.

## Icon (1024x1024, transparent background)

Follow the official logo pattern: describe the brand and the shapes that define the
mark, then demand legibility. Key phrasings:

> "Use clean, vector-like shapes, a strong silhouette, and balanced negative space.
> Favor simplicity over detail so it reads clearly at small and large sizes.
> Flat design, minimal strokes, no gradients unless essential.
> Fully transparent background. A single centered logo with generous padding,
> clean alpha edges, no solid backdrop, scenery, checkerboard, or watermark."

Compose the mark as ONE bold visual metaphor for what the project does (a CLI code
searcher → magnifier over brackets). Dominant color as hex + white accent. End with
"no text, no letters, no watermark". Mention "recognizable at 32px".

## Banner (1280x640 — GitHub social preview ratio)

Default banner style is a **poster with text**: project title, one-line subtitle,
and up to four feature chips.

Text rules (critical — one wrong character ruins the banner):

- Quote every string exactly: `title text reading exactly 'zcode-gpt-image2'`.
- Add "render it exactly once, clearly and legibly" and "no extra text".
- Keep it short: 1 title + 1 subtitle + at most 4 chips of 4–6 characters each.
  Chinese chips of 4–6 characters render more reliably than long sentences.
- End with: "render all text exactly as written with correct characters, no other
  text, no watermark".

### Style recipes — ROTATE between them so different projects don't look alike.
**Default preference (user-confirmed): recipe F, Ghibli-esque painterly** — warm
hand-painted skies, soft clouds, a small figure doing something related to the
project, big hand-lettered title. Unless a reference image or the project's tone
clearly calls for another recipe, generate F first and offer alternatives after.

Typography defaults (user-confirmed):
- Title is LARGE — the most prominent element ("HUGE BOLD title text", "big bold
  lettering, the most prominent element, clearly readable").
- Text block VERTICALLY CENTERED in the banner, visually middle-aligned.
- Feature chips in ONE single horizontal row.
- The user responded very well to: hand-lettered title + white/colored painted
  chips on the open sky area of the composition.

**A. Reference-fusion poster** (when a brand icon is fused in): the emblem from the
reference large on the left with accent glow, text block right, dark gradient
background echoing the reference colors.

**B. Cinematic scene**: full-bleed atmospheric background (deep sea, nebula,
mountains at dawn — pick a metaphor for the project's domain), huge title over it,
one-line slogan, small feature row at the bottom. Mood lighting, film-grade color.

**C. Hand-drawn illustration**: warm paper / watercolor / ink texture, a charming
hand-drawn metaphor object on the left, big display title and an English tagline on
the right, imperfect edges, cozy and memorable.

**D. Game-poster energy**: dynamic diagonal composition with the hero element
bursting through, bold italic title, glowing rim light, feature chips as a bottom
bar, small corner badges. Loud, high-saturation, made to impress.

**E. Anime illustration (user favorite)**: clean cel-shaded anime style, crisp line
art, vibrant but soft palette, atmospheric sky or city backdrop with light bloom.
One anime character mascot or an anime-styled scene embodying the project's purpose.
Title and subtitle BLOCK VERTICALLY CENTERED, never top- or bottom-crowded.

**F. Ghibli-esque painterly**: warm hand-painted gouache skies, gentle clouds,
nostalgic mood, soft edges; small figures in a big landscape that hints at the
project's domain; title vertically centered in the clearer sky area.

Text-block placement rule (all recipes): when the banner carries a title/subtitle,
the text block is VERTICALLY CENTERED within the banner — visually middle-aligned,
not stuck to the top or bottom edge. Phrase it as: "title and subtitle text block
vertically centered in the banner, visually middle-aligned".

If the banner contains small text, chips, or more than two text blocks, consider
`--res 2k` and/or `--quality high` — quality matters more than prompt wording for
small type.

## README illustration (1200x624)

- Thin line art with one gradient accent color, near-white background with dark
  strokes — must sit well on both GitHub light and dark themes.
- Wide banner composition, simple and clear, fits technical documentation.
- End with "no text, no watermark, clean vector style".

## Using reference images (`--ref-images`, images/edits endpoint)

1. **Assign roles**: identify each input by purpose — "image 1 is the brand emblem
   whose shape must stay recognizable; match its palette and lighting".
2. **Separate changes from constraints**: say "change only X" and list what must be
   preserved (geometry, layout, colors, label legibility).
3. **Style transfer phrasing**: "Use the same style from the input image and
   generate ..." — describe the NEW subject separately from the borrowed style.
4. **One change per edit**: don't stack style + text + layout changes in a single
   regeneration; fix the failed aspect only.

## Model notes (when the endpoint offers gpt-image-2.5 variants)

- `gpt-image-2.5-flare` — small model, speed-optimized, quality comparable to
  gpt-image-2. Good default for iteration.
- `gpt-image-2.5-sunburst` — base model, higher quality than gpt-image-2. Use when
  a demanding asset (text-dense banner, detailed illustration) fell short.
- Both support transparent backgrounds. Start with flare; escalate to sunburst only
  if quality is insufficient.

## General tips

- Hex colors in the prompt (`#8b5cf6`) steer the palette more reliably than color names.
- If the first result has stray text or watermarks, add "no typography of any kind"
  and regenerate just that asset.
- For icons that look muddy at small size, simplify: fewer elements, one symbol only.
