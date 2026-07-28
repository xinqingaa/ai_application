# V0 ingestion fixtures

这里保存 V0 “售后入口与订单状态”垂直切片的受控教学 fixtures。内容由课程人为编写，不是生产资料；文件本身使用真实 TXT、Markdown、DOCX 和 PDF 格式，并由真实 Parser 处理，不使用 Mock 解析结果。

`canonical_content.json` 是四种正常格式共同使用的业务事实。`manifest.json` 将它们声明为同一业务文档版本的互斥格式表示：每次实验独立加载其中一个，不能把四份内容同时写入同一知识库。

DOCX 和 PDF 由 `build_binary_fixtures.py` 从 canonical facts 可重复生成；TXT 和 Markdown 由测试对照同一 canonical source。生成脚本只服务 fixture，不属于产品运行入口。

正常 PDF 具有可提取文本层。`image_only_scan.pdf`、损坏 DOCX、错误编码 TXT 和空 Markdown 是人为构造的稳定失败材料，只用于验证错误边界。它们不能证明复杂真实文档的解析质量。
