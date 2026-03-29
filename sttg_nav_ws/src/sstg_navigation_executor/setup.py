from setuptools import find_packages, setup

package_name = 'sstg_navigation_executor'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/executor.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='daojie',
    maintainer_email='Daojie.PENG@qq.com',
    description='Navigation Execution Module for SSTG System - Nav2 Integration',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'executor_node = sstg_navigation_executor.executor_node:main'
        ],
    },
)
