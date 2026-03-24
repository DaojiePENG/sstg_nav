#!/usr/bin/env python3
"""
SSTG Perception Module Test Suite
"""

import sys
import os
from pathlib import Path

# Add workspace to path
workspace_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_path / 'install'))
sys.path.insert(0, str(workspace_path / 'src' / 'sstg_perception'))

import tempfile
import cv2
import numpy as np
from sstg_perception.panorama_capture import PanoramaCapture
from sstg_perception.semantic_extractor import SemanticExtractor, SemanticInfo, SemanticObject
from sstg_perception.vlm_client import VLMClient


def test_panorama_capture():
    """测试全景图采集"""
    print('\n' + '='*60)
    print('TEST 1: Panorama Capture')
    print('='*60)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            capture = PanoramaCapture(storage_path=tmpdir)
            
            # 创建测试图像
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # 采集四个方向
            results = []
            for i in range(4):
                result = capture.capture_panorama(test_image, node_id=1, pose={'x': 0, 'y': 0, 'theta': 0})
                results.append(result)
                assert result['angle'] == i * 90, f"Angle mismatch: {result['angle']} != {i*90}"
                assert result['complete'] == (i == 3), f"Complete flag mismatch at {i}"
                print(f"  ✓ Direction {i*90}°: {result['path']}")
            
            # 验证数据
            assert capture.is_panorama_complete(), "Panorama not complete"
            pano_data = capture.get_panorama_data()
            assert pano_data is not None, "Panorama data is None"
            assert len(pano_data['images']) == 4, f"Image count mismatch: {len(pano_data['images'])}"
            
            print("  ✓ All panorama images captured")
            print("  ✓ Panorama complete and data valid")
            return True
            
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_semantic_extractor():
    """测试语义提取器"""
    print('\n' + '='*60)
    print('TEST 2: Semantic Extractor')
    print('='*60)
    
    try:
        extractor = SemanticExtractor(confidence_threshold=0.5)
        
        # 测试数据 1: 正常的 JSON 格式
        test_response_1 = '''
        {
          "room_type": "living_room",
          "confidence": 0.95,
          "objects": [
            {"name": "sofa", "position": "left", "quantity": 1, "confidence": 0.9},
            {"name": "table", "position": "center", "quantity": 1, "confidence": 0.85},
            {"name": "lamp", "position": "right", "quantity": 2, "confidence": 0.8}
          ],
          "description": "A cozy living room with furniture"
        }
        '''
        
        success, info, error = extractor.extract_semantic_info(test_response_1)
        assert success, f"Failed to extract: {error}"
        assert info.room_type == "living_room", f"Room type mismatch: {info.room_type}"
        assert len(info.objects) == 3, f"Object count mismatch: {len(info.objects)}"
        print(f"  ✓ Extracted room_type: {info.room_type}")
        print(f"  ✓ Extracted objects: {len(info.objects)}")
        print(f"  ✓ Confidence: {info.confidence}")
        
        # 测试数据 2: JSON 格式带代码块
        test_response_2 = '''
        ```json
        {
          "room_type": "kitchen",
          "confidence": 0.88,
          "objects": [
            {"name": "refrigerator", "position": "left", "quantity": 1, "confidence": 0.95}
          ],
          "description": "Modern kitchen"
        }
        ```
        '''
        
        success, info, error = extractor.extract_semantic_info(test_response_2)
        assert success, f"Failed to extract from code block: {error}"
        assert info.room_type == "kitchen", f"Room type mismatch: {info.room_type}"
        print(f"  ✓ Extracted from code block: {info.room_type}")
        
        # 测试数据 3: 低置信度对象过滤
        test_response_3 = '''
        {
          "room_type": "bedroom",
          "confidence": 0.9,
          "objects": [
            {"name": "bed", "position": "center", "quantity": 1, "confidence": 0.95},
            {"name": "picture", "position": "wall", "quantity": 1, "confidence": 0.3}
          ],
          "description": "Bedroom"
        }
        '''
        
        success, info, error = extractor.extract_semantic_info(test_response_3)
        assert success, f"Failed to extract: {error}"
        assert len(info.objects) == 1, f"Should filter low confidence objects: {len(info.objects)}"
        assert info.objects[0].name == "bed", f"Object name mismatch"
        print(f"  ✓ Filtered low confidence objects (kept {len(info.objects)}/2)")
        
        # 测试合并
        info1 = SemanticInfo(
            room_type="living_room",
            objects=[SemanticObject("sofa", "left", 1, 0.9)],
            description="Room 1",
            confidence=0.9
        )
        info2 = SemanticInfo(
            room_type="living_room",
            objects=[SemanticObject("sofa", "left", 1, 0.85), SemanticObject("table", "center", 1, 0.8)],
            description="Room 2",
            confidence=0.88
        )
        
        merged = extractor.merge_semantic_infos([info1, info2], strategy='union')
        assert merged.room_type == "living_room", "Merge failed: room type"
        assert len(merged.objects) == 2, f"Merge failed: object count {len(merged.objects)}"
        print(f"  ✓ Merged infos: {len(merged.objects)} objects from 2 views")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vlm_client():
    """测试 VLM 客户端配置"""
    print('\n' + '='*60)
    print('TEST 3: VLM Client Configuration')
    print('='*60)
    
    try:
        # 测试不带 API Key 的情况
        client = VLMClient(api_key='', model='qwen-vl-plus')
        assert client.model == 'qwen-vl-plus', "Model mismatch"
        print(f"  ✓ VLMClient instantiated with model: {client.model}")
        
        # 测试日志函数
        logs = []
        client.set_logger(lambda msg: logs.append(msg))
        print(f"  ✓ Logger function set")
        
        # 测试提示词生成
        prompt = client._get_default_prompt()
        assert len(prompt) > 0, "Prompt is empty"
        assert "room_type" in prompt, "Prompt missing room_type"
        assert "objects" in prompt, "Prompt missing objects"
        print(f"  ✓ Default prompt generated ({len(prompt)} chars)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_integration():
    """集成测试"""
    print('\n' + '='*60)
    print('TEST 4: Integration Test')
    print('='*60)
    
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. 创建全景图
            capture = PanoramaCapture(storage_path=tmpdir)
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            for i in range(4):
                capture.capture_panorama(test_image, node_id=1, pose={'x': 0, 'y': 0, 'theta': 0})
            
            pano_data = capture.get_panorama_data()
            assert pano_data is not None, "Panorama data is None"
            print(f"  ✓ Created panorama with {len(pano_data['images'])} images")
            
            # 2. 创建语义信息
            extractor = SemanticExtractor()
            test_json = '''{
                "room_type": "living_room",
                "confidence": 0.95,
                "objects": [
                    {"name": "sofa", "position": "left", "quantity": 1, "confidence": 0.9}
                ],
                "description": "Living room with sofa"
            }'''
            
            success, info, error = extractor.extract_semantic_info(test_json)
            assert success, f"Extract failed: {error}"
            print(f"  ✓ Extracted semantic info: {info.room_type}")
            
            # 3. 验证信息序列化
            info_dict = info.to_dict()
            assert info_dict['room_type'] == 'living_room', "Serialization failed"
            print(f"  ✓ Serialized semantic info to dict")
            
            return True
            
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print('\n' + '#'*60)
    print('# SSTG Perception Module Test Suite')
    print('#'*60)
    
    tests = [
        ('Panorama Capture', test_panorama_capture),
        ('Semantic Extractor', test_semantic_extractor),
        ('VLM Client', test_vlm_client),
        ('Integration', test_integration),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} FAILED: {e}")
            results[name] = False
    
    # 打印总结
    print('\n' + '#'*60)
    print('# Test Summary')
    print('#'*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = '✓ PASS' if result else '✗ FAIL'
        print(f"  {status}: {name}")
    
    print(f'\nTotal: {passed}/{total} tests passed')
    
    if passed == total:
        print('\n✅ All tests passed!')
        return 0
    else:
        print(f'\n❌ {total - passed} test(s) failed')
        return 1


if __name__ == '__main__':
    sys.exit(main())
