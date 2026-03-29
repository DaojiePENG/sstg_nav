"""
导航规划器 - 构建导航计划
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import json


@dataclass
class NavigationStep:
    """导航步骤"""
    step_id: int
    from_node_id: int
    to_node_id: int
    action: str  # navigate, rotate, observe
    description: str
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'action': self.action,
            'description': self.description
        }


@dataclass
class NavigationPlanResult:
    """导航计划结果"""
    plan_id: str
    start_node_id: int
    goal_node_id: int
    path: List[int]  # 路径上的节点 ID 列表
    steps: List[NavigationStep]  # 详细步骤
    total_distance: float
    estimated_time: float  # 秒
    success: bool
    reasoning: str
    candidate_indices: List[int]  # 候选点在原列表中的索引
    
    def to_dict(self) -> Dict:
        return {
            'plan_id': self.plan_id,
            'start_node_id': self.start_node_id,
            'goal_node_id': self.goal_node_id,
            'path': self.path,
            'steps': [s.to_dict() for s in self.steps],
            'total_distance': self.total_distance,
            'estimated_time': self.estimated_time,
            'success': self.success,
            'reasoning': self.reasoning,
            'candidate_indices': self.candidate_indices
        }


class NavigationPlanner:
    """
    导航规划器
    
    功能：
    - 从候选点构建导航计划
    - 生成路径规划
    - 生成执行步骤
    """
    
    def __init__(self):
        """初始化规划器"""
        self.logger: Optional[callable] = None
        self.avg_move_speed = 0.5  # m/s
        self.avg_rotate_speed = 45  # deg/s
        
    def set_logger(self, logger_func):
        """设置日志函数"""
        self.logger = logger_func
    
    def _log(self, msg: str):
        """记录日志"""
        if self.logger:
            self.logger(f"[NavigationPlanner] {msg}")
    
    def plan_navigation(self,
                       candidates: List,
                       topological_nodes: Dict,
                       current_node_id: Optional[int] = None,
                       current_pose: Optional[Tuple] = None) -> NavigationPlanResult:
        """
        规划导航
        
        Args:
            candidates: 候选点列表
            topological_nodes: 拓扑图节点 {node_id: node_info}
            current_node_id: 当前节点 ID
            current_pose: 当前位置
        
        Returns:
            导航计划
        """
        if not candidates:
            return NavigationPlanResult(
                plan_id="failed",
                start_node_id=current_node_id or -1,
                goal_node_id=-1,
                path=[],
                steps=[],
                total_distance=0.0,
                estimated_time=0.0,
                success=False,
                reasoning="没有有效的候选点",
                candidate_indices=[]
            )
        
        # 获取目标节点（最优候选）
        goal_node = candidates[0]
        goal_node_id = goal_node.node_id
        
        # 如果当前节点未知，使用最近的节点
        if current_node_id is None:
            current_node_id = self._find_closest_node(current_pose, topological_nodes)
        
        # 规划路径
        path = self._plan_path(
            current_node_id,
            goal_node_id,
            topological_nodes
        )
        
        if not path:
            return NavigationPlanResult(
                plan_id="failed",
                start_node_id=current_node_id,
                goal_node_id=goal_node_id,
                path=[],
                steps=[],
                total_distance=0.0,
                estimated_time=0.0,
                success=False,
                reasoning=f"无法规划从节点 {current_node_id} 到节点 {goal_node_id} 的路径",
                candidate_indices=[]
            )
        
        # 生成导航步骤
        steps = self._generate_navigation_steps(path, topological_nodes)
        
        # 计算距离和时间
        total_distance = self._calculate_path_distance(path, topological_nodes)
        estimated_time = self._estimate_navigation_time(steps, total_distance)
        
        # 获取候选点索引
        candidate_indices = list(range(len(candidates)))
        
        plan = NavigationPlanResult(
            plan_id=f"plan_{current_node_id}_to_{goal_node_id}",
            start_node_id=current_node_id,
            goal_node_id=goal_node_id,
            path=path,
            steps=steps,
            total_distance=total_distance,
            estimated_time=estimated_time,
            success=True,
            reasoning=f"规划成功: {goal_node.match_reason}",
            candidate_indices=candidate_indices
        )
        
        self._log(f"规划完成: {len(path)} 个节点, 距离 {total_distance:.2f}m, 预计 {estimated_time:.1f}s")
        
        return plan
    
    def _find_closest_node(self,
                          pose: Optional[Tuple],
                          topological_nodes: Dict) -> int:
        """
        查找离当前位置最近的节点
        """
        if pose is None or not topological_nodes:
            return next(iter(topological_nodes.keys())) if topological_nodes else -1
        
        min_distance = float('inf')
        closest_node_id = -1
        
        for node_id, node_info in topological_nodes.items():
            node_pose = node_info.get('pose', {})
            dx = node_pose.get('x', 0) - pose[0]
            dy = node_pose.get('y', 0) - pose[1]
            distance = (dx**2 + dy**2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_node_id = node_id
        
        return closest_node_id
    
    def _plan_path(self,
                   start_node_id: int,
                   goal_node_id: int,
                   topological_nodes: Dict) -> List[int]:
        """
        使用 Dijkstra 算法规划路径
        """
        if start_node_id == goal_node_id:
            return [start_node_id]
        
        # 初始化
        distances = {node_id: float('inf') for node_id in topological_nodes}
        distances[start_node_id] = 0
        previous = {node_id: None for node_id in topological_nodes}
        unvisited = set(topological_nodes.keys())
        
        while unvisited:
            # 选择未访问节点中距离最小的
            current = min(
                unvisited,
                key=lambda node: distances[node],
                default=None
            )
            
            if current is None or distances[current] == float('inf'):
                break
            
            if current == goal_node_id:
                break
            
            unvisited.remove(current)
            
            # 更新邻居
            current_node = topological_nodes[current]
            neighbors = current_node.get('connections', [])
            
            for neighbor_id in neighbors:
                if neighbor_id in unvisited:
                    # 计算距离
                    current_pose = current_node.get('pose', {})
                    neighbor_node = topological_nodes.get(neighbor_id, {})
                    neighbor_pose = neighbor_node.get('pose', {})
                    
                    dx = neighbor_pose.get('x', 0) - current_pose.get('x', 0)
                    dy = neighbor_pose.get('y', 0) - current_pose.get('y', 0)
                    edge_distance = (dx**2 + dy**2) ** 0.5
                    
                    new_distance = distances[current] + edge_distance
                    
                    if new_distance < distances[neighbor_id]:
                        distances[neighbor_id] = new_distance
                        previous[neighbor_id] = current
        
        # 重建路径
        path = []
        current = goal_node_id
        
        while current is not None:
            path.insert(0, current)
            current = previous[current]
        
        # 验证路径
        if path[0] != start_node_id:
            return []
        
        return path
    
    def _generate_navigation_steps(self,
                                  path: List[int],
                                  topological_nodes: Dict) -> List[NavigationStep]:
        """
        从路径生成导航步骤
        """
        steps = []
        step_id = 0
        
        for i in range(len(path) - 1):
            from_node_id = path[i]
            to_node_id = path[i + 1]
            
            from_node = topological_nodes.get(from_node_id, {})
            to_node = topological_nodes.get(to_node_id, {})
            
            from_name = from_node.get('name', f'Node_{from_node_id}')
            to_name = to_node.get('name', f'Node_{to_node_id}')
            
            step = NavigationStep(
                step_id=step_id,
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                action='navigate',
                description=f"从 {from_name} 导航到 {to_name}"
            )
            
            steps.append(step)
            step_id += 1
            
            # 到达目标后观察
            if i == len(path) - 2:
                step = NavigationStep(
                    step_id=step_id,
                    from_node_id=to_node_id,
                    to_node_id=to_node_id,
                    action='observe',
                    description=f"在 {to_name} 观察"
                )
                steps.append(step)
        
        return steps
    
    def _calculate_path_distance(self,
                                path: List[int],
                                topological_nodes: Dict) -> float:
        """
        计算路径总距离
        """
        total_distance = 0.0
        
        for i in range(len(path) - 1):
            from_node_id = path[i]
            to_node_id = path[i + 1]
            
            from_node = topological_nodes.get(from_node_id, {})
            to_node = topological_nodes.get(to_node_id, {})
            
            from_pose = from_node.get('pose', {})
            to_pose = to_node.get('pose', {})
            
            dx = to_pose.get('x', 0) - from_pose.get('x', 0)
            dy = to_pose.get('y', 0) - from_pose.get('y', 0)
            distance = (dx**2 + dy**2) ** 0.5
            
            total_distance += distance
        
        return total_distance
    
    def _estimate_navigation_time(self,
                                 steps: List[NavigationStep],
                                 total_distance: float) -> float:
        """
        估计导航时间
        """
        # 基础移动时间
        movement_time = total_distance / self.avg_move_speed
        
        # 每次转向、观察等额外时间
        observation_time = sum(1 for s in steps if s.action == 'observe') * 2.0
        
        total_time = movement_time + observation_time
        
        return total_time
