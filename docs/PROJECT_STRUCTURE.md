# NovaWrite AI - 项目结构说明

## 📁 项目目录结构

```
nova-ai/
├── backend/                    # 后端服务
│   ├── services/              # 业务服务层
│   │   ├── consistency_checker.py       # 一致性检查服务
│   │   ├── content_similarity_checker.py # 内容相似度检查
│   │   ├── embedding_service.py         # 向量嵌入服务
│   │   ├── foreshadowing_matcher.py     # 伏笔匹配服务
│   │   └── vector_helper.py             # 向量操作辅助工具
│   ├── scripts/               # 脚本工具
│   │   ├── deploy_and_test.ps1/sh      # 部署和测试脚本
│   │   ├── install_dependencies.ps1/sh  # 依赖安装脚本
│   │   ├── migrate_*.py                 # 数据库迁移脚本
│   │   ├── create_user*.py              # 用户创建工具
│   │   ├── check_*.py                   # 各种检查工具
│   │   └── init_db.py                   # 数据库初始化
│   ├── tests/                 # 测试文件
│   │   ├── test_all_remote.py          # 远程测试
│   │   ├── test_create_novel*.py       # 小说创建测试
│   │   ├── test_db_connection.py       # 数据库连接测试
│   │   ├── test_embedding*.py          # 向量嵌入测试
│   │   └── test_*.py                    # 其他测试
│   ├── docs/                  # 文档
│   │   ├── README.md                    # 后端说明文档
│   │   ├── API_AUTHENTICATION.md        # API认证文档
│   │   └── api_integration_example.py   # API集成示例
│   ├── main.py               # FastAPI主应用
│   ├── models.py             # 数据库模型
│   ├── schemas.py            # Pydantic schemas
│   ├── auth.py               # 认证模块
│   ├── database.py           # 数据库连接
│   ├── config.py             # 配置文件
│   ├── gemini_service.py     # Gemini AI服务
│   ├── task_service.py       # 异步任务服务
│   ├── run.py                # 服务启动脚本
│   ├── requirements.txt      # Python依赖
│   └── config.example.env    # 环境变量示例
│
├── novawrite-ai---professional-novel-assistant/  # 前端应用
│   ├── components/           # React组件
│   │   ├── Dashboard.tsx             # 仪表盘
│   │   ├── OutlineView.tsx           # 大纲视图
│   │   ├── EditorView.tsx            # 编辑器视图
│   │   ├── CharacterView.tsx         # 角色视图
│   │   ├── WorldView.tsx             # 世界观视图
│   │   ├── TimelineView.tsx          # 时间线视图
│   │   ├── ForeshadowingView.tsx     # 伏笔视图
│   │   ├── NovelManager.tsx          # 小说管理器
│   │   ├── Login.tsx                 # 登录组件
│   │   └── ...
│   ├── services/             # 前端服务层
│   │   ├── apiService.ts             # API服务
│   │   ├── authService.ts            # 认证服务
│   │   ├── geminiService.ts          # AI服务
│   │   └── taskService.ts            # 任务服务
│   ├── scripts/              # 部署脚本
│   │   ├── deploy.ps1/sh             # 部署脚本
│   │   └── deploy-setup.sh           # 部署设置脚本
│   ├── docs/                 # 文档
│   │   ├── README.md                 # 前端说明
│   │   ├── DEPLOY.md                 # 部署文档
│   │   ├── API_DIAGNOSTIC.md         # API诊断
│   │   ├── TROUBLESHOOTING.md        # 故障排查
│   │   ├── QUICK_FIX.md              # 快速修复指南
│   │   └── nginx.conf.example        # Nginx配置示例
│   ├── dist/                 # 构建输出（自动生成）
│   ├── public/               # 静态资源
│   ├── App.tsx               # 主应用组件
│   ├── types.ts              # TypeScript类型定义
│   ├── package.json          # npm依赖
│   ├── vite.config.ts        # Vite配置
│   ├── tailwind.config.js    # Tailwind CSS配置
│   └── tsconfig.json         # TypeScript配置
│
└── README.md                 # 项目主说明文档

```

## 🗑️ 已清理的文件

### 删除的备份文件（9个）
- backend-security-update.tar.gz
- frontend-full-chapter-fix.tar.gz
- frontend-full-outline-fix.tar.gz
- frontend-outline-fix.tar.gz
- frontend-source*.tar.gz
- frontend-src-security-update.tar.gz
- frontend-with-refresh-token.tar.gz

### 删除的代理配置文件（10个）
- CLASH_CONFIG.md/yaml
- CLASH_IMPORT_LINKS.md
- CLASH_LINK.txt
- CLASH_QUICK_IMPORT.md
- clash-subscription.yaml
- V2RAY_CONFIG.md
- v2ray-config.json
- VLESS_REALITY_CONFIG.md
- vless-reality-config.json

### 删除的重复文件（2个）
- backend/auth_helper.py
- backend/captcha.py

### 删除的无用目录（1个）
- frontend/server/（已迁移到独立backend目录）

## 📊 清理统计

- **删除文件总数**: 23个
- **整理测试文件**: 12个 → backend/tests/
- **整理脚本文件**: 21个 → backend/scripts/, frontend/scripts/
- **整理文档文件**: 9个 → backend/docs/, frontend/docs/
- **减少根目录混乱**: 清理了所有备份和临时文件

## 🎯 项目结构优势

### 1. 清晰的分层架构
- **后端**: FastAPI + PostgreSQL + pgvector
- **前端**: React + TypeScript + Vite + Tailwind CSS
- **AI服务**: Gemini API集成

### 2. 代码组织良好
- 所有测试集中在 `tests/` 目录
- 所有脚本集中在 `scripts/` 目录
- 所有文档集中在 `docs/` 目录
- 业务逻辑在后端，前端只负责UI

### 3. 易于维护
- 核心代码清晰可见（backend/*.py, frontend/components/*.tsx）
- 配置文件集中管理
- 文档和工具分类明确

## 🚀 快速开始

### 后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### 前端
```bash
cd novawrite-ai---professional-novel-assistant
npm install
npm run dev
```

## 📚 相关文档

- [后端文档](backend/docs/README.md)
- [前端文档](novawrite-ai---professional-novel-assistant/docs/README.md)
- [部署文档](novawrite-ai---professional-novel-assistant/docs/DEPLOY.md)
- [故障排查](novawrite-ai---professional-novel-assistant/docs/TROUBLESHOOTING.md)

---

**最后更新**: 2024-12-31
**清理执行**: AI Assistant

