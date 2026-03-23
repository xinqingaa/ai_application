# 第 9 节练习：JSON 与 HTTP 请求

> 从这一节开始，进入 AI 应用开发核心。学到的技能可以直接用来调用 LLM API。

## 目录结构

```
09_json_http/
├── README.md
├── json_advanced.py        # 练习1：JSON 深入（嵌套处理、自定义序列化）
├── http_requests.py        # 练习2：requests 库（GET/POST、httpbin.org）
├── httpx_client.py         # 练习3：httpx 同步 + 异步预览
├── public_api.py           # 练习4：调用公开 API（解析响应、错误处理）
└── http_client_class.py    # 练习5：封装 HTTP 客户端类（重试、统一错误处理）
```

每个文件独立可运行，无包依赖关系。

## 安装依赖

```bash
pip install requests httpx
```

## 运行方式

```bash
cd source/01_python/09_json_http

# 练习1：纯 JSON 处理，无网络依赖
python json_advanced.py

# 练习2-5：需要联网（访问 httpbin.org）
python http_requests.py
python httpx_client.py
python public_api.py
python http_client_class.py
```

每个脚本都有交互式菜单，可以选择运行单个演示或全部运行。

## 建议学习顺序

| 顺序 | 文件 | 内容 | 是否联网 |
|------|------|------|---------|
| 1 | `json_advanced.py` | JSON 嵌套处理、自定义序列化 | 否 |
| 2 | `http_requests.py` | requests 库基础 | 是 |
| 3 | `httpx_client.py` | httpx 库 + async 预览 | 是 |
| 4 | `public_api.py` | 调用公开 API、错误处理 | 是 |
| 5 | `http_client_class.py` | 封装 HTTP 客户端类 | 是 |

## 知识点覆盖

- **JSON**：嵌套访问、安全取值、自定义序列化（datetime/Enum/dataclass）
- **requests**：GET/POST、params/json/headers、超时、异常处理、Session
- **httpx**：同步请求、Client 复用、超时配置、async 预览
- **实战**：调用公开 API、模拟 LLM API 格式、封装可复用客户端
- **错误处理**：超时重试、状态码判断、指数退避

## 注意事项

- 练习 2-5 需要**联网**访问 httpbin.org 和 jsonplaceholder.typicode.com
- 如果网络不通，练习 1（JSON）可以离线完成
- httpbin.org 偶尔会慢，耐心等待或稍后重试
