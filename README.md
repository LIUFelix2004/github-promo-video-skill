# github-promo-video-skill

给任意 GitHub 账号生成一条 **≤28 秒的简历宣传视频**的 Agent Skill。

**效果**：真实主页截图做封面，从横切面平躺远景动态立起到近景 → 三张 GitHub 白色仓库卡（Star 数字滚动计数、README 总结逐条滑入、技术标签）→ 纸条式结尾 + 大头像。GitHub 白色主色调，全片文字本地渲染——**零 AI 生成文字、零拼写错误、不出现无关品牌 logo**。

![demo](demo.gif)

## 快速开始

```bash
# 依赖：Python 3 + Pillow + numpy、ffmpeg、Noto Sans CJK 字体
pip install pillow numpy

# 1. 抓素材
python3 scripts/capture_frame.py <username> assets/page_frame.png
curl -L https://github.com/<username>.png -o assets/avatar.png
# （可选）把你有权使用的音乐放成 assets/bgm.m4a

# 2. 写配置：复制 examples/ 里的示例，填入真实数据
#    —— Star 数、仓库名、总结条全部来自实读 README，不要编造

# 3. 渲染
python3 scripts/render_promo.py --config config.json --out out.mp4
```

## 工作原理

- **封面**：对真实截图逐帧做透视变换插值（PIL），页面从平躺的横切面姿态立起并放大，叠加柔和投影与浅色渐变地面。
- **卡片**：统一的仓库卡版式，大数字用缓动函数从 0 计数到真实值，总结条错峰滑入，标签最后淡入——节奏对标短视频宣传片，但每一帧都由代码精确绘制。
- **拼接**：ffmpeg `xfade`（首个转场为白闪，其余溶解），BGM 自动裁切并在结尾淡出。

为什么不用 AI 视频生成做这些段落？实测 AI 生成的画面文字必有拼写错误、数字拼不完整、还会混入无关 logo。本地渲染牺牲一点"实景感"，换来文字 100% 准确和视觉语言统一——这是这套流水线迭代多版后的结论，细节见 [SKILL.md](SKILL.md)。

## 配置说明

见 [SKILL.md](SKILL.md) 的字段速览表，完整示例在 [examples/config.liufelix2004.json](examples/config.liufelix2004.json)（2 张项目卡 + 1 张概览卡）和 [examples/config.yujunzhixue.json](examples/config.yujunzhixue.json)（3 张全是完整项目卡）。

## 注意

- 本仓库**不附带任何音乐文件**；请使用你自己提供或有权使用的音频。
- 封面截图必须是目标主页的真实捕获帧；不要用 AI 生成的页面图（会编造仓库与数据）。

## License

MIT
