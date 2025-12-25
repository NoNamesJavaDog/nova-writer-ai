# pgvector 可选优化任务详解

## 📋 概述

这三个任务是可选的性能优化和调优任务，不影响核心功能的使用。可以根据实际需求决定是否实施。

---

## 🎯 任务1: pgvector-28 - Redis缓存层

### 目的
通过Redis缓存常用章节向量，减少数据库查询，提高检索性能。

### 适用场景
- ✅ 频繁检索相同章节
- ✅ 数据库查询成为性能瓶颈
- ✅ 有大量章节需要频繁访问
- ✅ 需要提高响应速度

### 不适用场景
- ❌ 章节数量较少（< 100章）
- ❌ 检索频率较低
- ❌ 没有Redis环境
- ❌ 内存资源有限

### 实施方案

#### 1. 缓存策略
```python
# 缓存键格式
chapter_embedding:{chapter_id}  # 章节向量
chapter_similar:{novel_id}:{query_hash}  # 相似度查询结果

# TTL设置
CHAPTER_EMBEDDING_TTL = 3600  # 1小时
QUERY_RESULT_TTL = 300  # 5分钟
```

#### 2. 缓存逻辑
```python
# 读取向量时
def get_chapter_embedding_with_cache(db, chapter_id, redis_client):
    cache_key = f"chapter_embedding:{chapter_id}"
    
    # 先查缓存
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 缓存未命中，查数据库
    embedding = db.execute(
        text("SELECT full_content_embedding FROM chapter_embeddings WHERE chapter_id = :id"),
        {"id": chapter_id}
    ).fetchone()
    
    # 写入缓存
    if embedding:
        redis_client.setex(
            cache_key,
            CHAPTER_EMBEDDING_TTL,
            json.dumps(embedding[0])
        )
    
    return embedding[0] if embedding else None
```

#### 3. 缓存失效
```python
# 章节更新时清除缓存
def invalidate_chapter_cache(redis_client, chapter_id):
    cache_key = f"chapter_embedding:{chapter_id}"
    redis_client.delete(cache_key)
    
    # 清除相关的查询缓存
    pattern = f"chapter_similar:*:{chapter_id}"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
```

### 预期效果
- ⚡ 检索速度提升：30-50%（缓存命中时）
- 📉 数据库负载降低：20-40%
- 💰 成本：需要Redis服务器（可接受）

### 实施难度
- **难度**: 中等
- **时间**: 1-2天
- **依赖**: Redis服务器、redis-py库

### 实施步骤
1. 安装Redis和redis-py库
2. 配置Redis连接
3. 实现缓存读取/写入逻辑
4. 实现缓存失效策略
5. 添加缓存命中率监控

---

## 🎯 任务2: pgvector-29 - 批量向量生成优化

### 目的
优化批量处理场景下的向量生成，减少API调用次数，提高处理效率。

### 适用场景
- ✅ 需要批量生成多个章节的向量
- ✅ API调用频率受限
- ✅ 需要处理大量历史章节
- ✅ 一次性导入多章节内容

### 不适用场景
- ❌ 单次只处理少量章节（< 10章）
- ❌ API调用频率限制不是问题
- ❌ 不需要批量处理功能
- ❌ 实时性要求高（批量处理需要时间）

### 实施方案

#### 1. 批量处理队列
```python
from queue import Queue
from threading import Thread
import time

class BatchEmbeddingProcessor:
    def __init__(self, max_workers=3, batch_size=10, delay=1.0):
        self.queue = Queue()
        self.max_workers = max_workers  # 最大并发数
        self.batch_size = batch_size  # 每批处理数量
        self.delay = delay  # API调用间隔（秒）
        self.service = EmbeddingService()
    
    def add_task(self, chapter_id, content):
        """添加任务到队列"""
        self.queue.put({
            'chapter_id': chapter_id,
            'content': content,
            'status': 'pending'
        })
    
    def process_batch(self):
        """批量处理任务"""
        batch = []
        while len(batch) < self.batch_size and not self.queue.empty():
            task = self.queue.get()
            batch.append(task)
        
        if not batch:
            return
        
        # 并发生成向量（控制并发数）
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for task in batch:
                future = executor.submit(
                    self.service.generate_embedding,
                    task['content']
                )
                futures.append((task, future))
                time.sleep(self.delay)  # 控制API调用频率
            
            # 获取结果
            for task, future in futures:
                try:
                    embedding = future.result(timeout=30)
                    task['embedding'] = embedding
                    task['status'] = 'completed'
                except Exception as e:
                    task['status'] = 'failed'
                    task['error'] = str(e)
        
        return batch
```

#### 2. 异步任务处理
```python
from celery import Celery

app = Celery('embedding_tasks')

@app.task
def batch_generate_embeddings(chapter_ids_and_contents):
    """批量生成向量"""
    service = EmbeddingService()
    results = []
    
    for chapter_id, content in chapter_ids_and_contents:
        try:
            embedding = service.generate_embedding(content)
            # 存储向量
            store_chapter_embedding_async(db, chapter_id, novel_id, content)
            results.append({'chapter_id': chapter_id, 'status': 'success'})
        except Exception as e:
            results.append({'chapter_id': chapter_id, 'status': 'failed', 'error': str(e)})
        time.sleep(0.5)  # 控制调用频率
    
    return results
```

#### 3. API调用优化
```python
# 使用批量API（如果Gemini API支持）
def generate_embeddings_batch(texts):
    """批量生成向量（如果API支持）"""
    # 注意：需要确认Gemini API是否支持批量调用
    # 如果支持，可以使用批量接口
    result = client.models.embed_content_batch(
        model="models/text-embedding-004",
        contents=texts,
        task_type="RETRIEVAL_DOCUMENT"
    )
    return result.embeddings
```

### 预期效果
- ⚡ 处理速度提升：50-70%（批量处理时）
- 📉 API调用次数减少：通过并发和批量调用
- 💰 成本：需要任务队列（Celery/RQ）或额外的线程管理

### 实施难度
- **难度**: 中等
- **时间**: 2-3天
- **依赖**: 任务队列（可选）、并发控制

### 实施步骤
1. 设计批量处理架构
2. 实现任务队列或线程池
3. 实现并发控制和API调用频率限制
4. 添加进度追踪和错误处理
5. 测试批量处理性能

---

## 🎯 任务3: pgvector-32 - 相似度阈值调优

### 目的
根据实际使用数据调整相似度阈值，优化检索精度和召回率。

### 适用场景
- ✅ 已有实际使用数据
- ✅ 发现检索结果不准确
- ✅ 需要优化查准率和查全率
- ✅ 针对特定场景优化

### 不适用场景
- ❌ 还没有实际使用数据
- ❌ 当前阈值已经满足需求
- ❌ 没有时间收集和分析数据
- ❌ 不同场景需要不同阈值

### 实施方案

#### 1. 数据收集
```python
# 记录检索结果和用户反馈
def log_similarity_search(
    novel_id, query_text, results, 
    similarity_threshold, user_feedback=None
):
    """记录相似度检索日志"""
    log_entry = {
        'novel_id': novel_id,
        'query_text': query_text,
        'threshold': similarity_threshold,
        'results_count': len(results),
        'results': [
            {
                'chapter_id': r['chapter_id'],
                'similarity': r['similarity'],
                'is_relevant': None  # 用户反馈
            }
            for r in results
        ],
        'user_feedback': user_feedback,
        'timestamp': time.time()
    }
    # 保存到数据库或日志文件
    save_search_log(log_entry)
```

#### 2. 阈值测试
```python
def test_thresholds(db, test_queries, thresholds=[0.6, 0.65, 0.7, 0.75, 0.8]):
    """测试不同阈值的效果"""
    service = EmbeddingService()
    results = []
    
    for threshold in thresholds:
        precision_scores = []
        recall_scores = []
        
        for query, expected_relevant in test_queries:
            # 执行检索
            retrieved = service.find_similar_chapters(
                db=db,
                novel_id=novel_id,
                query_text=query,
                similarity_threshold=threshold,
                limit=10
            )
            
            # 计算精度和召回率
            retrieved_ids = {r['chapter_id'] for r in retrieved}
            expected_ids = set(expected_relevant)
            
            if retrieved_ids:
                precision = len(retrieved_ids & expected_ids) / len(retrieved_ids)
                precision_scores.append(precision)
            
            if expected_ids:
                recall = len(retrieved_ids & expected_ids) / len(expected_ids)
                recall_scores.append(recall)
        
        avg_precision = statistics.mean(precision_scores) if precision_scores else 0
        avg_recall = statistics.mean(recall_scores) if recall_scores else 0
        f1_score = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0
        
        results.append({
            'threshold': threshold,
            'precision': avg_precision,
            'recall': avg_recall,
            'f1_score': f1_score
        })
    
    return results
```

#### 3. 阈值分析
```python
def analyze_optimal_threshold(search_logs):
    """分析最优阈值"""
    threshold_stats = {}
    
    for log in search_logs:
        threshold = log['threshold']
        if threshold not in threshold_stats:
            threshold_stats[threshold] = {
                'total_searches': 0,
                'relevant_results': 0,
                'total_results': 0,
                'user_satisfaction': []
            }
        
        stats = threshold_stats[threshold]
        stats['total_searches'] += 1
        stats['total_results'] += len(log['results'])
        
        # 统计相关结果（基于用户反馈）
        for result in log['results']:
            if result.get('is_relevant'):
                stats['relevant_results'] += 1
        
        if log.get('user_feedback'):
            stats['user_satisfaction'].append(log['user_feedback'])
    
    # 计算各阈值的指标
    for threshold, stats in threshold_stats.items():
        precision = stats['relevant_results'] / stats['total_results'] if stats['total_results'] > 0 else 0
        avg_satisfaction = statistics.mean(stats['user_satisfaction']) if stats['user_satisfaction'] else 0
        
        threshold_stats[threshold]['precision'] = precision
        threshold_stats[threshold]['avg_satisfaction'] = avg_satisfaction
    
    # 找到最优阈值（平衡精度和用户满意度）
    optimal = max(
        threshold_stats.items(),
        key=lambda x: x[1]['precision'] * 0.7 + x[1]['avg_satisfaction'] * 0.3
    )
    
    return optimal[0], threshold_stats
```

#### 4. 动态阈值配置
```python
# 配置文件或数据库
THRESHOLD_CONFIG = {
    'chapter_similarity': 0.7,  # 章节相似度
    'paragraph_similarity': 0.75,  # 段落相似度
    'foreshadowing_match': 0.8,  # 伏笔匹配
    'context_retrieval': 0.65,  # 上下文检索
    'consistency_check': 0.65,  # 一致性检查
}

# 使用配置
similar = service.find_similar_chapters(
    db=db,
    novel_id=novel_id,
    query_text=query_text,
    similarity_threshold=THRESHOLD_CONFIG['chapter_similarity']
)
```

### 当前建议阈值

| 用途 | 当前阈值 | 说明 |
|------|---------|------|
| 章节级检索 | 0.7 | 整体相似性，平衡精度和召回率 |
| 段落级匹配 | 0.75 | 精确匹配，更高精度 |
| 伏笔匹配 | 0.8 | 高精度，避免误匹配 |
| 生成前检查 | 0.8 | 警告阈值，较严格 |
| 生成后检查 | 0.85 | 严格阈值，识别重复 |
| 一致性检查 | 0.65 | 较宽松，考虑多角色场景 |
| 上下文检索 | 0.6 | 较低，获取更多相关章节 |

### 预期效果
- 📈 检索精度提升：10-20%
- 📈 用户满意度提升：通过优化阈值
- 💰 成本：主要是时间和数据分析成本

### 实施难度
- **难度**: 低（只需调整参数，但需要数据分析）
- **时间**: 1-2周（包括数据收集和分析）
- **依赖**: 实际使用数据、用户反馈

### 实施步骤
1. 收集实际使用数据（1-2周）
2. 记录检索日志和用户反馈
3. 测试不同阈值的效果
4. 分析最优阈值
5. 更新配置并验证效果

---

## 📊 任务对比

| 任务 | 优先级 | 难度 | 时间 | 预期效果 | 适用场景 |
|------|--------|------|------|---------|---------|
| Redis缓存 | 低 | 中等 | 1-2天 | 检索速度提升30-50% | 频繁检索，性能瓶颈 |
| 批量优化 | 低 | 中等 | 2-3天 | 处理速度提升50-70% | 批量处理，API限流 |
| 阈值调优 | 中 | 低 | 1-2周 | 精度提升10-20% | 有实际使用数据 |

## 💡 建议

### 何时实施Redis缓存
- 章节数量 > 500
- 日均检索次数 > 1000
- 数据库查询响应时间 > 500ms
- 有Redis环境或可以部署

### 何时实施批量优化
- 需要批量处理 > 100个章节
- API调用频率受限
- 需要批量导入历史数据
- 有任务队列系统（Celery/RQ）

### 何时实施阈值调优
- 系统已运行1个月以上
- 收集了足够的检索数据（> 100次）
- 发现检索结果不准确
- 有用户反馈数据

## ⚠️ 注意事项

1. **不要过早优化**：先确保核心功能稳定
2. **衡量成本效益**：评估实施成本和预期收益
3. **逐步实施**：一次实施一个优化，观察效果
4. **监控效果**：实施后持续监控性能指标

## 📚 相关文档

- **完整方案**：`PGVECTOR_INTEGRATION_PLAN.md`
- **使用指南**：`PGVECTOR_README.md`
- **性能测试**：`TEST_PERFORMANCE.md`

