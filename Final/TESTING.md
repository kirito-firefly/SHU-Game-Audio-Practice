# 制作检查与试听记录

检查日期为 2026 年 11 月 12 日，使用 Wwise 2025.1.11.9262、REAPER 7.85/x64。原始数据保存在 `Evidence/`。

## 资产检查

十二个正式 WAV 全部满足 48 kHz、24 bit PCM、双声道。三个循环各 60 秒，三个鸟鸣各 4 秒，三个草丛各 4 秒，三个铃音各 10 秒。全部无削波，整体 RMS 高于静音判定阈值。每个文件均记录 SHA256、峰值、RMS 和时长。三个循环使用交叉淡化处理接缝，报告另记录首末采样差值。[检测数据](Evidence/asset_validation.json)

REAPER 实际打开全部十二个媒体源，均在线且为 48 kHz 双声道。六轨混音由 REAPER 原生 `-renderproject` 导出，90 秒、48 kHz、24 bit、双声道，峰值约 −9.77 dBFS，RMS 约 −28.81 dBFS，削波采样为零。两个 RPP 的媒体路径已转换为相对路径。[工程检查](Evidence/reaper_validation.json) · [渲染检查](Evidence/reaper_render.json)

Wwise Originals 中的十二个 WAV 与正式资产逐字节一致。每个 Sound 保留一个激活 AudioFileSource，重复导入修复后，通过 `WwiseConsole verify --abort-on-load-issues`，退出码为 0。Soundcaster 保存六个独立层模块，并已重新打开核对。[源文件一致性](Evidence/source_consistency.json) · [Soundcaster 截图](Evidence/wwise_soundcaster.png)

## 完整场景播放

通过官方 WAAPI 启动 `Play_ChinjuForest`，在 Wwise Authoring 实际引擎中采集 **604.92 秒、1194 次**声部快照。采样约每 0.5 秒一次，采样从场景已经播放时开始。

- 风声、瀑布、虫鸣在每一次快照中均保持非虚拟声部。
- 九个随机文件全部出现，三组均覆盖三个变体。
- 根据相邻起点减去文件时长估计等待时间，鸟鸣为 12.275—24.474 秒，草丛为 20.316—34.577 秒，铃音为 60.015—76.386 秒，落在所设随机范围内。由于采样粒度，区间判断允许 0.8 秒误差，排除首个不完整间隔。
- 执行 `Stop_ChinjuForest` 后等待两秒，场景 transport 显示 stopped，声部列表为空。

初始延迟通过保存的随机器配置核对，首次触发的精确时间未在本次完整快照起点处测量。[完整采样](Evidence/full_scene_samples.jsonl) · [汇总](Evidence/playback_summary.json) · [停止测试](Evidence/stop_test.json) · [配置](Evidence/project_configuration.json)

## 距离衰减

注册独立 emitter 与 listener，通过 `ak.soundengine.setPosition` 改变实际坐标。读取 Voice Inspector 的声部贡献，四类声源在 0%、10%、50%、100% 最大距离处的相对音量分别约为 **0、−3、−18、−60 dB**，数值误差小于 0.02 dB。

公开测试副本中的临时 emitter 编号已映射为通用编号 1001，用于去除个人标识；距离、音量贡献与测试结果保持原值。后续测试脚本也改用通用编号。

| 层 | 检查距离，米 | 实际引擎总增益，dB |
|---|---|---|
| 瀑布 | 0 / 16 / 80 / 160 | −7 / −10 / −25 / −67 |
| 鸟鸣 | 0 / 6 / 30 / 60 | −12 / −15 / −30 / −72 |
| 草丛 | 0 / 1.5 / 7.5 / 15 | −9 / −12 / −27 / −69 |
| 铃音 | 0 / 12 / 60 / 120 | −10 / −13 / −28 / −70 |

在 Wwise 衰减编辑器中另外播放瀑布层，拖动距离预览游标核对近、中、远距离，图中衰减水平线及输出表头随距离变化。API 数值测试与界面预览共同验证位置变化对播放音量产生影响。[引擎原始贡献](Evidence/spatial_test.json) · [衰减曲线](Evidence/wwise_attenuation_waterfall.png) · [近距离预览](Evidence/wwise_preview_near.png) · [中距离预览](Evidence/wwise_preview_mid.png) · [远距离预览](Evidence/wwise_preview_far.png)

## 听感修改

首批风声反馈为“太杂太嘈杂了，像雨声”。重新生成轻柔风声后，再根据“再轻一些、叶声更少”的反馈，选取源文件 1—5.5 秒、18.5—23.5 秒的安静部分，以 0.25 秒交叉淡化衔接，将低通降至 1100 Hz、RMS 上限降至 −33 dBFS。最终完整混音反馈为“差不多了。环境的整体风格是哀怨轻柔的”。

本次十分钟测试记录声部连续性、随机调度和停止结果，九十秒混音用于人的整体听感确认。循环接缝已经处理，完整试听可继续作为复核入口。

## 报告检查

期末报告按提供的课程 DOCX 模板填写，保留标题、学期、身份栏、章节及提交要求，评分留空。正文包含完整平时调研、完整作品说明、可点击的完整链接和六张场景/制作图片；场景参考图注明外部出处，软件截图来自实际工程。原模板哈希未变，副本修改 document.xml、链接关系与图片类型声明，新增六张图片和页码，其他原有包内文件保持一致。正文采用 12 磅等线、1.2 倍行距，图注与表格采用 10—10.5 磅。PDF 由 Microsoft Word 导出，并用 Poppler 逐页渲染检查。公开目录使用通用文件名，可编辑 DOCX 与邮件正文保存在本地。[模板保留记录](Evidence/report_template_preservation.json)
