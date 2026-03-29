"""
Test navigation executor module
"""

import unittest
from sstg_navigation_executor.navigation_monitor import NavigationMonitor
from sstg_navigation_executor.feedback_handler import FeedbackHandler, NavigationStatus


class MockNode:
    """Mock ROS2 node"""
    def __init__(self):
        self.subscriptions = []
    
    def create_subscription(self, *args, **kwargs):
        return None
    
    def get_logger(self):
        return self
    
    def info(self, msg):
        print(f"[INFO] {msg}")


class TestNavigationMonitor(unittest.TestCase):
    """Test navigation monitor"""
    
    def setUp(self):
        self.node = MockNode()
        self.monitor = NavigationMonitor(self.node)
    
    def test_set_target(self):
        """Test setting target"""
        self.monitor.set_target(5.0, 3.0, 0.5)
        x, y, theta = self.monitor.get_target_pose()
        self.assertAlmostEqual(x, 5.0)
        self.assertAlmostEqual(y, 3.0)
        self.assertAlmostEqual(theta, 0.5)
    
    def test_distance_calculation(self):
        """Test distance calculation"""
        self.monitor.set_target(4.0, 3.0)
        self.monitor.current_x = 0.0
        self.monitor.current_y = 0.0
        
        distance = self.monitor.get_distance_to_target()
        self.assertAlmostEqual(distance, 5.0, places=1)


class TestFeedbackHandler(unittest.TestCase):
    """Test feedback handler"""
    
    def setUp(self):
        self.handler = FeedbackHandler()
    
    def test_start_navigation(self):
        """Test starting navigation"""
        feedback = self.handler.start_navigation(node_id=0)
        self.assertEqual(feedback.node_id, 0)
        self.assertEqual(feedback.status, NavigationStatus.STARTING)
    
    def test_on_reached(self):
        """Test navigation success"""
        feedback = self.handler.start_navigation(node_id=0)
        self.handler.on_reached()
        
        self.assertEqual(feedback.status, NavigationStatus.REACHED)
        self.assertTrue(feedback.is_success())


if __name__ == '__main__':
    unittest.main()
