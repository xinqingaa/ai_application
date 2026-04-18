# data

本目录用于放置第二章“文档处理”的样例输入。

当前约定：

- `product_overview.md`
  Markdown 样例，适合观察标题、段落和列表在切分后的效果。
- `faq.txt`
  纯文本样例，适合观察没有 Markdown 结构时的切分结果。

学习第二章时，建议先跑：

```bash
python scripts/build_index.py
python scripts/inspect_chunks.py
python scripts/inspect_chunks.py data/faq.txt
```
