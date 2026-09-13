---
name: project-visual-generator
description: Generate software icons, GitHub repo banners / social previews, and README illustrations for a project by calling the OpenAI gpt-image-2 API. Trigger on ANY casual mention of making project visuals — 生成图标、做个logo、生成横幅、banner、封面、配图、社交预览图、social preview、README 配图、项目视觉物料、icon、logo、画个图标、给项目整张图 — even very partial requests like just "生成横幅" or "给这个项目配个图" or "项目做完了,整点视觉素材". Also use it proactively right after finishing building a project when visual assets would help. Asset type, size, and style gaps are filled with smart defaults — never interrogate the user.
---

# Project Visual Generator

Generates project visual assets via the OpenAI `gpt-image-2` API. The value of this
skill is that the user does not write image prompts — you extract the project's
identity, craft professional prompts, and run the bundled script.

## Workflow

### 1. Fill in the gaps yourself — do NOT interrogate the user

Casual requests are the norm. Map whatever the user said to assets and defaults:

| User says | Generate | Assumed |
|---|---|---|
| 生成横幅 / banner / 封面 / social preview | `banner` | 1280x640, opaque |
| 图标 / logo / icon | `icon` | 1024x1024, transparent bg |
| 配图 / 插图 / README 配图 | `illustration` | 1200x624 |
| 图标和横幅 / 视觉物料 / 整点素材 (unspecified) | `icon,banner` | defaults each |
| mentions 2K / 4K / 高清 / 清晰 | add `--res` | maps to tier model |
| mentions 比例 (16:9, 9:16, 竖屏...) | add `--ratio` | |

Everything else has a default — project name/description/tech stack come from the
project's `package.json` / `pyproject.toml` / `README.md`; style and color from the
tech stack (step 3). **Proceed silently with defaults.** Only ask when the request
is truly ambiguous — e.g. "整点视觉素材" in a repo with no description at all, or the
user is talking about a project in a different directory. When you do ask, use your
interactive multiple-choice tool (in ZCode: AskUserQuestion) with ONE round of at
most 3 concrete options each, never open-ended questions. If the user explicitly
says 随便/你定/不用问 — just generate.

### 2. Ask two things (one round), then craft prompts

Before generating, ask ONE round via your multiple-choice tool (in ZCode:
AskUserQuestion). Only these two questions — everything else stays default:

1. **参考图** — "要不要融合参考图？" Options: 联网搜索品牌图标 (AI searches and
   downloads a reference) / 我自己提供图片 (user gives path(s)) / 不需要参考.
   Recommend searching when the project belongs to a known brand or tool
   (ZCode, Claude, Codex, DeepSeek...) — fusing the official icon style into the
   banner keeps branding consistent. Do the search and download yourself; never
   ask the user to find the image. If the user already supplied an image or said
   no reference, skip this question.
2. **生图模型** — relays often offer several image models at different prices.
   Run `--list-models` to see what the endpoint offers, then offer 2–4 concrete
   options (with prices if known). Skip when only one model exists or the user
   already named one.

If the user's request already answered a question (e.g. they pasted an image, or
said 用ZCode图标风格), skip it. Ask nothing else.

Then craft one English prompt per asset after reading
`references/prompt-guide.md`. Requirements for a good prompt:

- Describes the project's *purpose* as a visual metaphor, not just its name.
- Names the dominant color as a hex value.
- Ends with the negative constraints: "no text, no watermark" (icons additionally:
  "recognizable at 32px").
- Banner prompts specify the 2:1 layout: visual on the left, calm area on the right.

Do not rely on the script's fallback templates when you can write a better one — pass
your prompt via `--prompt-icon` / `--prompt-banner` / `--prompt-illustration`.
When reference images were agreed on (step 2), say in the prompt how they should be
used (e.g. "match the style and color of the reference image, keep its logo shape
recognizable") and pass them via `--ref-images path1,path2` — this switches the
script to the images/edits endpoint which fuses the reference style in.

### 3. Run the script

```bash
python "<skill-dir>/scripts/generate_assets.py" \
  --name "MyProject" --desc "one-line description" \
  --tech "Python AI CLI tool" --color "#8b5cf6" \
  --assets icon,banner --out ./docs/assets \
  --ratio 16:9 --res 2k \
  --prompt-icon "..." --prompt-banner "..." \
  --quality medium
```

`<skill-dir>` is this skill's base directory. Pass the user's explicit wishes (step 1), if any as
`--res 1k|2k|4k` and/or `--ratio W:H` (max 3:1). The script maps resolution tiers to
relay model variants automatically (`gpt-image-2` + `--res 2k` → model
`gpt-image-2-2k`, sizes 1024/2048/4096 long edge), and snaps explicit ratios to
gpt-image-2's constraints (multiples of 16, 655K–8.3M total pixels — 4K 1:1 becomes
2880x2880). Omit both flags for asset defaults (icon 1024x1024, banner 1280x640).
`--quality` is only sent when explicitly set (some relay channels reject it). Many
relay channels ignore `background: transparent` and return white-background PNGs —
if the user needs true transparency, generate then remove the background locally
with Pillow. The flags apply to every asset in one run — if the user wants
different settings per asset (e.g. square 2K icon + 16:9 banner), run the script
once per asset. Add:

- `--update-readme` — inserts banner + icon into `./README.md` after the first heading
  (run from the project root, or the script won't find the README).
- `--icon-sizes 16,32,48,64,128,256,512` — exports the icon at multiple sizes
  (needs Pillow). Useful for apps/packaging.
- `--background transparent` — overrides the default per-asset background
  (icons already default to transparent).
- `--quality high` — for a final banner; `medium` is fine for iteration.

### 4. Verify and report

Generation takes ~30–90s per image. After the script finishes, Read each generated
image to check it matches the project (correct metaphor, clean edges, no stray text).
If one is off, refine the prompt and regenerate that single asset only — don't redo
the ones that passed. Finally report the saved paths and whether the README was updated.

## Configuration (do this BEFORE generating, non-experts included)

Check whether a key is available with a cheap dry-run:

```bash
python "<skill-dir>/scripts/generate_assets.py" --name t --desc t --dry-run
```

If `"apiKeyConfigured": false`, help the user configure — they must NOT need to touch
environment variables. Ask them in chat for two things only: their API key (many
Chinese users use a relay/中转站, so also ask for the relay base URL), then write it
to the config file yourself with your file tools:

```json
// ~/.zcode/project-visual-generator.json
{ "apiKey": "sk-...", "baseUrl": "https://relay-address.com", "model": "gpt-image-2" }
```

Never repeat the full key back in chat, and never write the key into any file inside
a git repository. Alternatively the user can run
`python "<skill-dir>/scripts/generate_assets.py" --setup` in a terminal for an
interactive prompt. Priority order: CLI flags > environment variables > config file.
`baseUrl` accepts the relay address with or without a trailing `/v1`.

## Error handling

- The script retries 429/5xx three times with backoff. If all attempts fail, surface
  the API error detail to the user (it is printed to stderr) instead of retrying again.
- Missing API key (config error) → follow the Configuration section above: collect the
  key in chat, write the config file, then rerun. Do not prompt-fabricate a key.
- If Pillow is missing and `--icon-sizes` was requested, the single 1024px icon is
  still saved; just note that multi-size export was skipped.
