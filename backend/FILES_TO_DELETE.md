# 待删除的旧文件列表

以下文件已经迁移到新位置，可以安全删除：

## 根目录下的旧文件

### 已迁移到 core/
- ✅ `auth.py` → `core/security.py` (已合并)
- ✅ `auth_helper.py` → `core/security.py` (已合并)
- ✅ `captcha.py` → `core/security.py` (已合并)
- ✅ `config.py` → `core/config.py`
- ✅ `database.py` → `core/database.py`

### 已迁移到 models/
- ✅ `models.py` → `models/models.py`

### 已迁移到 schemas/
- ✅ `schemas.py` → `schemas/schemas.py`

### 已迁移到 services/ai/
- ✅ `gemini_service.py` → `services/ai/gemini_service.py`
- ✅ `chapter_writing_service.py` → `services/ai/chapter_writing_service.py`

### 已迁移到 services/task/
- ✅ `task_service.py` → `services/task/task_service.py`

## services/ 目录下的旧文件

### 已迁移到 services/embedding/
- ✅ `services/embedding_service.py` → `services/embedding/embedding_service.py`
- ✅ `services/vector_helper.py` → `services/embedding/vector_helper.py`
- ✅ `services/embedding_cache.py` → `services/embedding/embedding_cache.py`

### 已迁移到 services/analysis/
- ✅ `services/consistency_checker.py` → `services/analysis/consistency_checker.py`
- ✅ `services/content_similarity_checker.py` → `services/analysis/content_similarity_checker.py`
- ✅ `services/foreshadowing_matcher.py` → `services/analysis/foreshadowing_matcher.py`

## 已迁移到 utils/
- ✅ `test_structure.py` → `utils/test_structure.py`
- ✅ `test_structure_simple.py` → `utils/test_structure_simple.py`
- ✅ `verify_structure.py` → `utils/verify_structure.py`

## ⚠️ 删除前检查

在删除这些文件之前，请确保：

1. ✅ 所有新文件已正确创建
2. ✅ 导入路径已更新（main.py, run.py 等）
3. ✅ 测试通过
4. ✅ 生产环境已部署新版本

## 删除命令（谨慎使用）

```bash
# 根目录下的旧文件
rm backend/auth.py
rm backend/auth_helper.py
rm backend/captcha.py
rm backend/config.py
rm backend/database.py
rm backend/models.py
rm backend/schemas.py
rm backend/gemini_service.py
rm backend/chapter_writing_service.py
rm backend/task_service.py

# services/ 目录下的旧文件
rm backend/services/embedding_service.py
rm backend/services/vector_helper.py
rm backend/services/embedding_cache.py
rm backend/services/consistency_checker.py
rm backend/services/content_similarity_checker.py
rm backend/services/foreshadowing_matcher.py

# 工具脚本（可选，如果不再需要）
rm backend/test_structure.py
rm backend/test_structure_simple.py
rm backend/verify_structure.py
```

## 建议

建议在确认新结构完全正常工作后再删除旧文件，可以保留一段时间作为备份。

