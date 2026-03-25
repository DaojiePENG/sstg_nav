#!/bin/bash
# Complete SSTG Integration Test - All in One

set -e

WORKSPACE_DIR="/home/daojie/yahboomcar_ros2_ws"
SOURCE_CMD="source ${WORKSPACE_DIR}/yahboomcar_ws/install/setup.bash"
LOG_DIR="${WORKSPACE_DIR}/project_test/logs"

mkdir -p "$LOG_DIR"

echo "=================================================================================="
echo "🚀 SSTG Complete Integration Test"
echo "=================================================================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up processes..."
    kill $MM_PID $NLP_PID $PLAN_PID $EXEC_PID $IM_PID 2>/dev/null || true
    sleep 1
    echo "✓ All nodes stopped"
}

trap cleanup EXIT

# Start all nodes
echo "📍 Phase 1: Starting all ROS2 nodes..."
echo ""

eval "$SOURCE_CMD && ros2 run sstg_map_manager map_manager_node" > "$LOG_DIR/map_manager.log" 2>&1 &
MM_PID=$!
echo "  • Map Manager Node (PID: $MM_PID)"
sleep 1

eval "$SOURCE_CMD && ros2 run sstg_nlp_interface nlp_node" > "$LOG_DIR/nlp_node.log" 2>&1 &
NLP_PID=$!
echo "  • NLP Node (PID: $NLP_PID)"
sleep 1

eval "$SOURCE_CMD && ros2 run sstg_navigation_planner planning_node" > "$LOG_DIR/planning_node.log" 2>&1 &
PLAN_PID=$!
echo "  • Planning Node (PID: $PLAN_PID)"
sleep 1

eval "$SOURCE_CMD && ros2 run sstg_navigation_executor executor_node" > "$LOG_DIR/executor_node.log" 2>&1 &
EXEC_PID=$!
echo "  • Executor Node (PID: $EXEC_PID)"
sleep 1

eval "$SOURCE_CMD && ros2 run sstg_interaction_manager interaction_manager_node" > "$LOG_DIR/interaction_manager.log" 2>&1 &
IM_PID=$!
echo "  • Interaction Manager Node (PID: $IM_PID)"
sleep 3

echo ""
echo "📍 Phase 2: Verifying all services..."
echo ""

eval "$SOURCE_CMD && ros2 node list" > /tmp/nodes.txt
if [ -s /tmp/nodes.txt ]; then
    echo "  ✓ Nodes:"
    cat /tmp/nodes.txt | sed 's/^/    /'
fi

echo ""
eval "$SOURCE_CMD && ros2 service list | grep -E '(start_task|cancel_task|query_task_status|process_nlp_query|plan_navigation|get_node_pose|execute_navigation)' | sort" > /tmp/services.txt
if [ -s /tmp/services.txt ]; then
    echo "  ✓ Services:"
    cat /tmp/services.txt | sed 's/^/    /'
else
    echo "  ⚠️  Some services not yet available"
fi

echo ""
echo "📍 Phase 3: Running integration tests..."
echo ""

cd "$WORKSPACE_DIR"
eval "$SOURCE_CMD && python3 project_test/test_system_integration.py"

echo ""
echo "=================================================================================="
echo "✅ Integration test completed!"
echo "=================================================================================="
