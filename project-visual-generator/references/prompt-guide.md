# Prompt Guide for Project Visual Assets

English prompts work best with gpt-image models. Write one self-contained prompt per
asset; never chain multiple assets into one prompt.

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

Composition rules:

- One single bold abstract symbol — a visual metaphor for what the project *does*
  (e.g. a CLI tool that searches code → a stylized magnifier over brackets).
- Rounded-square badge composition; flat vector, not 3D, not photographic.
- High contrast, dominant color + white accent.
- Must survive being viewed at 32px: say "recognizable at 32px".
- Always end with: "no text, no letters, no watermark. Transparent background
  around the rounded square."

Example:

> App icon for a code-review assistant: an AI agent that reviews pull requests.
> Futuristic AI aesthetic, violet-to-indigo gradient glow. A single bold symbol of an
> eye merged with a code merge arrow, rounded-square badge composition, dominant
> color #8b5cf6, white accent. Flat vector, high contrast, instantly recognizable at
> 32px, clean edges, no text, no letters, no watermark. Transparent background around
> the rounded square.

## Banner (1280x640 — GitHub social preview ratio)

Default banner style is a **poster with text**: project title, one-line subtitle,
and up to four feature chips. gpt-image-2.5-class models render short text well.

Text rules (critical — one wrong character ruins the banner):

- Quote every string exactly: `title text reading exactly 'zcode-gpt-image2'`.
- End with: "render all text exactly as written with correct characters, no other
  text, no watermark".
- Keep it short: 1 title + 1 subtitle + at most 4 chips of 4–6 characters each.
  Chinese chips of 4–6 characters render more reliably than long sentences.
- Layout: visual/emblem on one side, text block on the other; chips in a row at the
  bottom of the text block.

### Style recipes — ROTATE between them so different projects don't look alike

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

General composition rules still apply: dominant color as hex, state the 2:1 layout,
no watermark. Say "render all text exactly as written" and nothing else textual.

## README illustration (1200x624)

Composition rules:

- Thin line art with one gradient accent color, light background — must sit well on
  both GitHub light and dark themes, so prefer near-white backgrounds with dark strokes.
- Wide banner composition, simple and clear, fits technical documentation.
- End with "no text, no watermark, clean vector style".

## General tips

- Hex colors in the prompt (`#8b5cf6`) steer the palette more reliably than color names.
- If the first result has stray text or watermarks, add "absolutely no typography of
  any kind" and regenerate just that asset.
- For icons, if the shape looks muddy at small size, simplify: fewer elements, one
  symbol only.
