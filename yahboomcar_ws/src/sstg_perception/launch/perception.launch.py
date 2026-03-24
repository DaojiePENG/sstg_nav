"""
SSTG Perception Node - ROS2 Launch File with Gemini 336L Camera
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """生成启动配置"""
    
    # ======================== 1. 相机参数声明 ========================
    color_width_arg = DeclareLaunchArgument(
        'color_width',
        default_value='1280',
        description='RGB image width'
    )
    color_height_arg = DeclareLaunchArgument(
        'color_height',
        default_value='800',
        description='RGB image height'
    )
    color_fps_arg = DeclareLaunchArgument(
        'color_fps',
        default_value='30',
        description='RGB image frame rate'
    )
    depth_width_arg = DeclareLaunchArgument(
        'depth_width',
        default_value='1280',
        description='Depth image width'
    )
    depth_height_arg = DeclareLaunchArgument(
        'depth_height',
        default_value='800',
        description='Depth image height'
    )
    depth_fps_arg = DeclareLaunchArgument(
        'depth_fps',
        default_value='30',
        description='Depth image frame rate'
    )
    enable_accel_arg = DeclareLaunchArgument(
        'enable_accel',
        default_value='true',
        description='Enable accelerometer'
    )
    enable_gyro_arg = DeclareLaunchArgument(
        'enable_gyro',
        default_value='true',
        description='Enable gyroscope'
    )
    
    # ======================== 2. Perception 参数声明 ========================
    declare_panorama_path = DeclareLaunchArgument(
        'panorama_storage_path',
        default_value='/tmp/sstg_perception',
        description='Path to store panorama images'
    )
    
    declare_confidence_threshold = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='Semantic confidence threshold'
    )
    
    # ======================== 3. 启动 Gemini 336L 相机 ========================
    try:
        orbbec_camera_share_dir = get_package_share_directory('orbbec_camera')
        gemini_launch_file = os.path.join(
            orbbec_camera_share_dir,
            'launch',
            'gemini_330_series.launch.py'
        )
        
        orbbec_camera_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gemini_launch_file),
            launch_arguments={
                'color_width': LaunchConfiguration('color_width'),
                'color_height': LaunchConfiguration('color_height'),
                'color_fps': LaunchConfiguration('color_fps'),
                'depth_width': LaunchConfiguration('depth_width'),
                'depth_height': LaunchConfiguration('depth_height'),
                'depth_fps': LaunchConfiguration('depth_fps'),
                'enable_accel': LaunchConfiguration('enable_accel'),
                'enable_gyro': LaunchConfiguration('enable_gyro'),
            }.items()
        )
    except Exception as e:
        print(f"Warning: Could not find orbbec_camera package: {e}")
        orbbec_camera_launch = None
    
    # ======================== 4. Perception Node ========================
    perception_node = Node(
        package='sstg_perception',
        executable='perception_node',
        name='perception_node',
        output='screen',
        parameters=[
            {
                'api_base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                'vlm_model': 'qwen-vl-plus',
                'panorama_storage_path': LaunchConfiguration('panorama_storage_path'),
                'rgb_topic': '/camera/rgb/image_raw',
                'depth_topic': '/camera/depth/image_raw',
                'confidence_threshold': LaunchConfiguration('confidence_threshold'),
                'max_retries': 3,
            }
        ]
    )
    
    # ======================== 5. 组装启动项 ========================
    ld = LaunchDescription()
    
    # 相机参数
    ld.add_action(color_width_arg)
    ld.add_action(color_height_arg)
    ld.add_action(color_fps_arg)
    ld.add_action(depth_width_arg)
    ld.add_action(depth_height_arg)
    ld.add_action(depth_fps_arg)
    ld.add_action(enable_accel_arg)
    ld.add_action(enable_gyro_arg)
    
    # Perception 参数
    ld.add_action(declare_panorama_path)
    ld.add_action(declare_confidence_threshold)
    
    # 启动相机（如果成功找到）
    if orbbec_camera_launch is not None:
        ld.add_action(orbbec_camera_launch)
    
    # 启动 Perception 节点
    ld.add_action(perception_node)
    
    return ld
