from setuptools import find_packages, setup

package_name = 'sstg_navigation_planner'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'rclpy', 'std_msgs', 'geometry_msgs', 'sstg_msgs'],
    zip_safe=True,
    maintainer='daojie',
    maintainer_email='Daojie.PENG@qq.com',
    description='SSTG Navigation Planner - 语义查询与路径规划',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'planning_node = sstg_navigation_planner.planning_node:main',
            'sstg_navigation_planner = sstg_navigation_planner.planning_node:main'
        ],
    },
)
