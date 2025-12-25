# 远程服务器测试指南

## 📋 测试步骤

由于当前环境限制，请在远程服务器上执行以下步骤：

### 1. 安装依赖

```bash
# 进入backend目录
cd backend

# 安装所有依赖
pip install -r requirements.txt

# 或者使用python -m pip
python -m pip install -r requirements.txt

# 如果使用虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 配置环境变量

确保 `.env` 文件中有：
```env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379/0  # 可选
```

### 3. 运行数据库迁移

```bash
cd backend
python migrate_add_pgvector.py
```

### 4. 运行测试

#### 功能完整性测试
```bash
python test_vector_features.py
```

#### API调用测试
```bash
python test_embedding_simple.py
```

#### 单元测试
```bash
python test_unit.py
```

#### 性能测试
```bash
python test_performance.py
```

### 5. 验证依赖安装

```bash
pip list | grep -E "redis|sqlalchemy|pgvector|google-genai"
```

或在Python中验证：
```python
import redis
import sqlalchemy
import pgvector
import google.genai

print("所有依赖已安装")
```

## 📦 关键依赖

- `pgvector==0.2.4` - PostgreSQL向量扩展
- `redis>=4.5.0` - Redis缓存（可选）
- `sqlalchemy==2.0.23` - ORM
- `google-genai>=0.2.0` - Gemini API
- `psycopg2-binary==2.9.9` - PostgreSQL驱动

## ⚠️ 注意事项

1. **PostgreSQL和pgvector扩展**：需要在数据库服务器上安装pgvector扩展
2. **Redis**：如果使用缓存功能，需要Redis服务器
3. **API Key**：确保Gemini API Key有效
4. **Python版本**：建议Python 3.8+

## 🔧 故障排除

### 依赖安装失败
```bash
# 升级pip
python -m pip install --upgrade pip

# 单独安装问题包
pip install pgvector --no-cache-dir
```

### 数据库连接失败
- 检查DATABASE_URL格式
- 确认数据库服务运行
- 检查网络连接

### Redis连接失败
- Redis是可选的，失败不影响核心功能
- 缓存功能会自动禁用

