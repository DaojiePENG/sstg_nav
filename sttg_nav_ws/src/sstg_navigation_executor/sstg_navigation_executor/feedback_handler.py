"""
反馈处理器 - 生成和处理导航反馈
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
import json


class NavigationStatus(Enum):
    """导航状态枚举"""
    IDLE = "idle"
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    REACHED = "reached"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class NavigationFeedback:
    """
    导航反馈信息
    
    Attributes:
        node_id: 目标节点 ID
        status: 导航状态
        progress: 进度 (0.0-1.0)
        current_pose: 当前位置 (x, y, theta)
        distance_to_target: 到目标的距离
        estimated_time_remaining: 预计剩余时间（秒）
        error_message: 错误信息（如果有的话）
        timestamp: 时间戳
        history: 历史日志
    """
    node_id: int
    status: NavigationStatus = NavigationStatus.IDLE
    progress: float = 0.0
    current_pose: tuple = field(default_factory=lambda: (0.0, 0.0, 0.0))
    distance_to_target: float = 0.0
    estimated_time_remaining: float = 0.0
    error_message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    history: list = field(default_factory=list)
    
    def add_log(self, message: str, level: str = "INFO"):
        """添加日志"""
        log_entry = {
            'time': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.history.append(log_entry)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['current_pose'] = {
            'x': self.current_pose[0],
            'y': self.current_pose[1],
            'theta': self.current_pose[2]
        }
        return data
    
    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def is_success(self) -> bool:
        """是否成功"""
        return self.status == NavigationStatus.REACHED
    
    def is_failure(self) -> bool:
        """是否失败"""
        return self.status in [NavigationStatus.FAILED, NavigationStatus.CANCELLED]
    
    def is_completed(self) -> bool:
        """是否完成"""
        return self.status in [NavigationStatus.REACHED, NavigationStatus.FAILED, NavigationStatus.CANCELLED]


class FeedbackHandler:
    """
    反馈处理器
    
    功能：
    - 创建和管理反馈信息
    - 追踪导航历史
    - 生成反馈报告
    """
    
    def __init__(self):
        """初始化反馈处理器"""
        self.current_feedback: Optional[NavigationFeedback] = None
        self.feedback_history = []
    
    def start_navigation(self, node_id: int) -> NavigationFeedback:
        """
        开始导航
        
        Args:
            node_id: 目标节点 ID
            
        Returns:
            反馈对象
        """
        self.current_feedback = NavigationFeedback(
            node_id=node_id,
            status=NavigationStatus.STARTING
        )
        self.current_feedback.add_log(f"开始导航到节点 {node_id}", "INFO")
        return self.current_feedback
    
    def update_progress(
        self,
        progress: float,
        current_pose: tuple,
        distance_to_target: float,
        estimated_time: float = 0.0
    ):
        """
        更新导航进度
        
        Args:
            progress: 进度 (0.0-1.0)
            current_pose: 当前位置 (x, y, theta)
            distance_to_target: 到目标的距离
            estimated_time: 预计剩余时间
        """
        if not self.current_feedback:
            return
        
        self.current_feedback.progress = max(0.0, min(1.0, progress))
        self.current_feedback.current_pose = current_pose
        self.current_feedback.distance_to_target = distance_to_target
        self.current_feedback.estimated_time_remaining = estimated_time
        
        if self.current_feedback.status == NavigationStatus.STARTING:
            self.current_feedback.status = NavigationStatus.IN_PROGRESS
    
    def on_reached(self):
        """导航成功"""
        if not self.current_feedback:
            return
        
        self.current_feedback.status = NavigationStatus.REACHED
        self.current_feedback.progress = 1.0
        self.current_feedback.error_message = ""
        self.current_feedback.add_log("✓ 已到达目标", "INFO")
        
        self.feedback_history.append(self.current_feedback)
    
    def on_failed(self, error_message: str):
        """导航失败"""
        if not self.current_feedback:
            return
        
        self.current_feedback.status = NavigationStatus.FAILED
        self.current_feedback.error_message = error_message
        self.current_feedback.add_log(f"❌ 导航失败: {error_message}", "ERROR")
        
        self.feedback_history.append(self.current_feedback)
    
    def on_cancelled(self):
        """导航被取消"""
        if not self.current_feedback:
            return
        
        self.current_feedback.status = NavigationStatus.CANCELLED
        self.current_feedback.error_message = "导航被取消"
        self.current_feedback.add_log("⏸ 导航已取消", "WARN")
        
        self.feedback_history.append(self.current_feedback)
    
    def get_current_feedback(self) -> Optional[NavigationFeedback]:
        """获取当前反馈"""
        return self.current_feedback
    
    def get_feedback_history(self, limit: int = 10) -> list:
        """
        获取反馈历史
        
        Args:
            limit: 返回的最大条数
            
        Returns:
            反馈列表
        """
        return self.feedback_history[-limit:]
    
    def get_statistics(self) -> dict:
        """
        获取统计信息
        
        Returns:
            包含统计数据的字典
        """
        total = len(self.feedback_history)
        success = sum(1 for f in self.feedback_history if f.is_success())
        failed = sum(1 for f in self.feedback_history if f.is_failure())
        
        return {
            'total_navigations': total,
            'successful': success,
            'failed': failed,
            'success_rate': success / total * 100 if total > 0 else 0.0
        }
