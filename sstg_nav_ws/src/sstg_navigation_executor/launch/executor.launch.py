from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Launch the SSTG Navigation Executor node."""

    executor_node = Node(
        package='sstg_navigation_executor',
        executable='executor_node',
        name='navigation_executor',
        output='screen',
        parameters=[
            {'nav2_available': True},
            {'update_rate': 10},
            {'position_threshold': 0.2},
            {'orientation_threshold': 0.1}
        ]
    )

    return LaunchDescription([
        executor_node
    ])