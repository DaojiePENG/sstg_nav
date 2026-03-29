"""
导航监控器 - 监控机器人位置和导航状态
"""

from typing import Optional, Tuple, Callable
from geometry_msgs.msg import PoseWithCovarianceStamped
from tf_transformations import euler_from_quaternion
import rclpy
from rclpy.node import Node
import math


class NavigationMonitor:
    """
    导航监控器
    
    功能：
    - 订阅机器人位置话题
    - 监控导航进度
    - 计算距离和方向
    """
    
    def __init__(self, node: Node):
        """
        初始化监控器
        
        Args:
            node: ROS2 节点
        """
        self.node = node
        self.logger = node.get_logger()
        
        # 当前位置
        self.current_pose = None
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0
        
        # 目标信息
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_theta = 0.0
        
        # 订阅位置话题
        self.pose_subscription = node.create_subscription(
            PoseWithCovarianceStamped,
            'amcl_pose',
            self._pose_callback,
            qos_profile=rclpy.qos.QoSProfile(depth=10)
        )
        
        self.logger.info("✓ 导航监控器初始化")
    
    def _pose_callback(self, msg: PoseWithCovarianceStamped):
        """处理位置更新"""
        self.current_pose = msg
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        # 从四元数提取欧拉角
        quat = msg.pose.pose.orientation
        roll, pitch, yaw = euler_from_quaternion([quat.x, quat.y, quat.z, quat.w])
        self.current_theta = yaw
    
    def set_target(self, x: float, y: float, theta: float = 0.0):
        """
        设置导航目标
        
        Args:
            x: 目标 X 坐标
            y: 目标 Y 坐标
            theta: 目标方向（弧度）
        """
        self.target_x = x
        self.target_y = y
        self.target_theta = theta
        self.logger.info(f"🎯 目标已设置: ({x:.2f}, {y:.2f}), θ={math.degrees(theta):.1f}°")
    
    def get_distance_to_target(self) -> float:
        """
        获取到目标的距离
        
        Returns:
            距离（米）
        """
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        return math.sqrt(dx*dx + dy*dy)
    
    def get_angle_to_target(self) -> float:
        """
        获取到目标的方向角
        
        Returns:
            方向角（弧度）
        """
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        return math.atan2(dy, dx)
    
    def get_progress(self, initial_distance: Optional[float] = None) -> float:
        """
        获取导航进度（0.0-1.0）
        
        Args:
            initial_distance: 初始距离（用于计算百分比）
            
        Returns:
            进度比例
        """
        if initial_distance is None or initial_distance <= 0.0:
            return 0.0
        
        current_distance = self.get_distance_to_target()
        progress = max(0.0, 1.0 - (current_distance / initial_distance))
        return min(1.0, progress)
    
    def is_near_target(self, threshold: float = 0.2) -> bool:
        """
        判断是否接近目标
        
        Args:
            threshold: 距离阈值（米）
            
        Returns:
            是否接近
        """
        return self.get_distance_to_target() < threshold
    
    def is_aligned_with_target(self, threshold: float = 0.1) -> bool:
        """
        判断方向是否对齐目标
        
        Args:
            threshold: 角度阈值（弧度）
            
        Returns:
            是否对齐
        """
        angle_diff = abs(self.current_theta - self.target_theta)
        # 处理角度环绕
        angle_diff = min(angle_diff, 2 * math.pi - angle_diff)
        return angle_diff < threshold
    
    def get_current_pose(self) -> Tuple[float, float, float]:
        """
        获取当前位置
        
        Returns:
            (x, y, theta)
        """
        return self.current_x, self.current_y, self.current_theta
    
    def get_target_pose(self) -> Tuple[float, float, float]:
        """
        获取目标位置
        
        Returns:
            (x, y, theta)
        """
        return self.target_x, self.target_y, self.target_theta
    
    def get_status_dict(self) -> dict:
        """
        获取状态字典
        
        Returns:
            包含各种状态信息的字典
        """
        distance = self.get_distance_to_target()
        
        return {
            'current_position': (self.current_x, self.current_y),
            'current_heading': math.degrees(self.current_theta),
            'target_position': (self.target_x, self.target_y),
            'target_heading': math.degrees(self.target_theta),
            'distance_to_target': distance,
            'angle_to_target': math.degrees(self.get_angle_to_target()),
            'near_target': self.is_near_target(),
            'aligned': self.is_aligned_with_target()
        }
