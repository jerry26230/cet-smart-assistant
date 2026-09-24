# CET 智能备考助手

软件工程课程项目，基于成熟开源软件 [Anki](https://github.com/ankitects/anki) 的插件机制进行二次开发，不修改 Anki 核心源码。

## 当前阶段：Task 002

通过“工具 → CET 智能备考助手”打开资料窗口，填写四级总分、听力、阅读、写作翻译、六级目标、备考天数和每日学习分钟数。支持输入校验、本地 JSON 保存和重新打开时自动回填。2026-09-24 已在 Windows + Anki 26.9.3 完成实机验证，详见 [Task 002 验证报告](docs/task002-verification.md)。

此前的最小插件验收保留在 [Task 001 验证报告](docs/task001-verification.md)，当前菜单已升级为资料窗口。成绩分析、学习计划、卡组联动和练习反馈尚未实现。

## 环境

- Windows + Anki Desktop（插件在 Anki 内置 Python 环境运行）。
- PyCharm 用于编辑源码，不需要单独安装 PyQt 或其他 Python 依赖。
- 已验证 Anki 26.9.3；其他版本尚未验证。

## 文件结构

```text
软件工程/
├── README.md
├── cet_smart_assistant/
│   ├── __init__.py       # 菜单注册与当前账户路径
│   ├── models.py         # 资料结构与校验
│   ├── data_service.py   # JSON 读写与原子保存
│   └── ui.py             # Qt 表单
├── tests/test_profile.py
└── docs/                 # 阶段验收报告及截图
```

## Windows 安装

1. 打开 Anki，选择“工具 → 插件 → 查看文件”（英文界面：Tools → Add-ons → View Files）。以该按钮打开的实际插件目录为准。
2. 关闭 Anki。
3. 将本项目的整个 `cet_smart_assistant` 文件夹复制进该插件目录。
4. 标准安装通常对应 `%APPDATA%\Anki2\addons21\cet_smart_assistant\__init__.py`。自定义数据目录可能不同。
5. 重新打开 Anki，进入用户配置。

不要只复制 `__init__.py` 到 `addons21` 根目录，也不要额外套一层同名目录。

## 运行与验收

1. 确认启动时没有插件错误。
2. 打开“工具”，确认出现“CET 智能备考助手”。
3. 点击菜单，打开“CET 智能备考助手 · 基本信息”窗口。
4. 输入演示数据：总分 470、听力 115、阅读 190、写作翻译 165、目标 500、90 天、每天 120 分钟。
5. 点击“保存资料”，预期显示“资料已保存”。
6. 关闭并重新启动 Anki，再次打开窗口，确认七项值完整回填。

首次没有资料时各项为空；关闭窗口不会自动保存修改。验证时已在当前账户保存上述 Student A 演示数据，可在界面中改为自己的资料。

## 输入与存储规则

- 分数范围：总分 0～710、听力/阅读 0～248.5、写作翻译 0～213、六级目标 1～710。
- 天数必须为 1～3650 的整数，每日分钟数为 1～1440 的整数；这是本阶段的产品输入范围。
- 空值、非数字、无穷值、超范围输入不能保存。分项合计与总分差异超过 10 分时提醒，仍允许保存；10 分是录入提醒阈值，不是考试评分规则。
- 每个 Anki 账户单独保存：`<Anki 账户目录>/cet_smart_assistant/user_data.json`。
- 本机验证路径：`%APPDATA%\Anki2\账户 1\cet_smart_assistant\user_data.json`。
- 保存采用同目录临时文件加原子替换，保留已有练习历史。读取损坏或不支持版本的文件时禁用保存，原文件保持不变。请备份后修复资料文件并重新打开窗口。
- 资料不通过 AnkiWeb 同步，也不包含在本项目 Git 中；备份时请单独复制资料目录。
- 当前记录的是手动输入的剩余天数，尚不自动随日期递减。

## 单元测试

在项目目录执行：

```powershell
python -m unittest discover -s tests -v
```

测试不依赖 Anki 或 Qt，覆盖范围校验、分数差异、JSON 往返、历史保留及失败保护。Windows 受限沙箱可能限制 Python 临时目录的访问；普通本机终端可运行上述测试。

## PyCharm 编辑方式

在 PyCharm 中打开本项目的“软件工程”目录，编辑对应模块。修改后关闭 Anki，将插件源码复制到 Anki 插件目录，再重启 Anki。资料在账户目录中，与插件源码分开保存。

不要通过 PyCharm 的 Run 直接运行插件入口：`aqt`、主窗口和菜单由 Anki 提供。编辑器若提示无法解析 `aqt`，不代表插件在 Anki 中无法运行。

## 启动失败时检查

- 菜单不出现：核对插件目录层级，确认插件已启用并已重启 Anki。
- 出现 `No module named aqt`：确认是在 Anki 内加载，而不是用普通 Python 执行文件。
- 启动时报错：保存完整错误信息和 Anki 版本，并核对复制的文件是否完整。
- 中文乱码：确保源文件保存为 UTF-8。

## 实现依据

菜单注册使用 `aqt.mw`、`QAction`、`qconnect` 和 `mw.form.menuTools.addAction`；提示框使用 `showInfo`，遵循 [Anki 官方最小插件示例](https://addon-docs.ankiweb.net/a-basic-addon.html)。

## 后续开发

Task 002 已完成。下一阶段为分项得分率计算与薄弱项识别，保持推荐算法与 GUI 分离，随后再开发学习计划。核心离线运行；复习调度交给 Anki。按阶段保留 Git 提交、测试结果及演示数据。

## Git 日志

本项目已建立独立本地 Git 仓库，默认分支为 `main`。在项目目录终端执行 `git log --oneline` 查看提交摘要，或执行 `git log --stat` 查看每次提交涉及的文件。当前提交分别记录最小插件实现与实机验收证据；未配置远程仓库或推送至 GitHub。
