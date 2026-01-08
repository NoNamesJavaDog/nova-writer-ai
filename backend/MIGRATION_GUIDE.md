# 后端代码结构迁移指南

## 概述

后端代码已重构为模块化结构，提高了代码组织性和可维护性。

## 新目录结构

```
backend/
├── api/                    # API 路由层（待实现）
│   └── routers/           
├── core/                   # ✅ 核心基础设施（已完成）
│   ├── config.py          
│   ├── database.py        
│   └── security.py        
├── models/                 # ✅ 数据库模型（已完成）
│   └── models.py          
├── schemas/                # ✅ 数据模型（已完成）
│   └── schemas.py         
└── services/               # ✅ 业务服务（部分完成）
    ├── ai/                # ✅ AI服务
    ├── task/              # ✅ 任务服务
    └── embedding/         # ⚠️ 需要移动
```

## 已完成的迁移

### 1. 核心模块 (core/)
- ✅ `config.py` → `core/config.py`
- ✅ `database.py` → `core/database.py`
- ✅ `auth.py` + `auth_helper.py` + `captcha.py` → `core/security.py` (合并)

### 2. 数据模型
- ✅ `models.py` → `models/models.py`
- ✅ `schemas.py` → `schemas/schemas.py`

### 3. AI 服务
- ✅ `gemini_service.py` → `services/ai/gemini_service.py`
- ✅ `chapter_writing_service.py` → `services/ai/chapter_writing_service.py`

### 4. 任务服务
- ✅ `task_service.py` → `services/task/task_service.py`

## 待完成的迁移

### 1. API 路由拆分 (api/routers/)
- ⏳ 将 `main.py` 中的路由拆分到各个 router 文件
- ⏳ 创建 `api/dependencies.py` 用于通用依赖

### 2. 其他服务移动
- ⏳ `services/embedding_service.py` → `services/embedding/embedding_service.py`
- ⏳ `services/vector_helper.py` → `services/embedding/vector_helper.py`
- ⏳ 其他服务文件整理

## 导入路径变更

### 已更新的导入

```python
# ✅ 配置和数据库
from core.config import CORS_ORIGINS, DEBUG
from core.database import get_db, SessionLocal, Base

# ✅ 认证和安全
from core.security import (
    get_current_user,
    create_access_token,
    generate_captcha,
    verify_captcha,
    handle_login_failure
)

# ✅ 模型和模式（通过 __init__.py 导出）
from models import User, Novel, Chapter  # 路径不变，但实际从 models/models.py 导入
from schemas import UserCreate, NovelResponse  # 路径不变

# ✅ AI 服务
from services.ai import (
    generate_full_outline,
    write_and_save_chapter,
    ChapterWritingContext
)

# ✅ 任务服务
from services.task import create_task, get_task_executor
```

### 临时兼容层

为了保持向后兼容，旧的根目录文件仍然存在。建议逐步迁移到新结构。

## 下一步工作

1. **修复所有导入路径** - 更新所有文件中的导入语句
2. **拆分 main.py** - 将路由按功能模块拆分
3. **移动剩余服务** - 整理 services/ 目录下的其他文件
4. **更新测试和脚本** - 确保测试和脚本使用新的导入路径
5. **删除旧文件** - 确认新结构稳定后，删除根目录下的旧文件

## 注意事项

- ⚠️ 新结构和旧结构目前并存，需要逐步迁移
- ⚠️ `main.py` 中的导入路径仍使用旧路径，需要更新
- ⚠️ 测试文件和脚本可能需要更新导入路径

## 验证新结构

可以运行以下命令检查导入是否正确：

```bash
# 检查核心模块
python -c "from backend.core import get_db, get_current_user; print('✅ Core OK')"

# 检查模型
python -c "from backend.models import User, Novel; print('✅ Models OK')"

# 检查服务
python -c "from backend.services.ai import generate_full_outline; print('✅ AI Services OK')"
```

