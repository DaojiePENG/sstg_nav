"""
SSTG Perception Node - 感知和语义标注 ROS2 节点
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
import os
from pathlib import Path
import json
from typing import Optional

try:
    import sstg_msgs.msg as sstg_msg
    import sstg_msgs.srv as sstg_srv
except ImportError:
    # 如果直接运行，使用空模块代替
    class DummyModule:
        pass
    sstg_msg = DummyModule()
    sstg_srv = DummyModule()

from sstg_perception.camera_subscriber import CameraSubscriber
from sstg_perception.panorama_capture import PanoramaCapture
from sstg_perception.vlm_client import VLMClientWithRetry
from sstg_perception.semantic_extractor import SemanticExtractor, SemanticInfo, SemanticObject


class PerceptionNode(Node):
    """
    SSTG 感知节点
    
    功能：
    - RGB-D 图像采集
    - 四方向全景图采集
    - VLM 语义标注
    - 结果发布
    """
    
    def __init__(self):
        super().__init__('perception_node')
        
        # 参数配置 - API Key 优先从环境变量读取
        api_key_from_env = os.getenv('DASHSCOPE_API_KEY', '')
        self.declare_parameter('api_key', api_key_from_env)
        self.declare_parameter('api_base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.declare_parameter('vlm_model', 'qwen-vl-plus')
        self.declare_parameter('panorama_storage_path', '/tmp/sstg_perception')
        self.declare_parameter('rgb_topic', '/camera/rgb/image_raw')
        self.declare_parameter('depth_topic', '/camera/depth/image_raw')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('max_retries', 3)
        
        # 从参数获取 API Key（环境变量已设置为默认值）
        self.api_key = self.get_parameter('api_key').value
        self.api_base_url = self.get_parameter('api_base_url').value
        self.vlm_model = self.get_parameter('vlm_model').value
        self.panorama_storage_path = self.get_parameter('panorama_storage_path').value
        self.rgb_topic = self.get_parameter('rgb_topic').value
        self.depth_topic = self.get_parameter('depth_topic').value
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.max_retries = self.get_parameter('max_retries').value
        
        # 验证 API Key
        if not self.api_key:
            self.get_logger().warn('API Key not configured. VLM annotation will be disabled.')
        
        # 初始化相机订阅器
        self.camera_subscriber = CameraSubscriber(
            rgb_topic=self.rgb_topic,
            depth_topic=self.depth_topic
        )
        
        # 初始化全景图采集器
        self.panorama_capture = PanoramaCapture(
            storage_path=self.panorama_storage_path
        )
        self.panorama_capture.set_logger(self.get_logger().info)
        
        # 初始化 VLM 客户端
        if self.api_key:
            self.vlm_client = VLMClientWithRetry(
                api_key=self.api_key,
                base_url=self.api_base_url,
                model=self.vlm_model,
                max_retries=self.max_retries
            )
            self.vlm_client.set_logger(self.get_logger().info)
        else:
            self.vlm_client = None
        
        # 初始化语义提取器
        self.extractor = SemanticExtractor(confidence_threshold=self.confidence_threshold)
        self.extractor.set_logger(self.get_logger().info)
        
        # 发布器
        self.semantic_pub = self.create_publisher(
            sstg_msg.SemanticAnnotation,
            'semantic_annotations',
            qos_profile=QoSProfile(depth=10)
        )
        
        # 服务
        self.create_service(
            sstg_srv.CaptureImage,
            'capture_panorama',
            self._capture_panorama_callback
        )
        
        self.create_service(
            sstg_srv.AnnotateSemantic,
            'annotate_semantic',
            self._annotate_semantic_callback
        )
        
        self.get_logger().info('Perception Node initialized successfully')
    
    def _capture_panorama_callback(self, request, response):
        """
        全景图采集服务回调
        
        参数: node_id, pose (x, y, theta)
        """
        try:
            node_id = request.node_id
            pose = {
                'x': float(request.pose.position.x),
                'y': float(request.pose.position.y),
                'theta': 0.0
            }
            
            self.get_logger().info(f'Capturing panorama for node {node_id}')
            
            # 检查相机是否就绪
            if not self.camera_subscriber.is_ready():
                if not self.camera_subscriber.wait_for_images(timeout=5.0):
                    response.success = False
                    response.error_message = 'Camera not responding'
                    return response
            
            # 采集四个方向的图像
            panorama_data = self.panorama_capture.capture_four_directions(
                self.camera_subscriber,
                node_id,
                pose,
                rotation_callback=None  # 暂不支持自动旋转
            )
            
            if panorama_data is None:
                response.success = False
                response.error_message = 'Failed to capture panorama'
                return response
            
            # 保存元数据
            self.panorama_capture.save_metadata(panorama_data)
            
            response.success = True
            response.image_paths = json.dumps(panorama_data['images'])
            
            self.get_logger().info(f'✓ Panorama captured: {panorama_data["images"]}')
            
        except Exception as e:
            response.success = False
            response.error_message = str(e)
            self.get_logger().error(f'Capture error: {e}')
        
        return response
    
    def _annotate_semantic_callback(self, request, response):
        """
        语义标注服务回调
        
        参数: image_path, node_id (可选)
        """
        try:
            image_path = request.image_path
            node_id = request.node_id
            
            self.get_logger().info(f'Annotating semantic for: {image_path}')
            
            if not Path(image_path).exists():
                response.success = False
                response.error_message = f'Image not found: {image_path}'
                return response
            
            # 调用 VLM
            if not self.vlm_client:
                response.success = False
                response.error_message = 'VLM client not configured'
                return response
            
            vlm_response = self.vlm_client.call_semantic_annotation(image_path)
            
            if not vlm_response.success:
                response.success = False
                response.error_message = vlm_response.error
                return response
            
            # 提取语义信息
            success, semantic_info, error = self.extractor.extract_semantic_info(
                vlm_response.content
            )
            
            if not success:
                response.success = False
                response.error_message = f'Failed to extract semantic: {error}'
                return response
            
            # 构建响应
            response.success = True
            response.room_type = semantic_info.room_type
            response.description = semantic_info.description
            response.confidence = semantic_info.confidence
            
            for obj in semantic_info.objects:
                semantic_obj = sstg_msg.SemanticObject()
                semantic_obj.name = obj.name
                semantic_obj.position = obj.position
                semantic_obj.quantity = obj.quantity
                semantic_obj.confidence = obj.confidence
                response.objects.append(semantic_obj)
            
            # 发布标注结果
            self._publish_semantic_annotation(
                node_id, image_path, semantic_info
            )
            
            self.get_logger().info(
                f'✓ Semantic annotation complete: room={semantic_info.room_type}, '
                f'objects={len(semantic_info.objects)}'
            )
            
        except Exception as e:
            response.success = False
            response.error_message = str(e)
            self.get_logger().error(f'Annotation error: {e}')
        
        return response
    
    def _publish_semantic_annotation(self, node_id: int, image_path: str,
                                    semantic_info: SemanticInfo) -> None:
        """发布语义标注消息"""
        msg = sstg_msg.SemanticAnnotation()
        msg.node_id = node_id
        msg.image_path = image_path
        msg.room_type = semantic_info.room_type
        msg.description = semantic_info.description
        msg.confidence = semantic_info.confidence
        
        for obj in semantic_info.objects:
            semantic_obj = sstg_msg.SemanticObject()
            semantic_obj.name = obj.name
            semantic_obj.position = obj.position
            semantic_obj.quantity = obj.quantity
            semantic_obj.confidence = obj.confidence
            msg.objects.append(semantic_obj)
        
        self.semantic_pub.publish(msg)
    
    def destroy_node(self):
        """清理资源"""
        self.camera_subscriber.destroy_node()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\nShutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
