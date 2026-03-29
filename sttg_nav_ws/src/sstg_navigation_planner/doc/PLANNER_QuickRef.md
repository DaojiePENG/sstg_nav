# SSTG Navigation Planner - 快速参考

## ⚡ 一行启动

```bash
ros2 run sstg_navigation_planner planning_node
```

## 🎯 常用命令

### 调用规划服务
```bash
# 基本查询：导航到客厅
ros2 service call /plan_navigation sstg_msgs/srv/PlanNavigation \
  '{intent: "navigate_to", entities: "[\"客厅\"]", confidence: 0.95, current_node: 0}'

# 物体定位：找椅子
ros2 service call /plan_navigation sstg_msgs/srv/PlanNavigation \
  '{intent: "locate_object", entities: "[\"椅子\"]", confidence: 0.9, current_node: 0}'
```

### 监听规划结果
```bash
ros2 topic echo /navigation_plans
```

## 🐍 Python 快速示例

### 示例 1：基本语义匹配
```python
from sstg_navigation_planner import SemanticMatcher

matcher = SemanticMatcher()
nodes = {
    0: {'name': '客厅', 'room_type': 'living_room', 'semantic_tags': ['sofa', 'TV']},
    1: {'name': '卧室', 'room_type': 'bedroom', 'semantic_tags': ['bed']}
}

matches = matcher.match_query_to_nodes(
    intent='navigate_to',
    entities=['客厅'],
    confidence=0.95,
    topological_nodes=nodes
)

for m in matches:
    print(f"{m.node_name}: {m.match_score:.2f}")
```

### 示例 2：完整规划流程
```python
from sstg_navigation_planner import SemanticMatcher, CandidateGenerator, NavigationPlanner

matcher = SemanticMatcher()
generator = CandidateGenerator()
planner = NavigationPlanner()

# 拓扑图
nodes = {
    0: {
        'name': '客厅',
        'room_type': 'living_room',
        'pose': {'x': 0, 'y': 0, 'z': 0},
        'connections': [1, 2]
    },
    1: {
        'name': '卧室',
        'room_type': 'bedroom',
        'pose': {'x': 5, 'y': 0, 'z': 0},
        'connections': [0, 2]
    },
    2: {
        'name': '厨房',
        'room_type': 'kitchen',
        'pose': {'x': 0, 'y': 5, 'z': 0},
        'connections': [0, 1]
    }
}

# 1. 语义匹配
matches = matcher.match_query_to_nodes('navigate_to', ['厨房'], 0.95, nodes)

# 2. 候选生成
candidates = generator.generate_candidates(matches, nodes, (0, 0, 0))

# 3. 路径规划
plan = planner.plan_navigation(candidates, nodes, current_node_id=0)

# 4. 打印结果
print(f"规划成功: {plan.success}")
print(f"路径: {plan.path}")
print(f"距离: {plan.total_distance:.2f}m")
print(f"时间: {plan.estimated_time:.1f}s")
```

### 示例 3：候选点评分
```python
from sstg_navigation_planner import CandidateGenerator

generator = CandidateGenerator(max_candidates=5)
candidates = generator.generate_candidates(matches, nodes, current_pose=(1, 1, 0))

for i, c in enumerate(candidates):
    print(f"{i+1}. {c.node_name}")
    print(f"   综合得分: {c.relevance_score:.3f}")
    print(f"   - 语义: {c.semantic_score:.3f}")
    print(f"   - 距离: {c.distance_score:.3f}")
    print(f"   - 可达性: {c.accessibility_score:.3f}")
```

## 📁 目录结构

```
sstg_navigation_planner/
├── sstg_navigation_planner/
│   ├── __init__.py                    # 包初始化与导出
│   ├── semantic_matcher.py            # 语义匹配（MatchResult）
│   ├── candidate_generator.py         # 候选生成（CandidatePoint）
│   ├── navigation_planner.py          # 路径规划（NavigationPlanResult）
│   └── planning_node.py               # ROS2 节点
├── test/
│   └── test_navigation_planner.py     # 单元测试
├── doc/
│   ├── MODULE_GUIDE.md                # 完整指南
│   └── PLANNER_QuickRef.md            # 快速参考（本文件）
├── setup.py                           # Python 包配置
├── package.xml                        # ROS2 包定义
└── resource/sstg_navigation_planner   # 包索引文件
```

## 🔧 参数配置

### 通过 ROS2 参数
```bash
ros2 run sstg_navigation_planner planning_node \
  --ros-args \
  -p max_candidates:=10 \
  -p min_match_score:=0.5 \
  -p map_service_name:='/custom_map_service'
```

## 🎨 意图与匹配

| 意图 | 实体类型 | 示例查询 | 匹配策略 |
|-----|---------|---------|---------|
| `navigate_to` | 房间名称 | "带我去客厅" | 房间类型匹配 |
| `locate_object` | 物体名称 | "找椅子" | 语义标签匹配 |
| `query_info` | 通用 | "这里是什么" | 上下文匹配 |
| `ask_direction` | 位置 | "怎么走到卧室" | 路径规划 |

## 📊 API 快速参考

### SemanticMatcher
```python
matcher = SemanticMatcher()
matcher.set_logger(print_func)

matches = matcher.match_query_to_nodes(
    intent="navigate_to",      # 意图
    entities=["客厅"],         # 实体列表
    confidence=0.95,           # 置信度
    topological_nodes=nodes    # 拓扑图
)
# 返回: List[MatchResult]
```

### CandidateGenerator
```python
generator = CandidateGenerator(max_candidates=5)
generator.set_logger(print_func)

candidates = generator.generate_candidates(
    match_results=matches,         # 匹配结果
    topological_nodes=nodes,       # 拓扑图
    current_pose=(x, y, z)        # 当前位置（可选）
)
# 返回: List[CandidatePoint]
```

### NavigationPlanner
```python
planner = NavigationPlanner()
planner.set_logger(print_func)

plan = planner.plan_navigation(
    candidates=candidates,         # 候选点
    topological_nodes=nodes,       # 拓扑图
    current_node_id=0,            # 当前节点
    current_pose=(x, y, z)        # 当前位置（可选）
)
# 返回: NavigationPlanResult
```

## 🧪 测试

```bash
# 运行所有测试
python3 test/test_navigation_planner.py

# 运行特定测试
python3 -m unittest test_navigation_planner.TestSemanticMatcher.test_room_match
```

## ⚙️ 得分计算

### 综合相关度得分（Relevance Score）
```
综合得分 = 语义得分×0.5 + 距离得分×0.3 + 可达性得分×0.2
```

### 语义匹配得分
```
基础相似度（40%） + 类型匹配（30%） + 置信度（30%）
```

### 距离得分
```
score = exp(-distance / 5.0)
距离越近，得分越高
```

### 可达性得分
```
根据连接数确定：
- 4+ 连接: 1.0
- 3 连接: 0.9
- 2 连接: 0.8
- 1 连接: 0.6
- 0 连接: 0.4（孤立）
```

## 🚀 性能提示

- **快速原型**：使用 mock 拓扑图进行开发测试
- **大规模图**：考虑实现 A* 算法替代 Dijkstra
- **实时应用**：预计算常用路径或使用缓存
- **多查询**：批量处理以减少重复计算

## 📞 常见问题

**Q: 如何添加自定义房间类型？**
A: 编辑 `SemanticMatcher.ROOM_TYPE_ALIASES`，添加别名映射

**Q: 如何修改候选点排序方式？**
A: 继承 `CandidateGenerator` 并重写 `_calculate_distance_score()` 等方法

**Q: 能否支持多语言？**
A: 扩展 `ROOM_TYPE_ALIASES` 和 `OBJECT_TYPE_MAPPING` 字典即可

**Q: 如何与 Nav2 集成？**
A: 在上游的 `sstg_navigation_executor` 模块中使用规划结果

## 🔗 相关文档

- [Module Guide](MODULE_GUIDE.md) - 详细文档
- [NLP Interface](../../sstg_nlp_interface/doc/NLP_QuickRef.md) - 自然语言理解
- [Map Manager](../../sstg_map_manager/SSTG_MapManager_QuickRef.md) - 拓扑图管理
