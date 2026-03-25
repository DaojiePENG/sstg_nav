#!/usr/bin/env python3
"""
Initialize test topological map for SSTG system testing
"""

import json
import time
from pathlib import Path

def create_test_map():
    """Create a test topological map with semantic information"""

    # Test map data with semantic information
    # 重要：包含中文别名以支持中文查询匹配
    test_map = {
        "nodes": [
            {
                "id": 0,
                "name": "客厅",
                "pose": {
                    "x": 0.0,
                    "y": 0.0,
                    "theta": 0.0
                },
                "panorama_paths": {},
                "semantic_info": {
                    "room_type": "living_room",
                    "room_type_cn": "客厅",
                    "aliases": ["客厅", "沙发", "电视", "休息区", "大厅"],
                    "confidence": 0.95,
                    "objects": [
                        {"name": "sofa", "name_cn": "沙发", "position": "center", "quantity": 1, "confidence": 0.95},
                        {"name": "tv", "name_cn": "电视", "position": "north_wall", "quantity": 1, "confidence": 0.95},
                        {"name": "table", "name_cn": "茶几", "position": "center", "quantity": 1, "confidence": 0.9}
                    ],
                    "semantic_tags": ["rest", "comfortable", "entertainment", "main_space"],
                    "description": "主客厅区域，包含沙发、电视和茶几"
                },
                "created_time": time.time(),
                "last_updated": time.time()
            },
            {
                "id": 1,
                "name": "厨房",
                "pose": {
                    "x": 3.0,
                    "y": 0.0,
                    "theta": 0.0
                },
                "panorama_paths": {},
                "semantic_info": {
                    "room_type": "kitchen",
                    "room_type_cn": "厨房",
                    "aliases": ["厨房", "烹饪区", "餐厅", "用餐区"],
                    "confidence": 0.95,
                    "objects": [
                        {"name": "stove", "name_cn": "炉灶", "position": "east_wall", "quantity": 1, "confidence": 0.95},
                        {"name": "fridge", "name_cn": "冰箱", "position": "north_wall", "quantity": 1, "confidence": 0.95},
                        {"name": "table", "name_cn": "餐桌", "position": "center", "quantity": 1, "confidence": 0.9}
                    ],
                    "semantic_tags": ["cooking", "food", "dining", "utility"],
                    "description": "厨房区域，包含炉灶、冰箱和餐桌"
                },
                "created_time": time.time(),
                "last_updated": time.time()
            },
            {
                "id": 2,
                "name": "卧室",
                "pose": {
                    "x": 0.0,
                    "y": 3.0,
                    "theta": 1.57
                },
                "panorama_paths": {},
                "semantic_info": {
                    "room_type": "bedroom",
                    "room_type_cn": "卧室",
                    "aliases": ["卧室", "睡眠区", "休息室", "床房"],
                    "confidence": 0.95,
                    "objects": [
                        {"name": "bed", "name_cn": "床", "position": "center", "quantity": 1, "confidence": 0.95},
                        {"name": "wardrobe", "name_cn": "衣柜", "position": "west_wall", "quantity": 1, "confidence": 0.9},
                        {"name": "desk", "name_cn": "书桌", "position": "south_wall", "quantity": 1, "confidence": 0.85}
                    ],
                    "semantic_tags": ["sleep", "rest", "quiet", "private"],
                    "description": "卧室区域，包含床、衣柜和书桌"
                },
                "created_time": time.time(),
                "last_updated": time.time()
            },
            {
                "id": 3,
                "name": "卫生间",
                "pose": {
                    "x": -2.0,
                    "y": 1.0,
                    "theta": -0.78
                },
                "panorama_paths": {},
                "semantic_info": {
                    "room_type": "bathroom",
                    "room_type_cn": "卫生间",
                    "aliases": ["卫生间", "浴室", "洗手间", "厕所"],
                    "confidence": 0.9,
                    "objects": [
                        {"name": "toilet", "name_cn": "马桶", "position": "north_wall", "quantity": 1, "confidence": 0.95},
                        {"name": "sink", "name_cn": "水槽", "position": "east_wall", "quantity": 1, "confidence": 0.9},
                        {"name": "shower", "name_cn": "淋浴", "position": "west_wall", "quantity": 1, "confidence": 0.9}
                    ],
                    "semantic_tags": ["hygiene", "washing", "utility", "private"],
                    "description": "卫生间区域，包含马桶、水槽和淋浴"
                },
                "created_time": time.time(),
                "last_updated": time.time()
            }
        ],
        "edges": [
            {"source": 0, "target": 1, "weight": 3.0},
            {"source": 0, "target": 2, "weight": 3.0},
            {"source": 0, "target": 3, "weight": 2.5},
            {"source": 1, "target": 2, "weight": 4.2},
            {"source": 2, "target": 3, "weight": 3.5}
        ]
    }

    return test_map

def main():
    """Main function"""
    map_file = "/tmp/topological_map.json"

    # Create test map
    test_map = create_test_map()

    # Save to file
    with open(map_file, 'w', encoding='utf-8') as f:
        json.dump(test_map, f, indent=2, ensure_ascii=False)

    print(f"✅ Test topological map created: {map_file}")
    print(f"   - {len(test_map['nodes'])} nodes with semantic information")
    print(f"   - {len(test_map['edges'])} edges connecting nodes")
    print("\n📍 Nodes with semantic information:")
    for node in test_map['nodes']:
        semantic = node['semantic_info']
        aliases = semantic.get('aliases', [])
        print(f"  • Node {node['id']}: {semantic['room_type_cn']} ({semantic['room_type']})")
        print(f"    - 别名: {', '.join(aliases)}")
        print(f"    - 对象: {', '.join([obj['name_cn'] for obj in semantic['objects']])}")
        print(f"    - 描述: {semantic['description']}")
    
    print("\n✅ Map file ready for ROS2 nodes")
    print(f"   Start nodes with: ./run_integration_test.sh")

if __name__ == "__main__":
    main()