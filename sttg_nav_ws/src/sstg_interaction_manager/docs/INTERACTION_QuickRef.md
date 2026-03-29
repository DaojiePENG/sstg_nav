# SSTG Interaction Manager - Quick Reference

## Launching the Node

```bash
# Source ROS2 environment
source install/setup.bash

# Run interaction manager node
ros2 run sstg_interaction_manager interaction_manager_node
```

Expected output:
```
[INFO] sstg_interaction_manager initialized
```

## Available Services

### 1. start_task (ProcessNLPQuery)

**Topic:** `/start_task`

Initiates a new navigation task.

**Usage (Correct JSON format):**
```bash
ros2 service call /start_task sstg_msgs/srv/ProcessNLPQuery \
  "{text_input: 'Go to the living room', context: 'inside house'}"
```

**Alternative (YAML line-by-line):**
```bash
ros2 service call /start_task sstg_msgs/srv/ProcessNLPQuery \
  "text_input: 'Go to the living room'
context: 'inside house'"
```

**Fields:**
- `text_input` (string): User command
- `context` (string): Additional context (optional)

**Response:**
- `success` (bool): Whether task started successfully
- `query_json` (string): Planning result JSON
- `intent` (string): Parsed NLP intent
- `confidence` (float): Intent confidence (0-1)
- `error_message` (string): Error details if failed

**Examples:**

Command: "Find the TV remote"
```bash
ros2 service call /start_task sstg_msgs/srv/ProcessNLPQuery \
  "{text_input: 'Find the TV remote', context: 'living room'}"
```

Response:
```yaml
intent: "find_object"
confidence: 0.92
query_json: '{"object":"TV remote", "location":"living room"}'
error_message: ""
```

Command: "Take me to the kitchen"
```bash
ros2 service call /start_task sstg_msgs/srv/ProcessNLPQuery \
  "{text_input: 'Take me to the kitchen', context: ''}"
```

Response:
```yaml
intent: "navigate_to"
confidence: 0.98
query_json: '{"target":"kitchen"}'
error_message: ""
```

### 2. cancel_task (Trigger)

**Topic:** `/cancel_task`

Cancels currently executing task.

**Usage:**
```bash
ros2 service call /cancel_task std_srvs/srv/Trigger {}
```

**Response:**
```yaml
success: true
message: "Task canceled"
```

**Behavior:**
- Only works if task is in NAVIGATING, PLANNING, or UNDERSTANDING state
- Returns error if no task active
- Transitions task to CANCELED state

### 3. query_task_status (Trigger)

**Topic:** `/query_task_status`

Returns current task state.

**Usage:**
```bash
ros2 service call /query_task_status std_srvs/srv/Trigger {}
```

**Response Examples:**

Active task:
```yaml
success: true
message: "navigating"
```

Idle:
```yaml
success: true
message: "idle"
```

Completed:
```yaml
success: true
message: "completed"
```

Failed:
```yaml
success: true
message: "failed"
```

---

## Task State Diagram

```
START
  │
  └──▶ IDLE
         │
         │ (start_task)
         ▼
      UNDERSTANDING
         │
    ┌────┴────┐
    │          │
   YES        NO (error)
    │          │
    ▼          └─────┐
 PLANNING            │
    │                │
┌───┴────┐           │
│         │           │
YES      NO (error)  │
│         │           │
▼         └───────┐  │
NAVIGATING        │  │
    │             │  │
┌───┴────┐        │  │
│         │        │  │
OK      FAIL      │  │
│         │        │  │
▼         ▼        │  │
COMPLETED FAILED◄──┤  │
    │         │    │  │
    │         │    │  │
    └────┬────┴────┴──┘
         │
      (idle)
         ▼
       IDLE (next task)

(cancel_task) ──▶ CANCELED
```

---

## Troubleshooting

### Issue: "Service unavailable" error

**Cause:** Upstream service (NLP, Planner, Executor, Map Manager) not running.

**Solution:**
```bash
# Check if services are available
ros2 service list

# Expected services:
# /process_nlp_query (from sstg_nlp_interface)
# /plan_navigation (from sstg_navigation_planner)
# /get_node_pose (from sstg_map_manager)
# /execute_navigation (from sstg_navigation_executor)

# Start missing services:
ros2 run sstg_nlp_interface nlp_interface_node
ros2 run sstg_navigation_planner planner_node
ros2 run sstg_map_manager map_manager_node
ros2 run sstg_navigation_executor executor_node
```

### Issue: Task times out

**Cause:** Service taking longer than 5 seconds to respond.

**Solution:**
1. Check service logs for performance issues
2. Increase timeout in source code if acceptable
3. Verify network connectivity

### Issue: Navigation fails after planning succeeds

**Cause:** Planned node unreachable or Nav2 configuration error.

**Solution:**
1. Check Nav2 logs: `ros2 node info /navigate_to_pose`
2. Verify target node is in map database
3. Check AMCL localization status: `ros2 topic echo /amcl_pose`
4. Try manual navigation: `ros2 action send_goal /navigate_to_pose ...`

### Issue: Service call returns "TaskBusy"

**Cause:** Previous task still active (not in IDLE/COMPLETED/FAILED/CANCELED state).

**Solution:**
```bash
# Query status to check state
ros2 service call /query_task_status std_srvs/srv/Trigger {}

# Cancel if necessary
ros2 service call /cancel_task std_srvs/srv/Trigger {}

# Wait for state transition, then retry
```

---

## Testing with Real Services

### Setup (5 terminals)

**Terminal 1: Map Manager**
```bash
ros2 run sstg_map_manager map_manager_node
```

**Terminal 2: NLP Interface**
```bash
ros2 run sstg_nlp_interface nlp_interface_node
```

**Terminal 3: Navigation Planner**
```bash
ros2 run sstg_navigation_planner planner_node
```

**Terminal 4: Navigation Executor**
```bash
ros2 run sstg_navigation_executor executor_node
```

**Terminal 5: Interaction Manager**
```bash
ros2 run sstg_interaction_manager interaction_manager_node
```

### Send Test Task

```bash
ros2 service call /start_task sstg_msgs/srv/ProcessNLPQuery \
  "text_input: 'Navigate to the office'" \
  "context: 'main floor'"
```

### Monitor Feedback

```bash
ros2 topic echo /navigation_feedback
```

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Start to Navigation | ~500ms | Typical full pipeline |
| NLP Processing | 100-500ms | VLM API call latency |
| Planning | 50-200ms | Dijkstra algorithm |
| Execution Initiation | 100-300ms | Nav2 goal acceptance |
| Feedback Loop | 100ms (10Hz) | Real-time monitoring |
| Service Timeout | 5s | Per service call |

---

## Version

- **Package:** sstg_interaction_manager
- **Version:** 0.1.0
- **Release Date:** 2026-03-25
- **Status:** ✅ Stable

---

## Related Documentation

- [MODULE_GUIDE.md](MODULE_GUIDE.md) - Detailed architecture and design
- [../../SSTG-Nav-Plan.md](../../SSTG-Nav-Plan.md) - System-wide planning
- [../sstg_navigation_executor/docs/](../sstg_navigation_executor/docs/) - Executor documentation
- [../sstg_navigation_planner/docs/](../sstg_navigation_planner/docs/) - Planner documentation
