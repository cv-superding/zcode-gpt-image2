# project-visual-generator

一个 ZCode Skill：项目开发完成后，AI 自动提取项目特征、编写生图提示词，调用 OpenAI
**gpt-image-2** 接口，一次性生成风格匹配的**软件图标**、**GitHub 仓库横幅（social
preview）**和 **README 配图**，无需手动编写生图 prompt。

## 安装（全局生效）

把 `project-visual-generator/` 目录复制到用户技能目录：

```bash
# Windows (PowerShell)
Copy-Item -Recurse project-visual-generator "$env:USERPROFILE\.agents\skills\"

# Git Bash
cp -r project-visual-generator ~/.agents/skills/
```

或者只在某个项目里生效：复制到 `<项目>/.agents/skills/`。

## 配置（小白友好，无需环境变量）

**方式一（推荐）：让 AI 帮你配。** 装好 skill 后直接对 ZCode 说"生成图标"，如果没配
Key，AI 会在对话里向你要 Key 和中转站地址，然后自动写入配置文件——你只需要在聊天里
粘贴一次。

**方式二：交互式配置。** 在终端运行一次：

```bash
python project-visual-generator/scripts/generate_assets.py --setup
```

按提示输入 API Key 和中转站地址（回车跳过可保留默认），保存到：

```
~/.zcode/project-visual-generator.json
{ "apiKey": "sk-...", "baseUrl": "https://你的中转站地址", "model": "gpt-image-2" }
```

**方式三：环境变量**（适合服务器/CI）：

```bash
export OPENAI_API_KEY="sk-..."          # Windows: setx OPENAI_API_KEY "sk-..."
export OPENAI_BASE_URL="https://中转站"  # Windows: setx OPENAI_BASE_URL "https://..."
```

读取优先级：命令行参数 > 环境变量 > 配置文件。`baseUrl` 带不带 `/v1` 都可以。
请勿把含 Key 的配置文件提交到任何仓库。

## 使用

安装后对 ZCode 说：

> 给这个项目生成图标和 GitHub 横幅

AI 会自动读取项目的 `package.json` / `pyproject.toml` / `README.md` 提取名称、简介、
技术栈，自行编写生图提示词并调用脚本。

也可以直接命令行调用：

```bash
python project-visual-generator/scripts/generate_assets.py \
  --name "MyProject" --desc "AI powered code reviewer" \
  --tech "Python AI CLI" --assets icon,banner \
  --out ./docs/assets --update-readme --icon-sizes 16,32,48,64,128,256,512
```

常用参数：

| 参数 | 说明 |
|---|---|
| `--assets icon,banner,illustration` | 要生成的资产（默认 icon,banner） |
| `--ratio 16:9` | 自定义画幅比例（1:1 / 16:9 / 9:16 / 2:1 等，最大 3:1） |
| `--res 1k/2k/4k` | 分辨率档位：自动映射到分档模型名（`gpt-image-2-1k/2k/4k`，长边 1024/2048/4096；超出 gpt-image-2 官方像素上限时自动钳制，如 4K 方图 → 2880x2880） |
| `--quality low/medium/high` | 生成质量与费用（默认 medium） |
| `--icon-sizes 16,32,...` | 多尺寸图标导出（需 Pillow） |
| `--update-readme` | 自动把横幅和图标插入 README 开头 |
| `--prompt-icon/--prompt-banner` | 覆盖内置提示词模板 |
| `--dry-run` | 只打印提示词不调用接口 |
| `--base-url` | API 中转地址 |

## 通用性

Skill 按标准 OpenAI Images API 编写，**不绑定任何中转站**：

- 请求体只发最简字段（model/prompt/n/size），扩展参数（`quality`/`background`）仅在
  显式指定时发送，且遇到 400 自动降级重试——兼容官方 API 和各类中转站
- `--res 2k` 等分档会先查询端点的 `/v1/models`：有 `gpt-image-2-2k` 这类分档变体才用
  （省钱的计费档位），没有就退回标准模型 + 显式尺寸
- 请求带浏览器 User-Agent 并支持 `--proxy` / 配置文件 `proxy` 字段走本地代理
  （应对 Cloudflare 风控和 CDN 抽风）
- 中转站忽略透明背景参数返回白底图时，自动用 Pillow 从边缘泛洪抠图（只抠背景，
  保留主体内部白色），图标输出真透明 RGBA；返回真透明则原样保留

## 资产规格

| 资产 | 尺寸 | 说明 |
|---|---|---|
| icon | 1024x1024，透明背景 | gpt-image-2 支持自定义尺寸与透明背景 |
| banner | 1280x640 | GitHub social preview 的 2:1 规格，直接生成无需裁剪 |
| illustration | 1200x624 | 宽高为 16 的倍数（gpt-image-2 的约束） |

## 与豆包方案的差异

原始设计按 DSH 插件规范（Node.js + skill.json）给出，本实现改为 ZCode Skill 规范
（SKILL.md + scripts/），并修正了几个技术问题：

1. `images.generate` 对 GPT Image 模型返回 `b64_json`，不支持
   `response_format: 'url'`（那是 DALL-E 的参数）——脚本直接解码 base64，同时兼容
   返回 url 的中转站。
2. 提示词不再写死在代码里，而是由 AI 按 `references/prompt-guide.md` 的构图规则现场
   编写，`--prompt-*` 参数传入；内置模板仅作兜底。
3. 增加了 `OPENAI_BASE_URL` 中转支持、失败重试、README 自动插入、多尺寸图标导出。
