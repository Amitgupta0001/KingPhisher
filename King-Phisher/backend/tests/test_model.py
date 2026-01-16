"""
Unit tests for model training and evaluation.
"""

import pytest
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import train_model
import pandas as pd

class TestModelTraining:
    """Test model training functionality."""
    
    def test_model_training_completes(self):
        """Test that model training completes without errors."""
        # This test requires the data file to exist
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'email_phishing_data.csv')
        if not os.path.exists(data_path):
            pytest.skip("Training data not available")
        
        result = train_model()
        assert result is True
    
    def test_metrics_file_created(self):
        """Test that metrics file is created after training."""
        metrics_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model_metrics.json')
        if not os.path.exists(metrics_path):
            pytest.skip("Model not trained yet")
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        assert 'performance' in metrics
        assert 'accuracy' in metrics['performance']
        assert 'precision' in metrics['performance']
        assert 'recall' in metrics['performance']
        assert 'f1_score' in metrics['performance']
        assert 'roc_auc' in metrics['performance']
    
    def test_metrics_values_valid(self):
        """Test that metrics have valid values (0-1 range)."""
        metrics_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model_metrics.json')
        if not os.path.exists(metrics_path):
            pytest.skip("Model not trained yet")
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        perf = metrics['performance']
        assert 0 <= perf['accuracy'] <= 1
        assert 0 <= perf['precision'] <= 1
        assert 0 <= perf['recall'] <= 1
        assert 0 <= perf['f1_score'] <= 1
        assert 0 <= perf['roc_auc'] <= 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
