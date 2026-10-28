# CET 智能备考 Android App

这是面向 Android / 华为平板的独立应用，不要求安装 Anki。首版支持离线词汇学习、复习排期、考试倒计时与每日学习计划。

## 当前功能

- 安装后首次启动，将四级、六级、雅思三套内置词库写入本机 SQLite 数据库。
- 词汇学习按“到期复习优先，再学习今日新词”组织；每套词库每日最多安排 20 个新词。
- 每次翻卡后可选择“忘了、有点难、记住了、很熟”，应用根据选择安排后续复习日期。
- 分别显示已学量、总未学习量、待复习量和今日新词额度。
- 可设置考试日期、每日学习分钟数和专项重点，倒计时与每日时间安排在本机计算。
- 最近七天复习次数、首次学习量和各词库进度保存在本地。
- 不需要网络、Anki、账号或 API Key；学习记录不会上传服务器。

复习间隔是本项目的简化规则，不宣称复刻 Anki/FSRS 的调度效果。后续可以在这个原生 App 上继续加入阅读/写作语境训练、专项练习记录、备份恢复、可选 AI 和 AnkiDroid 卡片导出。

## 生成 APK

仓库中的 GitHub Actions 会在 `android/` 内容更新到 `main` 后自动生成 debug APK。构建成功后，在该仓库的 **Actions → Android APK → 对应运行 → Artifacts** 下载 ZIP，解压后取得 `app-debug.apk`。

也可以在安装了 JDK 17、Android SDK 36 和 Gradle 8.13 的电脑上执行：

```powershell
gradle --no-daemon -p android :app:assembleDebug
```

APK 输出在 `android/app/build/outputs/apk/debug/app-debug.apk`。debug APK 使用调试签名，适合本人侧载体验；它不是应用市场发布包。未来更新 debug 包时，保留相同签名即可覆盖安装。

## 安装到 DBR-W10

DBR-W10 对应 HUAWEI MatePad 11 2023。可先在平板的“设置 → 关于平板”确认 HarmonyOS 版本。将 APK 下载/传到平板，在文件管理器中打开并按系统提示安装；若系统拒绝该 APK，需以这台设备上 HarmonyOS/卓易通的实际支持情况为准，届时再评估鸿蒙原生包。

安装后直接打开“CET 智能备考”。首次导入三套词库需要几秒钟，完成后即可离线使用。

## 词库来源

词库 JSON、许可证、来源说明和校验摘要与桌面插件使用相同来源，位于 `app/src/main/assets/vocabularies/`。数据来源及授权见该目录中的 `NOTICE.md`、`LICENSE` 和 `provenance.json`。
