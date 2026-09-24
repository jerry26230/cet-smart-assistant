# CET 智能备考助手

软件工程课程项目，基于成熟开源软件 [Anki](https://github.com/ankitects/anki) 的插件机制进行二次开发，不修改 Anki 核心源码。

## 当前阶段：Task 001

仅注册“工具 → CET 智能备考助手”菜单，点击显示启动成功提示。成绩分析、学习计划、卡组联动和练习反馈均尚未实现；先通过 Anki 实机验收再进入 Task 002。

## 环境

- Windows + Anki Desktop（插件在 Anki 内置 Python 环境运行）。
- PyCharm 用于编辑源码，不需要单独安装 PyQt 或其他 Python 依赖。
- 实际 Anki 版本与实机运行结果尚待确认。

## 文件结构

```text
软件工程/
├── README.md
└── cet_smart_assistant/
    └── __init__.py
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
3. 点击菜单，预期弹出：

   ```text
   CET Smart Assistant is running successfully.
   ```

4. 关闭提示，再次点击，确认仍正常显示。
5. 重启 Anki，再次验证菜单和提示。

上述实机操作全部通过才算完成 Phase 0。源码检查不能代替 Anki 内实际运行验证。

## PyCharm 编辑方式

在 PyCharm 中打开本项目的“软件工程”目录，编辑 `cet_smart_assistant/__init__.py`。每次保存后，将修改后的插件文件夹复制到 Anki 插件目录，再重启 Anki。

不要通过 PyCharm 的 Run 直接运行插件入口：`aqt`、主窗口和菜单由 Anki 提供。编辑器若提示无法解析 `aqt`，不代表插件在 Anki 中无法运行。

## 启动失败时检查

- 菜单不出现：核对插件目录层级，确认插件已启用并已重启 Anki。
- 出现 `No module named aqt`：确认是在 Anki 内加载，而不是用普通 Python 执行文件。
- 启动时报错：保存完整错误信息和 Anki 版本，并核对复制的文件是否完整。
- 中文乱码：确保源文件保存为 UTF-8。

## 实现依据

菜单注册使用 `aqt.mw`、`QAction`、`qconnect` 和 `mw.form.menuTools.addAction`；提示框使用 `showInfo`，遵循 [Anki 官方最小插件示例](https://addon-docs.ankiweb.net/a-basic-addon.html)。

## 后续开发

实机验收 Task 001 后进入成绩输入与 JSON 保存阶段。推荐算法与 GUI 分离；核心离线运行；复习调度交给 Anki。按阶段保留 Git 提交、测试结果及演示数据。
