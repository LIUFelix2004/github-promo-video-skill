---
name: github-promo-video
description: 为任意 GitHub 账号生成一条 ≤28 秒的简历宣传视频：真实主页截图做封面（横切面平躺、由远到近动态立起）+ GitHub 白色仓库卡片（Star 数字滚动计数、README 总结逐条滑入）+ 纸条式结尾。全部文字本地渲染，零 AI 生成文字、零拼写错误。适用于"给这个 GitHub 做个宣传视频/简历视频/同款视频"类请求。
---

# GitHub 简历宣传视频（同款流水线）

成片结构（总时长 ≤28s，默认约 24.5s）：

1. **动态封面**（5.5s）：目标账号 GitHub 主页的真实截图，从"横切面平躺远景"连续透视变换到"直立倾斜近景"，浅色渐变地面 + 柔和投影，白闪转场。
2. **项目卡 ×3**（每张 6–6.5s）：GitHub 白色仓库卡，同款版式 — 仓库名、副标题、红/蓝大数字从 0 滚到真实 Star/Fork 数、4 条 README 总结逐条滑入、底部技术标签淡入。卡 1、2 是 Star 最高的两个项目；卡 3 是"更多项目"概览（大数字 = 仓库总数 / 近一年贡献数）。
3. **纸条结尾**（4.5s）：纸条逐条贴入（用户名 / @github / 昵称 / 代表作 · Star 数，末条红底），右侧大号圆形头像（粉色描边）放大入场。
4. **音乐**：用户提供的音频文件（见注意事项），无口播。

## 硬性规则

- **封面必须是真实捕获的主页帧**：用 `scripts/capture_frame.py` 自己截取，或用无头浏览器截图。禁止用 AI 生成/重绘主页（会编造仓库名、伪造数据），禁止直接套用他人提供的截图当封面而不说明。
- **所有上屏文字只来自 config**：数字、仓库名、总结条全部本地排版（PIL），不使用 AI 视频生成承载文字 —— 这是本流水线文字零错误、且全片不出现无关品牌 logo 的根本原因。
- **项目介绍必须基于 README 实读**：按 Star 排序取前 2–3 个项目，打开 README 提炼成每项 4 条一句话总结再写入 config；只拿仓库列表描述凑数不合格。Star 第 3 名若内容单薄（如 README 只有一行），并入卡 3 概览并在交付时说明。
- **交付前抽帧自检**：至少检查封面起始帧、每张卡成型帧、结尾帧；发现文字/数字问题必须修后再交付，并向用户如实说明残余瑕疵。

## 步骤

### 1. 调研账号
- 打开 `https://github.com/<user>?tab=repositories&sort=stargazers` 拿到 Star 排名与计数。
- 打开主页确认：显示名、followers、仓库总数、近一年贡献数、置顶仓库。
- 逐个打开 Star 前 2–3 名仓库的 README，写出每个项目 4 条总结（功能/形态/技术/特点），技术标签 4–6 个。

### 2. 准备素材（assets/）
```bash
python3 scripts/capture_frame.py <user> assets/page_frame.png   # 主页截图（真实帧）
curl -L https://github.com/<user>.png -o assets/avatar.png       # 头像（或从主页截取）
# BGM：把用户提供的音频放到 assets/bgm.m4a（可选）
```

### 3. 写 config
复制 `examples/config.example.json` 为 `config.json`，把第 1 步的真实数据与总结填进去（路径相对 config 所在目录或用绝对路径）。

### 4. 渲染
```bash
python3 scripts/render_promo.py --config config.json --out out.mp4
```
需要：Python 3 + Pillow + numpy、ffmpeg、Noto Sans CJK 字体（脚本会自动在常见路径查找）。

### 5. 抽帧自检后交付
用 ffmpeg 在 0.4s / 每段中点 / 结尾各抽一帧核对：数字与 Star 数一致、文字无错位、封面是真实页面、结尾纸条完整。把成片与一段"结构说明 + 已知瑕疵"一起发给用户。

## config 字段速览

| 字段 | 说明 |
|---|---|
| `username` / `display_name` | 账号名 / 显示名（结尾纸条用） |
| `page_frame` / `avatar` / `bgm` | 素材路径；`bgm` 可为 null（无音乐） |
| `cards` | 恰好 3 张：`{name, sub, n1, l1, n2, l2, rows[4], chips[]}`；n1/l1 红色大数字+标签（如 303 / Stars），n2/l2 蓝色（如 33 / Forks）；卡 3 可用 Repositories / Contributions |
| `finale_strips` | 4 条纸条文本，末条自动红底 |
| `durations` | 可选：`{cover, cards[3], finale}` 秒数，总和减转场后应 ≤28 |

## 注意事项

- **音乐版权**：仓库不附带任何 BGM。只能用用户自己提供或有权使用的音频文件，不要把从他人视频里提取的音轨再分发。
- 截帧服务（thum.io）首次请求返回占位图是正常排队现象，脚本已处理"取两次"。
- 全片不出现苹果等无关品牌 logo 是设计结果（本地渲染无外部素材），无需额外处理。
