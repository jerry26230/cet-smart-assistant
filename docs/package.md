# 0.1.0 安装包

首个 .ankiaddon 打包版本，包含当前全部正式功能、三套词库和来源授权文件。不是 AnkiWeb 发布，也不宣称自动更新。

构建：`python scripts/build_addon.py`，输出至 downloads。显式文件白名单排除个人数据、密钥、缓存、测试、运行环境及本机答辩材料。插件文件位于压缩包根目录，manifest.json 固定 package 为 cet_smart_assistant，与既有手动安装目录一致。新增正式模块时需更新白名单，升级时更新 human_version。

格式遵循 [Anki 官方分发说明](https://addon-docs.ankiweb.net/sharing.html)。在桌面 Anki 工具 → 插件 → 从文件安装，选包后重启。用户无需解压。

验证：87 项单元测试通过，包括压缩包 CRC、白名单、相同源文件重复构建一致、源码一致、三套词库哈希与条目数。另在本机 Anki 26.9.3 运行时调用实际 AddonManager.readManifestFile，清单通过；临时解包后全部模块语法检查通过，并成功加载 3815 / 5371 / 4974 条词汇。未操作用户当前账户或宣称完成安装对话框点击验收。AI 服务实连及新版词卡实机视觉验收的既有边界仍适用。

安装包与 SHA256 文件提交到 GitHub downloads 目录，README 提供直接下载入口。
