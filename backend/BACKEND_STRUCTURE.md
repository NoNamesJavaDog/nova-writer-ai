# 后端代码结构说明

## 目录结构

```
backend/
├── api/                    # API 路由层
│   ├── __init__.py
│   ├── dependencies.py     # 通用依赖（限流、异常处理等）
│   └── routers/           # 路由模块
│       ├── __init__.py
│       ├── auth.py        # 认证路由
│       ├── novels.py      # 小说路由
│       ├── volumes.py     # 卷路由
│       ├── chapters.py    # 章节路由
│       ├── characters.py  # 角色路由
│       ├── world_settings.py  # 世界观路由
│       ├── timeline.py    # 时间线路由
│       ├── foreshadowings.py  # 伏笔路由
│       ├── ai.py          # AI生成路由
│       └── tasks.py       # 任务路由
│
├── core/                   # 核心基础设施
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   └── security.py        # 认证、授权、密码、验证码
│
├── models/                 # 数据库模型
│   ├── __init__.py
│   └── models.py          # SQLAlchemy 模型
│
├── schemas/                # Pydantic 数据模型
│   ├── __init__.py
│   └── schemas.py         # 请求/响应模型
│
├── services/               # 业务服务层
│   ├── __init__.py
│   ├── ai/                # AI 相关服务
│   │   ├── __init__.py
│   │   ├── gemini_service.py          # Gemini API 调用
│   │   └── chapter_writing_service.py # 章节写作服务
│   ├── embedding/         # 向量嵌入服务
│   │   ├── __init__.py
│   │   ├── embedding_service.py
│   │   └── vector_helper.py
│   ├── task/              # 任务管理服务
│   │   ├── __init__.py
│   │   └── task_service.py
│   ├── batch_embedding_processor.py
│   ├── consistency_checker.py
│   ├── content_similarity_checker.py
│   ├── embedding_cache.py
│   └── foreshadowing_matcher.py
│
├── main.py                 # FastAPI 应用入口
├── run.py                  # 启动脚本
├── requirements.txt        # 依赖列表
├── config.example.env      # 配置示例
│
├── scripts/                # 工具脚本
│   ├── init_db.py
│   ├── migrate_db.py
│   └── ...
│
├── tests/                  # 测试文件
│   └── ...
│
└── docs/                   # 文档
    └── ...
```

## 模块说明

### core/ - 核心基础设施
- **config.py**: 应用配置（数据库、JWT、CORS等）
- **database.py**: 数据库连接和会话管理
- **security.py**: 认证、授权、密码处理、验证码

### models/ - 数据库模型
- 所有 SQLAlchemy ORM 模型定义

### schemas/ - 数据模型
- 所有 Pydantic 模型（请求/响应验证）

### services/ - 业务服务
- **ai/**: AI 生成相关服务
- **embedding/**: 向量嵌入和检索服务
- **task/**: 后台任务管理服务
- 其他工具服务

### api/routers/ - API 路由
- 按功能模块拆分的路由处理器

## 迁移指南

### 导入路径变更

旧导入 → 新导入：

```python
# 配置和数据库
from config import ... → from core.config import ...
from database import ... → from core.database import ...

# 认证和安全
from auth import ... → from core.security import ...
from auth_helper import ... → from core.security import ...
from captcha import ... → from core.security import ...

# 模型和模式
from models import ... → from models import ...  (通过 __init__.py 导出)
from schemas import ... → from schemas import ... (通过 __init__.py 导出)

# AI 服务
from gemini_service import ... → from services.ai import ...
from chapter_writing_service import ... → from services.ai import ...

# 任务服务
from task_service import ... → from services.task import ...
```

## 优势

1. **清晰的分层结构**: API层、服务层、数据层分离
2. **模块化**: 相关功能组织在一起
3. **易于维护**: 每个模块职责单一明确
4. **便于扩展**: 新功能可以轻松添加到对应模块

