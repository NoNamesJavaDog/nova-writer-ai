# Nova AI Service

Nova AI 小说创作助手的 AI 微服务。

## 功能特性

- **大纲生成**: 生成完整大纲、卷大纲（支持流式输出）
- **章节生成**: 生成章节列表、章节内容（支持流式输出）
- **元数据分析**: 生成角色、世界观、时间线、伏笔等
- **内容提取**: 提取章节伏笔、章节钩子等
- **多提供商支持**: 支持 Gemini、Claude、OpenAI（通过 HTTP Header 选择）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，并填写配置：

```bash
cp .env.example .env
```

必需配置：
- `GEMINI_API_KEY`: Gemini API 密钥

可选配置：
- `GEMINI_PROXY`: 代理服务器地址（用于绕过地区限制）
- `GEMINI_MODEL`: 模型名称（默认: gemini-2.0-flash-exp）

### 3. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

或直接运行：

```bash
python -m app.main
```

### 4. 访问 API 文档

启动服务后，访问：
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## API 端点

### 健康检查

- `GET /health` - 检查服务状态

### 大纲生成

- `POST /api/v1/outline/generate-full` - 生成完整大纲（非流式）
- `POST /api/v1/outline/generate-volume` - 生成卷大纲（非流式）
- `POST /api/v1/outline/generate-volume-stream` - 流式生成卷大纲
- `POST /api/v1/outline/modify-by-dialogue` - 对话修改大纲

### 章节生成

- `POST /api/v1/chapter/generate-outline` - 生成章节列表
- `POST /api/v1/chapter/write-content` - 生成章节内容（非流式）
- `POST /api/v1/chapter/write-content-stream` - 流式生成章节内容
- `POST /api/v1/chapter/summarize` - 总结章节内容

### 元数据分析

- `POST /api/v1/analysis/generate-characters` - 生成角色列表
- `POST /api/v1/analysis/generate-world-settings` - 生成世界观
- `POST /api/v1/analysis/generate-timeline` - 生成时间线
- `POST /api/v1/analysis/generate-foreshadowings` - 生成伏笔
- `POST /api/v1/analysis/extract-foreshadowings` - 提取章节伏笔
- `POST /api/v1/analysis/extract-chapter-hook` - 提取章节钩子

## 使用示例

### 选择 AI 提供商

通过 HTTP Header `X-Provider` 选择提供商（默认: gemini）：

```bash
# 使用 Gemini
curl -X POST "http://localhost:8001/api/v1/outline/generate-full" \
  -H "X-Provider: gemini" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "星际迷航",
    "genre": "科幻",
    "synopsis": "一个关于星际探索的故事"
  }'

# 使用 Claude（需要配置 CLAUDE_API_KEY）
curl -X POST "http://localhost:8001/api/v1/outline/generate-full" \
  -H "X-Provider: claude" \
  -H "Content-Type: application/json" \
  -d '{...}'

// 使用 DeepSeek（OpenAI 兼容格式）
curl -X POST "http://localhost:8001/api/v1/outline/generate-full" \
  -H "X-Provider: deepseek" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deep Seek Chronicle",
    "genre": "science fiction",
    "synopsis": "A story powered by DeepSeek Reasoner"
  }'
```

### 流式响应

流式端点返回 SSE（Server-Sent Events）格式：

```javascript
const eventSource = new EventSource('http://localhost:8001/api/v1/outline/generate-volume-stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.chunk) {
    console.log('收到内容:', data.chunk);
  } else if (data.done) {
    console.log('生成完成');
    eventSource.close();
  } else if (data.error) {
    console.error('错误:', data.error);
    eventSource.close();
  }
};
```

## 项目结构

```
nova-ai-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 主应用入口
│   ├── config.py               # 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py     # 路由注册
│   │       ├── health.py       # 健康检查
│   │       ├── outline.py      # 大纲生成
│   │       ├── chapter.py      # 章节生成
│   │       └── analysis.py     # 元数据分析
│   ├── core/
│   │   └── providers/          # AI 提供商实现
│   │       ├── __init__.py
│   │       ├── base.py         # 抽象基类
│   │       └── gemini.py       # Gemini 实现
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── requests.py         # 请求模型
│   │   └── responses.py        # 响应模型
│   └── utils/
│       └── __init__.py
├── tests/                      # 测试文件
├── .env.example                # 环境变量模板
├── requirements.txt            # 依赖列表
└── README.md                   # 项目文档
```

## 环境变量说明

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `GEMINI_API_KEY` | Gemini API 密钥 | - | 是 |
| `GEMINI_PROXY` | 代理服务器地址 | http://127.0.0.1:40000 | 否 |
| `GEMINI_MODEL` | Gemini 模型名称 | gemini-2.0-flash-exp | 否 |
| `HOST` | 服务监听地址 | 0.0.0.0 | 否 |
| `PORT` | 服务监听端口 | 8001 | 否 |
| `LOG_LEVEL` | 日志级别 | INFO | 否 |

| `DEFAULT_AI_PROVIDER` | 默认 AI 提供商（在略过 X-Provider 时生效） | gemini | 否 |

## 开发说明

### 添加新的 AI 提供商

1. 在 `app/core/providers/` 目录下创建新的提供商实现（继承 `AIServiceProvider`）
2. 在 `app/core/providers/__init__.py` 中注册新提供商
3. 在 `app/config.py` 中添加相应的配置
4. 在 `app/api/dependencies.py` 中添加提供商的依赖注入逻辑

### 错误处理

所有端点都包含错误处理，返回标准的错误响应：

```json
{
  "error": "错误信息",
  "detail": "详细错误信息"
}
```

### 日志记录

所有关键操作都会记录日志，包括：
- 请求开始和完成
- 错误和异常
- 性能指标

## 许可证

MIT License

## DeepSeek provider configuration

- `DEEPSEEK_API_KEY`: DeepSeek API key (required when using `X-Provider: deepseek`)
- `DEEPSEEK_BASE_URL`: Base URL for DeepSeek, defaults to `https://api.deepseek.com`
- `DEEPSEEK_PROXY`: Optional HTTP/SOCKS proxy if DeepSeek is blocked in your region
- `DEEPSEEK_MODEL`: DeepSeek model name (`deepseek-reasoner` recommended)
- `DEEPSEEK_TIMEOUT_MS`: Request timeout in milliseconds (default 300000)

## Provider selection

- `DEFAULT_AI_PROVIDER` sets the provider used when the request omits the `X-Provider` header. Valid values: `gemini`, `deepseek`, `claude`, `openai`.
