# SSTG Perception Module - 快速参考卡

## ⚡ 一句话启动

```bash
export DASHSCOPE_API_KEY="sk-942e8661f10f492280744a26fe7b953b"
ros2 launch sstg_perception perception.launch.py
```

---

## 🔧 常用命令

### 启动相机和感知节点
```bash
source /opt/ros/humble/setup.bash
export DASHSCOPE_API_KEY="sk-942e8661f10f492280744a26fe7b953b"
ros2 launch sstg_perception perception.launch.py
```

### 仅启动相机（不启动感知）
```bash
source /opt/ros/humble/setup.bash
ros2 launch orbbec_camera gemini_330_series.launch.py
```

### 查看相机话题
```bash
ros2 topic list | grep camera
```

### 查看相机图像
```bash
ros2 topic echo /camera/rgb/image_raw --once
ros2 run image_view image_view image:=/camera/rgb/image_raw
```

### 运行测试
```bash
cd /home/daojie/yahboomcar_ros2_ws/yahboomcar_ws/src/sstg_perception/test
python3 test_perception.py
```

### 构建包
```bash
cd /home/daojie/yahboomcar_ros2_ws/yahboomcar_ws
colcon build --symlink-install --packages-select sstg_perception
```

---

## 📡 ROS2 服务调用

### 采集全景图
```bash
ros2 service call /perception_node/capture_panorama sstg_msgs/CaptureImage \
  "{node_id: 0, pose: {position: {x: 1.0, y: 2.0, z: 0.0}, orientation: {w: 1.0}}}"
```

### 语义标注
```bash
ros2 service call /perception_node/annotate_semantic sstg_msgs/AnnotateSemantic \
  "{image_path: '/tmp/image.jpg', node_id: 0}"
```

### 订阅标注结果
```bash
ros2 topic echo /semantic_annotations
```

---

## 🐍 Python API 快速示例

### 创建全景图
```python
from sstg_perception.panorama_capture import PanoramaCapture
import cv2

capture = PanoramaCapture(storage_path='/tmp/sstg_perception')
image = cv2.imread('image.jpg')

for i in range(4):
    result = capture.capture_panorama(image, node_id=0, pose={'x': 0, 'y': 0, 'theta': 0})
    print(f"Captured: {result['angle']}°")
```

### 提取语义信息
```python
from sstg_perception.semantic_extractor import SemanticExtractor

extractor = SemanticExtractor(confidence_threshold=0.5)

json_str = '''{
    "room_type": "living_room",
    "confidence": 0.95,
    "objects": [{"name": "sofa", "position": "left", "quantity": 1, "confidence": 0.9}],
    "description": "Living room"
}'''

success, info, error = extractor.extract_semantic_info(json_str)
if success:
    print(f"Room: {info.room_type}, Objects: {len(info.objects)}")
```

### 调用 VLM
```python
from sstg_perception.vlm_client import VLMClient
import os

api_key = os.getenv('DASHSCOPE_API_KEY')
client = VLMClient(api_key=api_key, model='qwen-vl-plus')

response = client.call_semantic_annotation('/tmp/image.jpg')
print(response.content)
```

---

## 📁 目录结构

```
sstg_perception/
├── sstg_perception/           # 核心模块
│   ├── __init__.py
│   ├── camera_subscriber.py   # 相机订阅器
│   ├── panorama_capture.py    # 全景图采集
│   ├── vlm_client.py          # VLM 客户端
│   ├── semantic_extractor.py  # 语义提取
│   └── perception_node.py     # ROS2 节点
├── launch/                     # 启动文件
│   └── perception.launch.py   # 集成相机和感知
├── config/                     # 配置文件
│   └── perception_config.yaml
├── test/                       # 测试脚本
│   └── test_perception.py
├── doc/                        # 文档
│   └── MODULE_GUIDE.md
├── package.xml                # ROS2 包配置
├── CMakeLists.txt             # CMake 配置
├── setup.py                   # Python 包配置
└── setup.cfg
```

---

## 🔌 消息和服务定义

### 服务: capture_panorama
- 请求: node_id, pose
- 响应: success, image_paths (JSON), error_message

### 服务: annotate_semantic
- 请求: image_path, node_id
- 响应: success, room_type, confidence, description, objects

### 话题: semantic_annotations (发布)
- 消息类型: sstg_msgs/SemanticAnnotation

---

## 🎯 数据流

```
相机 (Gemini 336L)
  ↓
CameraSubscriber (RGB-D)
  ↓
PanoramaCapture (4 directions)
  ↓
VLMClient (qwen-vl-plus)
  ↓
SemanticExtractor (JSON 解析)
  ↓
PerceptionNode (ROS2 服务/话题)
  ↓
其他模块 (sstg_map_manager, ...)
```

---

## 📊 参数配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| api_base_url | https://dashscope.aliyuncs.com/compatible-mode/v1 | API 基础 URL |
| vlm_model | qwen-vl-plus | VLM 模型名称 |
| panorama_storage_path | /tmp/sstg_perception | 图像存储路径 |
| rgb_topic | /camera/rgb/image_raw | RGB 图像话题 |
| depth_topic | /camera/depth/image_raw | 深度图话题 |
| confidence_threshold | 0.5 | 置信度阈值 |
| max_retries | 3 | API 最大重试次数 |
| color_width | 1280 | RGB 分辨率宽 |
| color_height | 800 | RGB 分辨率高 |
| color_fps | 30 | RGB 帧率 |
| depth_width | 1280 | 深度分辨率宽 |
| depth_height | 800 | 深度分辨率高 |
| depth_fps | 30 | 深度帧率 |

---

## 🔑 环境变量

```bash
# API Key（必须设置）
export DASHSCOPE_API_KEY="sk-942e8661f10f492280744a26fe7b953b"

# ROS2 设置
source /opt/ros/humble/setup.bash

# 工作空间设置
source ~/yahboomcar_ros2_ws/yahboomcar_ws/install/setup.bash
```

---

## 📝 日志和调试

```bash
# 查看节点日志
ros2 run sstg_perception perception_node

# 查看所有 ROS2 节点
ros2 node list

# 查看所有话题
ros2 topic list

# 查看所有服务
ros2 service list

# 监听话题
ros2 topic echo /semantic_annotations
```

---

## 💡 常见用法

### 场景 1: 远程建图和语义标注
1. 启动相机和感知节点
2. 操纵机器人到目标位置
3. 调用 capture_panorama 采集全景
4. 调用 annotate_semantic 进行标注
5. 结果通过 semantic_annotations 话题发布

### 场景 2: 批量标注历史图像
```python
from sstg_perception.vlm_client import VLMClientWithRetry
import os

client = VLMClientWithRetry(
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    max_retries=3
)

image_files = ['/tmp/img1.jpg', '/tmp/img2.jpg']
responses = client.batch_annotate(image_files, delay_between_calls=1.0)

for resp in responses:
    print(resp.content)
```

### 场景 3: 多视图信息融合
```python
from sstg_perception.semantic_extractor import SemanticExtractor

extractor = SemanticExtractor()

# 合并 4 个方向的语义信息
merged = extractor.merge_semantic_infos(
    [info_0deg, info_90deg, info_180deg, info_270deg],
    strategy='average'
)

print(f"Merged room: {merged.room_type}")
print(f"All objects: {len(merged.objects)}")
```

---

## 🚨 故障快速排查

| 问题 | 症状 | 解决方案 |
|------|------|--------|
| 相机不工作 | 无 RGB/深度话题 | 检查 USB 连接，运行 `lsusb` |
| API Key 错误 | 401 错误 | 检查环境变量: `echo $DASHSCOPE_API_KEY` |
| 超时 | 请求挂起 30s | 检查网络，增加 max_retries |
| JSON 解析失败 | 无对象提取 | 检查 VLM 输出格式 |
| 包找不到 | ImportError | 重新构建: `colcon build ...` |

---

**版本**: v0.1.0  
**最后更新**: 2026-03-24  
**维护者**: SSTG-Nav Team
