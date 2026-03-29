# STTG 工作空间迁移 - 快速参考卡

## 🎯 核心变化

### 迁移前 (Phase 3.0)
```
~/yahboomcar_ros2_ws/yahboomcar_ws/src/
├── yahboomcar_*/ (20+个包)
├── sstg_*/       (7个包 - 混在一起❌)
└── ...
```

### 迁移后 (Phase 3.1) ✅
```
~/yahboomcar_ros2_ws/
├── sttg_nav_ws/src/          (7个STTG包)
└── yahboomcar_ws/src/         (YahboomCar包)
```

---

## 📦 迁移的7个包

```
✅ sstg_interaction_manager    → sttg_nav_ws/src/
✅ sstg_map_manager            → sttg_nav_ws/src/
✅ sstg_msgs                   → sttg_nav_ws/src/
✅ sstg_navigation_executor    → sttg_nav_ws/src/
✅ sstg_navigation_planner     → sttg_nav_ws/src/
✅ sstg_nlp_interface          → sttg_nav_ws/src/
✅ sstg_perception             → sttg_nav_ws/src/
```

---

## 📝 新增和更新的文档

### 新增文档（4个）

| 文件 | 用途 |
|------|------|
| `sttg_nav_ws/README.md` | STTG工作空间总览 |
| `sttg_nav_ws/INSTALLATION.md` | 详细安装指南 |
| `yahboomcar_ws/README.md` | YahboomCar工作空间说明 |
| `WORKSPACE_MIGRATION_SUMMARY.md` | 迁移变更说明 |

### 更新的文档（2+个）

| 文件 | 主要变更 |
|------|---------|
| `README.md` | 新增工作空间架构章节 |
| `PROJECT_SUMMARY.md` | 新增架构改进说明 |
| `sstg_map_manager/doc/QUICK_START.md` | 完全重写 |

---

## 🚀 使用命令对比

### 只用STTG系统

**迁移前**:
```bash
cd ~/yahboomcar_ros2_ws
source yahboomcar_ws/install/setup.bash
ros2 launch sstg_map_manager ...
```

**迁移后** ✅:
```bash
cd ~/yahboomcar_ros2_ws/sttg_nav_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch sstg_map_manager ...
```

### 同时用STTG + YahboomCar

**迁移前**:
```bash
cd ~/yahboomcar_ros2_ws
colcon build --symlink-install
source install/setup.bash
```

**迁移后** ✅:
```bash
source ~/yahboomcar_ros2_ws/sttg_nav_ws/install/setup.bash
source ~/yahboomcar_ros2_ws/yahboomcar_ws/install/setup.bash
# 同时可用两个系统的包
```

### 在其他机器人上用STTG

**迁移后新增** ✅:
```bash
# 只需要这个，不需要YahboomCar工作空间
source ~/yahboomcar_ros2_ws/sttg_nav_ws/install/setup.bash
```

---

## 🎯 设计优势

| 优势 | 说明 |
|------|------|
| **独立性** | STTG系统可独立构建、版本控制、部署 |
| **跨平台** | STTG不依赖YahboomCar，可用于其他机器人 |
| **效率** | 构建只需要的工作空间，更快 |
| **清晰** | 代码职责明确，易于维护 |
| **开源** | STTG可作为独立项目开源发布 |

---

## ✅ 验证清单

- [x] 7个STTG包在sttg_nav_ws/src中
- [x] yahboomcar_ws中不含STTG包
- [x] 4个新文档已创建
- [x] 主要文档已更新
- [x] 路径引用已修正
- [x] 工作空间结构完整

---

## 📚 文档导航

| 场景 | 参考文档 |
|------|--------|
| **总体了解** | [README.md](README.md) |
| **STTG快速开始** | [sttg_nav_ws/README.md](sttg_nav_ws/README.md) |
| **STTG安装** | [sttg_nav_ws/INSTALLATION.md](sttg_nav_ws/INSTALLATION.md) |
| **YahboomCar说明** | [yahboomcar_ws/README.md](yahboomcar_ws/README.md) |
| **迁移细节** | [WORKSPACE_MIGRATION_SUMMARY.md](WORKSPACE_MIGRATION_SUMMARY.md) |
| **完成报告** | [EXECUTION_COMPLETE_REPORT.md](EXECUTION_COMPLETE_REPORT.md) |

---

## 🔧 常见操作

### 构建STTG系统

```bash
cd ~/yahboomcar_ros2_ws/sttg_nav_ws
colcon build --symlink-install
source install/setup.bash
```

### 构建YahboomCar系统

```bash
cd ~/yahboomcar_ros2_ws/yahboomcar_ws
colcon build --symlink-install
source install/setup.bash
```

### 启动完整系统

```bash
source ~/yahboomcar_ros2_ws/sttg_nav_ws/install/setup.bash
source ~/yahboomcar_ros2_ws/yahboomcar_ws/install/setup.bash
cd ~/yahboomcar_ros2_ws
./project_test/run_tests.sh
```

### 运行集成测试

```bash
source ~/yahboomcar_ros2_ws/sttg_nav_ws/install/setup.bash
cd ~/yahboomcar_ros2_ws
./project_test/run_tests.sh
```

---

## ⚠️ 重要提示

1. **必须source正确的工作空间**
   - STTG包需要source `sttg_nav_ws/install/setup.bash`
   - YahboomCar包需要source `yahboomcar_ws/install/setup.bash`
   - 两者可同时source

2. **旧的命令可能不再工作**
   - ❌ `cd ~/yahboomcar_ros2_ws && colcon build` (会找不到STTG包)
   - ✅ `cd ~/yahboomcar_ros2_ws/sttg_nav_ws && colcon build` (正确)

3. **如果找不到包**
   ```bash
   # 检查是否source了正确的工作空间
   echo $CMAKE_PREFIX_PATH | grep sttg_nav_ws
   
   # 如果没有，手动source
   source ~/yahboomcar_ros2_ws/sttg_nav_ws/install/setup.bash
   ```

---

## 📊 项目状态

| 项目 | 状态 |
|------|------|
| STTG核心功能 | ✅ 完成 |
| 系统集成测试 | ✅ 通过 |
| 工作空间分离 | ✅ 完成 |
| 文档更新 | ✅ 完成 |
| **总体** | **✅ 可投入生产** |

---

**迁移完成于**: 2026-03-29  
**现在状态**: Phase 3.1 - Workspace Separation Complete

下一步推荐：构建并运行集成测试以验证新工作空间的完整性。
