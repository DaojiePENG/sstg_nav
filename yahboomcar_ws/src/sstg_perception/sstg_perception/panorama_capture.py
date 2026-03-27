"""
全景图采集管理器 - 按 90 度间隔采集四个方向的图像
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json
import threading
import time


class PanoramaCapture:
    """
    全景图采集管理器
    
    功能：
    - 四个方向（0°/90°/180°/270°）图像采集
    - 图像保存和管理
    - 位姿与图像关联
    """
    
    def __init__(self, storage_path: str = '/tmp/sstg_panorama',
                 image_format: str = 'png'):
        """
        初始化全景图采集器
        
        Args:
            storage_path: 图像存储路径
            image_format: 图像格式 ('png' or 'jpg')
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.image_format = image_format
        self.panorama_angles = [0, 90, 180, 270]  # 四个采集方向
        self.images = {}  # {angle: image_array}
        self.image_paths = {}  # {angle: file_path}
        self.node_id = None
        self.timestamp = None
        self.pose = None
        self.lock = threading.Lock()
        
        self.get_logger_func = print  # 可以被覆盖用于 ROS2 日志
    
    def set_logger(self, logger_func) -> None:
        """设置日志函数"""
        self.get_logger_func = logger_func
    
    def capture_panorama(self, rgb_image: np.ndarray,
                        depth_image: Optional[np.ndarray] = None,
                        node_id: int = None,
                        pose: Dict = None) -> Dict:
        """
        采集一次全景图（单个方向）
        
        Args:
            rgb_image: RGB 图像
            depth_image: 深度图（可选）
            node_id: 节点 ID
            pose: 机器人位姿 {'x': float, 'y': float, 'theta': float}
        
        Returns:
            采集结果字典
        """
        if node_id is not None:
            self.node_id = node_id
        if pose is not None:
            self.pose = pose
        
        with self.lock:
            self.timestamp = datetime.now().isoformat()
            
            # 获取当前已采集的方向数（用于推断当前采集的角度）
            current_count = len(self.images)
            if current_count >= len(self.panorama_angles):
                self._reset_current_panorama()
                current_count = 0
            
            angle = self.panorama_angles[current_count]
            self.images[angle] = rgb_image.copy()
            
            # 保存图像文件
            image_path = self._save_image(rgb_image, angle)
            self.image_paths[angle] = str(image_path)
            
            if depth_image is not None:
                self._save_image(depth_image, angle, is_depth=True)
            
            result = {
                'angle': angle,
                'path': str(image_path),
                'timestamp': self.timestamp,
                'count': len(self.images),
                'complete': len(self.images) >= len(self.panorama_angles)
            }
            
            self.get_logger_func(f'✓ Captured panorama: angle={angle}°, path={image_path.name}')
            
            return result
    
    def capture_four_directions(self, camera_subscriber,
                               node_id: int,
                               pose: Dict,
                               rotation_callback=None,
                               wait_after_rotation: float = 1.5) -> Dict:
        """
        连续采集四个方向的图像（需要旋转）

        Args:
            camera_subscriber: CameraSubscriber 实例
            node_id: 节点 ID
            pose: 机器人位姿
            rotation_callback: 旋转回调函数(angle) -> bool
            wait_after_rotation: 旋转后等待时间（秒），让图像稳定

        Returns:
            完整的全景数据字典，失败返回None
        """
        self.node_id = node_id
        self.pose = pose
        self._reset_current_panorama()

        all_paths = {}

        # 检查相机是否就绪
        if not camera_subscriber.is_ready():
            self.get_logger_func('✗ Camera not ready before panorama capture')
            return None

        for idx, angle in enumerate(self.panorama_angles):
            self.get_logger_func(f'📸 Capturing direction {idx+1}/4: {angle}°')

            # 如果有旋转回调，执行旋转
            if rotation_callback is not None:
                self.get_logger_func(f'🔄 Rotating to {angle}°...')
                rotation_ok = rotation_callback(angle)
                if not rotation_ok:
                    self.get_logger_func(f'✗ Rotation to {angle}° failed')
                    return None

                # 等待旋转完成和图像稳定
                self.get_logger_func(f'⏳ Waiting {wait_after_rotation}s for stabilization...')
                time.sleep(wait_after_rotation)
            else:
                # 手动旋转模式：等待用户手动旋转
                if idx > 0:  # 第一个方向不需要等待
                    self.get_logger_func(f'⏸  Please manually rotate to {angle}° and press Enter')
                    # 注意：这里不能直接使用 input()，因为这是在ROS2节点中
                    time.sleep(0.5)  # 短暂延迟

            # 获取最新图像
            rgb, depth = camera_subscriber.get_latest_pair()

            # 验证图像有效性
            if rgb is None:
                self.get_logger_func(f'✗ Failed to get RGB image at {angle}°')
                return None

            if rgb.size == 0:
                self.get_logger_func(f'✗ Empty RGB image at {angle}°')
                return None

            # 保存图像
            result = self.capture_panorama(rgb, depth, node_id, pose)
            all_paths[angle] = result['path']

            self.get_logger_func(f'✓ Direction {angle}° captured: {result["path"]}')

        # 构建完整的全景数据
        panorama_data = {
            'node_id': node_id,
            'pose': pose,
            'timestamp': self.timestamp,
            'images': all_paths,
            'complete': True
        }

        self.get_logger_func(f'✅ Panorama capture complete! All 4 directions saved.')

        return panorama_data
    
    def _save_image(self, image: np.ndarray, angle: int,
                   is_depth: bool = False) -> Path:
        """保存图像到文件"""
        if self.node_id is None:
            node_dir = self.storage_path / 'temp'
        else:
            node_dir = self.storage_path / f'node_{self.node_id}'
        
        node_dir.mkdir(parents=True, exist_ok=True)
        
        suffix = 'depth' if is_depth else 'rgb'
        filename = f'{angle:03d}deg_{suffix}.{self.image_format}'
        filepath = node_dir / filename
        
        cv2.imwrite(str(filepath), image)
        return filepath
    
    def _reset_current_panorama(self) -> None:
        """重置当前全景数据"""
        with self.lock:
            self.images.clear()
            self.image_paths.clear()
    
    def get_panorama_data(self) -> Dict:
        """获取完整的全景数据"""
        with self.lock:
            if len(self.images) < len(self.panorama_angles):
                return None
            
            return {
                'node_id': self.node_id,
                'timestamp': self.timestamp,
                'pose': self.pose,
                'images': self.image_paths.copy(),
                'complete': True
            }
    
    def is_panorama_complete(self) -> bool:
        """检查全景采集是否完成"""
        with self.lock:
            return len(self.images) >= len(self.panorama_angles)
    
    def get_image_by_angle(self, angle: int) -> Optional[np.ndarray]:
        """获取指定角度的图像"""
        with self.lock:
            return self.images.get(angle)
    
    def save_metadata(self, metadata: Dict, filename: str = 'panorama_metadata.json') -> Path:
        """保存全景元数据"""
        if self.node_id is not None:
            node_dir = self.storage_path / f'node_{self.node_id}'
            node_dir.mkdir(parents=True, exist_ok=True)
            filepath = node_dir / filename
        else:
            filepath = self.storage_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return filepath
