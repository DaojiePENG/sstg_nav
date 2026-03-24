#!/usr/bin/env python3
"""
SSTG Perception Module Verification Script
验证 sstg_perception 模块的完整功能
"""

import sys
import os
from pathlib import Path

# 添加工作空间到路径
workspace_path = Path(__file__).parent
sys.path.insert(0, str(workspace_path / 'yahboomcar_ws' / 'install'))
sys.path.insert(0, str(workspace_path / 'yahboomcar_ws' / 'src' / 'sstg_perception'))


def verify_imports():
    """验证导入"""
    print('\n' + '='*60)
    print('VERIFICATION 1: Module Imports')
    print('='*60)
    
    try:
        from sstg_perception.camera_subscriber import CameraSubscriber
        print("  ✓ CameraSubscriber imported")
        
        from sstg_perception.panorama_capture import PanoramaCapture
        print("  ✓ PanoramaCapture imported")
        
        from sstg_perception.vlm_client import VLMClient, VLMClientWithRetry
        print("  ✓ VLMClient imported")
        
        from sstg_perception.semantic_extractor import SemanticExtractor, SemanticInfo, SemanticObject
        print("  ✓ SemanticExtractor imported")
        
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def verify_configuration():
    """验证配置"""
    print('\n' + '='*60)
    print('VERIFICATION 2: Configuration')
    print('='*60)
    
    api_key = os.getenv('DASHSCOPE_API_KEY', '')
    if api_key:
        print(f"  ✓ API Key configured: {api_key[:20]}...")
    else:
        print("  ⚠️  API Key not configured (optional for testing)")
    
    config_file = Path(__file__).parent / 'yahboomcar_ws' / 'src' / 'sstg_perception' / 'config' / 'perception_config.yaml'
    if config_file.exists():
        print(f"  ✓ Config file exists: {config_file}")
    else:
        print(f"  ⚠️  Config file not found: {config_file}")
    
    return True


def verify_functionality():
    """验证功能"""
    print('\n' + '='*60)
    print('VERIFICATION 3: Core Functionality')
    print('='*60)
    
    try:
        from sstg_perception.panorama_capture import PanoramaCapture
        from sstg_perception.semantic_extractor import SemanticExtractor
        import numpy as np
        
        # 测试 PanoramaCapture
        capture = PanoramaCapture()
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = capture.capture_panorama(test_image, node_id=0, pose={'x': 0, 'y': 0, 'theta': 0})
        
        if result['angle'] == 0:
            print("  ✓ PanoramaCapture works correctly")
        else:
            print("  ✗ PanoramaCapture failed")
            return False
        
        # 测试 SemanticExtractor
        extractor = SemanticExtractor(confidence_threshold=0.5)
        test_json = '''{
            "room_type": "living_room",
            "confidence": 0.95,
            "objects": [{"name": "sofa", "position": "left", "quantity": 1, "confidence": 0.9}],
            "description": "Living room"
        }'''
        
        success, info, error = extractor.extract_semantic_info(test_json)
        if success and info.room_type == "living_room":
            print("  ✓ SemanticExtractor works correctly")
        else:
            print(f"  ✗ SemanticExtractor failed: {error}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_ros2_integration():
    """验证 ROS2 集成"""
    print('\n' + '='*60)
    print('VERIFICATION 4: ROS2 Integration')
    print('='*60)
    
    try:
        import rclpy
        print("  ✓ ROS2 (rclpy) available")
        
        try:
            import sstg_msgs.msg
            print("  ✓ sstg_msgs available")
            return True
        except ImportError:
            print("  ⚠️  sstg_msgs not available (will work with mock)")
            return True
            
    except ImportError:
        print("  ⚠️  ROS2 not available (standalone mode)")
        return True


def verify_launch_files():
    """验证启动文件"""
    print('\n' + '='*60)
    print('VERIFICATION 5: Launch Files')
    print('='*60)
    
    launch_file = Path(__file__).parent / 'yahboomcar_ws' / 'src' / 'sstg_perception' / 'launch' / 'perception.launch.py'
    if launch_file.exists():
        print(f"  ✓ Launch file exists: {launch_file.name}")
        
        try:
            with open(launch_file) as f:
                content = f.read()
                if 'generate_launch_description' in content:
                    print("  ✓ Launch file is valid")
                    return True
        except Exception as e:
            print(f"  ✗ Launch file error: {e}")
            return False
    else:
        print(f"  ✗ Launch file not found: {launch_file}")
        return False


def verify_documentation():
    """验证文档"""
    print('\n' + '='*60)
    print('VERIFICATION 6: Documentation')
    print('='*60)
    
    docs = [
        ('MODULE_GUIDE.md', 'Module usage guide'),
        ('PERCEPTION_QuickRef.md', 'Quick reference'),
    ]
    
    doc_dir = Path(__file__).parent / 'yahboomcar_ws' / 'src' / 'sstg_perception' / 'doc'
    
    for doc_file, desc in docs:
        path = doc_dir / doc_file
        if path.exists():
            size = path.stat().st_size
            print(f"  ✓ {doc_file} ({size} bytes) - {desc}")
        else:
            print(f"  ✗ {doc_file} not found")
            return False
    
    return True


def verify_package_structure():
    """验证包结构"""
    print('\n' + '='*60)
    print('VERIFICATION 7: Package Structure')
    print('='*60)
    
    base_dir = Path(__file__).parent / 'yahboomcar_ws' / 'src' / 'sstg_perception'
    
    required_files = [
        'package.xml',
        'setup.py',
        'setup.cfg',
        'sstg_perception/__init__.py',
        'sstg_perception/camera_subscriber.py',
        'sstg_perception/panorama_capture.py',
        'sstg_perception/vlm_client.py',
        'sstg_perception/semantic_extractor.py',
        'sstg_perception/perception_node.py',
    ]
    
    all_exist = True
    for file in required_files:
        path = base_dir / file
        if path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} not found")
            all_exist = False
    
    return all_exist


def main():
    print("\n" + "#"*60)
    print("# SSTG Perception Module - Full Verification")
    print("#"*60)
    
    checks = [
        ('Imports', verify_imports),
        ('Configuration', verify_configuration),
        ('Functionality', verify_functionality),
        ('ROS2 Integration', verify_ros2_integration),
        ('Launch Files', verify_launch_files),
        ('Documentation', verify_documentation),
        ('Package Structure', verify_package_structure),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} verification failed: {e}")
            results[name] = False
    
    # 总结
    print('\n' + "#"*60)
    print("# Verification Summary")
    print("#"*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f'\nTotal: {passed}/{total} verifications passed')
    
    if passed == total:
        print("\n✅ All verifications passed!")
        print("\n📚 Next steps:")
        print("  1. Set API Key: export DASHSCOPE_API_KEY=\"sk-...\"")
        print("  2. Launch with: ros2 launch sstg_perception perception.launch.py")
        print("  3. Or run directly: python3 /home/daojie/yahboomcar_ros2_ws/run_perception.py")
        return 0
    else:
        print(f"\n❌ {total - passed} verification(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
