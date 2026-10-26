# 0.1.0 安装包

首个 .ankiaddon 打包版本，包含当前全部正式功能、三套词库和来源授权文件。不是 AnkiWeb 发布，也不宣称自动更新。

构建：`python scripts/build_addon.py`，输出至 downloads。显式文件白名单排除个人数据、密钥、缓存、测试、运行环境及本机答辩材料。插件文件位于压缩包根目录，manifest.json 固定 package 为 cet_smart_assistant，与既有手动安装目录一致。新增正式模块时需更新白名单，升级时更新 human_version。

格式遵循 [Anki 官方分发说明](https://addon-docs.ankiweb.net/sharing.html)。在桌面 Anki 工具 → 插件 → 从文件安装，选包后重启。用户无需解压。

验证：87 项单元测试通过，包括压缩包 CRC、白名单、相同源文件重复构建一致、源码一致、三套词库哈希与条目数。另在本机 Anki 26.9.3 运行时调用实际 AddonManager.readManifestFile，清单通过；临时解包后全部模块语法检查通过，并成功加载 3815 / 5371 / 4974 条词汇。未操作用户当前账户或宣称完成安装对话框点击验收。AI 服务实连及新版词卡实机视觉验收的既有边界仍适用。

安装包与 SHA256 文件提交到 GitHub downloads 目录，README 提供直接下载入口。

## 0.1.1（2026-09-30）

新增每日任务草稿保存、撤销评价、进度条与继续学习。当前推荐下载 downloads/cet-smart-assistant-0.1.1.ankiaddon；保留 0.1.0 历史包。88 项测试及真实 Anki 清单解析、解包词库验证通过。安装方式相同，旧任务无需迁移即可读取。

## 0.1.2（2026-09-30）

新增可选错因、同方向复练提示及第二组语境。当前推荐 downloads/cet-smart-assistant-0.1.2.ankiaddon。89 项测试与实际 Anki 清单/词库验证通过；安装方式不变，旧记录兼容。

## 0.1.3（2026-09-30）

针对独立测试反馈修复空任务输入，小屏滚动、关闭入口和键盘默认按钮。推荐 downloads/cet-smart-assistant-0.1.3.ankiaddon。89 项单元测试、扩展 Qt 交互、Anki 包验证通过，详见 ux-review-013.md。

## 0.1.4（2026-10-09）

新增主窗口“本周学习回顾”。当前安装包为 downloads/cet-smart-assistant-0.1.4.ankiaddon。91 项测试通过，真实 Qt 与 Anki 清单/词库验证完成。

## 0.1.5（2026-10-19）

新增主窗口“备份本机学习资料”，导出插件本地 JSON 记录与已保存词语用法到 ZIP；压缩包说明备份范围和手动恢复方式。Anki 卡片/复习进度仍使用 Anki 集合备份，API 密钥不会打包。自动化验证覆盖内容、缺失文件、原子替换失败保护；95 项回归测试、安装包白名单、ZIP 结构与清单 JSON 检查通过。本次未在 Anki 桌面窗口重新进行安装点击验收。见 [本机资料备份说明](local-backup.md)。

## 0.1.6（2026-10-25）

将阅读 / 写作原创训练词由 12 个扩充到 36 个，新增词汇的基础专项卡共 72 张，并为每个词补充第二组每日练习语境；内置单词用法说明覆盖 40 词。示例用于搭配与语义练习，不是历年真题，也未进行考试词频统计。更新下载链接、SHA256 文件、版本清单和展示页。

验证记录：96 项回归测试通过，包含 36 个词的两方向卡片数量、每词第二组语境和内置指南覆盖检查；源码编译通过。构建后的 0.1.6 包通过 ZIP CRC、白名单清单、模块语法、解包后词库数量和训练内容导入检查。SHA256：`67fff67ad18cf58db3ce6cd5d4787d584e95be35e22a0633ece238afd3233727`，文件见 [安装包](../downloads/cet-smart-assistant-0.1.6.ankiaddon) 与 [校验文件](../downloads/cet-smart-assistant-0.1.6.ankiaddon.sha256)。当前执行环境没有 Anki 的 `anki` / `aqt` Python 包，因此本次未执行真实 Anki 后端或桌面安装点击验证；`tests/verify_training_backend.py` 和 `tests/verify_package.py` 可在 Anki 兼容运行环境继续验证。构建命令为 `python scripts/build_addon.py`。

## 0.1.7（2026-10-26）

增加本机学习资料恢复向导，包含 ZIP 文件白名单、CRC 和大小校验、运行时 JSON 格式校验、变更预览、恢复前资料备份、二次确认、原子写入与失败回滚。ZIP 中未包含的文件会保留，超出恢复大小上限的资料不会被导出成无法恢复的备份。11 项备份 / 恢复专项单元测试通过，覆盖恢复、未包含文件保留、坏数据和路径拒绝、损坏 ZIP 拒绝、大小限制、恢复前备份冲突和模拟磁盘失败后的回滚；`compileall` 通过。完整回归测试曾在受限沙箱内因 Python 新建临时目录后无法写入而中断，尚未取得全量结果。

构建包包含 31 个白名单文件，ZIP CRC、manifest 版本、包内源码语法与 SHA256 校验通过。SHA256：`7e5989c1ab00a07f3a5ea8add53f91d55386e675f88bfabe91802001f724229f`，见 [安装包](../downloads/cet-smart-assistant-0.1.7.ankiaddon) 和 [校验文件](../downloads/cet-smart-assistant-0.1.7.ankiaddon.sha256)。随后已在 Anki 26.9.3 安装 0.1.7 并重启；学习计划窗口和恢复入口正常加载，恢复文件选择器已打开后取消，未改动学习资料。

## 0.1.8（2026-10-26）

主窗口新增词汇库存统计，实时区分仍处于新卡状态的词汇总量与 Anki 调度器提供的今日新卡数量，并按四级、六级、雅思、自定义词汇牌组分别展示。父牌组今日额度使用 Anki 的 `deck_due_tree()` 结果，因此遵循 Anki 当前每日上限。统计仅覆盖助手约定的四类词汇牌组；其他牌组、专项训练卡不计入词汇总量。打开助手时读取一次，也可点“刷新词汇统计”重新读取。

验证记录：新增统计逻辑的 2 项单元测试通过，`compileall` 通过。安装包包含 32 个白名单文件，ZIP CRC、文件清单、manifest 版本和两次构建一致性检查通过；SHA256 为 `fe74b17011b422ba10d318b401efa9f18fdc3b45c318b88b60cdf1ce481a5c1a`，见 [安装包](../downloads/cet-smart-assistant-0.1.8.ankiaddon) 和 [校验文件](../downloads/cet-smart-assistant-0.1.8.ankiaddon.sha256)。全量单元测试在受限环境中未能完成：Python 临时目录写入被拒绝，备份和打包测试报权限错误，另有每日任务测试卡在临时文件创建；`verify_package.py` 需要 Anki 的 `aqt`，当前系统 Python 未安装该运行时。0.1.8 尚未在桌面 Anki 中安装验收。
