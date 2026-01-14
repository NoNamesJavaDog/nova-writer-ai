# 审计系统设计方案

## 一、设计目标

在一键生成卷大纲和一键生成章节列表任务完成后，自动进行质量审计检查，发现问题并提供修复建议。

## 二、审计检查内容

### 2.1 卷大纲审计检查项

#### 1. 结构完整性检查
- ✅ 是否包含【字数规划】
- ✅ 是否包含【章节规划】
- ✅ 是否包含本卷定位、结构、剧情节点等必要部分
- ⚠️ 字数规划格式是否正确（如：15-30万字）
- ⚠️ 章节规划是否为具体数字（不能是范围）

#### 2. 内容质量检查
- ⚠️ 字数规划是否合理（通常15-30万字）
- ⚠️ 章节数量是否合理（通常10-30章）
- ⚠️ 剧情节点数量是否充足（至少12-25个）
- ⚠️ 关键场景建议是否提供（至少8个）

#### 3. 一致性检查
- ⚠️ 字数规划与章节规划是否匹配（平均每章字数合理）
- ⚠️ 本卷内容是否与全书大纲一致
- ⚠️ 是否包含后续卷的内容（不应该包含）

#### 4. 格式检查
- ⚠️ Markdown格式是否正确
- ⚠️ 标题层级是否合理
- ⚠️ 列表格式是否正确

### 2.2 章节列表审计检查项

#### 1. 数量检查
- ✅ 章节数量是否符合预期（与卷大纲的【章节规划】对比）
- ⚠️ 章节数量是否在合理范围内（10-50章）

#### 2. 内容完整性检查
- ✅ 每个章节是否有标题
- ✅ 每个章节是否有摘要
- ⚠️ 章节标题是否重复
- ⚠️ 章节摘要是否为空或过短（少于10字）

#### 3. 顺序和连贯性检查
- ✅ 章节顺序是否正确（chapter_order连续）
- ⚠️ 章节标题是否体现故事发展（如：第1章、第2章...）
- ⚠️ 相邻章节摘要是否有关联性

#### 4. 一致性检查
- ⚠️ 章节内容是否与卷大纲的剧情节点对应
- ⚠️ 章节是否包含后续卷的内容（不应该包含）
- ⚠️ 章节是否与全书大纲一致

#### 5. 质量检查
- ⚠️ 章节标题是否过于简单（如：只有"第一章"）
- ⚠️ 章节摘要是否过于简短（建议至少20字）
- ⚠️ 章节摘要是否包含关键信息（人物、事件、冲突）

## 三、系统架构设计

### 3.1 审计服务模块

```
backend/services/audit_service.py
```

**核心类：**
- `AuditService` - 审计服务主类
- `VolumeOutlineAuditor` - 卷大纲审计器
- `ChapterListAuditor` - 章节列表审计器

### 3.2 审计结果模型

```python
class AuditResult:
    - status: str  # "passed", "warning", "failed"
    - checks: List[AuditCheck]  # 检查项列表
    - summary: str  # 审计摘要
    - suggestions: List[str]  # 修复建议

class AuditCheck:
    - check_type: str  # 检查类型
    - severity: str  # "error", "warning", "info"
    - message: str  # 检查结果消息
    - passed: bool  # 是否通过
    - details: dict  # 详细信息
    - suggestion: str  # 修复建议（可选）
```

### 3.3 审计触发时机

1. **任务完成时自动触发**
   - 在 `generate_volume_outline_task` 完成后
   - 在 `generate_chapters_task` 完成后
   - 审计结果保存到任务结果中

2. **手动触发**
   - 提供独立的审计接口：`POST /api/novels/{novel_id}/volumes/{volume_id}/audit-outline`
   - 提供独立的审计接口：`POST /api/novels/{novel_id}/volumes/{volume_id}/audit-chapters`

### 3.4 审计结果存储

1. **任务结果中存储**
   - 在 `Task.result` 中添加 `audit_result` 字段
   - 格式：JSON字符串

2. **独立审计记录表（可选）**
   - 如果需要历史审计记录，可以创建 `AuditRecord` 表
   - 字段：id, novel_id, volume_id, audit_type, audit_result, created_at

## 四、实现方案

### 4.1 审计服务接口设计

```python
class AuditService:
    def audit_volume_outline(
        self, 
        novel_id: str, 
        volume_id: str, 
        volume_outline: str,
        full_outline: str = None
    ) -> AuditResult:
        """审计卷大纲"""
        pass
    
    def audit_chapter_list(
        self,
        novel_id: str,
        volume_id: str,
        chapters: List[Chapter],
        volume_outline: str = None
    ) -> AuditResult:
        """审计章节列表"""
        pass
```

### 4.2 审计检查器实现

#### 卷大纲审计器

```python
class VolumeOutlineAuditor:
    def check_structure(self, outline: str) -> List[AuditCheck]:
        """检查结构完整性"""
        checks = []
        
        # 检查字数规划
        if "【字数规划】" not in outline:
            checks.append(AuditCheck(
                check_type="structure",
                severity="error",
                message="缺少【字数规划】",
                passed=False,
                suggestion="请确保卷大纲包含【字数规划】部分"
            ))
        
        # 检查章节规划
        if "【章节规划】" not in outline:
            checks.append(AuditCheck(
                check_type="structure",
                severity="error",
                message="缺少【章节规划】",
                passed=False,
                suggestion="请确保卷大纲包含【章节规划】部分"
            ))
        
        # ... 其他检查
        
        return checks
    
    def check_content_quality(self, outline: str) -> List[AuditCheck]:
        """检查内容质量"""
        pass
    
    def check_consistency(self, outline: str, full_outline: str) -> List[AuditCheck]:
        """检查一致性"""
        pass
```

#### 章节列表审计器

```python
class ChapterListAuditor:
    def check_count(self, chapters: List[Chapter], expected_count: int) -> List[AuditCheck]:
        """检查章节数量"""
        checks = []
        
        actual_count = len(chapters)
        if actual_count != expected_count:
            checks.append(AuditCheck(
                check_type="count",
                severity="warning",
                message=f"章节数量不匹配：期望{expected_count}章，实际{actual_count}章",
                passed=False,
                details={"expected": expected_count, "actual": actual_count},
                suggestion="请检查章节规划或重新生成章节列表"
            ))
        
        return checks
    
    def check_completeness(self, chapters: List[Chapter]) -> List[AuditCheck]:
        """检查内容完整性"""
        pass
    
    def check_consistency(self, chapters: List[Chapter], volume_outline: str) -> List[AuditCheck]:
        """检查一致性"""
        pass
```

### 4.3 任务集成

在任务完成时调用审计：

```python
# 在 generate_volume_outline_task 完成后
def execute_volume_outline_generation():
    # ... 生成卷大纲 ...
    
    # 任务完成后进行审计
    from services.audit_service import AuditService
    audit_service = AuditService()
    audit_result = audit_service.audit_volume_outline(
        novel_id=novel_id,
        volume_id=volume.id,
        volume_outline=volume.outline,
        full_outline=novel_obj.full_outline
    )
    
    # 将审计结果添加到任务结果中
    task_result = {
        "volume_id": volume.id,
        "volume_title": volume.title,
        "audit_result": audit_result.to_dict()  # 审计结果
    }
    task_obj.result = json.dumps(task_result)
```

## 五、前端展示方案

### 5.1 审计结果展示

在任务完成后，前端显示审计结果：

1. **审计状态指示器**
   - ✅ 通过（绿色）
   - ⚠️ 警告（黄色）
   - ❌ 失败（红色）

2. **审计详情面板**
   - 显示所有检查项
   - 按严重程度分组（错误、警告、信息）
   - 显示修复建议

3. **审计摘要**
   - 总检查项数
   - 通过/警告/失败数量
   - 关键问题摘要

### 5.2 前端组件设计

```typescript
interface AuditResult {
  status: 'passed' | 'warning' | 'failed';
  checks: AuditCheck[];
  summary: string;
  suggestions: string[];
}

interface AuditCheck {
  checkType: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  passed: boolean;
  details?: Record<string, any>;
  suggestion?: string;
}

// 组件
<AuditResultPanel auditResult={auditResult} />
```

## 六、扩展性设计

### 6.1 可配置的检查规则

通过配置文件定义检查规则：

```python
AUDIT_RULES = {
    "volume_outline": {
        "min_word_count": 150000,
        "max_word_count": 300000,
        "min_chapter_count": 10,
        "max_chapter_count": 30,
        "min_plot_nodes": 12,
        "min_scenes": 8
    },
    "chapter_list": {
        "min_summary_length": 20,
        "max_title_length": 50,
        "check_duplicate_titles": True,
        "check_sequence": True
    }
}
```

### 6.2 可扩展的检查器

通过插件机制支持自定义检查器：

```python
class BaseAuditor:
    def register_checker(self, checker: Callable):
        """注册自定义检查器"""
        pass
```

## 七、实施步骤

### 阶段1：基础审计框架
1. 创建 `AuditService` 基础类
2. 定义 `AuditResult` 和 `AuditCheck` 模型
3. 实现基本的审计接口

### 阶段2：卷大纲审计
1. 实现 `VolumeOutlineAuditor`
2. 实现结构完整性检查
3. 实现内容质量检查
4. 集成到 `generate_volume_outline_task`

### 阶段3：章节列表审计
1. 实现 `ChapterListAuditor`
2. 实现数量检查
3. 实现内容完整性检查
4. 集成到 `generate_chapters_task`

### 阶段4：前端展示
1. 创建审计结果展示组件
2. 在任务完成时显示审计结果
3. 提供审计详情面板

### 阶段5：优化和扩展
1. 添加更多检查规则
2. 优化检查性能
3. 支持自定义检查器

## 八、示例输出

### 审计结果示例

```json
{
  "status": "warning",
  "summary": "发现3个警告，0个错误",
  "checks": [
    {
      "check_type": "structure",
      "severity": "warning",
      "message": "章节规划格式不规范：应为具体数字",
      "passed": false,
      "details": {
        "found": "10-15章",
        "expected": "12章"
      },
      "suggestion": "请修改为具体数字，如：12章"
    },
    {
      "check_type": "count",
      "severity": "warning",
      "message": "章节数量不匹配：期望12章，实际10章",
      "passed": false,
      "details": {
        "expected": 12,
        "actual": 10
      },
      "suggestion": "请重新生成章节列表或调整章节规划"
    },
    {
      "check_type": "completeness",
      "severity": "info",
      "message": "第3章摘要过短（仅8字）",
      "passed": true,
      "details": {
        "chapter_index": 3,
        "summary_length": 8
      },
      "suggestion": "建议补充章节摘要，至少20字"
    }
  ],
  "suggestions": [
    "修改章节规划为具体数字",
    "重新生成章节列表以匹配章节规划",
    "补充章节摘要内容"
  ]
}
```

## 九、优势

1. **自动化**：任务完成后自动审计，无需手动检查
2. **可扩展**：易于添加新的检查规则
3. **可配置**：检查规则可配置，适应不同需求
4. **用户友好**：清晰的审计结果展示和修复建议
5. **非阻塞**：审计失败不影响任务完成，只提供警告

## 十、注意事项

1. **性能考虑**：审计不应显著影响任务完成时间
2. **准确性**：检查规则需要准确，避免误报
3. **用户体验**：审计结果应该清晰易懂，提供可操作的修复建议
4. **可选择性**：用户可以选择忽略某些警告


