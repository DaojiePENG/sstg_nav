#!/usr/bin/env python3
"""
Diagnose NLP and Planning integration - test map matching and candidate generation
"""

import rclpy
from rclpy.node import Node
import json
import time
from sstg_msgs.srv import ProcessNLPQuery, PlanNavigation, QuerySemantic


class DiagnoseNLPPlanning(Node):
    def __init__(self):
        super().__init__('diagnose_nlp_planning')
        
        self.nlp_client = self.create_client(ProcessNLPQuery, 'process_nlp_query')
        self.plan_client = self.create_client(PlanNavigation, 'plan_navigation')
        self.map_client = self.create_client(QuerySemantic, 'query_semantic')
        
        self.get_logger().info('Diagnosis node initialized')

    def diagnose_map(self):
        """Check what the map manager has loaded"""
        self.get_logger().info("\n" + "="*60)
        self.get_logger().info("Phase 1: MAP CHECK")
        self.get_logger().info("="*60)
        
        if not self.map_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Map service not available')
            return False
        
        # Query empty to get all nodes
        map_req = QuerySemantic.Request()
        map_req.query = ''
        
        map_future = self.map_client.call_async(map_req)
        rclpy.spin_until_future_complete(self, map_future, timeout_sec=5.0)
        
        if not map_future.done():
            self.get_logger().error('Map query timeout')
            return False
        
        map_result = map_future.result()
        self.get_logger().info(f"✓ Map service found {len(map_result.node_ids)} nodes")
        
        if map_result.semantics:
            for i, (node_id, semantic) in enumerate(zip(map_result.node_ids, map_result.semantics)):
                self.get_logger().info(f"  Node {node_id}: {semantic.room_type} - {semantic.description}")
        
        return True

    def diagnose_nlp(self, test_queries):
        """Test NLP processing"""
        self.get_logger().info("\n" + "="*60)
        self.get_logger().info("Phase 2: NLP ANALYSIS")
        self.get_logger().info("="*60)
        
        if not self.nlp_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('NLP service not available')
            return {}
        
        results = {}
        
        for query in test_queries:
            self.get_logger().info(f"\n📝 Query: '{query}'")
            
            nlp_req = ProcessNLPQuery.Request()
            nlp_req.text_input = query
            nlp_req.context = 'home'
            
            nlp_future = self.nlp_client.call_async(nlp_req)
            rclpy.spin_until_future_complete(self, nlp_future, timeout_sec=5.0)
            
            if not nlp_future.done():
                self.get_logger().error(f'  ✗ NLP timeout')
                results[query] = None
                continue
            
            nlp_result = nlp_future.result()
            
            if not nlp_result.success:
                self.get_logger().error(f"  ✗ NLP failed: {nlp_result.error_message}")
                results[query] = None
                continue
            
            self.get_logger().info(f"  ✓ Intent: {nlp_result.intent}")
            self.get_logger().info(f"  ✓ Confidence: {nlp_result.confidence:.2f}")
            
            # Parse query JSON
            try:
                query_data = json.loads(nlp_result.query_json)
                if isinstance(query_data, dict):
                    entities = query_data.get('entities', [])
                    self.get_logger().info(f"  ✓ Entities: {entities}")
                else:
                    entities = query_data if isinstance(query_data, list) else [query_data]
                    self.get_logger().info(f"  ✓ Entities: {entities}")
            except:
                self.get_logger().error(f"  ✗ Failed to parse query JSON")
                entities = []
            
            results[query] = {
                'intent': nlp_result.intent,
                'confidence': nlp_result.confidence,
                'entities': entities,
                'query_json': nlp_result.query_json
            }
        
        return results

    def diagnose_planning(self, nlp_results):
        """Test planning with NLP results"""
        self.get_logger().info("\n" + "="*60)
        self.get_logger().info("Phase 3: PLANNING MATCHING")
        self.get_logger().info("="*60)
        
        if not self.plan_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Planning service not available')
            return
        
        for query, nlp_result in nlp_results.items():
            if nlp_result is None:
                continue
            
            self.get_logger().info(f"\n📍 Planning for: '{query}'")
            
            plan_req = PlanNavigation.Request()
            plan_req.intent = nlp_result['intent']
            plan_req.entities = nlp_result['query_json']
            plan_req.confidence = nlp_result['confidence']
            plan_req.current_node = -1
            
            plan_future = self.plan_client.call_async(plan_req)
            rclpy.spin_until_future_complete(self, plan_future, timeout_sec=5.0)
            
            if not plan_future.done():
                self.get_logger().error(f"  ✗ Planning timeout")
                continue
            
            plan_result = plan_future.result()
            
            if not plan_result.success:
                self.get_logger().error(f"  ✗ Planning failed: {plan_result.reasoning}")
            else:
                self.get_logger().info(f"  ✓ Candidates: {plan_result.candidate_node_ids}")
                self.get_logger().info(f"  ✓ Reasoning: {plan_result.reasoning}")

    def run_diagnosis(self):
        """Run full diagnosis"""
        self.get_logger().info("🔍 Starting NLP-Planning Diagnosis\n")
        
        # Phase 1: Check map
        if not self.diagnose_map():
            return False
        
        # Phase 2: Test NLP with various queries
        test_queries = [
            '去客厅',           # Go to living room
            '去客厅沙发',       # Go to living room sofa
            '找沙发',           # Find sofa
            '去卧室',           # Go to bedroom
            '去厨房',           # Go to kitchen
            '查询洗手间',       # Query bathroom
        ]
        
        nlp_results = self.diagnose_nlp(test_queries)
        
        # Phase 3: Test planning with NLP results
        self.diagnose_planning(nlp_results)
        
        self.get_logger().info("\n" + "="*60)
        self.get_logger().info("✅ Diagnosis complete")
        self.get_logger().info("="*60)


def main():
    rclpy.init()
    node = DiagnoseNLPPlanning()
    
    try:
        node.run_diagnosis()
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
