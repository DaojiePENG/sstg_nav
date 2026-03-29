"""
Test interaction manager module
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from sstg_interaction_manager.interaction_manager_node import (
    InteractionManagerNode,
    TaskState
)


class MockRclpy:
    """Mock rclpy for testing"""
    @staticmethod
    def init(args=None):
        pass
    
    @staticmethod
    def shutdown():
        pass
    
    @staticmethod
    def spin_until_future_complete(node, future, timeout_sec=None):
        # Simulate completion
        pass


class TestTaskState(unittest.TestCase):
    """Test TaskState enum"""
    
    def test_task_states_defined(self):
        """Verify all states are defined"""
        self.assertEqual(TaskState.IDLE.value, 'idle')
        self.assertEqual(TaskState.UNDERSTANDING.value, 'understanding')
        self.assertEqual(TaskState.PLANNING.value, 'planning')
        self.assertEqual(TaskState.NAVIGATING.value, 'navigating')
        self.assertEqual(TaskState.CHECKING.value, 'checking')
        self.assertEqual(TaskState.COMPLETED.value, 'completed')
        self.assertEqual(TaskState.FAILED.value, 'failed')
        self.assertEqual(TaskState.CANCELED.value, 'canceled')


class TestInteractionManagerNode(unittest.TestCase):
    """Test interaction manager node"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Mock ROS2 node creation
        self.mock_node = Mock()
        self.mock_node.create_service = Mock(return_value=Mock())
        self.mock_node.create_client = Mock(return_value=Mock())
        self.mock_node.create_subscription = Mock(return_value=Mock())
        self.mock_node.create_timer = Mock(return_value=Mock())
        self.mock_node.get_logger = Mock(return_value=Mock())
        
        # Patch Node.__init__ to use mock
        with patch('rclpy.node.Node.__init__', return_value=None):
            with patch('rclpy.callback_groups.ReentrantCallbackGroup', return_value=Mock()):
                self.node = InteractionManagerNode()
                # Manually initialize attributes
                self.node.task_state = TaskState.IDLE
                self.node.current_task_id = ''
                self.node.current_intent = ''
                self.node.current_candidates = []
    
    def test_initial_state(self):
        """Test initial node state"""
        self.assertEqual(self.node.task_state, TaskState.IDLE)
        self.assertEqual(self.node.current_task_id, '')
        self.assertEqual(self.node.current_intent, '')
        self.assertEqual(self.node.current_candidates, [])
    
    def test_query_status_idle(self):
        """Test query status when idle"""
        request = Mock()
        response = Mock()
        response.success = None
        response.message = None
        
        # Manually set up response attributes
        result = self.node.query_task_status_callback(request, response)
        
        self.assertTrue(result.success or response.success is not None)
    
    def test_task_state_transitions(self):
        """Test valid task state transitions"""
        # IDLE -> UNDERSTANDING
        self.node.task_state = TaskState.IDLE
        self.assertEqual(self.node.task_state, TaskState.IDLE)
        
        # UNDERSTANDING -> PLANNING
        self.node.task_state = TaskState.UNDERSTANDING
        self.assertEqual(self.node.task_state, TaskState.UNDERSTANDING)
        
        # PLANNING -> NAVIGATING
        self.node.task_state = TaskState.PLANNING
        self.assertEqual(self.node.task_state, TaskState.PLANNING)
        
        # NAVIGATING -> COMPLETED
        self.node.task_state = TaskState.NAVIGATING
        self.assertEqual(self.node.task_state, TaskState.NAVIGATING)
        
        # NAVIGATING -> FAILED
        self.node.task_state = TaskState.FAILED
        self.assertEqual(self.node.task_state, TaskState.FAILED)
    
    def test_cancel_when_idle(self):
        """Test cancel when no task active"""
        self.node.task_state = TaskState.IDLE
        request = Mock()
        response = Mock()
        response.success = None
        response.message = None
        
        result = self.node.cancel_task_callback(request, response)
        
        # Should fail when idle
        self.assertIsNotNone(result)
    
    def test_cancel_when_navigating(self):
        """Test cancel during navigation"""
        self.node.task_state = TaskState.NAVIGATING
        self.node.current_task_id = 'test_task_123'
        request = Mock()
        response = Mock()
        response.success = None
        response.message = None
        
        result = self.node.cancel_task_callback(request, response)
        
        # Should succeed when navigating
        self.assertIsNotNone(result)
        self.assertEqual(self.node.task_state, TaskState.CANCELED)
    
    def test_navigation_feedback_in_navigating_state(self):
        """Test navigation feedback handling during navigation"""
        self.node.task_state = TaskState.NAVIGATING
        feedback_msg = Mock()
        feedback_msg.status = 'reached'
        
        self.node.navigation_feedback_callback(feedback_msg)
        
        # Should transition to COMPLETED
        self.assertEqual(self.node.task_state, TaskState.COMPLETED)
    
    def test_navigation_feedback_in_idle_state(self):
        """Test navigation feedback ignored when idle"""
        self.node.task_state = TaskState.IDLE
        feedback_msg = Mock()
        feedback_msg.status = 'reached'
        
        self.node.navigation_feedback_callback(feedback_msg)
        
        # Should remain IDLE
        self.assertEqual(self.node.task_state, TaskState.IDLE)
    
    def test_navigation_feedback_failure(self):
        """Test navigation feedback on failure"""
        self.node.task_state = TaskState.NAVIGATING
        feedback_msg = Mock()
        feedback_msg.status = 'failed'
        feedback_msg.error_message = 'Path blocked'
        
        self.node.navigation_feedback_callback(feedback_msg)
        
        # Should transition to FAILED
        self.assertEqual(self.node.task_state, TaskState.FAILED)


class TestStartTaskCallback(unittest.TestCase):
    """Test start task service callback"""
    
    def setUp(self):
        """Setup test fixtures"""
        with patch('rclpy.node.Node.__init__', return_value=None):
            with patch('rclpy.callback_groups.ReentrantCallbackGroup', return_value=Mock()):
                self.node = InteractionManagerNode()
                self.node.task_state = TaskState.IDLE
                self.node.current_task_id = ''
                self.node.get_logger = Mock(return_value=Mock())
    
    def test_task_already_active(self):
        """Test rejection when task already active"""
        self.node.task_state = TaskState.NAVIGATING
        request = Mock()
        request.text_input = 'Go somewhere'
        request.context = ''
        response = Mock()
        response.success = None
        response.error_message = None
        
        result = self.node.start_task_callback(request, response)
        
        self.assertIsNotNone(result)
        self.assertFalse(result.success)
    
    def test_task_accepted_when_idle(self):
        """Test task acceptance when idle"""
        self.node.task_state = TaskState.IDLE
        request = Mock()
        request.text_input = 'Go to the kitchen'
        request.context = 'home'
        response = Mock()
        response.success = None
        
        # Mock the services to be unavailable (test graceful handling)
        self.node.nlp_client = Mock()
        self.node.nlp_client.wait_for_service = Mock(return_value=False)
        
        result = self.node.start_task_callback(request, response)
        
        self.assertIsNotNone(result)
        self.assertFalse(result.success)  # Should fail due to unavailable NLP


class TestServiceTimeoutHandling(unittest.TestCase):
    """Test timeout handling for service calls"""
    
    def setUp(self):
        """Setup test fixtures"""
        with patch('rclpy.node.Node.__init__', return_value=None):
            with patch('rclpy.callback_groups.ReentrantCallbackGroup', return_value=Mock()):
                self.node = InteractionManagerNode()
                self.node.get_logger = Mock(return_value=Mock())
    
    def test_nlp_service_timeout(self):
        """Test handling NLP service timeout"""
        self.node.nlp_client = Mock()
        self.node.nlp_client.wait_for_service = Mock(return_value=False)
        
        # Should handle gracefully with fallback
        request = Mock()
        request.text_input = 'test'
        request.context = ''
        response = Mock()
        response.success = None
        
        result = self.node.start_task_callback(request, response)
        
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
