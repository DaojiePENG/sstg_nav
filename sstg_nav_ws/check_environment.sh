#!/bin/bash

# SSTG Navigation System 环境检查脚本
# 在构建前运行此脚本检查系统环境

echo "================================================"
echo "SSTG Navigation System - 环境检查"
echo "================================================"
echo ""

PASS=0
FAIL=0

# 检查函数
check_item() {
    local name=$1
    local command=$2
    local expected=$3
    
    if eval "$command" &>/dev/null; then
        if [ -z "$expected" ] || eval "$command" | grep -q "$expected"; then
            echo "✓ $name"
            ((PASS++))
            return 0
        else
            echo "✗ $name (版本不符)"
            ((FAIL++))
            return 1
        fi
    else
        echo "✗ $name (未安装或不可用)"
        ((FAIL++))
        return 1
    fi
}

# 详细检查函数
check_item_verbose() {
    local name=$1
    local command=$2
    local expected=$3
    local fix=$4
    
    if eval "$command" &>/dev/null; then
        local result=$(eval "$command")
        if [ -z "$expected" ] || echo "$result" | grep -q "$expected"; then
            echo "✓ $name"
            echo "  → $result"
            ((PASS++))
            return 0
        else
            echo "✗ $name (版本不符)"
            echo "  → 当前: $result"
            echo "  → 需要: $expected"
            if [ -n "$fix" ]; then
                echo "  → 解决: $fix"
            fi
            ((FAIL++))
            return 1
        fi
    else
        echo "✗ $name (未安装或不可用)"
        if [ -n "$fix" ]; then
            echo "  → 解决: $fix"
        fi
        ((FAIL++))
        return 1
    fi
}

echo "1. 检查Python环境"
echo "---"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$PYTHON_VERSION" = "3.10" ] || [ "$PYTHON_VERSION" = "3.11" ] || [ "$PYTHON_VERSION" = "3.12" ]; then
    echo "✓ Python版本"
    echo "  → Python $PYTHON_VERSION"
    ((PASS++))
else
    echo "✗ Python版本"
    echo "  → 当前: Python $PYTHON_VERSION"
    echo "  → 需要: 3.10、3.11 或 3.12"
    ((FAIL++))
fi
echo ""

echo "2. 检查ROS2环境"
echo "---"
check_item_verbose "ROS2发行版" \
    "echo \$ROS_DISTRO" \
    "humble" \
    "运行: source /opt/ros/humble/setup.bash"
check_item_verbose "ROS2命令" \
    "which ros2" \
    "" \
    "运行: sudo apt install ros-humble-desktop"
echo ""

echo "3. 检查构建工具"
echo "---"
check_item_verbose "colcon版本" \
    "colcon --help 2>&1 | head -1" \
    "" \
    "运行: sudo apt install python3-colcon-common-extensions"
check_item_verbose "setuptools版本" \
    "pip show setuptools | grep Version | cut -d' ' -f2" \
    "^6[0-9]\." \
    "运行: pip install 'setuptools<70' (关键!)"

# 特别检查setuptools
SETUPTOOLS_VERSION=$(pip show setuptools 2>/dev/null | grep Version | cut -d' ' -f2)
if [ -n "$SETUPTOOLS_VERSION" ]; then
    SETUPTOOLS_MAJOR=$(echo $SETUPTOOLS_VERSION | cut -d'.' -f1)
    if [ "$SETUPTOOLS_MAJOR" -ge 70 ]; then
        echo ""
        echo "⚠️  警告: setuptools版本过新 ($SETUPTOOLS_VERSION)"
        echo "   ROS2 colcon需要版本 < 70"
        echo "   解决方案:"
        echo "   - 运行: pip install 'setuptools<70'"
        echo "   - 如果使用conda: conda run -n hw_nav pip install 'setuptools<70'"
        ((FAIL++))
    fi
fi
echo ""

echo "4. 检查项目结构"
echo "---"
check_item "SSTG包目录" \
    "test -d src/sstg_msgs && test -d src/sstg_nlp_interface"
check_item "安装脚本" \
    "test -f install/setup.bash"
echo ""

echo "5. 检查依赖包"
echo "---"
check_item "rclpy包" \
    "python3 -c 'import rclpy'"
check_item "fastapi包" \
    "python3 -c 'import fastapi'"
check_item "networkx包" \
    "python3 -c 'import networkx'"
echo ""

echo "================================================"
echo "检查结果摘要"
echo "================================================"
echo "通过: $PASS 项"
echo "失败: $FAIL 项"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✓ 所有检查通过! 你的系统已准备好构建SSTG"
    echo ""
    echo "下一步:"
    echo "  cd $(pwd)"
    echo "  colcon build --symlink-install"
    exit 0
else
    echo "✗ 有 $FAIL 项检查失败，请按上述提示修复"
    echo ""
    echo "修复后，再次运行此脚本:"
    echo "  bash check_environment.sh"
    exit 1
fi
