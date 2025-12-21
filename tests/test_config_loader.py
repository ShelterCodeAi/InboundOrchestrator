#!/usr/bin/env python3
"""
Tests for the ConfigLoader class.
"""
import unittest
import sys
from pathlib import Path
import tempfile
import json

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from inbound_orchestrator.utils.config_loader import ConfigLoader
from inbound_orchestrator.rules.rule_engine import EmailRule
from inbound_orchestrator.sqs.sqs_client import SQSQueue


class TestConfigLoader(unittest.TestCase):
    """Test cases for ConfigLoader class."""
    
    def test_load_yaml_file(self):
        """Test loading YAML configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
test_key: test_value
number: 42
list:
  - item1
  - item2
""")
            config_path = f.name
        
        try:
            config = ConfigLoader.load_file(config_path)
            self.assertEqual(config['test_key'], 'test_value')
            self.assertEqual(config['number'], 42)
            self.assertEqual(len(config['list']), 2)
        finally:
            Path(config_path).unlink()
    
    def test_load_json_file(self):
        """Test loading JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'test_key': 'test_value', 'number': 42}, f)
            config_path = f.name
        
        try:
            config = ConfigLoader.load_file(config_path)
            self.assertEqual(config['test_key'], 'test_value')
            self.assertEqual(config['number'], 42)
        finally:
            Path(config_path).unlink()
    
    def test_load_file_not_found(self):
        """Test loading non-existent file."""
        with self.assertRaises(FileNotFoundError):
            ConfigLoader.load_file('/nonexistent/path/to/file.yaml')
    
    def test_save_yaml_file(self):
        """Test saving configuration to YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            data = {'test_key': 'test_value', 'number': 42}
            ConfigLoader.save_file(data, config_path, format='yaml')
            
            # Load it back to verify
            loaded = ConfigLoader.load_file(config_path)
            self.assertEqual(loaded['test_key'], 'test_value')
            self.assertEqual(loaded['number'], 42)
        finally:
            Path(config_path).unlink()
    
    def test_save_json_file(self):
        """Test saving configuration to JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            data = {'test_key': 'test_value', 'number': 42}
            ConfigLoader.save_file(data, config_path, format='json')
            
            # Load it back to verify
            loaded = ConfigLoader.load_file(config_path)
            self.assertEqual(loaded['test_key'], 'test_value')
            self.assertEqual(loaded['number'], 42)
        finally:
            Path(config_path).unlink()
    
    def test_load_rules(self):
        """Test loading rules from configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
rules:
  - name: test_rule
    description: Test rule
    condition: "priority == 'high'"
    action: test_queue
    priority: 100
    enabled: true
""")
            config_path = f.name
        
        try:
            rules = ConfigLoader.load_rules(config_path)
            self.assertEqual(len(rules), 1)
            self.assertEqual(rules[0].name, 'test_rule')
            self.assertEqual(rules[0].action, 'test_queue')
        finally:
            Path(config_path).unlink()
    
    def test_load_rules_with_invalid_rule(self):
        """Test loading rules with an invalid rule."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
rules:
  - name: valid_rule
    description: Valid rule
    condition: "priority == 'high'"
    action: test_queue
    priority: 100
    enabled: true
  - name: invalid_rule
    # Missing required fields
    description: Invalid rule
""")
            config_path = f.name
        
        try:
            rules = ConfigLoader.load_rules(config_path)
            # Should load only the valid rule
            self.assertEqual(len(rules), 1)
            self.assertEqual(rules[0].name, 'valid_rule')
        finally:
            Path(config_path).unlink()
    
    def test_save_rules(self):
        """Test saving rules to configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            rules = [
                EmailRule(
                    name='rule1',
                    description='First rule',
                    condition="priority == 'high'",
                    action='queue1',
                    priority=100,
                    enabled=True
                ),
                EmailRule(
                    name='rule2',
                    description='Second rule',
                    condition="priority == 'low'",
                    action='queue2',
                    priority=50,
                    enabled=False
                )
            ]
            
            ConfigLoader.save_rules(rules, config_path)
            
            # Load it back to verify
            loaded_rules = ConfigLoader.load_rules(config_path)
            self.assertEqual(len(loaded_rules), 2)
            self.assertEqual(loaded_rules[0].name, 'rule1')
            self.assertEqual(loaded_rules[1].name, 'rule2')
        finally:
            Path(config_path).unlink()
    
    def test_load_queues(self):
        """Test loading queues from configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
queues:
  - name: test_queue
    url: https://sqs.us-east-1.amazonaws.com/123456789012/test
    description: Test queue
""")
            config_path = f.name
        
        try:
            queues = ConfigLoader.load_queues(config_path)
            self.assertEqual(len(queues), 1)
            self.assertEqual(queues[0].name, 'test_queue')
        finally:
            Path(config_path).unlink()
    
    def test_save_queues(self):
        """Test saving queues to configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            queues = [
                SQSQueue(
                    name='queue1',
                    url='https://sqs.us-east-1.amazonaws.com/123456789012/queue1',
                    description='First queue'
                ),
                SQSQueue(
                    name='queue2',
                    url='https://sqs.us-east-1.amazonaws.com/123456789012/queue2',
                    description='Second queue'
                )
            ]
            
            ConfigLoader.save_queues(queues, config_path)
            
            # Load it back to verify
            loaded_queues = ConfigLoader.load_queues(config_path)
            self.assertEqual(len(loaded_queues), 2)
            self.assertEqual(loaded_queues[0].name, 'queue1')
            self.assertEqual(loaded_queues[1].name, 'queue2')
        finally:
            Path(config_path).unlink()
    
    def test_load_full_config(self):
        """Test loading full configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
settings:
  default_queue: default

queues:
  - name: test_queue
    url: https://sqs.us-east-1.amazonaws.com/123456789012/test
    description: Test queue

rules:
  - name: test_rule
    description: Test rule
    condition: "priority == 'high'"
    action: test_queue
    priority: 100
    enabled: true

aws_config:
  region: us-east-1

logging_config:
  level: INFO
""")
            config_path = f.name
        
        try:
            config = ConfigLoader.load_full_config(config_path)
            
            self.assertIn('rules', config)
            self.assertIn('queues', config)
            self.assertIn('settings', config)
            self.assertIn('aws_config', config)
            self.assertIn('logging_config', config)
            
            self.assertEqual(len(config['rules']), 1)
            self.assertEqual(len(config['queues']), 1)
            self.assertEqual(config['settings']['default_queue'], 'default')
        finally:
            Path(config_path).unlink()
    
    def test_create_sample_config(self):
        """Test creating sample configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            ConfigLoader.create_sample_config(config_path)
            
            # Load it to verify
            config = ConfigLoader.load_file(config_path)
            
            self.assertIn('settings', config)
            self.assertIn('queues', config)
            self.assertIn('rules', config)
            self.assertGreater(len(config['queues']), 0)
            self.assertGreater(len(config['rules']), 0)
        finally:
            Path(config_path).unlink()


if __name__ == '__main__':
    unittest.main()
