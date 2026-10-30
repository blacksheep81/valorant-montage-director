# Valorant Montage Director

为普通玩家的 Valorant / 无畏契约录屏设计短篇炫酷 montage 的 Agent Skill。

单杀、双杀、甩枪和身法处理都可以成为素材；默认设计 30–60 秒精剪，按音乐与素材调整。

## 能做什么

- 分析参考片，区分实际观察与设计建议。
- 挑选素材、安排音乐锚点、变速、转场、文字与声音处理。
- 提供五种风格及各自可独立复制的完整 prompt。
- 在 Agent 已具备剪辑工具时指导制作、预览和验收。

| 风格 | 表现方向 |
| --- | --- |
| 柔光情绪 | 温柔音乐与利落枪法的反差 |
| 回忆拼贴 | 画中画、闪回与匹配剪辑 |
| 冷色卡点 | 切分节奏、变速和集中冲击 |
| R&B 律动 | 松弛弹性，让枪声参与节奏 |
| 空灵爆发 | 氛围铺垫与视觉高潮 |

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
- [参考视频与证据状态](references/reference-videos.md)。

## 当前状态与限制

这是指导型 Skill，不自带视频编辑器、自动击杀识别器或渲染引擎，也不保证任何模型仅凭提示词就能输出视频。实际制作依赖所用 Agent 的视频、音频与剪辑能力。

五种风格目前是创作提案，并非对参考视频完成实看后的分类。参考页面信息已核对，其中一条已验证可播放，但完整逐镜分析和音频卡点分析尚未完成。文件结构已经校验，尚未以真实素材完成端到端剪辑验证。

仓库仅提供原创工作流、提示词和参考链接，不包含第三方视频或音乐。使用素材时需具备相应权限。本项目与 Riot Games 无隶属关系。
