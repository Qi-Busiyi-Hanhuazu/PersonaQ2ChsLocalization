# AGENTS.md

## 项目概述

《女神异闻录Q2 新电影迷宫》（Persona Q2，3DS）的简体中文本地化补丁项目。构建产物是 Luma 重定向补丁（`out/00040000001CBE00/`，标题 ID `00040000001CBE00`）和 `.cia` 安装包，GitHub Actions 自动发布开发版到 `publish` tag。仓库只包含汉化所需的最小资源，不含游戏 ROM。

## 常用命令

**构建**（Windows + PowerShell；前置条件：Python 3.10+、.NET 8 SDK，`requirements.txt` 依赖已安装）：

```powershell
pip install -r requirements.txt
. scripts\build_patch.ps1
```

构建需要 `original_files/` 下的游戏解密文件（用户自备）和 `files/fonts/` 下的字体（`*.ttf` 被 gitignore；CI 用 `scripts/download_fonts.ps1` 下载 MiSans/思源黑体，主字体 `FZFWQingYinTiJWB.ttf` 需自行授权获取）。

**代码检查**（提交前运行）：

```powershell
pre-commit run --all-files
```

钩子包括：行尾统一 LF（JSON 无末尾换行要求除外）、去尾随空格、ruff 导入排序和格式化（`indent-width=2`、`line-length=120`），全部排除 `original_files/`。项目没有测试框架，验证方式是完整构建后在实机/模拟器测试。

## 构建流水线

`scripts/build_patch.ps1` 串联整个流水线（所有 Python 脚本均从仓库根目录运行，共享 `scripts/helper.py` 中的路径常量和工具函数）：

1. **解包**：`bin/3dstool/3dstool.exe` 解包 `original_files/00000002.app`，CRI `cpkmakec` 解包 `patch101.cpk`/`patch102.cpk`/`addition_files.cpk` 到 `unpacked/`。
2. **编译助手**：`dotnet publish` 编译 C# 子模块 `bin/PersonaQ2ChsLocalizationHelper`（基于 PersonaEditor 库），其 `export`/`import` 命令负责把游戏中的文本容器（`.bf`/`.bmd`/`.ctd`/`.ftd`/`.qtd`/`.tbl`）在二进制和 JSON 之间转换。
3. **导出文本**：`export_code_bin.py`（`code.bin` 中硬编码字符串，另有 `helper.py` 的 `HARDCODED_TEXTS_CODE_BIN` 替换表）、`export_ctd.py`、`export_tbl.py`（道具/技能表）→ `convert_messages_to_json.py` 把消息 JSON 拆成逐行条目，丢弃占位垃圾文本（`TRASH_PATTERN` 匹配）。
4. **合并翻译**：`import_csv_to_json.py` 把 `texts/zh_Hans/` 的翻译合并进工作副本 → `generate_char_table.py` 生成码表 → `convert_json_to_messages.py` 把译文编码回 cp932 消息格式 → `import_*.py` 写回二进制，C# 助手 `import` 打包。
5. **字体**：见下文“字体与码表”。
6. **重打包**：`cpkmakec` 重建 CPK，`makerom` 生成 `.cia`。

其他辅助脚本：`remove_duplicate_files.py`/`copy_duplicate_files.py` 按 `files/duplicate_files.json` 对游戏内重复文件去重翻译；`import_official_names.py` 用 `files/official_translations/`（P5R/P4G/P3P 等官方中文版的译名 CSV）自动覆盖匹配的原文；`convert_csv_to_xlsx.py` 把 texts JSON 转成 xlsx 供人工翻译。

## 翻译文件格式（texts/）

`texts/ja/` 与 `texts/zh_Hans/` 是平行 JSON 树，路径对应游戏内文件（如 `init/cmptable.bin_camp_msg.bmd.json`）。**ja 是导出产物（translation == original），只改 zh_Hans**。每条目字段：

- `key`：文件内唯一 ID（消息行如 `line_123_0`，code.bin 用地址 `offset_XXXXXXXX_n`）
- `original`：原文
- `translation`：译文
- `stage`：翻译状态标记，由外部翻译流程维护（`import_official_names.py` 自动匹配官方译名时置 9）
- `context`：翻译备注/机翻参考

游戏文本以 cp932（Shift-JIS）编码。翻译时控制字节写作 `{XX XX}` 形式，常见序列在 `helper.py` 中映射为易读占位符：`[P3姓]`/`[P4名]`/`[P5全]`（主角名）、`[占位A xx]`、`[颜色 xx]`、`[道具 xxxx]` 等；译文中必须使用占位符形式，导入时由 `convert_back_special_controls` 还原。`convert_zh_hans_to_shift_jis` 负责把译文按码表编码回 Shift-JIS（数字/字母转全角，不在码表中的字符替换为 `?` 并告警）。

## 字体与码表

游戏字体是 BCFNT 格式的 12×12/13×13 点阵字体（`font/seurapro_*_*.bcfnt`）。Shift-JIS 码位不足以放下全部简体字，流水线的处理策略：

1. `generate_char_table.py` 扫描全部译文用字：cp932 已有汉字直接复用；简体字经 `files/zh_hans_2_kanji.json` 映射到日文汉字的码位；仍不够则从 cp932 未分配码位中取。结果写入 `out/char_table.json`（码位→简体字），随构建产物发布（供模拟器显示日文存档名字用）。
2. `create_new_font.py` 用 fontTools + Pillow 按码表渲染字形，`bin/3dstools/bcfnt.py` 打包回 BCFNT。

## 目录职责

- `files/`：汉化资源——`fonts/`（字体及 P3P/P4G/P5R 码表）、`images/`（已翻译贴图，PNG + 打包好的 `.ctpk`，构建时由 `copy_images.py` 拷入补丁）、`replace/`（整体替换文件）、`official_translations/`、`zh_hans_2_kanji.json`、`duplicate_files.json`。
- `bin/`：两个 git 子模块——`PersonaQ2ChsLocalizationHelper`（C#/.NET 8 文本格式工具，改动需 push 子模块仓库并更新引用）和 `3dstools`（Python 的 BCFNT 等 3DS 格式工具）；另有直接提交的二进制工具 3dstool、makerom、CRI cpkmakec。
- `original_files/`、`unpacked/`、`temp/`、`out/`、`maintenance/`：均被 gitignore。`unpacked/`/`temp/` 是构建中间产物；`maintenance/` 是一次性维护脚本（更新 CIA、贴图放大等），不属于构建流程。

## 注意事项

- `XZ_LANGUAGE` 环境变量可切换目标语言（默认 `zh_Hans`）。
- 构建脚本假定 Windows 环境；`build_patch.ps1` 会自动编译 C# 子模块，改完子模块后无需手动 publish。
- 提交前确保 texts 下的 JSON 是 LF 换行（pre-commit 会修正）。
