# SSTG Interaction Manager - Module Guide

## Overview

The SSTG Interaction Manager (Phase 4.2) orchestrates the entire navigation and task execution workflow. It coordinates between multiple system components—NLP understanding, navigation planning, execution, perception, and user feedback—to provide a seamless end-to-end task management experience.

**Key Features:**
- Comprehensive task state machine (8 states)
- Service-based architecture for modular integration
- Asynchronous multi-service coordination
- Real-time feedback monitoring from executor
- Graceful error handling and task cancellation
- Extensible design for future perception/checking stages

---

## Architecture

### System Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SSTG Interaction Manager                            │
│                      (Phase 4.2)                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────┐                                            │
│  │   start_task()       │ ◄─ User Instruction (ProcessNLPQuery)     │
│  │   Service Callback   │                                            │
│  └──────┬───────────────┘                                            │
│         │                                                             │
│    ┌────▼─────────────────────────────────────────┐                 │
│    │  Task Processing Pipeline                    │                 │
│    │                                              │                 │
│    │  1. UNDERSTANDING (NLP Intent Parser)        │                 │
│    │     ↓                                        │                 │
│    │  2. PLANNING (Navigation Planner)            │                 │
│    │     ↓                                        │                 │
│    │  3. POSE RETRIEVAL (Map Manager)             │                 │
│    │     ↓                                        │                 │
│    │  4. EXECUTION (Navigation Executor)          │                 │
│    │     ↓                                        │                 │
│    │  5. FEEDBACK MONITORING (Real-time)          │                 │
│    └────┬─────────────────────────────────────────┘                 │
│         │                                                             │
│  ┌──────▼──────────────────┐  ┌─────────────────┐                   │
│  │ cancel_task()           │  │ query_status()  │                   │
│  │ (Trigger Service)       │  │ (Trigger)       │                   │
│  └─────────────────────────┘  └─────────────────┘                   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Task State Machine

```
                           ┌─────────────┐
                           │    IDLE     │
                           └──────┬──────┘
                                  │
                    (start_task)  │
                                  ▼
                        ┌──────────────────┐
                        │  UNDERSTANDING   │ ◄─────┐
                        └──────┬───────────┘       │
                               │                  │
                          (NLP OK)               (Error)
                               ▼                  │
                        ┌──────────────────┐      │
                        │    PLANNING      │──────┤
                        └──────┬───────────┘      │
                               │                  │
                          (Plan OK)              (Error)
                               ▼                  │
                        ┌──────────────────┐      │
                        │ NAVIGATING       │──────┤
                        └──────┬───────────┘      │
                               │                  │
                    ┌──────────┴──────────┐      (Error)
                    │                     │       │
            (reached)  │             (failed) │       │
                    ▼                     ▼       │
            ┌──────────────┐    ┌──────────────┐ │
            │  COMPLETED   │    │   FAILED     │─┘
            └──────────────┘    └──────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                               ▼
                        (cancel_task)
                               ▼
                        ┌──────────────┐
                        │   CANCELED   │
                        └──────────────┘
```

---

## Component Details

### 1. InteractionManagerNode (`interaction_manager_node.py`)

**Purpose:** Main ROS2 node implementing the task orchestration workflow.

**Key Classes:**

#### TaskState (Enum)
Defines all possible task states:
```python
class TaskState(Enum):
    IDLE = 'idle'           # No active task
    UNDERSTANDING = 'understanding'  # Processing NLP
    PLANNING = 'planning'   # Generating navigation plan
    NAVIGATING = 'navigating'  # Executing navigation
    CHECKING = 'checking'   # Semantic perception (future)
    COMPLETED = 'completed'  # Task succeeded
    FAILED = 'failed'       # Task failed
    CANCELED = 'canceled'   # Task canceled by user
```

#### InteractionManagerNode
Main node class managing task lifecycle.

**Attributes:**
- `task_state: TaskState` - Current task state
- `current_task_id: str` - Unique task identifier (timestamp-based)
- `current_intent: str` - Parsed NLP intent
- `current_candidates: list[int]` - Available navigation targets
- `callback_group: ReentrantCallbackGroup` - Thread-safe callback handling

**Services:**

##### start_task() [ProcessNLPQuery]
Initiates a new task execution.

**Request:**
```
string text_input         # User command ("Go to living room sofa")
string context           # Additional context
```

**Response:**
```
bool success             # Operation success
string query_json       # Planning result JSON
string intent          # Parsed intent
float32 confidence     # Intent confidence
string error_message   # Error details if failed
```

**Workflow:**
1. Check if task already running
2. Call NLP service (process_nlp_query)
3. Call planner service (plan_navigation)
4. Retrieve target node pose (get_node_pose)
5. Execute navigation (execute_navigation)
6. Monitor feedback (subscribed to navigation_feedback)

**Error Handling:**
- Returns early if service unavailable with fallback message
- Transitions to FAILED state on any step failure
- Logs all errors for debugging

##### cancel_task() [Trigger]
Cancels currently executing task.

**Response:**
```
bool success
string message          # Status message
```

**Behavior:**
- Only active on NAVIGATING, PLANNING, or UNDERSTANDING states
- Transitions to CANCELED state
- Logs cancellation event

##### query_task_status() [Trigger]
Returns current task status.

**Response:**
```
bool success
string message          # Current state as string
```

**Behavior:**
- Always returns current state
- Used for polling task progress

**Subscriptions:**

##### navigation_feedback [sstg_msgs/NavigationFeedback]
Monitors executor feedback to track navigation progress.

**Callback:**
```python
def navigation_feedback_callback(self, msg):
    # Updates task state based on executor status
    # msg.status: 'starting', 'in_progress', 'reached', 'failed'
```

**State Transitions:**
- `msg.status == 'reached'` → `COMPLETED`
- `msg.status == 'failed'` → `FAILED`

---

## Service Integration

### Internal Service Clients

The node interacts with these services (must be available):

1. **process_nlp_query** (sstg_nlp_interface)
   - Input: text_input, context
   - Output: intent, confidence, query_json
   - Timeout: 5s

2. **plan_navigation** (sstg_navigation_planner)
   - Input: intent, entities, confidence, current_node
   - Output: candidate_node_ids, plan_json, reasoning
   - Timeout: 5s

3. **get_node_pose** (sstg_map_manager)
   - Input: node_id
   - Output: pose (geometry_msgs/PoseStamped)
   - Timeout: 5s

4. **execute_navigation** (sstg_navigation_executor)
   - Input: target_pose, node_id
   - Output: success, message
   - Timeout: 5s

### Wait-for-Service Logic

Each client waits 3 seconds for service availability before timing out. If unavailable, the task transitions to FAILED with error message.

---

## Usage Examples

### Example 1: Start a Navigation Task

**Terminal 1 (Start Interaction Manager):**
```bash
ros2 run sstg_interaction_manager interaction_manager_node
```

**Terminal 2 (Send Task Request):**
```bash
ros2 service call /start_task sstg_msgs/srv/ProcessNLPQuery \
  "text_input: 'Go to the living room sofa'" "context: 'inside house'"
```

**Expected Output:**
```
success: true
intent: 'navigate_to'
confidence: 0.95
query_json: '{"target":"sofa", "room":"living_room"}'
error_message: ''
```

### Example 2: Query Task Status

```bash
ros2 service call /query_task_status std_srvs/srv/Trigger {}
```

**Response:**
```
success: true
message: 'navigating'
```

### Example 3: Cancel Active Task

```bash
ros2 service call /cancel_task std_srvs/srv/Trigger {}
```

**Response:**
```
success: true
message: 'Task canceled'
```

---

## Error Handling Strategy

### Graceful Degradation

1. **Service Unavailable:** Log warning, return FAILED with reason
2. **Timeout (5s):** Assume service crashed, fail task
3. **Service Error Response:** Forward error message to user

### Recovery

- User can retry (automatically restarts from IDLE)
- Task history preserved in logs
- No automatic retry logic (explicit user action required)

---

## Logging

All significant events are logged with timestamps:

```
[INFO] Start task 20260325101530: Go to living room
[INFO] Task 20260325101530 NLP intent: navigate_to (conf: 0.95)
[INFO] Task 20260325101530 plan candidates: [2, 5, 8]
[INFO] Task 20260325101530 navigation started node 2
[INFO] Task 20260325101530 completed
```

---

## Future Extensions (Phase 4.3+)

1. **Checking Stage:** Perception integration after reaching target
2. **Multi-turn Dialogue:** Handle clarification requests
3. **Adaptive Planning:** Retry with alternative candidates on failure
4. **User Feedback Loop:** Explicit confirmation before navigation
5. **Task History:** Persistent logging and analysis

---

## Testing

See `test/test_interaction_manager.py` for unit and integration test cases.

Supported test scenarios:
- Task startup and state transitions
- Service timeout handling
- Feedback monitoring and completion detection
- Task cancellation
- Concurrent task requests (should be rejected)

---

## Performance Metrics

- **Task Startup to Navigation Initiation:** ~500ms (typical)
- **Service Call Timeout:** 5 seconds per step (configurable)
- **Feedback Loop Frequency:** 10 Hz (from executor)
- **Max Concurrent Tasks:** 1 (sequential only)

---

## Dependencies

- `rclpy`: ROS2 Python client
- `std_srvs`: Standard ROS2 service definitions
- `geometry_msgs`: Pose message definitions
- `sstg_msgs`: Project-specific messages
- `sstg_nlp_interface`, `sstg_navigation_planner`, `sstg_map_manager`, `sstg_navigation_executor`: Service providers

---

## Version History

| Version | Date       | Changes |
|---------|-----------|---------|
| 0.1.0   | 2026-03-25 | Initial release with 5-stage task pipeline |

---

## References

- [SSTG-Nav-Plan.md](../../SSTG-Nav-Plan.md) - Overall system design
- [sstg_navigation_executor](../sstg_navigation_executor/) - Executor module documentation
- [sstg_navigation_planner](../sstg_navigation_planner/) - Planner module documentation
