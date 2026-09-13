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

Composition rules:

- State the 2:1 wide layout explicitly.
- Left two thirds: abstract tech visual evoking the project's domain, dominant color
  over a deep dark gradient (dark backgrounds read well on GitHub).
- Right third: calm, uncluttered area — GitHub overlays nothing, but users often add
  the repo title there later.
- No text in the image: generated text is a common failure point and repo titles are
  better added by the user. End with "no text, no watermark".

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
