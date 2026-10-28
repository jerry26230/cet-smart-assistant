# 数据来源与版权声明 / Data Source & Attribution

## 词库数据来源

本仓库所有词库 JSON 均由 **ECDICT** 生成：

- 项目：ECDICT — Free English to Chinese Dictionary Database
- 作者：Linwei (skywind3000)
- 仓库：https://github.com/skywind3000/ECDICT
- 许可证：**MIT License**

## MIT License 原文

```
MIT License

Copyright (c) 2025 Linwei

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 词库派生规则（全部客观、可复现）

| 词库 | 派生规则 |
|---|---|
| cet4 / cet6 / kaoyan / toefl / ielts_core / gre | ECDICT 按考试大纲的事实性标注（tag 字段） |
| *_high_freq | 对应大纲词汇 ∩ 语料库词频（bnc/frq 字段）排名前 N |
| ielts_basic | 雅思词汇 ∩（牛津 3000 ∪ 柯林斯 ≥3 星） |
| ielts_advanced | 雅思词汇 − 基础词 |
| gmat | 学术英语大纲词汇（gre tag）剔除牛津 3000 后按词频取前 3000，与 GMAC 官方无关 |
| sat | 学术英语大纲词汇（cet6/toefl/gre tag）剔除牛津 3000 后按词频取前 4500，与 College Board 官方无关 |

生成脚本见 WordTyper 主仓库 `scripts/generate_from_ecdict.py`。

## 商标声明

CET、IELTS、TOEFL、GRE、GMAT、SAT 等名称均为其各自所有者的商标。
本仓库词库仅为备考参考，与任何考试官方机构无关，未获其认可或授权。
