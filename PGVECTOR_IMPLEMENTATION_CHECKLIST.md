# PostgreSQL 向量数据库集成 - 实施检查清单

## 📋 快速参考

本清单包含 35 个具体任务，按 5 个阶段组织。

---

## 🔧 阶段1：基础设施（1-2天）

### 数据库设置
- [ ] **pgvector-1**: 在PostgreSQL数据库中安装pgvector扩展
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

- [ ] **pgvector-2**: 创建数据库迁移脚本 - chapter_embeddings表
  - 字段：id, chapter_id, novel_id, full_content_embedding, paragraph_embeddings, chunk_count
  - 外键约束
  - 索引

- [ ] **pgvector-3**: 创建数据库迁移脚本 - character_embeddings表
  - 字段：id, character_id, novel_id, full_description_embedding

- [ ] **pgvector-4**: 创建数据库迁移脚本 - world_setting_embeddings表
  - 字段：id, world_setting_id, novel_id, full_description_embedding

- [ ] **pgvector-5**: 创建数据库迁移脚本 - foreshadowing_embeddings表
  - 字段：id, foreshadowing_id, novel_id, content_embedding

- [ ] **pgvector-6**: 为所有向量表创建索引（IVFFlat或HNSW）
  - chapter_embeddings: full_content_embedding 索引
  - character_embeddings: full_description_embedding 索引
  - world_setting_embeddings: full_description_embedding 索引
  - foreshadowing_embeddings: content_embedding 索引

### 依赖安装
- [ ] **pgvector-7**: 更新requirements.txt添加pgvector和embedding相关依赖
  ```txt
  pgvector==0.2.4
  # 确认 Gemini Embedding API 的具体包名
  ```

---

## 💻 阶段2：核心功能（3-5天）

### EmbeddingService 基础
- [ ] **pgvector-8**: 创建backend/services/embedding_service.py基础框架
  - 类定义
  - 初始化方法
  - 数据库连接

- [ ] **pgvector-9**: 实现EmbeddingService.generate_embedding() - 使用Gemini API生成向量
  - 确认 Gemini Embedding API 的具体调用方式
  - 错误处理
  - 返回向量数组

- [ ] **pgvector-10**: 实现文本分块函数_split_into_chunks() - 智能段落分割
  - 按句号、问号、感叹号分割
  - 保持语义完整性
  - 控制chunk大小（默认500字）

### 向量存储
- [ ] **pgvector-11**: 实现store_chapter_embedding() - 存储章节向量（完整+段落级）
  - 生成完整内容向量
  - 分段落生成向量数组
  - 存储到数据库
  - 处理更新逻辑（ON CONFLICT）

### 向量检索
- [ ] **pgvector-12**: 实现find_similar_chapters() - 语义相似章节检索
  - 使用 cosine 相似度（<=> 操作符）
  - 支持排除章节ID
  - 支持相似度阈值
  - 返回相似章节列表（含相似度分数）

- [ ] **pgvector-13**: 实现find_similar_paragraphs() - 段落级精确匹配
  - 使用段落向量数组
  - 找到最相似的段落
  - 返回段落内容和所属章节信息

### ConsistencyChecker 服务
- [ ] **pgvector-14**: 创建backend/services/consistency_checker.py服务
  - 类定义
  - 依赖 EmbeddingService

- [ ] **pgvector-15**: 实现check_character_consistency() - 角色一致性检查
  - 获取角色设定向量
  - 从章节内容提取角色相关描述
  - 计算相似度
  - 返回一致性评分和建议

- [ ] **pgvector-16**: 实现suggest_relevant_context() - 智能上下文推荐
  - 使用章节标题和摘要生成查询向量
  - 调用 find_similar_chapters
  - 返回最相关的上下文章节

---

## 🔗 阶段3：集成应用（2-3天）

### API 集成
- [ ] **pgvector-17**: 在章节创建API中集成向量存储（异步任务）
  - 修改 backend/routers/chapters.py
  - 在章节创建后触发异步向量生成
  - 使用 asyncio.create_task 或 Celery

- [ ] **pgvector-18**: 在章节更新API中集成向量更新逻辑
  - 检测内容是否变更
  - 如果变更，更新向量
  - 异步处理

- [ ] **pgvector-19**: 修改gemini_service.py的write_chapter_content_stream() - 使用智能上下文检索替代固定前3章
  - 添加 novel_id 和 current_chapter_id 参数
  - 调用 suggest_relevant_context
  - 使用返回的上下文替代 previous_chapters_context
  - 保持向后兼容（如果没有 novel_id，使用原逻辑）

### 新API端点
- [ ] **pgvector-20**: 创建API端点 POST /api/novels/{novel_id}/chapters/check-similarity - 内容相似度检查
  - 接收 content 和 current_chapter_id（可选）
  - 调用 find_similar_chapters
  - 返回相似章节列表和警告

- [ ] **pgvector-21**: 创建API端点 POST /api/novels/{novel_id}/foreshadowings/match-resolutions - 智能伏笔匹配
  - 获取章节内容
  - 获取所有未解决的伏笔
  - 使用向量相似度匹配
  - 返回匹配结果

- [ ] **pgvector-22**: 在角色和世界观创建/更新时存储向量
  - 角色创建/更新时调用存储向量
  - 世界观创建/更新时调用存储向量
  - 异步处理

---

## ⚡ 阶段4：增强功能（3-5天）

### 向量存储扩展
- [ ] **pgvector-23**: 实现角色描述向量存储逻辑
  - 组合角色所有字段（name, personality, background等）
  - 生成向量
  - 存储到 character_embeddings 表

- [ ] **pgvector-24**: 实现世界观设定向量存储逻辑
  - 组合世界观描述
  - 生成向量
  - 存储到 world_setting_embeddings 表

- [ ] **pgvector-25**: 实现伏笔向量存储逻辑
  - 使用伏笔内容生成向量
  - 存储到 foreshadowing_embeddings 表

### 智能匹配
- [ ] **pgvector-26**: 实现智能伏笔匹配算法
  - 从章节内容生成查询向量
  - 与所有未解决伏笔向量比较
  - 找到相似度高的伏笔
  - 返回匹配结果和置信度

- [ ] **pgvector-27**: 在生成章节内容前添加相似度预检查（可选，避免重复）
  - 在 gemini_service 中调用 check-similarity API
  - 如果有高相似度内容，警告用户
  - 可选择继续生成或调整提示

---

## 🚀 阶段5：优化测试（2-3天）

### 性能优化
- [ ] **pgvector-28**: 添加Redis缓存层 - 缓存常用章节向量
  - 缓存最近使用的章节向量
  - TTL: 1小时
  - 缓存键格式：chapter_embedding:{chapter_id}

- [ ] **pgvector-29**: 实现批量向量生成优化 - 减少API调用
  - 批量处理多个章节
  - 控制并发数（避免API限流）
  - 使用队列管理任务

- [ ] **pgvector-30**: 添加错误处理和重试机制
  - API调用失败重试（最多3次）
  - 记录错误日志
  - 向量生成失败不应阻塞主流程

### 测试和调优
- [ ] **pgvector-31**: 性能测试 - 向量生成和检索速度
  - 测试单章节向量生成时间
  - 测试相似度检索响应时间
  - 测试并发性能
  - 记录基准数据

- [ ] **pgvector-32**: 相似度阈值调优 - 根据实际效果调整
  - 测试不同阈值（0.7, 0.75, 0.8, 0.85）
  - 评估查准率和查全率
  - 选择最优阈值

- [ ] **pgvector-33**: 添加日志记录和监控
  - 记录向量生成耗时
  - 记录检索次数和命中率
  - 记录错误和异常
  - 添加监控指标

- [ ] **pgvector-34**: 编写单元测试和集成测试
  - EmbeddingService 单元测试
  - ConsistencyChecker 单元测试
  - API端点集成测试
  - 数据库操作测试

- [ ] **pgvector-35**: 文档更新 - API文档和使用说明
  - 更新API文档
  - 添加使用示例
  - 更新部署文档
  - 添加故障排除指南

---

## ⚠️ 重要注意事项

### Gemini Embedding API 确认
- [ ] **关键**: 需要确认 Gemini Embedding API 的实际可用性
  - Google 可能没有独立的 Gemini Embedding API
  - 可能需要使用 Vertex AI 的 embedding 模型
  - 或者使用其他 embedding 服务（OpenAI, Cohere等）
  - **建议**: 如果 Gemini Embedding 不可用，考虑使用：
    - Google Vertex AI `text-embedding-004`
    - OpenAI `text-embedding-3-small` 或 `text-embedding-3-large`
    - 开源模型：Sentence Transformers（中文优化：paraphrase-multilingual-MiniLM-L12-v2）

### 实施优先级
1. **必须实现** (阶段1-3): 核心功能，直接影响写作质量
2. **应该实现** (阶段4): 增强功能，提升用户体验
3. **可选实现** (阶段5部分): 性能优化，根据实际情况决定

### 风险控制
- 向量生成失败不应影响章节的正常保存
- 所有向量操作使用异步任务
- 添加降级方案（向量服务不可用时使用原逻辑）

---

## 📊 进度追踪

总任务数：35
- 阶段1：7 个任务
- 阶段2：9 个任务
- 阶段3：6 个任务
- 阶段4：5 个任务
- 阶段5：8 个任务

完成度：0/35 (0%)

