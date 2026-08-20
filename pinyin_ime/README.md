# 拼音候选查询 Hook 模块

本模块挂接游戏原有的字典候选接口，而不是修改最终姓名缓冲。拼音数据不再嵌入 `code.bin`，而是存放在 RomFS 中原版未使用的 `njubase2.a` 文件槽。

当前数据库由项目字形表与 Rime 单字拼音/词频数据生成，包含 409 个无声调拼音、4106 个可存档单字候选。每个读音最多保留游戏原生缓冲允许的 80 个候选，并按 Rime 词频排序。

例如：

```text
jie -> 接 / 借 / 解 / 節 / 姐 / 街 / 界 / 結 / 籍 / 皆 / 戒 / 介 ...
```

项目字形表会把 `節`、`結` 等存储字符显示成对应简体，因此游戏中预期候选开头为：

```text
接 / 借 / 解 / 节 / 姐 / 街 / 界 / 结 / 籍 / 皆 / 戒 / 介 ...
```

模块识别半角大小写字母和 CP932 全角大小写字母；`lv`、`nv` 等用 `v` 表示 `ü`。数据库中没有的输入完整回退到原版 iWnn 查询。

## 挂钩位置

- `0x001F2B54`：输入组合串，返回候选数量。
- `0x001F2B14`：输入候选索引，把对应 CP932 字符串写入游戏的 0x30 字节候选项。
- 注入代码位于已验证全零的 code cave `0x0052D5A0`。
- 原版加载的 `32/njpsq2Memo.a` 路径被改为 `32/njubase2.a`。
- 字典路径拼接函数只在加载 `32/njubase2.a` 时使用更新 RomFS 的 `eom:` 前缀；其他 iWnn 字典继续使用基础 RomFS 的 `rom:` 前缀。
- 新 `njubase2.a` 由脚本生成最小 NJDC 容器，并在容器结尾追加 `PYDB`，不读取或包含任何基础字典文件。
- 拼音映射源为构建时生成的 `temp/pinyin_db.json`；`scripts/build_pinyin_db.py` 负责生成覆盖文件。

候选栏显示、触摸/方向键选择、确认以及写入姓名继续使用游戏原有实现。

## 构建与验证

`scripts/replace_code_bin.py` 会调用 `scripts/build_pinyin_ime.py`，使用 devkitARM 编译并安装三个 ARM 跳转，同时把 memo 字典路径重定向到更新 RomFS 中的 `njubase2.a`。安装前会校验三个挂钩点、原始路径字符串和 code cave，避免对不匹配版本静默打补丁。

`scripts/build_pinyin_db.py` 只根据 `pinyin_db.json` 生成最小 NJDC 容器和 `PYDB` 数据，不需要外部依赖。输出位置为：

```text
out/00040000001CBE00/romfs/iWnn/dic/JA_small/32/njubase2.a
```

## 预编译缓存

`pinyin_ime/prebuilt/` 保存 ARM 载荷。构建时的选择规则：

- 检测到 devkitARM 时，从汇编源码重新生成 ARM 载荷。
- 缺少 devkitARM 时，校验并使用预编译 ARM 载荷。
- 汇编源码已变化而缓存未更新时直接报错，不会使用过期缓存。
- 外置拼音数据库始终根据 `pinyin_db.json` 重新生成，不使用预编译缓存。

在具备 devkitARM 的开发机上刷新缓存：

```powershell
python scripts/build_pinyin_ime.py --precompile
```

只检查缓存是否与当前源码一致：

```powershell
python scripts/build_pinyin_ime.py --check-prebuilt
```
