"""
Tests for Advanced Training Configuration System

Tests sophisticated hyperparameter optimization, training logic editing,
AI-assisted training strategy suggestions, A/B testing capabilities, and comprehensive
training monitoring with gradient analysis and loss curves.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
"""

import pytest
import tempfile
import shutil
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.ai_karen_engine.core.response.advanced_training_config import (
    AdvancedTrainingConfigManager,
    AdvancedTrainingConfig,
    HyperparameterSweepConfig,
    ABTestConfig,
    TrainingLogicConfig,
    OptimizationConfig,
    MonitoringConfig,
    HyperparameterRange,
    OptimizationAlgorithm,
    LossFunction,
    SchedulerType,
    TrainingMetrics,
    GridSearchOptimizer,
    RandomSearchOptimizer,
    AITrainingAssistant,
    ABTestManager
)


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for test configurations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def training_manager(temp_config_dir):
    """Create training manager with temporary config directory."""
    return AdvancedTrainingConfigManager(config_dir=temp_config_dir)


@pytest.fixture
def sample_training_config():
    """Create sample training configuration."""
    return AdvancedTrainingConfig(
        model_id="test_model",
        dataset_id="test_dataset",
        training_logic=TrainingLogicConfig(
            gradient_accumulation_steps=2,
            gradient_clipping=1.0,
            mixed_precision=True
        ),
        optimization=OptimizationConfig(
            algorithm=OptimizationAlgorithm.ADAMW,
            learning_rate=1e-4,
            weight_decay=0.01
        ),
        monitoring=MonitoringConfig(
            track_gradients=True,
            track_weights=True,
            gradient_histogram_frequency=10
        ),
        max_epochs=50,
        batch_size=32
    )


@pytest.fixture
def sample_hyperparameter_sweep():
    """Create sample hyperparameter sweep configuration."""
    return HyperparameterSweepConfig(
        parameters={
            "learning_rate": HyperparameterRange(
                min_value=1e-5,
                max_value=1e-3,
                log_scale=True
            ),
            "batch_size": HyperparameterRange(
                min_value=16,
                max_value=128,
                discrete_values=[16, 32, 64, 128]
            )
        },
        search_strategy="grid",
        max_trials=20,
        objective_metric="validation_loss",
        objective_direction="minimize"
    )


@pytest.fixture
def sample_ab_test_config():
    """Create sample A/B test configuration."""
    return ABTestConfig(
        test_name="optimizer_comparison",
        control_config={"optimizer": "adam", "learning_rate": 1e-4},
        treatment_configs=[
            {"optimizer": "adamw", "learning_rate": 1e-4},
            {"optimizer": "sgd", "learning_rate": 1e-3}
        ],
        traffic_split=[0.5, 0.25, 0.25],
        success_metric="validation_accuracy",
        minimum_sample_size=50
    )


class TestAdvancedTrainingConfig:
    """Test advanced training configuration creation and management."""
    
    def test_create_advanced_config(self, training_manager):
        """Test creating advanced training configuration."""
        config_data = {
            "model_id": "test_model",
            "dataset_id": "test_dataset",
            "max_epochs": 100,
            "batch_size": 32
        }
        
        config = training_manager.create_advanced_config(config_data)
        
        assert config.model_id == "test_model"
        assert config.dataset_id == "test_dataset"
        assert config.max_epochs == 100
        assert config.batch_size == 32
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)
    
    def test_save_and_load_config(self, training_manager, sample_training_config):
        """Test saving and loading training configuration."""
        # Save configuration
        config_id = training_manager.save_config(sample_training_config)
        assert config_id.startswith("config_test_model_")
        
        # Load configuration
        loaded_config = training_manager.load_config(config_id)
        
        assert loaded_config.model_id == sample_training_config.model_id
        assert loaded_config.dataset_id == sample_training_config.dataset_id
        assert loaded_config.training_logic.gradient_clipping == 1.0
        assert loaded_config.optimization.algorithm == OptimizationAlgorithm.ADAMW
        assert loaded_config.monitoring.track_gradients is True
    
    def test_load_nonexistent_config(self, training_manager):
        """Test loading non-existent configuration raises error."""
        with pytest.raises(FileNotFoundError):
            training_manager.load_config("nonexistent_config")


class TestHyperparameterOptimization:
    """Test hyperparameter optimization functionality."""
    
    def test_grid_search_optimizer(self, sample_hyperparameter_sweep):
        """Test grid search hyperparameter optimizer."""
        optimizer = GridSearchOptimizer(sample_hyperparameter_sweep)
        
        # Test parameter suggestion
        params1 = optimizer.suggest_parameters(0)
        assert "learning_rate" in params1
        assert "batch_size" in params1
        assert params1["batch_size"] in [16, 32, 64, 128]
        
        # Test different trial
        params2 = optimizer.suggest_parameters(1)
        assert params1 != params2  # Should be different parameters
        
        # Test reporting results
        optimizer.report_result(0, params1, 0.5, {"accuracy": 0.85})
        optimizer.report_result(1, params2, 0.3, {"accuracy": 0.90})
        
        # Test getting best parameters
        best_params, best_score = optimizer.get_best_parameters()
        assert best_score == 0.3  # Lower is better for minimization
        assert best_params == params2
    
    def test_random_search_optimizer(self, sample_hyperparameter_sweep):
        """Test random search hyperparameter optimizer."""
        sample_hyperparameter_sweep.search_strategy = "random"
        sample_hyperparameter_sweep.max_trials = 10
        
        optimizer = RandomSearchOptimizer(sample_hyperparameter_sweep)
        
        # Test parameter suggestions
        params_list = []
        for i in range(5):
            params = optimizer.suggest_parameters(i)
            params_list.append(params)
            assert "learning_rate" in params
            assert "batch_size" in params
            assert 1e-5 <= params["learning_rate"] <= 1e-3
            assert params["batch_size"] in [16, 32, 64, 128]
        
        # Should generate different parameters
        assert len(set(str(p) for p in params_list)) > 1
        
        # Test reporting and best parameters
        for i, params in enumerate(params_list):
            optimizer.report_result(i, params, np.random.random(), {})
        
        best_params, best_score = optimizer.get_best_parameters()
        assert best_params is not None
        assert isinstance(best_score, float)
    
    def test_hyperparameter_sweep_integration(self, training_manager, sample_training_config):
        """Test hyperparameter sweep integration."""
        # Add sweep configuration
        sample_training_config.hyperparameter_sweep = HyperparameterSweepConfig(
            parameters={
                "learning_rate": HyperparameterRange(min_value=1e-5, max_value=1e-3, log_scale=True)
            },
            search_strategy="random",
            max_trials=5
        )
        
        # Start sweep
        sweep_id = training_manager.start_hyperparameter_sweep(sample_training_config)
        assert sweep_id.startswith("sweep_test_model_")
        
        # Get suggestions and report results
        for trial in range(3):
            suggestion = training_manager.get_sweep_suggestion(sweep_id, trial)
            assert "learning_rate" in suggestion
            
            # Report result
            training_manager.report_sweep_result(
                sweep_id, trial, suggestion, np.random.random(), {"accuracy": np.random.random()}
            )
        
        # Get best parameters
        best_params, best_score = training_manager.get_sweep_best_params(sweep_id)
        assert best_params is not None
        assert isinstance(best_score, float)


class TestAITrainingAssistant:
    """Test AI-assisted training strategy suggestions."""
    
    def test_suggest_training_strategy(self):
        """Test AI training strategy suggestions."""
        assistant = AITrainingAssistant()
        
        suggestions = assistant.suggest_training_strategy(
            model_type="transformer",
            dataset_size=10000,
            hardware_specs={"gpu_memory_gb": 8, "has_gpu": True, "cpu_cores": 8}
        )
        
        assert "optimization_config" in suggestions
        assert "training_logic" in suggestions
        assert "monitoring_recommendations" in suggestions
        assert "potential_issues" in suggestions
        assert "mitigation_strategies" in suggestions
        
        # Check specific recommendations
        assert "learning_rate" in suggestions["optimization_config"]
        assert "batch_size" in suggestions["optimization_config"]
        assert suggestions["training_logic"]["mixed_precision"] is True
        assert "gpu_utilization" in suggestions["monitoring_recommendations"]
    
    def test_analyze_training_progress(self):
        """Test training progress analysis."""
        assistant = AITrainingAssistant()
        metrics = TrainingMetrics()
        
        # Add some sample metrics
        for epoch in range(10):
            metrics.add_epoch_metrics(epoch, {
                "loss": 1.0 - epoch * 0.1,
                "val_loss": 1.0 - epoch * 0.08,
                "gradient_norm": 0.5 + np.random.normal(0, 0.1)
            })
        
        analysis = assistant.analyze_training_progress(metrics)
        
        assert "status" in analysis
        assert "issues_detected" in analysis
        assert "recommendations" in analysis
        assert "early_stopping_suggestion" in analysis
        assert analysis["status"] in ["healthy", "needs_attention"]
    
    def test_gradient_explosion_detection(self):
        """Test gradient explosion detection."""
        assistant = AITrainingAssistant()
        metrics = TrainingMetrics()
        
        # Add metrics with gradient explosion
        for epoch in range(5):
            metrics.add_epoch_metrics(epoch, {
                "loss": 1.0,
                "gradient_norm": 15.0  # High gradient norm
            })
        
        analysis = assistant.analyze_training_progress(metrics)
        
        assert "gradient_explosion" in analysis["issues_detected"]
        assert any("gradient_explosion" in rec["issue"] for rec in analysis["recommendations"])
    
    def test_overfitting_detection(self):
        """Test overfitting detection."""
        assistant = AITrainingAssistant()
        metrics = TrainingMetrics()
        
        # Add metrics showing overfitting pattern
        for epoch in range(15):
            train_loss = max(0.1, 1.0 - epoch * 0.1)
            val_loss = max(0.3, 1.0 - epoch * 0.05)  # Validation loss higher than training
            
            metrics.add_epoch_metrics(epoch, {
                "loss": train_loss,
                "val_loss": val_loss,
                "gradient_norm": 0.5
            })
        
        analysis = assistant.analyze_training_progress(metrics)
        
        assert "overfitting" in analysis["issues_detected"]
        assert any("overfitting" in rec["issue"] for rec in analysis["recommendations"])


class TestABTestManager:
    """Test A/B testing functionality."""
    
    def test_create_ab_test(self, sample_ab_test_config):
        """Test creating A/B test."""
        manager = ABTestManager()
        
        test_id = manager.create_ab_test(sample_ab_test_config)
        assert test_id.startswith("ab_test_optimizer_comparison_")
        assert test_id in manager.active_tests
    
    def test_invalid_traffic_split(self):
        """Test A/B test with invalid traffic split."""
        manager = ABTestManager()
        
        config = ABTestConfig(
            test_name="invalid_test",
            control_config={},
            treatment_configs=[{}],
            traffic_split=[0.6, 0.5],  # Sums to 1.1, invalid
            success_metric="accuracy"
        )
        
        with pytest.raises(ValueError, match="Traffic split must sum to 1.0"):
            manager.create_ab_test(config)
    
    def test_treatment_assignment(self, sample_ab_test_config):
        """Test treatment assignment consistency."""
        manager = ABTestManager()
        test_id = manager.create_ab_test(sample_ab_test_config)
        
        # Test consistent assignment for same user
        treatment1, config1 = manager.assign_treatment(test_id, "user123")
        treatment2, config2 = manager.assign_treatment(test_id, "user123")
        
        assert treatment1 == treatment2
        assert config1 == config2
        
        # Test different users get potentially different treatments
        treatments = set()
        for i in range(20):
            treatment, _ = manager.assign_treatment(test_id, f"user{i}")
            treatments.add(treatment)
        
        # Should have at least 2 different treatments with reasonable probability
        assert len(treatments) >= 2
    
    def test_record_and_analyze_results(self, sample_ab_test_config):
        """Test recording and analyzing A/B test results."""
        manager = ABTestManager()
        test_id = manager.create_ab_test(sample_ab_test_config)
        
        # Record results for different treatments
        np.random.seed(42)  # For reproducible results
        
        # Control group - lower performance
        for i in range(60):
            manager.record_result(test_id, f"control_user_{i}", "control", 
                                np.random.normal(0.7, 0.1))
        
        # Treatment 1 - higher performance
        for i in range(60):
            manager.record_result(test_id, f"treatment1_user_{i}", "treatment_1", 
                                np.random.normal(0.8, 0.1))
        
        # Treatment 2 - similar to control
        for i in range(60):
            manager.record_result(test_id, f"treatment2_user_{i}", "treatment_2", 
                                np.random.normal(0.72, 0.1))
        
        # Analyze results
        analysis = manager.analyze_test_results(test_id)
        
        assert analysis["status"] == "complete"
        assert "treatment_stats" in analysis
        assert "comparisons" in analysis
        assert len(analysis["comparisons"]) == 2  # Two treatments compared to control
        
        # Check if treatment 1 shows significant improvement
        treatment1_comparison = next(c for c in analysis["comparisons"] if c["treatment"] == "treatment_1")
        assert treatment1_comparison["improvement_percent"] > 0
    
    def test_insufficient_data_analysis(self, sample_ab_test_config):
        """Test analysis with insufficient data."""
        manager = ABTestManager()
        test_id = manager.create_ab_test(sample_ab_test_config)
        
        # Record only a few results
        for i in range(10):
            manager.record_result(test_id, f"user_{i}", "control", 0.7)
        
        analysis = manager.analyze_test_results(test_id)
        
        assert analysis["status"] == "insufficient_data"
        assert "need" in analysis["message"]


class TestTrainingMetrics:
    """Test training metrics tracking and analysis."""
    
    def test_training_metrics_basic(self):
        """Test basic training metrics functionality."""
        metrics = TrainingMetrics()
        
        # Add epoch metrics
        metrics.add_epoch_metrics(0, {
            "loss": 1.0,
            "val_loss": 1.2,
            "accuracy": 0.7,
            "val_accuracy": 0.65,
            "learning_rate": 1e-4,
            "gradient_norm": 0.5,
            "epoch_time": 120.5,
            "memory_usage": 0.8,
            "custom_metric1": 0.9
        })
        
        assert len(metrics.loss_history) == 1
        assert len(metrics.validation_loss_history) == 1
        assert len(metrics.accuracy_history) == 1
        assert len(metrics.learning_rate_history) == 1
        assert len(metrics.gradient_norms) == 1
        assert len(metrics.epoch_times) == 1
        assert len(metrics.memory_usage) == 1
        assert "custom_metric1" in metrics.custom_metrics
    
    def test_loss_curve_data(self):
        """Test loss curve data generation."""
        metrics = TrainingMetrics()
        
        # Add multiple epochs
        for epoch in range(5):
            metrics.add_epoch_metrics(epoch, {
                "loss": 1.0 - epoch * 0.1,
                "val_loss": 1.2 - epoch * 0.08
            })
        
        loss_data = metrics.get_loss_curve_data()
        
        assert "epochs" in loss_data
        assert "train_loss" in loss_data
        assert "val_loss" in loss_data
        assert len(loss_data["epochs"]) == 5
        assert len(loss_data["train_loss"]) == 5
        assert len(loss_data["val_loss"]) == 5
        assert loss_data["epochs"] == [0, 1, 2, 3, 4]
    
    def test_gradient_analysis(self):
        """Test gradient analysis functionality."""
        metrics = TrainingMetrics()
        
        # Add gradient data
        gradient_norms = [0.5, 0.6, 15.0, 0.4, 1e-8]  # Include explosion and vanishing
        for i, norm in enumerate(gradient_norms):
            metrics.add_epoch_metrics(i, {"gradient_norm": norm})
        
        analysis = metrics.get_gradient_analysis()
        
        assert "mean_gradient_norm" in analysis
        assert "std_gradient_norm" in analysis
        assert "gradient_norm_history" in analysis
        assert "gradient_explosion_detected" in analysis
        assert "gradient_vanishing_detected" in analysis
        
        assert analysis["gradient_explosion_detected"] is True  # 15.0 > 10.0
        assert analysis["gradient_vanishing_detected"] is True  # 1e-8 < 1e-6


class TestAdvancedTrainingConfigManager:
    """Test the main advanced training configuration manager."""
    
    def test_ai_suggestions_integration(self, training_manager):
        """Test AI suggestions integration."""
        suggestions = training_manager.get_ai_suggestions(
            model_type="transformer",
            dataset_size=5000,
            hardware_specs={"gpu_memory_gb": 16, "has_gpu": True, "cpu_cores": 12}
        )
        
        assert isinstance(suggestions, dict)
        assert "optimization_config" in suggestions
        assert "training_logic" in suggestions
    
    def test_training_metrics_lifecycle(self, training_manager):
        """Test complete training metrics lifecycle."""
        training_id = "test_training_123"
        
        # Initialize metrics
        metrics = training_manager.initialize_training_metrics(training_id)
        assert isinstance(metrics, TrainingMetrics)
        assert training_id in training_manager.training_metrics
        
        # Update metrics
        for epoch in range(3):
            training_manager.update_training_metrics(training_id, epoch, {
                "loss": 1.0 - epoch * 0.2,
                "val_loss": 1.1 - epoch * 0.15,
                "gradient_norm": 0.5
            })
        
        # Get analysis
        analysis = training_manager.get_training_analysis(training_id)
        assert "status" in analysis
        assert "issues_detected" in analysis
        
        # Get loss curves
        loss_data = training_manager.get_loss_curve_data(training_id)
        assert len(loss_data["train_loss"]) == 3
        
        # Get gradient analysis
        gradient_analysis = training_manager.get_gradient_analysis(training_id)
        assert "mean_gradient_norm" in gradient_analysis
        
        # Export report
        report = training_manager.export_training_report(training_id)
        assert "training_id" in report
        assert "metrics" in report
        assert "analysis" in report
    
    def test_nonexistent_training_metrics(self, training_manager):
        """Test accessing non-existent training metrics."""
        with pytest.raises(ValueError, match="Training nonexistent not found"):
            training_manager.get_training_analysis("nonexistent")
        
        with pytest.raises(ValueError, match="Training nonexistent not found"):
            training_manager.get_loss_curve_data("nonexistent")
        
        with pytest.raises(ValueError, match="Training nonexistent not found"):
            training_manager.get_gradient_analysis("nonexistent")


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_complete_hyperparameter_optimization_workflow(self, training_manager):
        """Test complete hyperparameter optimization workflow."""
        # Create configuration with hyperparameter sweep
        config = AdvancedTrainingConfig(
            model_id="integration_test_model",
            dataset_id="integration_test_dataset",
            hyperparameter_sweep=HyperparameterSweepConfig(
                parameters={
                    "learning_rate": HyperparameterRange(min_value=1e-5, max_value=1e-3, log_scale=True),
                    "batch_size": HyperparameterRange(min_value=16, max_value=128, discrete_values=[16, 32, 64])
                },
                search_strategy="random",
                max_trials=5,
                objective_metric="validation_loss",
                objective_direction="minimize"
            )
        )
        
        # Start sweep
        sweep_id = training_manager.start_hyperparameter_sweep(config)
        
        # Run trials
        best_objective = float('inf')
        for trial in range(3):
            # Get suggestion
            params = training_manager.get_sweep_suggestion(sweep_id, trial)
            
            # Simulate training with these parameters
            objective_value = np.random.uniform(0.1, 1.0)
            metrics = {"accuracy": np.random.uniform(0.7, 0.95)}
            
            # Report result
            training_manager.report_sweep_result(sweep_id, trial, params, objective_value, metrics)
            
            if objective_value < best_objective:
                best_objective = objective_value
        
        # Get best parameters
        best_params, best_score = training_manager.get_sweep_best_params(sweep_id)
        
        assert best_params is not None
        assert best_score <= best_objective
        assert "learning_rate" in best_params
        assert "batch_size" in best_params
    
    def test_ab_test_with_training_monitoring(self, training_manager):
        """Test A/B test combined with training monitoring."""
        # Create A/B test
        ab_config = ABTestConfig(
            test_name="training_monitoring_test",
            control_config={"optimizer": "adam"},
            treatment_configs=[{"optimizer": "adamw"}],
            traffic_split=[0.5, 0.5],
            success_metric="final_accuracy",
            minimum_sample_size=20
        )
        
        test_id = training_manager.create_ab_test(ab_config)
        
        # Simulate training sessions for both treatments
        for user_id in range(100):  # Increase sample size to meet minimum requirement
            treatment, config = training_manager.get_ab_test_assignment(test_id, f"user_{user_id}")
            
            # Initialize training metrics for this user's session
            training_id = f"training_{user_id}"
            training_manager.initialize_training_metrics(training_id)
            
            # Simulate training epochs
            final_accuracy = 0.7 if treatment == "control" else 0.75  # Treatment slightly better
            final_accuracy += np.random.normal(0, 0.05)  # Add noise
            
            for epoch in range(5):
                accuracy = final_accuracy * (epoch + 1) / 5
                training_manager.update_training_metrics(training_id, epoch, {
                    "loss": 1.0 - accuracy,
                    "accuracy": accuracy,
                    "gradient_norm": 0.5
                })
            
            # Record A/B test result
            training_manager.record_ab_test_result(test_id, f"user_{user_id}", treatment, final_accuracy)
        
        # Analyze A/B test results
        analysis = training_manager.analyze_ab_test(test_id)
        
        assert analysis["status"] == "complete"
        assert len(analysis["comparisons"]) == 1
        
        # The treatment should show some improvement (though may not be statistically significant with small sample)
        treatment_comparison = analysis["comparisons"][0]
        assert treatment_comparison["treatment"] == "treatment_1"


if __name__ == "__main__":
    pytest.main([__file__])