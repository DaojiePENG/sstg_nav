# SSTG Perception 模块修复总结

## 修复日期
2026-03-26

## 问题和解决方案

### 1. 摄像头话题名称不匹配
**问题**: 模块使用错误的话题名 `/camera/rgb/image_raw`，而实际摄像头发布的是 `/camera/color/image_raw`

**修复文件**:
- `src/sstg_perception/sstg_perception/camera_subscriber.py` - 修改默认话题参数
- `src/sstg_perception/sstg_perception/perception_node.py` - 修改默认话题参数
- `src/sstg_perception/launch/perception.launch.py` - 简化启动文件，删除重复的相机驱动启动，改正话题参数
- `src/sstg_perception/doc/MODULE_GUIDE.md` - 更新文档

**改变**:
```
/camera/rgb/image_raw → /camera/color/image_raw
/camera/depth/image_raw (保持不变)
```

### 2. VLM API 消息格式错误
**问题**: 阿里云 Dashscope VLM API 拒绝了请求，错误提示需要使用 `image_url` 而不是 `image`

**错误信息**:
```
API Error: 400 - Invalid value: image. Supported values are: 'text','image_url','video_url' and 'video'.
```

**修复文件**:
- `src/sstg_perception/sstg_perception/vlm_client.py`

**改变**:
```python
# 旧格式
{
    'type': 'image',
    'image': f'data:image/jpeg;base64,{image_data}'
}

# 新格式
{
    'type': 'image_url',
    'image_url': {
        'url': f'data:image/jpeg;base64,{image_data}'
    }
}
```

### 3. ROS2 服务响应结构错误
**问题**: 
- `AnnotateSemantic.srv` 缺少 `error_message` 字段
- `SemanticAnnotation.msg` 消息中的字段结构不匹配

**修复文件**:
- `src/sstg_msgs/srv/AnnotateSemantic.srv` - 添加 `error_message` 字段
- `src/sstg_perception/sstg_perception/perception_node.py` - 修改发布代码使用 SemanticData 嵌套结构

**改变**:
```
AnnotateSemantic.srv 添加:
string error_message

SemanticAnnotation 消息现在正确使用:
semantic_data.room_type
semantic_data.objects[]
semantic_data.confidence
semantic_data.description
```

### 4. Launch 文件优化
**问题**: Launch 文件尝试启动 orbbec_camera 驱动，但相机已经运行，导致冲突

**修复**: 简化 launch 文件，仅启动 perception_node，不重复启动相机驱动

## 测试结果

### ✅ 相机话题正常
```
/camera/color/image_raw - 28 Hz
/camera/depth/image_raw - 正常发布
```

### ✅ Perception Node 正常启动
```
CameraSubscriber initialized:
  RGB Topic: /camera/color/image_raw
  Depth Topic: /camera/depth/image_raw
Perception Node initialized successfully
```

### ✅ annotate_semantic 服务工作正常
```
请求: /home/daojie/Pictures/kitchen.png
响应:
  success: True
  room_type: '餐厅'
  objects: 7 个对象 (餐桌、餐椅、花瓶、装饰画、时钟、书架、门)
  confidence: 0.95
  description: '这是一个现代风格的餐厅...'
```

## 编译命令

```bash
cd /home/daojie/yahboomcar_ros2_ws/yahboomcar_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select sstg_msgs sstg_perception
```

## 启动命令

```bash
export DASHSCOPE_API_KEY="sk-942e8661f10f492280744a26fe7b953b"
source /opt/ros/humble/setup.bash
ros2 launch sstg_perception perception.launch.py
```

## 测试服务

```bash
ros2 service call /annotate_semantic sstg_msgs/AnnotateSemantic \
  "{image_path: '/home/daojie/Pictures/kitchen.png', node_id: 0}"
```

## 修复总结
所有主要问题已修复：
1. ✅ 摄像头话题名称正确
2. ✅ VLM API 调用成功
3. ✅ ROS2 服务响应格式正确
4. ✅ Launch 文件优化
5. ✅ 所有服务和话题正常工作
