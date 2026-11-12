# 镇守之森环境声音设计

上海大学《基础实践》期末作品 · 2026 年 11 月

以《原神》稻妻镇守之森为设计对象，使用轻柔的森林风声、虫鸣和远景流水构成底色，零星穿插鸟鸣、草丛窸窣和悠远铃音，表现哀怨、幽静与孤寂。瀑布与铃音作为画面外设计声源。

[完整设计与制作说明](DESIGN.md) 包含场景参考图、声音需求、素材制作、试听修改、Wwise 配置和测试截图。

## 打开作品

1. 直接播放 [九十秒混音](Preview/ChinjuForest_90s.wav)，了解整体听感。
2. 使用 Wwise **2025.1.11.9262** 打开 [ChinjuForest_Ambience.wproj](ChinjuForest_Ambience/ChinjuForest_Ambience.wproj)。首次打开会生成本地缓存。
3. 在 Events 中试听 `Play_ChinjuForest`，使用 `Stop_ChinjuForest` 停止。各层另有 `Play_WindLeaves`、`Play_Waterfall`、`Play_Insects`、`Play_Birds`、`Play_Rustles`、`Play_Bells`。
4. 在 Sessions → Soundcaster Sessions → Default Work Unit 打开 `ChinjuForest_Test`，六个模块分别控制各层。三种随机层包含首次延迟，播放后等待即可听到。总场景事件和各层模块均可独立试听，同时开启会叠加播放。
5. 使用 REAPER **7.85** 打开 [资产剪辑工程](Audio_Edit/ChinjuForest_Assets.rpp) 或 [六轨混音工程](Audio_Edit/ChinjuForest_Mix.rpp)。所有媒体路径为相对路径，移动时保留 Final 目录结构。

## 资产与播放

正式资产均为 48 kHz、24 bit、双声道 PCM WAV。

| 层 | 文件 | 时长 | 播放 | 最大预览距离 |
|---|---|---|---|---|
| 风与叶声 | AMB_WindLeaves_Loop | 60 秒 | 无限循环 | 全局 |
| 远处流水 | AMB_Waterfall_Loop | 60 秒 | 无限循环、3D 衰减 | 160 米 |
| 细微虫鸣 | AMB_Insects_Loop | 60 秒 | 无限循环 | 全局 |
| 鸟鸣 | SFX_Bird_01—03 | 各 4 秒 | Shuffle，结束后等待 12—25 秒 | 60 米 |
| 草丛窸窣 | SFX_Rustle_01—03 | 各 4 秒 | Shuffle，结束后等待 18—35 秒 | 15 米 |
| 日式铃音 | SFX_Bell_01—03 | 各 10 秒 | Shuffle，结束后等待 45—80 秒 | 120 米 |

首次延迟分别为鸟鸣 8—15 秒、草丛 15—25 秒、铃音 30—50 秒。Shuffle 保证三个变体轮换，启用避免紧邻重复。四条衰减曲线在最大距离的 0%、10%、50%、100% 处为 0、−3、−18、−60 dB。

本工程以 Wwise Authoring 为试听入口。米制距离用于课程原型，运行时需要游戏为各 emitter 提供实际坐标和 listener。混音预览安排了不同左右声像及远近音量，便于展示空间层次。九十秒试听使用固定编排，Wwise 按随机容器独立调度。

## 制作与验证

AI 素材使用 Stable Audio 官方服务，实际界面模型为 `default (Stable Audio 3)`。风声根据“雨噪感过强”和“再轻一些、叶声更少”的反馈重新生成并调整，最终混音获听感确认。四批生成使用 48 个免费积分，实际支出为零。

素材经 FFmpeg 与 Python 处理，保留选用源文件、滤波参数、交叉淡化和增益记录。REAPER 实际读取全部资产并原生渲染九十秒混音。Wwise 配置通过官方 WAAPI 完成，完整场景实际采样 604.92 秒，随机素材覆盖、停止行为与引擎距离衰减已检查。[处理记录](Audio_Edit/edit_decisions.json) · [测试说明](TESTING.md) · [来源授权](SOURCES.md)

## 文件内容

- `Assets/` 包含十二个正式 WAV。
- `Audio_Edit/` 包含资产工程、混音工程及处理记录。
- `ChinjuForest_Ambience/` 包含 Wwise 工程及所需 Originals。
- `Sources/` 包含采用的 AI 下载文件、自然录音选段和虫鸣源文件。
- `Preview/` 包含九十秒 REAPER 混音及编排表。
- `Evidence/` 包含格式、导入、播放、衰减测试数据及软件截图。
- `Images/` 包含有出处的场景参考图。
- `Report/` 包含按课程模板填写的完整 PDF，正文保留课程要求的身份栏。
- `Tools/` 包含素材处理、路径整理、ReaScript 和 WAAPI 脚本。

## 复现处理

素材处理脚本需要 Python、numpy、soundfile 和 FFmpeg。将 `FFMPEG` 环境变量设为本机可用的可执行文件。完整公园原录音可从 SOURCES.md 下载，文件名保留 `park_ambience_river.wav` 和 `park_ambience_birds.wav`。

```powershell
python Final/Tools/audio_assets.py build --downloads <公园原录音目录>
python Final/Tools/portable_reaper.py
python Final/Tools/audio_assets.py validate
```

处理脚本产生独立的 NumPy 预览。交付的 `ChinjuForest_90s.wav` 来自 REAPER 原生渲染。可在 REAPER 打开 Mix 工程后使用 Render，或通过 REAPER 的 `-renderproject` 命令渲染。重新运行 `reaper_verify_and_mix.lua` 会另建混音工程并渲染辅助文件，之后运行路径整理脚本即可恢复相对路径。

Wwise 需启用本机 WAAPI HTTP 8090。`wwise_project.py build` 配置对象，`import` 导入资产，`spatial_test.py` 读取实际引擎距离贡献。测试会播放声音并创建临时 emitter/listener，完成后清理。

## 提交材料

[报告 PDF](Report/ChinjuForest_Final_Report.pdf) · [完整作品说明](DESIGN.md)

邮件与智慧实习实训平台上传由学生完成。11 月 15 日前将 PDF 上传至“过程文档”。
