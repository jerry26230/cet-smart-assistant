# Android 独立 App 首版记录

日期：2026-10-28 · 版本：0.1.0

## 目标与范围

在保留现有 Anki 桌面插件的同时，新增一款不依赖 Anki 的 Android 应用。首版面向 Android 手机和平板，数据保存在应用私有 SQLite 数据库中，不要求注册、联网或提供 AI API。

## 已实现

- 首次启动导入四级、六级、雅思三套内置词库，共 14,160 条；词库文件保留原始授权、来源及 SHA-256 记录。
- 提供离线翻卡、释义检索、四级/六级/雅思切换。
- 新卡每日每套限 20 个；复习卡优先，清楚展示已学、总未学习、待复习和今日额度。
- 自评选项为“忘了 / 有点难 / 记住了 / 很熟”，使用独立的简化间隔规则。
- 可设置考试日期、每日学习分钟数和重点专项，自动生成倒计时和时间分配。
- 查看最近七天学习记录和词库进度。
- UI 按手机与平板宽度调整，学习数据留在本机。

## 工程与构建

原生 Android：Kotlin、Jetpack Compose、SQLite。`minSdk=26`，`targetSdk=34`。GitHub Actions 在更新 Android 源码后构建并上传 `app-debug.apk`，Artifact 保留 30 天。安装和构建步骤见 [Android App 指南](../android/README.md)。

当前工作电脑没有 Android SDK/Gradle，不能在本机编译或连接真实平板；本地 Python 回归测试不是 Android 构建验证。提交后应以 GitHub Actions 构建结果确认 APK，再在 DBR-W10 实机安装验收。

## 已知边界

- 0.1.0 首版聚焦词汇复习、倒计时和计划；阅读/写作语境训练、专项练习历史、备份恢复、AI 和可选 AnkiDroid 导出尚未移植。
- 新词和复习间隔采用简单透明规则，不等同于 Anki/FSRS，当前不承诺最优记忆效果。
- DBR-W10 是 HUAWEI MatePad 11 2023。APK 是否可安装还受实际 HarmonyOS 版本和华为 APK 兼容层支持情况影响；需在设备上验收，系统拒绝时再转做鸿蒙原生 HAP。
- 首版是 Android debug APK，用于侧载试用，不是华为应用市场发布包。

## 验证状态

- [x] 现有桌面项目 105 项 Python 单元测试通过。
- [x] Android 词库数量、SHA-256 与插件来源记录一致：四级 3,815、六级 5,371、雅思 4,974。
- [x] `git diff --check` 无空白错误。
- [ ] Android Gradle 构建：等待推送后的 GitHub Actions。
- [ ] DBR-W10 安装与触控流程：等待拿到 APK 后实机验收。
