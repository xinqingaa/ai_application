# llm_reliability_lab

这里保存可靠调用与稳定失败复现入口。完整准备、运行、输出解读和修改任务见 [可靠调用实验](../../../course/lessons/006.reliability-and-errors.lab.md)。

`reliability_compare.py` 默认调用真实模型；模拟失败只用于稳定观察重试、不可重试和显式降级边界。它不能作为模型效果证据，也不能把缺少凭证或供应商失败转换成成功结果。
