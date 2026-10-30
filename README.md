# Valorant Montage Director

为普通玩家的 Valorant / 无畏契约录屏设计短篇炫酷 montage 的 Agent Skill。

单杀、双杀、甩枪和身法处理都可以成为素材；默认设计 30–60 秒精剪，按音乐与素材调整。

## 能做什么

- 分析参考片，区分实际观察与设计建议。
- 挑选素材、安排音乐锚点、变速、转场、文字与声音处理。
- 提供八种风格及各自可独立复制的完整 prompt，附实测节奏基准。
- 自带 `scripts/analyze_montage.py`，用 ffmpeg 测参考片或成片的剪点、镜头长度、闪白和响度。
- 在 Agent 已具备剪辑工具时指导制作、预览和验收。

| 风格 | 表现方向 |
| --- | --- |
| 柔光情绪 | 温柔音乐与利落枪法的反差 |
| 回忆拼贴 | 画中画、闪回与匹配剪辑 |
| 冷色卡点 | 切分节奏、变速和集中冲击 |
| R&B 律动 | 松弛弹性，让枪声参与节奏 |
| 空灵爆发 | 长镜头铺垫，后段越亮越密 |
| 歌词排版 edit | 一词一镜，大字被手臂/枪遮挡（TikTok 流行做法） |
| 击杀反馈卡点 | 15–30 秒，击杀图标和音效当节拍 |
| 整活梗向 | 保留 HUD，标注与定格制造笑点 |

## 安装到 Codex

将本仓库克隆到用户级 Skills 目录：

```bash
git clone https://github.com/blacksheep81/valorant-montage-director.git ~/.codex/skills/valorant-montage-director
```

如果目标目录已存在，请先检查已有内容，避免覆盖。新建聊天后调用：

```text
用 $valorant-montage-director，把我提供的素材做成35秒冷色卡点风。
先分析素材和音乐，再给出时间线与预览。
```

也可以只生成方案：

```text
用 $valorant-montage-director，分别给我柔光情绪和R&B律动的剪辑方案与prompt。
```

## 文件

- [SKILL.md](SKILL.md)：Agent 工作流与验收要求。
- [五套风格与完整 Prompt](references/styles-and-prompts.md)。
- [参考片实测记录](references/reference-videos.md)：11 条 B站 / TikTok 作品的测量与观察。
- [scripts/analyze_montage.py](scripts/analyze_montage.py)：节奏分析脚本，只依赖 Python 标准库和 ffmpeg。

## 当前状态与限制

这是指导型 Skill，不自带视频编辑器、自动击杀识别器或渲染引擎，也不保证任何模型仅凭提示词就能输出视频。实际制作依赖所用 Agent 的视频、音频与剪辑能力。

2026-10-31 实际播放并逐帧采样了 11 条参考（B站 7 条、TikTok 4 条），风格已按实测修订，证据等级见参考记录。抖音因需登录尚未实测；TikTok 音轨未取得，只有画面数据。R&B 律动目前没有对应的实测参考。尚未以真实素材完成端到端剪辑验证。

仓库仅提供原创工作流、提示词和参考链接，不包含第三方视频或音乐。使用素材时需具备相应权限。本项目与 Riot Games 无隶属关系。
