# Nova AI Service - 快速开始

## 1 分钟快速启动

### 第一步：安装依赖
```bash
cd nova-ai-service
pip install -r requirements.txt
```

### 第二步：配置环境
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，至少需要设置：
# GEMINI_API_KEY=your_actual_api_key_here
```

### 第三步：启动服务
```bash
# 方式1：使用 uvicorn（推荐开发环境）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 方式2：直接运行
python -m app.main
```

### 第四步：访问 API 文档
打开浏览器访问：http://localhost:8001/docs

## 快速测试

### 测试 1：健康检查
```bash
curl http://localhost:8001/health
```

预期响应：
```json
{
  "status": "ok",
  "service": "nova-ai-service",
  "version": "1.0.0"
}
```

### 测试 2：生成完整大纲
```bash
curl -X POST http://localhost:8001/api/v1/outline/generate-full \
  -H "Content-Type: application/json" \
  -H "X-Provider: gemini" \
  -d '{
    "title": "星际迷航",
    "genre": "科幻",
    "synopsis": "一个关于星际探索的故事"
  }'
```

### 测试 3：流式生成（使用 JavaScript）
```javascript
const response = await fetch('http://localhost:8001/api/v1/outline/generate-volume-stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Provider': 'gemini'
  },
  body: JSON.stringify({
    novel_title: "星际迷航",
    full_outline: "完整大纲内容...",
    volume_title: "第一卷：启程",
    volume_summary: "主角开始了他的星际之旅",
    characters: [],
    volume_index: 0
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.chunk) console.log(data.chunk);
      if (data.done) console.log('生成完成');
      if (data.error) console.error('错误:', data.error);
    }
  }
}
```

## 常用 API 端点

### 大纲生成
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/outline/generate-full` | POST | 生成完整大纲 |
| `/api/v1/outline/generate-volume` | POST | 生成卷大纲 |
| `/api/v1/outline/generate-volume-stream` | POST | 流式生成卷大纲 |
| `/api/v1/outline/modify-by-dialogue` | POST | 对话修改大纲 |

### 章节生成
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/chapter/generate-outline` | POST | 生成章节列表 |
| `/api/v1/chapter/write-content` | POST | 生成章节内容 |
| `/api/v1/chapter/write-content-stream` | POST | 流式生成章节内容 |
| `/api/v1/chapter/summarize` | POST | 总结章节内容 |

### 元数据分析
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/analysis/generate-characters` | POST | 生成角色列表 |
| `/api/v1/analysis/generate-world-settings` | POST | 生成世界观 |
| `/api/v1/analysis/generate-timeline` | POST | 生成时间线 |
| `/api/v1/analysis/generate-foreshadowings` | POST | 生成伏笔 |
| `/api/v1/analysis/extract-foreshadowings` | POST | 提取章节伏笔 |
| `/api/v1/analysis/extract-chapter-hook` | POST | 提取章节钩子 |

## 切换 AI 提供商

通过 HTTP Header `X-Provider` 选择提供商：

```bash
# 使用 Gemini（默认）
curl -H "X-Provider: gemini" ...

# 使用 Claude（需要配置 CLAUDE_API_KEY）
curl -H "X-Provider: claude" ...

# 使用 OpenAI（需要配置 OPENAI_API_KEY）
curl -H "X-Provider: openai" ...
```

## 环境变量说明

### 必需配置
```bash
GEMINI_API_KEY=your_api_key_here
```

### 可选配置
```bash
# 代理服务器（用于绕过地区限制）
GEMINI_PROXY=http://127.0.0.1:40000

# 服务端口
PORT=8001

# 日志级别
LOG_LEVEL=INFO

# CORS 配置（生产环境需要修改）
CORS_ORIGINS=*
```

## 常见问题

### Q1: 提示 "GEMINI_API_KEY 未配置"
**A**: 在 `.env` 文件中设置 `GEMINI_API_KEY=your_actual_api_key`

### Q2: 提示 "location is not supported"
**A**: 配置代理服务器：`GEMINI_PROXY=http://127.0.0.1:40000`

### Q3: 如何启用调试模式？
**A**: 在 `.env` 文件中设置 `DEBUG=True` 并使用 `--reload` 参数启动

### Q4: 如何查看详细日志？
**A**: 设置 `LOG_LEVEL=DEBUG` 查看更详细的日志

### Q5: 流式响应如何使用？
**A**: 使用支持 SSE（Server-Sent Events）的客户端，参考上面的 JavaScript 示例

## 项目结构速览

```
nova-ai-service/
├── app/
│   ├── main.py              # 主应用入口
│   ├── config.py            # 配置管理
│   ├── api/
│   │   ├── dependencies.py  # 依赖注入
│   │   └── v1/              # API v1
│   │       ├── health.py    # 健康检查
│   │       ├── outline.py   # 大纲生成
│   │       ├── chapter.py   # 章节生成
│   │       └── analysis.py  # 元数据分析
│   ├── core/
│   │   └── providers/       # AI 提供商
│   └── schemas/             # 请求/响应模型
├── .env                     # 环境变量（需要创建）
├── .env.example             # 环境变量模板
├── requirements.txt         # 依赖列表
└── README.md                # 项目文档
```

## 下一步

1. 查看完整 API 文档：http://localhost:8001/docs
2. 阅读详细文档：`README.md`
3. 查看实现总结：`IMPLEMENTATION_SUMMARY.md`
4. 运行测试：`python test_import.py`

## 获取帮助

- API 文档：http://localhost:8001/docs
- 项目文档：README.md
- 实现总结：IMPLEMENTATION_SUMMARY.md
