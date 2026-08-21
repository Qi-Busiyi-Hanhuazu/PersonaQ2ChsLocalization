# 拼音数据来源

`pinyin_db.json` 由 `scripts/generate_pinyin_mapping.py` 生成，使用以下上游数据：

- [Rime 朙月拼音](https://github.com/rime/rime-luna-pinyin) 的 `luna_pinyin.dict.yaml`：单字拼音及多音字比例。
- [Rime 八股文](https://github.com/rime/rime-essay) 的 `essay.txt`：候选常用度排序。
- 本项目生成的 `out/char_table.json`：显示汉字到游戏 CP932 存储码位的映射。

生成命令：

```powershell
python scripts/generate_pinyin_mapping.py
```

每个读音最多保留 80 个单字候选，以匹配游戏原生候选缓冲区数量。生成结果只包含当前项目字体和码表能够显示、能够写入姓名存档的字符。

上游授权分别见对应仓库；Rime 朙月拼音仓库包含其数据来源说明，Rime 八股文使用 LGPL-3.0。
