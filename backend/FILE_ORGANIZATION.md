# Backend 文件分类整理说明

## 📁 目录结构

```
backend/
├── api/                    # API 路由层
│   └── routers/           # 路由模块（待拆分）
│
├── core/                   # ✅ 核心基础设施
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   └── security.py        # 认证、授权、密码、验证码
│
├── models/                 # ✅ 数据库模型
│   ├── __init__.py
│   └── models.py          # SQLAlchemy ORM 模型
│
├── schemas/                # ✅ 数据模式
│   ├── __init__.py
│   └── schemas.py         # Pydantic 请求/响应模型
│
├── services/               # ✅ 业务服务层
│   ├── __init__.py
│   ├── ai/                # AI 相关服务
│   │   ├── __init__.py
│   │   ├── gemini_service.py          # Gemini API 调用
│   │   └── chapter_writing_service.py # 章节写作服务
│   │
│   ├── embedding/         # ✅ 向量嵌入服务
│   │   ├── __init__.py
│   │   ├── embedding_service.py      # 嵌入服务主类
│   │   ├── vector_helper.py          # 向量存储辅助函数
│   │   └── embedding_cache.py        # 嵌入缓存
│   │
│   ├── analysis/          # ✅ 内容分析服务
│   │   ├── __init__.py
│   │   ├── consistency_checker.py    # 一致性检查
│   │   ├── content_similarity_checker.py  # 内容相似度检查
│   │   └── foreshadowing_matcher.py  # 伏笔匹配
│   │
│   ├── task/              # ✅ 任务管理服务
│   │   ├── __init__.py
│   │   └── task_service.py           # 后台任务管理
│   │
│   ├── batch_embedding_processor.py # 批量嵌入处理
│
├── utils/                  # ✅ 工具脚本
│   ├── __init__.py
│   ├── test_structure.py
│   ├── test_structure_simple.py
│   └── verify_structure.py
│
├── scripts/                # 数据库和部署脚本
│   ├── init_db.py
│   ├── migrate_db.py
│   └── ...
│
├── tests/                  # 测试文件
│   └── ...
│
├── docs/                   # 文档
│   └── ...
│
├── main.py                 # ⚠️ 主应用入口（待更新导入）
├── run.py                  # ⚠️ 启动脚本（待更新导入）
└── requirements.txt        # 依赖列表
```

## 📋 文件分类

### ✅ 已整理的文件

#### 核心模块 (core/)
- `config.py` - 应用配置
- `database.py` - 数据库连接
- `security.py` - 认证、授权、密码、验证码（合并了 auth.py, auth_helper.py, captcha.py）

#### 数据层
- `models/models.py` - 数据库模型
- `schemas/schemas.py` - Pydantic 模型

#### AI 服务 (services/ai/)
- `gemini_service.py` - Gemini API 调用
- `chapter_writing_service.py` - 章节写作服务

#### 向量嵌入服务 (services/embedding/)
- `embedding_service.py` - 嵌入服务主类
- `vector_helper.py` - 向量存储辅助函数
- `embedding_cache.py` - 嵌入缓存

#### 内容分析服务 (services/analysis/)
- `consistency_checker.py` - 一致性检查
- `content_similarity_checker.py` - 内容相似度检查
- `foreshadowing_matcher.py` - 伏笔匹配

#### 任务服务 (services/task/)
- `task_service.py` - 后台任务管理

#### 工具脚本 (utils/)
- `test_structure.py` - 结构测试
- `test_structure_simple.py` - 简单结构测试
- `verify_structure.py` - 结构验证

### ⚠️ 待删除的旧文件（已迁移）

根目录下的以下文件可以删除（已迁移到新位置）：
- `auth.py` → 已合并到 `core/security.py`
- `auth_helper.py` → 已合并到 `core/security.py`
- `captcha.py` → 已合并到 `core/security.py`
- `config.py` → 已移动到 `core/config.py`
- `database.py` → 已移动到 `core/database.py`
- `models.py` → 已移动到 `models/models.py`
- `schemas.py` → 已移动到 `schemas/schemas.py`
- `gemini_service.py` → 已移动到 `services/ai/gemini_service.py`
- `chapter_writing_service.py` → 已移动到 `services/ai/chapter_writing_service.py`
- `task_service.py` → 已移动到 `services/task/task_service.py`

### 📝 需要更新的文件

以下文件需要更新导入路径：
- `main.py` - 更新所有导入路径
- `run.py` - 更新导入路径
- `services/ai/chapter_writing_service.py` - 更新 embedding 服务导入
- 测试文件中的导入路径

## 🔄 导入路径变更

### 旧路径 → 新路径

```python
# 配置和数据库
from config import ... → from core.config import ...
from database import ... → from core.database import ...

# 认证和安全
from auth import ... → from core.security import ...
from auth_helper import ... → from core.security import ...
from captcha import ... → from core.security import ...

# 模型和模式
from models import ... → from models import ... (通过 __init__.py)
from schemas import ... → from schemas import ... (通过 __init__.py)

# AI 服务
from gemini_service import ... → from services.ai import ...
from chapter_writing_service import ... → from services.ai import ...

# 向量嵌入服务
from services.embedding_service import ... → from services.embedding import ...
from services.vector_helper import ... → from services.embedding import ...

# 分析服务
from services.consistency_checker import ... → from services.analysis import ...
from services.content_similarity_checker import ... → from services.analysis import ...
from services.foreshadowing_matcher import ... → from services.analysis import ...

# 任务服务
from task_service import ... → from services.task import ...
```

## ✨ 整理优势

1. **清晰的分类** - 按功能模块组织文件
2. **易于查找** - 相关功能集中在一起
3. **便于维护** - 职责单一，修改影响范围小
4. **便于扩展** - 新功能可以轻松添加到对应模块
5. **减少冲突** - 不同模块的文件不会相互干扰

