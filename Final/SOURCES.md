# 素材来源与授权

核对与制作日期为 2026 年 11 月 12 日。文件名对应 `Assets/`，具体选段和处理参数保存在 `Audio_Edit/edit_decisions.json`。

## 自然录音

| 正式资产 | 作者与作品 | 源格式及选用方式 | 页面授权 |
|---|---|---|---|
| AMB_Waterfall_Loop | Thimras，Park ambiences，park_ambience_river.wav | 48 kHz 双声道公园河流录音，选取 30—100 秒并循环处理 | CC0 |
| SFX_Bird_01—03 | Thimras，Park ambiences，park_ambience_birds.wav | 48 kHz 双声道录音，选取三个相互分离的 4 秒片段 | CC0 |
| AMB_Insects_Loop | Wolfgang_，Crickets Ambient Noise - loopable，crickets_1.mp3 | 约 11.45 秒 MP3，解码、滤波、重采样及循环处理 | CC0 |

Park ambiences 录于澳大利亚阿德莱德。三个鸟鸣文件是不同录音片段。河流录音含水流越过低落差的声音，经处理用于远景瀑布表现。保留了足够制作本作品的选段，全长原录音可通过以下链接取得。

[Park ambiences 来源与 CC0 标注](https://opengameart.org/content/park-ambiences) · [河流原文件](https://opengameart.org/sites/default/files/park_ambience_river.wav) · [鸟鸣原文件](https://opengameart.org/sites/default/files/park_ambience_birds.wav)

[Crickets 来源与 CC0 标注](https://opengameart.org/content/crickets-ambient-noise-loopable) · [虫鸣原文件](https://opengameart.org/sites/default/files/crickets_1.mp3) · [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)

## AI 生成

风声、三条草丛和三条铃音通过 Stable Audio 官方网站生成。界面实际模型标签为 `default (Stable Audio 3)`，质量 `standard`，seed 为 `random`，steps 和 cfg_scale 为 `auto`。生成页面未提供实际随机种子数值。采用的三类实际请求已保存为 `Evidence/generation_requests.json`，包含完整英文提示词。

| 批次 | 时长与数量 | 积分 | 采用情况 |
|---|---|---|---|
| 首批风声 | 30 秒 × 4 | 16 | 因密集且有雨噪感而弃用 |
| 铃音 | 10 秒 × 3 | 12 | 三条均采用 |
| 草丛窸窣 | 4 秒 × 3 | 12 | 三条均采用 |
| 轻柔风声 | 30 秒 × 2 | 8 | 采用 Take 1 的安静片段 |

共使用 48/50 免费积分，剩余 2，实际支出 0 元。采用的 AI 下载文件为 **44.1 kHz、16 bit、双声道 WAV**，正式资产经处理转换为 48 kHz、24 bit。音频规格转换记录在处理脚本和报告中。

Stable Audio 的官方授权说明允许用户分发独立生成音频。本项目用于课程作品及公开工程提交，AI 文件按生成服务适用条款处理。CC0 标记对应上表的自然录音。保留来源及服务说明，便于复核。[Stable Audio 官方服务](https://stableaudio.com/) · [官方使用授权说明](https://kb.stability.ai/knowledge-base/stable-audio-commerical-and-usage-licensing)

## 编辑与工具

REAPER 7.85 评估版用于工程检查与最终混音原生导出。FFmpeg、Python、numpy 和 soundfile 用于确定性素材处理与检测。Wwise 2025.1.11.9262 通过官方 WAAPI 配置和测试，工程保留可编辑层级。

场景名称及视觉设定来自《原神》稻妻镇守之森，相关权利归米哈游。本作品的音频为 AI 生成或上述 CC0 素材加工。铃音与瀑布为画面外创意设计。

## 场景参考图片

`Images/ChinjuForest_Reference.png` 为本人在《原神》中拍摄的镇守之森实机截图，选自本次提供的“素材图”文件夹，原始文件名为 `20261112101048.png`。图片按原始内容收录，用于课程场景分析，游戏画面相关权利归米哈游。
