#!/usr/bin/env python3
"""Generate project visual assets (icon / GitHub banner / README illustration)
via the OpenAI gpt-image-2 API.

Zero hard dependencies: the API call uses urllib from the standard library.
Pillow is optional and only used for multi-size icon export (--icon-sizes).

Environment:
    OPENAI_API_KEY    required (or pass --api-key, or store in the config file)
    OPENAI_BASE_URL   optional, for API proxies/relays (e.g. https://your-proxy.com
                      with or without a trailing /v1)

Beginners do not need environment variables: run `--setup` once to interactively
write `~/.zcode/project-visual-generator.json` ({"apiKey", "baseUrl", "model",
"quality"}), or let the agent write that file directly. Priority:
CLI flags > environment variables > config file.

Exit codes: 0 = all requested assets generated, 1 = at least one failed or config error.
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = "gpt-image-2"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".zcode", "project-visual-generator.json")

# gpt-image-2 accepts custom sizes: width/height multiples of 16,
# aspect ratio <= 3:1, total pixels 655,360 .. 8,294,400.
MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400
ASSET_SPECS = {
    "icon":         {"size": "1024x1024", "background": "transparent", "default": True},
    "banner":       {"size": "1280x640",  "background": "auto"},         # GitHub social preview 2:1
    "illustration": {"size": "1200x624",  "background": "auto"},         # README illustration
}

RES_LONG_EDGE = {"1k": 1024, "2k": 2048, "4k": 4096}

# Resolution tiers map to relay model-name variants (gpt-image-2-2k etc.); the
# explicit size parameter is still sent so aspect ratios work.
def tier_model(base_model, res):
    if not res or base_model.endswith(f"-{res}"):
        return base_model
    return f"{base_model}-{res}"


def fetch_model_ids(api_key, base_url, proxy="", timeout=30):
    """Best-effort: return the set of model ids the endpoint offers, or None."""
    url = resolve_base_url(base_url) + "/models"
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler(
            {"http": proxy, "https": proxy} if proxy else {}))
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}", "User-Agent": BROWSER_UA})
    try:
        with opener.open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {m.get("id") for m in data.get("data", []) if m.get("id")}
    except Exception:  # noqa: BLE001 - purely an optimization; any failure -> None
        return None


def resolve_relay_model(base_model, res, available):
    """Use the relay's tier variant (gpt-image-2-2k) only when it actually exists;
    otherwise the base model with an explicit size works on official API too."""
    if not res:
        return base_model
    tier = tier_model(base_model, res)
    if available is None or tier in available:
        return tier
    return base_model


def trim_flat_margins(png_bytes, threshold=3, max_frac=0.35, padding=12):
    """Auto-crop flat (low-detail) margins around the content, e.g. the empty
    dark bands AI banners tend to leave. Crops at most max_frac of each side.
    Returns (bytes, crop_box) — unchanged bytes when there is nothing to trim."""
    import io
    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    gray = img.convert("L")
    w, h = gray.size
    px = gray.load()

    def line_detail(fixed, along, axis):
        detail = 0
        prev = px[fixed, 0] if axis == "col" else px[0, fixed]
        for i in range(1, along):
            cur = px[fixed, i] if axis == "col" else px[i, fixed]
            detail = max(detail, abs(cur - prev))
            prev = cur
        return detail

    def advance(start, stop, step, limit, axis):
        pos = start
        while pos != stop and (abs(pos - start) < limit) and \
                line_detail(pos, w if axis == "row" else h, axis) < threshold:
            pos += step
        return pos

    top = advance(0, h, 1, h * max_frac, "row")
    bottom = advance(h - 1, 0, -1, h * max_frac, "row")
    left = advance(0, w, 1, w * max_frac, "col")
    right = advance(w - 1, 0, -1, w * max_frac, "col")

    box = (max(0, left - padding), max(0, top - padding),
           min(w, right + 1 + padding), min(h, bottom + 1 + padding))
    if box == (0, 0, w, h):
        return png_bytes, None
    buf = io.BytesIO()
    img.crop(box).save(buf, "PNG")
    return buf.getvalue(), box


def remove_white_background(png_bytes, threshold=243):
    """Turn a white background into transparency for icons.

    Flood-fills from the image borders so white *inside* the subject is kept,
    then softens the boundary. Returns (bytes, changed). Pillow required.
    """
    import io
    from collections import deque
    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    if img.getchannel("A").getextrema()[0] < 250:
        return png_bytes, False  # API already returned real transparency
    w, h = img.size
    px = img.load()
    visited = bytearray(w * h)
    queue = deque()
    for x in range(w):
        queue.append((x, 0))
        queue.append((x, h - 1))
    for y in range(h):
        queue.append((0, y))
        queue.append((w - 1, y))

    def is_white(p):
        return p[0] >= threshold and p[1] >= threshold and p[2] >= threshold

    while queue:
        x, y = queue.popleft()
        idx = y * w + x
        if visited[idx]:
            continue
        p = px[x, y]
        if not is_white(p):
            continue
        visited[idx] = 1
        px[x, y] = (p[0], p[1], p[2], 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[ny * w + nx]:
                queue.append((nx, ny))

    # Feather: soften semi-white pixels that touch the removed region
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            if visited[idx]:
                continue
            p = px[x, y]
            lum = (p[0] + p[1] + p[2]) / 3
            if lum >= 200 and any(
                0 <= x + dx < w and 0 <= y + dy < h and visited[(y + dy) * w + x + dx]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                px[x, y] = (p[0], p[1], p[2],
                            max(0, min(255, int(255 * (threshold - lum) / 43))))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue(), True


def size_from_ratio(res_tier, ratio):
    """Compute a valid gpt-image-2 size string from a resolution tier and W:H ratio."""
    if res_tier not in RES_LONG_EDGE:
        raise ValueError(f"res must be one of: {', '.join(RES_LONG_EDGE)}")
    if ":" not in ratio:
        raise ValueError("ratio must look like 16:9")
    rw, rh = (int(x) for x in ratio.split(":"))
    if min(rw, rh) <= 0 or max(rw, rh) / min(rw, rh) > 3:
        raise ValueError("aspect ratio must be between 1:3 and 3:1 (gpt-image-2 limit)")
    long_edge = RES_LONG_EDGE[res_tier]
    if rw >= rh:
        w, h = long_edge, round(long_edge * rh / rw)
    else:
        h, w = long_edge, round(long_edge * rw / rh)
    w, h = max(16, round(w / 16) * 16), max(16, round(h / 16) * 16)

    area = w * h
    if area > MAX_PIXELS:  # snap down with floor so we never exceed the cap
        f = (MAX_PIXELS / area) ** 0.5
        w, h = int(w * f / 16) * 16, int(h * f / 16) * 16
    elif area < MIN_PIXELS:  # snap up with ceil so we clear the floor
        f = (MIN_PIXELS / area) ** 0.5
        w, h = -(-w * f // 16) * 16, -(-h * f // 16) * 16
    return f"{int(w)}x{int(h)}"


def resolve_size(spec, ratio, res):
    """No flags -> the asset's default size. Either flag -> computed size."""
    if not ratio and not res:
        return spec["size"]
    if ratio:
        rw, rh = (int(x) for x in ratio.split(":"))
    else:
        sw, sh = (int(x) for x in spec["size"].split("x"))
        rw, rh = sw, sh
    return size_from_ratio(res or "2k", f"{rw}:{rh}")

# ---------------------------------------------------------------------------
# Prompt templates (fallbacks; the agent is expected to pass crafted prompts)
# ---------------------------------------------------------------------------

STYLE_MAP = [
    ("ai|ml|llm|agent|deep learning|machine learning|gpt",
     "#8b5cf6", "futuristic AI aesthetic, soft violet-to-indigo gradient glow, subtle neural mesh"),
    ("vue|react|frontend|ui|web|css|component",
     "#06b6d4", "clean modern UI design language, bright flat style, glassy highlights"),
    ("cli|backend|api|server|rust|go|python tool|devtool|framework",
     "#10b981", "solid engineering aesthetic, dark tech background with precise geometry"),
    ("blockchain|web3|crypto|nft",
     "#f59e0b", "cyberpunk gradient, geometric line art, amber accents"),
    ("vision|cv|camera|image processing",
     "#ec4899", "computer-vision visual language, lens and pixel motifs"),
]


def match_style(tech_stack):
    tech = (tech_stack or "").lower()
    for pattern, color, style in STYLE_MAP:
        if any(k in tech for k in pattern.split("|")):
            return color, style
    return "#3b82f6", "modern tech minimalist, flat vector, gentle blue gradient"


def build_fallback_prompt(asset, name, desc, tech, color):
    matched_color, style = match_style(tech)
    main = color or matched_color
    if asset == "icon":
        return (
            f"App icon for a software project called {name}: {desc}. "
            f"{style}. A single bold abstract symbol representing the project's core idea, "
            f"rounded-square composition, dominant color {main}, white accent. "
            "Flat vector, high contrast, instantly recognizable at 32px, clean edges, "
            "no text, no letters, no watermark. Transparent background around the rounded square."
        )
    if asset == "banner":
        return (
            f"GitHub repository social preview banner for the open source project {name}: {desc}. "
            f"{style}. Wide 2:1 composition: left two thirds show an abstract tech visual "
            f"evoking {tech or 'software development'} in color palette {main} over a deep dark gradient; "
            "right third is a calm, uncluttered area suitable for overlaying the project title later. "
            "Professional open source project style, no text, no watermark."
        )
    return (
        f"Minimalist illustration for the README of the project {name}: {desc}. "
        f"{style}, thin line art with gradient accent color {main}, light background, "
        "simple and clear, fits technical documentation, wide banner composition, "
        "no text, no watermark, clean vector style."
    )


# ---------------------------------------------------------------------------
# Config file
# ---------------------------------------------------------------------------

def load_config(path=None):
    """Read the optional JSON config file; return {} when absent or invalid."""
    cfg_path = path or CONFIG_PATH
    try:
        with open(cfg_path, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        return cfg if isinstance(cfg, dict) else {}
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as err:
        print(f"warning: could not read {cfg_path}: {err}", file=sys.stderr)
        return {}


def write_config(cfg, path=None):
    cfg_path = path or CONFIG_PATH
    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    try:  # POSIX only; Windows ignores this
        os.chmod(cfg_path, 0o600)
    except OSError:
        pass
    return cfg_path


def run_setup():
    """Interactive first-run configuration for beginners."""
    cfg = load_config()
    print("Project Visual Generator setup")
    print(f"Config file: {CONFIG_PATH}\n")
    current_key = cfg.get("apiKey", "")
    key = input(f"API key [{'*' * 6 + current_key[-4:] if current_key else 'not set'}]: ").strip()
    url = input(f"Base URL [{cfg.get('baseUrl') or 'https://api.openai.com'}] "
                "(relay/proxy address, blank to keep): ").strip()
    model = input(f"Model [{cfg.get('model') or DEFAULT_MODEL}]: ").strip()
    if key:
        cfg["apiKey"] = key
    if url:
        cfg["baseUrl"] = url
    if model:
        cfg["model"] = model
    write_config(cfg)
    print(f"\nSaved to {CONFIG_PATH}. You can now generate assets.")


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

def resolve_base_url(base_url):
    base = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com").rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    return base


BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def build_multipart(fields, files, boundary):
    import io
    buf = io.BytesIO()
    for key, value in fields.items():
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    for name, filename, data in files:
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
        buf.write(b"Content-Type: application/octet-stream\r\n\r\n")
        buf.write(data)
        buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue()


def call_api_edits(prompt, size, model, ref_images, api_key, base_url, timeout=300,
                   proxy=""):
    """Generate with reference image(s) via the images/edits endpoint (multipart)."""
    import uuid
    url = resolve_base_url(base_url) + "/images/edits"
    files = []
    for path in ref_images:
        with open(path, "rb") as fh:
            files.append(("image[]", os.path.basename(path), fh.read()))
    boundary = "----zcode" + uuid.uuid4().hex
    body = build_multipart(
        {"model": model, "prompt": prompt, "n": "1", "size": size}, files, boundary)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler(
            {"http": proxy, "https": proxy} if proxy else {}))
    headers = {"Authorization": f"Bearer {api_key}", "User-Agent": BROWSER_UA,
               "Content-Type": f"multipart/form-data; boundary={boundary}"}
    last_err = None
    for attempt in range(3):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with opener.open(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            item = data["data"][0]
            if item.get("b64_json"):
                return base64.b64decode(item["b64_json"])
            if item.get("url"):
                img_req = urllib.request.Request(item["url"], headers={"User-Agent": BROWSER_UA})
                with opener.open(img_req, timeout=timeout) as img:
                    return img.read()
            raise RuntimeError("response contained neither b64_json nor url")
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", "replace")[:300]
            last_err = RuntimeError(f"HTTP {err.code}: {detail}")
            print(f"  attempt {attempt + 1} failed: {detail}", file=sys.stderr)
            if attempt < 2:
                time.sleep(10 * (attempt + 1))
        except (urllib.error.URLError, RuntimeError, KeyError) as err:
            last_err = err
            print(f"  attempt {attempt + 1} failed: {err}", file=sys.stderr)
            if attempt < 2:
                time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"image generation failed after retries: {last_err}")


def call_api(prompt, size, quality, background, model, api_key, base_url, timeout=300,
             proxy=""):
    url = resolve_base_url(base_url) + "/images/generations"
    # Minimal payload first (model/prompt/n/size) — the format every relay accepts.
    # quality/background are appended only when explicitly requested, and the whole
    # payload is retried without them on HTTP 400 (some channels reject extras).
    base_payload = {"model": model, "prompt": prompt, "n": 1, "size": size}
    extras = {}
    if quality != "auto":
        extras["quality"] = quality
    if background != "auto":
        extras["background"] = background
    variants = [dict(base_payload, **extras), base_payload] if extras else [base_payload]
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler(
            {"http": proxy, "https": proxy} if proxy else {}))
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
               "User-Agent": BROWSER_UA}
    last_err = None
    rejected = False
    for vi, payload in enumerate(variants):
        for attempt in range(3):
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                         headers=headers, method="POST")
            try:
                with opener.open(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                item = data["data"][0]
                if item.get("b64_json"):
                    return base64.b64decode(item["b64_json"])
                if item.get("url"):  # relays return a download URL instead of b64
                    img_req = urllib.request.Request(item["url"], headers={"User-Agent": BROWSER_UA})
                    with opener.open(img_req, timeout=timeout) as img:
                        return img.read()
                raise RuntimeError("response contained neither b64_json nor url")
            except urllib.error.HTTPError as err:
                detail = err.read().decode("utf-8", "replace")[:300]
                last_err = RuntimeError(f"HTTP {err.code}: {detail}")
                if err.code == 400 and vi < len(variants) - 1:
                    rejected = True  # deterministic: retry with the next payload variant
                    break
                print(f"  attempt {attempt + 1} failed: {detail}", file=sys.stderr)
                if attempt < 2:
                    time.sleep(10 * (attempt + 1))
            except (urllib.error.URLError, RuntimeError, KeyError) as err:
                last_err = err
                print(f"  attempt {attempt + 1} failed: {err}", file=sys.stderr)
                if attempt < 2:
                    time.sleep(10 * (attempt + 1))
        if rejected and vi < len(variants) - 1:
            print("  extended parameters rejected, retrying without them", file=sys.stderr)
    raise RuntimeError(f"image generation failed after retries: {last_err}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return slug or "project"


def save_image(content, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(content)
    return out_path


def export_icon_sizes(src_png, sizes, out_dir, slug):
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed; skipping multi-size icon export "
              "(pip install pillow)", file=sys.stderr)
        return []
    written = []
    icon = Image.open(src_png).convert("RGBA")
    for size in sizes:
        resized = icon.resize((size, size), Image.LANCZOS)
        path = os.path.join(out_dir, f"icon-{slug}-{size}.png")
        resized.save(path, "PNG")
        written.append(path)
    return written


def update_readme(banner_path, icon_path, readme_path):
    if not os.path.isfile(readme_path):
        return "skipped (no README.md found)"
    with open(readme_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if "<!-- visual-assets" in text:
        return "skipped (visual assets already present)"
    lines = text.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines[:10]):
        if line.lstrip().startswith("# "):
            insert_at = i + 1
            break
    block = []
    if icon_path:
        block.append(f'\n<p align="center"><img src="{icon_path}" width="96" alt="icon"></p>\n')
    if banner_path:
        block.append(f'<p align="center"><img src="{banner_path}" alt="banner"></p>\n')
    lines[insert_at:insert_at] = block
    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    return f"updated ({readme_path})"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Generate project visual assets via gpt-image-2")
    p.add_argument("--name", default="", help="project name")
    p.add_argument("--desc", default="", help="one-line project description")
    p.add_argument("--tech", default="", help="tech stack, e.g. 'Python AI CLI tool'")
    p.add_argument("--color", default="", help="primary color hex, e.g. #8b5cf6")
    p.add_argument("--assets", default="icon,banner",
                   help="comma list of: icon,banner,illustration (default: icon,banner)")
    p.add_argument("--ratio", default="", help="aspect ratio W:H, e.g. 16:9, 9:16, 1:1 (max 3:1)")
    p.add_argument("--res", default="", choices=["", "1k", "2k", "4k"],
                   help="resolution tier; long edge 1280/2560/3840 (default: 2k when --ratio is given)")
    p.add_argument("--out", default="./docs/assets", help="output directory")
    p.add_argument("--model", default="", help="base model, e.g. gpt-image-2 (default; "
                                               "--res appends the tier suffix automatically)")
    p.add_argument("--quality", default="auto", choices=["auto", "low", "medium", "high"],
                   help="only sent when set; some relay channels reject it")
    p.add_argument("--background", default="auto", choices=["auto", "transparent", "opaque"],
                   help="override per-asset background (icon defaults to transparent)")
    p.add_argument("--api-key", default="", help="defaults to OPENAI_API_KEY env or config file")
    p.add_argument("--base-url", default="", help="defaults to OPENAI_BASE_URL env or config file")
    p.add_argument("--ref-images", default="",
                   help="comma-separated reference image paths; switches to the "
                        "images/edits endpoint so the style of the reference(s) is fused in")
    p.add_argument("--list-models", action="store_true",
                   help="list image-generation models offered by the endpoint and exit")
    p.add_argument("--config", default="", help=f"alternative config file (default: {CONFIG_PATH})")
    p.add_argument("--proxy", default="", help="HTTP proxy for the API call, e.g. http://127.0.0.1:7897 "
                                               "(defaults to 'proxy' field in config file)")
    p.add_argument("--setup", action="store_true",
                   help="interactive setup: write API key / base URL to the config file")
    p.add_argument("--prompt-icon", default="", help="full prompt override for icon")
    p.add_argument("--prompt-banner", default="", help="full prompt override for banner")
    p.add_argument("--prompt-illustration", default="", help="full prompt override for illustration")
    p.add_argument("--icon-sizes", default="",
                   help="comma list like 16,32,48,64,128,256,512 (needs Pillow)")
    p.add_argument("--trim", action="store_true",
                   help="auto-crop flat margins (recommended for banner/illustration)")
    p.add_argument("--update-readme", action="store_true",
                   help="insert banner/icon into ./README.md after the first heading")
    p.add_argument("--dry-run", action="store_true", help="print prompts and exit, no API call")
    return p.parse_args()


def main():
    args = parse_args()
    if args.setup:
        run_setup()
        return 0

    cfg = load_config(args.config)
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY") or cfg.get("apiKey", "")
    base_url = args.base_url or os.environ.get("OPENAI_BASE_URL") or cfg.get("baseUrl", "")
    proxy = args.proxy or cfg.get("proxy", "")

    if args.list_models:
        if not api_key:
            print("error: no API key configured", file=sys.stderr)
            return 1
        ids = fetch_model_ids(api_key, base_url, proxy)
        if ids is None:
            print("error: could not fetch model list", file=sys.stderr)
            return 1
        keywords = ("image", "dall", "flux", "seed", "banana", "midjourney", "mj_",
                    "sd3", "stable", "kontext", "grok-2-image", "draw")
        image_models = sorted(i for i in ids if any(k in i.lower() for k in keywords))
        print(json.dumps({"image_models": image_models}, ensure_ascii=False, indent=2))
        return 0

    ref_images = [p.strip() for p in args.ref_images.split(",") if p.strip()] if args.ref_images else []
    for path in ref_images:
        if not os.path.isfile(path):
            print(f"error: reference image not found: {path}", file=sys.stderr)
            return 1

    if not args.dry_run and (not args.name or not args.desc):
        print("error: --name and --desc are required for generation", file=sys.stderr)
        return 1
    base_model = args.model or cfg.get("model") or DEFAULT_MODEL
    if args.res and not base_model.endswith(f"-{args.res}"):
        model = tier_model(base_model, args.res)  # e.g. gpt-image-2 + 2k -> gpt-image-2-2k
    else:
        model = base_model
    if args.quality == "auto" and cfg.get("quality") in ("low", "medium", "high"):
        args.quality = cfg["quality"]

    assets = [a.strip() for a in args.assets.split(",") if a.strip()]
    unknown = [a for a in assets if a not in ASSET_SPECS]
    if unknown:
        print(f"unknown asset type(s): {', '.join(unknown)}; "
              f"valid: {', '.join(ASSET_SPECS)}", file=sys.stderr)
        return 1

    if not api_key and not args.dry_run:
        print("error: no API key found. Fix it in any of these ways:\n"
              "  1. paste your key into the chat and let the agent write it to "
              f"{CONFIG_PATH}\n"
              "  2. run: python generate_assets.py --setup\n"
              "  3. set the OPENAI_API_KEY environment variable", file=sys.stderr)
        return 1

    try:
        for asset in assets:
            resolve_size(ASSET_SPECS[asset], args.ratio, args.res)
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    # Relay tier variants (gpt-image-2-2k) are only used when the endpoint actually
    # offers them; the base model with an explicit size works everywhere else.
    if not args.dry_run and args.res:
        available = fetch_model_ids(api_key, base_url, proxy)
        resolved = resolve_relay_model(base_model, args.res, available)
        if resolved != model:
            print(f"  note: relay has no '{model}'; using '{resolved}' "
                  "with explicit size", file=sys.stderr)
        model = resolved

    slug = slugify(args.name)
    prompts = {
        "icon": args.prompt_icon,
        "banner": args.prompt_banner,
        "illustration": args.prompt_illustration,
    }
    for asset in assets:
        if not prompts[asset]:
            prompts[asset] = build_fallback_prompt(asset, args.name, args.desc, args.tech, args.color)

    if args.dry_run:
        print(json.dumps({
            "model": model, "quality": args.quality, "out": args.out,
            "apiKeyConfigured": bool(api_key),
            "baseUrl": base_url or "https://api.openai.com",
            "assets": [
                {"type": a, "size": resolve_size(ASSET_SPECS[a], args.ratio, args.res),
                 "background": args.background if args.background != "auto"
                 else ASSET_SPECS[a]["background"],
                 "prompt": prompts[a]} for a in assets
            ],
        }, ensure_ascii=False, indent=2))
        return 0

    results = []
    ok = True
    for asset in assets:
        spec = ASSET_SPECS[asset]
        background = args.background if args.background != "auto" else spec["background"]
        size = resolve_size(spec, args.ratio, args.res)
        out_path = os.path.join(args.out, f"{asset}-{slug}.png")
        print(f"[{asset}] generating {size} ({background}) -> {out_path}")
        try:
            if ref_images:
                content = call_api_edits(prompts[asset], size, model, ref_images,
                                         api_key, base_url, proxy=proxy)
            else:
                content = call_api(prompts[asset], size, args.quality, background,
                                   model, api_key, base_url, proxy=proxy)
            save_image(content, out_path)
            entry = {"type": asset, "path": out_path, "status": "ok"}
            if background == "transparent":
                try:
                    with open(out_path, "rb") as fh:
                        raw = fh.read()
                    cleaned, changed = remove_white_background(raw)
                    if changed:  # channel ignored the param; remove white bg locally
                        with open(out_path, "wb") as fh:
                            fh.write(cleaned)
                        entry["background_removed"] = True
                except Exception as err:  # noqa: BLE001 - keep the opaque image
                    print(f"  note: background removal skipped ({err})", file=sys.stderr)
            if args.trim and asset in ("banner", "illustration"):
                try:
                    with open(out_path, "rb") as fh:
                        raw = fh.read()
                    trimmed, box = trim_flat_margins(raw)
                    if box:
                        with open(out_path, "wb") as fh:
                            fh.write(trimmed)
                        entry["trimmed"] = True
                except Exception as err:  # noqa: BLE001 - keep the untrimmed image
                    print(f"  note: trim skipped ({err})", file=sys.stderr)
            if asset == "icon" and args.icon_sizes:
                sizes = [s.strip() for s in args.icon_sizes.split(",") if s.strip().isdigit()]
                extra = export_icon_sizes(out_path, [int(s) for s in sizes], args.out, slug)
                entry["icon_sizes"] = extra
            results.append(entry)
        except Exception as err:  # noqa: BLE001 - report and continue with remaining assets
            ok = False
            results.append({"type": asset, "status": "error", "error": str(err)})

    print(json.dumps({"success": ok, "assets": results}, ensure_ascii=False, indent=2))
    if ok and args.update_readme:
        banner = next((r["path"] for r in results if r["type"] == "banner"), "")
        icon = next((r["path"] for r in results if r["type"] == "icon"), "")
        banner_rel = os.path.relpath(banner, ".") if banner else ""
        icon_rel = os.path.relpath(icon, ".") if icon else ""
        status = update_readme(banner_rel.replace("\\", "/"), icon_rel.replace("\\", "/"), "README.md")
        print(f"README: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
