# SSTG 测试工具

本目录包含 SSTG 导航系统的测试脚本和工具。

## 📁 文件说明

### 启动脚本

- **`start_nodes.sh`** - 启动所有 SSTG 节点用于测试
  - 启动并监控所有核心服务
  - 提供服务健康检查
  - 支持优雅的清理和退出
  - 使用: `./start_nodes.sh`

- **`run_test.sh`** - 运行完整的集成测试
  - 启动所有服务
  - 执行自动化测试
  - 生成测试报告
  - 使用: `./run_test.sh`

### 测试工具

- **`test_system_integration.py`** - 系统集成测试脚本
  - 测试服务可用性
  - 验证 NLP→Planning→Execution 完整流程
  - 测试任务管理功能（状态查询、取消）
  - 使用: `python3 test_system_integration.py`

- **`init_test_map.py`** - 测试地图初始化工具
  - 生成测试用拓扑地图
  - 保存到 Redis 数据库
  - 使用: `python3 init_test_map.py`

- **`diagnose_nlp_planning.py`** - NLP-规划诊断工具
  - 调试 NLP 到 Planning 的数据流
  - 验证语义匹配逻辑
  - 使用: `python3 diagnose_nlp_planning.py`

## 🚀 快速开始

### 1. 基本测试流程

```bash
cd ~/yahboomcar_ros2_ws/project_test

# 步骤1: 初始化测试地图
python3 init_test_map.py

# 步骤2: 启动所有节点
./start_nodes.sh

# 步骤3: 在另一个终端运行测试
python3 test_system_integration.py
```

### 2. 一键集成测试

```bash
# 自动完成上述所有步骤
./run_test.sh
```

## 📊 测试输出

- **日志**: `logs/` 目录下保存各节点日志
- **报告**: `integration_test_report.md` 包含测试结果

## ⚙️ 配置

测试脚本使用以下默认配置：

- 工作空间: `/home/daojie/yahboomcar_ros2_ws`
- ROS2 环境: `yahboomcar_ws/install/setup.bash`
- 日志目录: `project_test/logs/`

如需修改，请编辑脚本中的配置变量。

## 🔧 故障排查

### 服务未启动

```bash
# 检查 ROS2 环境
source ~/yahboomcar_ros2_ws/yahboomcar_ws/install/setup.bash
ros2 pkg list | grep sstg

# 检查节点状态
ros2 node list

# 检查服务列表
ros2 service list | grep -E '(start_task|process_nlp_query|plan_navigation)'
```

### 测试失败

```bash
# 查看详细日志
tail -f logs/*.log

# 单独测试各组件
ros2 service call /process_nlp_query sstg_msgs/srv/ProcessNLPQuery "{text_input: '去客厅', context: 'home'}"
```

## 📝 注意事项

- 确保 Redis 服务正在运行（Map Manager 依赖）
- 首次测试前必须运行 `init_test_map.py` 初始化地图
- 测试需要 ROS2 环境已正确配置
- Nav2 功能测试需要实际机器人或仿真环境
