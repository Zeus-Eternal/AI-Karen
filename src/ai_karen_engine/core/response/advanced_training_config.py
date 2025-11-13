"""
Advanced Training Configuration System

This module provides sophisticated hyperparameter optimization, training logic editing,
AI-assisted training strategy suggestions, A/B testing capabilities, and comprehensive
training monitoring with gradient analysis and loss curves.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import numpy as np
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class OptimizationAlgorithm(Enum):
    """Supported optimization algorithms for hyperparameter tuning."""
    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"
    RMSPROP = "rmsprop"
    ADAGRAD = "adagrad"
    ADADELTA = "adadelta"


class LossFunction(Enum):
    """Supported loss functions for training."""
    CROSS_ENTROPY = "cross_entropy"
    MSE = "mse"
    MAE = "mae"
    HUBER = "huber"
    FOCAL = "focal"
    CONTRASTIVE = "contrastive"


class SchedulerType(Enum):
    """Learning rate scheduler types."""
    CONSTANT = "constant"
    LINEAR = "linear"
    COSINE = "cosine"
    EXPONENTIAL = "exponential"
    STEP = "step"
    PLATEAU = "plateau"


@dataclass
class HyperparameterRange:
    """Defines a range for hyperparameter optimization."""
    min_value: float
    max_value: float
    step: Optional[float] = None
    log_scale: bool = False
    discrete_values: Optional[List[Union[float, int, str]]] = None


@dataclass
class TrainingLogicConfig:
    """Configuration for custom training logic."""
    custom_loss_function: Optional[str] = None
    gradient_accumulation_steps: int = 1
    gradient_clipping: Optional[float] = None
    mixed_precision: bool = False
    checkpoint_frequency: int = 100
    validation_frequency: int = 50
    early_stopping_patience: int = 10
    early_stopping_threshold: float = 1e-4


@dataclass
class OptimizationConfig:
    """Advanced optimization configuration."""
    algorithm: OptimizationAlgorithm = OptimizationAlgorithm.ADAMW
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1e-8
    momentum: float = 0.9  # For SGD
    scheduler_type: SchedulerType = SchedulerType.COSINE
    scheduler_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HyperparameterSweepConfig:
    """Configuration for hyperparameter sweeps."""
    parameters: Dict[str, HyperparameterRange] = field(default_factory=dict)
    search_strategy: str = "grid"  # grid, random, bayesian
    max_trials: int = 50
    max_concurrent_trials: int = 3
    objective_metric: str = "validation_loss"
    objective_direction: str = "minimize"  # minimize or maximize
    early_termination: bool = True
    early_termination_patience: int = 5


@dataclass
class ABTestConfig:
    """Configuration for A/B testing training strategies."""
    test_name: str
    control_config: Dict[str, Any]
    treatment_configs: List[Dict[str, Any]]
    traffic_split: List[float]  # Should sum to 1.0
    success_metric: str = "validation_accuracy"
    minimum_sample_size: int = 100
    statistical_significance_threshold: float = 0.05
    test_duration_hours: int = 24


@dataclass
class MonitoringConfig:
    """Configuration for training monitoring."""
    track_gradients: bool = True
    track_weights: bool = True
    track_activations: bool = False
    gradient_histogram_frequency: int = 10
    weight_histogram_frequency: int = 50
    loss_curve_smoothing: float = 0.1
    metrics_logging_frequency: int = 1
    tensorboard_logging: bool = True
    wandb_logging: bool = False


@dataclass
class AdvancedTrainingConfig:
    """Complete advanced training configuration."""
    model_id: str
    dataset_id: str
    training_logic: TrainingLogicConfig = field(default_factory=TrainingLogicConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    hyperparameter_sweep: Optional[HyperparameterSweepConfig] = None
    ab_test: Optional[ABTestConfig] = None
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    max_epochs: int = 100
    batch_size: int = 32
    validation_split: float = 0.2
    random_seed: int = 42
    device: str = "auto"
    distributed_training: bool = False
    num_workers: int = 4
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the configuration with JSON-friendly timestamps."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data


class TrainingMetrics:
    """Container for training metrics and monitoring data."""
    
    def __init__(self):
        self.loss_history: List[float] = []
        self.validation_loss_history: List[float] = []
        self.accuracy_history: List[float] = []
        self.validation_accuracy_history: List[float] = []
        self.learning_rate_history: List[float] = []
        self.gradient_norms: List[float] = []
        self.weight_norms: Dict[str, List[float]] = {}
        self.gradient_histograms: List[Dict[str, np.ndarray]] = []
        self.weight_histograms: List[Dict[str, np.ndarray]] = []
        self.epoch_times: List[float] = []
        self.memory_usage: List[float] = []
        self.custom_metrics: Dict[str, List[float]] = {}
    
    def add_epoch_metrics(self, epoch: int, metrics: Dict[str, Any]):
        """Add metrics for a specific epoch."""
        if 'loss' in metrics:
            self.loss_history.append(metrics['loss'])
        if 'val_loss' in metrics:
            self.validation_loss_history.append(metrics['val_loss'])
        if 'accuracy' in metrics:
            self.accuracy_history.append(metrics['accuracy'])
        if 'val_accuracy' in metrics:
            self.validation_accuracy_history.append(metrics['val_accuracy'])
        if 'learning_rate' in metrics:
            self.learning_rate_history.append(metrics['learning_rate'])
        if 'gradient_norm' in metrics:
            self.gradient_norms.append(metrics['gradient_norm'])
        if 'epoch_time' in metrics:
            self.epoch_times.append(metrics['epoch_time'])
        if 'memory_usage' in metrics:
            self.memory_usage.append(metrics['memory_usage'])
        
        # Handle custom metrics
        for key, value in metrics.items():
            if key.startswith('custom_'):
                if key not in self.custom_metrics:
                    self.custom_metrics[key] = []
                self.custom_metrics[key].append(value)
    
    def get_loss_curve_data(self) -> Dict[str, List[float]]:
        """Get data for plotting loss curves."""
        return {
            'epochs': list(range(len(self.loss_history))),
            'train_loss': self.loss_history,
            'val_loss': self.validation_loss_history
        }
    
    def get_gradient_analysis(self) -> Dict[str, Any]:
        """Get gradient analysis data."""
        if not self.gradient_norms:
            return {}
        
        return {
            'mean_gradient_norm': np.mean(self.gradient_norms),
            'std_gradient_norm': np.std(self.gradient_norms),
            'gradient_norm_history': self.gradient_norms,
            'gradient_explosion_detected': any(norm > 10.0 for norm in self.gradient_norms),
            'gradient_vanishing_detected': any(norm < 1e-6 for norm in self.gradient_norms)
        }


class HyperparameterOptimizer(ABC):
    """Abstract base class for hyperparameter optimization strategies."""
    
    @abstractmethod
    def suggest_parameters(self, trial_number: int) -> Dict[str, Any]:
        """Suggest parameters for the next trial."""
        pass
    
    @abstractmethod
    def report_result(self, trial_number: int, parameters: Dict[str, Any], 
                     objective_value: float, metrics: Dict[str, Any]):
        """Report the result of a trial."""
        pass
    
    @abstractmethod
    def get_best_parameters(self) -> Tuple[Dict[str, Any], float]:
        """Get the best parameters found so far."""
        pass


class GridSearchOptimizer(HyperparameterOptimizer):
    """Grid search hyperparameter optimizer."""
    
    def __init__(self, config: HyperparameterSweepConfig):
        self.config = config
        self.parameter_grid = self._generate_parameter_grid()
        self.current_trial = 0
        self.results = []
        self.best_params = None
        self.best_score = float('inf') if config.objective_direction == 'minimize' else float('-inf')
    
    def _generate_parameter_grid(self) -> List[Dict[str, Any]]:
        """Generate all parameter combinations for grid search."""
        import itertools
        
        param_names = list(self.config.parameters.keys())
        param_values = []
        
        for param_name, param_range in self.config.parameters.items():
            if param_range.discrete_values:
                values = param_range.discrete_values
            else:
                if param_range.step:
                    if param_range.log_scale:
                        values = np.logspace(
                            np.log10(param_range.min_value),
                            np.log10(param_range.max_value),
                            int((np.log10(param_range.max_value) - np.log10(param_range.min_value)) / param_range.step) + 1
                        ).tolist()
                    else:
                        values = np.arange(param_range.min_value, param_range.max_value + param_range.step, param_range.step).tolist()
                else:
                    # Default to 10 values
                    if param_range.log_scale:
                        values = np.logspace(np.log10(param_range.min_value), np.log10(param_range.max_value), 10).tolist()
                    else:
                        values = np.linspace(param_range.min_value, param_range.max_value, 10).tolist()
            
            param_values.append(values)
        
        # Generate all combinations
        combinations = list(itertools.product(*param_values))
        return [dict(zip(param_names, combo)) for combo in combinations]
    
    def suggest_parameters(self, trial_number: int) -> Dict[str, Any]:
        """Suggest parameters for the next trial."""
        if trial_number >= len(self.parameter_grid):
            raise StopIteration("All parameter combinations have been tried")
        
        return self.parameter_grid[trial_number]
    
    def report_result(self, trial_number: int, parameters: Dict[str, Any], 
                     objective_value: float, metrics: Dict[str, Any]):
        """Report the result of a trial."""
        self.results.append({
            'trial': trial_number,
            'parameters': parameters,
            'objective_value': objective_value,
            'metrics': metrics
        })
        
        is_better = (
            (self.config.objective_direction == 'minimize' and objective_value < self.best_score) or
            (self.config.objective_direction == 'maximize' and objective_value > self.best_score)
        )
        
        if is_better:
            self.best_score = objective_value
            self.best_params = parameters.copy()
    
    def get_best_parameters(self) -> Tuple[Dict[str, Any], float]:
        """Get the best parameters found so far."""
        return self.best_params, self.best_score


class RandomSearchOptimizer(HyperparameterOptimizer):
    """Random search hyperparameter optimizer."""
    
    def __init__(self, config: HyperparameterSweepConfig):
        self.config = config
        self.results = []
        self.best_params = None
        self.best_score = float('inf') if config.objective_direction == 'minimize' else float('-inf')
        np.random.seed(42)  # For reproducibility
    
    def suggest_parameters(self, trial_number: int) -> Dict[str, Any]:
        """Suggest parameters for the next trial."""
        if trial_number >= self.config.max_trials:
            raise StopIteration("Maximum number of trials reached")
        
        parameters = {}
        for param_name, param_range in self.config.parameters.items():
            if param_range.discrete_values:
                parameters[param_name] = np.random.choice(param_range.discrete_values)
            else:
                if param_range.log_scale:
                    log_min = np.log10(param_range.min_value)
                    log_max = np.log10(param_range.max_value)
                    log_value = np.random.uniform(log_min, log_max)
                    parameters[param_name] = 10 ** log_value
                else:
                    parameters[param_name] = np.random.uniform(param_range.min_value, param_range.max_value)
        
        return parameters
    
    def report_result(self, trial_number: int, parameters: Dict[str, Any], 
                     objective_value: float, metrics: Dict[str, Any]):
        """Report the result of a trial."""
        self.results.append({
            'trial': trial_number,
            'parameters': parameters,
            'objective_value': objective_value,
            'metrics': metrics
        })
        
        is_better = (
            (self.config.objective_direction == 'minimize' and objective_value < self.best_score) or
            (self.config.objective_direction == 'maximize' and objective_value > self.best_score)
        )
        
        if is_better:
            self.best_score = objective_value
            self.best_params = parameters.copy()
    
    def get_best_parameters(self) -> Tuple[Dict[str, Any], float]:
        """Get the best parameters found so far."""
        return self.best_params, self.best_score


class AITrainingAssistant:
    """AI-assisted training strategy suggestions and parameter tuning."""
    
    def __init__(self):
        self.knowledge_base = self._load_training_knowledge()
    
    def _load_training_knowledge(self) -> Dict[str, Any]:
        """Load training knowledge base for AI assistance."""
        return {
            'model_types': {
                'transformer': {
                    'recommended_lr': (1e-5, 5e-4),
                    'recommended_batch_size': (8, 64),
                    'recommended_warmup_steps': (500, 2000),
                    'common_issues': ['gradient_explosion', 'overfitting', 'slow_convergence']
                },
                'cnn': {
                    'recommended_lr': (1e-4, 1e-2),
                    'recommended_batch_size': (16, 128),
                    'recommended_warmup_steps': (100, 1000),
                    'common_issues': ['vanishing_gradients', 'overfitting']
                },
                'rnn': {
                    'recommended_lr': (1e-4, 1e-2),
                    'recommended_batch_size': (32, 256),
                    'recommended_warmup_steps': (200, 1500),
                    'common_issues': ['gradient_explosion', 'vanishing_gradients', 'slow_training']
                }
            },
            'optimization_strategies': {
                'gradient_explosion': {
                    'solutions': ['gradient_clipping', 'lower_learning_rate', 'batch_normalization'],
                    'parameters': {'gradient_clip': 1.0, 'lr_reduction': 0.5}
                },
                'vanishing_gradients': {
                    'solutions': ['residual_connections', 'batch_normalization', 'higher_learning_rate'],
                    'parameters': {'lr_increase': 2.0}
                },
                'overfitting': {
                    'solutions': ['dropout', 'weight_decay', 'early_stopping', 'data_augmentation'],
                    'parameters': {'dropout_rate': 0.1, 'weight_decay': 0.01}
                },
                'slow_convergence': {
                    'solutions': ['learning_rate_scheduling', 'optimizer_change', 'batch_size_increase'],
                    'parameters': {'lr_schedule': 'cosine', 'batch_size_multiplier': 2}
                }
            }
        }
    
    def suggest_training_strategy(self, model_type: str, dataset_size: int, 
                                hardware_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal training strategy based on model and hardware."""
        suggestions = {
            'optimization_config': {},
            'training_logic': {},
            'monitoring_recommendations': [],
            'potential_issues': [],
            'mitigation_strategies': []
        }
        
        # Get model-specific recommendations
        if model_type in self.knowledge_base['model_types']:
            model_info = self.knowledge_base['model_types'][model_type]
            
            # Learning rate suggestion
            lr_min, lr_max = model_info['recommended_lr']
            if dataset_size < 1000:
                suggested_lr = lr_min * 2  # Higher LR for small datasets
            elif dataset_size > 100000:
                suggested_lr = lr_min  # Lower LR for large datasets
            else:
                suggested_lr = (lr_min + lr_max) / 2
            
            suggestions['optimization_config']['learning_rate'] = suggested_lr
            
            # Batch size suggestion based on hardware
            batch_min, batch_max = model_info['recommended_batch_size']
            gpu_memory = hardware_specs.get('gpu_memory_gb', 4)
            
            if gpu_memory >= 16:
                suggested_batch_size = min(batch_max, 64)
            elif gpu_memory >= 8:
                suggested_batch_size = min(batch_max, 32)
            else:
                suggested_batch_size = min(batch_max, 16)
            
            suggestions['optimization_config']['batch_size'] = suggested_batch_size
            
            # Common issues and mitigation
            suggestions['potential_issues'] = model_info['common_issues']
            for issue in model_info['common_issues']:
                if issue in self.knowledge_base['optimization_strategies']:
                    strategy = self.knowledge_base['optimization_strategies'][issue]
                    suggestions['mitigation_strategies'].append({
                        'issue': issue,
                        'solutions': strategy['solutions'],
                        'parameters': strategy['parameters']
                    })
        
        # Hardware-specific recommendations
        if hardware_specs.get('has_gpu', False):
            suggestions['training_logic']['mixed_precision'] = True
            suggestions['monitoring_recommendations'].append('gpu_utilization')
        
        if hardware_specs.get('cpu_cores', 1) > 4:
            suggestions['training_logic']['num_workers'] = min(hardware_specs['cpu_cores'], 8)
        
        return suggestions
    
    def analyze_training_progress(self, metrics: TrainingMetrics) -> Dict[str, Any]:
        """Analyze training progress and suggest improvements."""
        analysis = {
            'status': 'healthy',
            'issues_detected': [],
            'recommendations': [],
            'early_stopping_suggestion': False
        }
        
        if not metrics.loss_history:
            return analysis
        
        # Check for gradient explosion
        gradient_analysis = metrics.get_gradient_analysis()
        if gradient_analysis.get('gradient_explosion_detected', False):
            analysis['issues_detected'].append('gradient_explosion')
            analysis['recommendations'].append({
                'issue': 'gradient_explosion',
                'suggestion': 'Reduce learning rate by 50% and add gradient clipping',
                'parameters': {'learning_rate_multiplier': 0.5, 'gradient_clip': 1.0}
            })
        
        # Check for vanishing gradients
        if gradient_analysis.get('gradient_vanishing_detected', False):
            analysis['issues_detected'].append('vanishing_gradients')
            analysis['recommendations'].append({
                'issue': 'vanishing_gradients',
                'suggestion': 'Increase learning rate and consider batch normalization',
                'parameters': {'learning_rate_multiplier': 2.0}
            })
        
        # Check for overfitting
        if len(metrics.loss_history) > 10 and len(metrics.validation_loss_history) > 10:
            recent_train_loss = np.mean(metrics.loss_history[-5:])
            recent_val_loss = np.mean(metrics.validation_loss_history[-5:])
            
            if recent_val_loss > recent_train_loss * 1.5:
                analysis['issues_detected'].append('overfitting')
                analysis['recommendations'].append({
                    'issue': 'overfitting',
                    'suggestion': 'Add regularization or early stopping',
                    'parameters': {'weight_decay': 0.01, 'dropout_rate': 0.1}
                })
        
        # Check for plateau
        if len(metrics.loss_history) > 20:
            recent_losses = metrics.loss_history[-10:]
            loss_std = np.std(recent_losses)
            if loss_std < 0.001:
                analysis['issues_detected'].append('training_plateau')
                analysis['recommendations'].append({
                    'issue': 'training_plateau',
                    'suggestion': 'Consider learning rate scheduling or early stopping',
                    'parameters': {'lr_schedule': 'reduce_on_plateau'}
                })
                analysis['early_stopping_suggestion'] = True
        
        # Overall status
        if analysis['issues_detected']:
            analysis['status'] = 'needs_attention'
        
        return analysis
    
    def optimize_hyperparameters(self, current_config: AdvancedTrainingConfig, 
                                performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest hyperparameter optimizations based on performance history."""
        suggestions = {}
        
        if not performance_history:
            return suggestions
        
        # Analyze performance trends
        recent_performance = performance_history[-5:] if len(performance_history) >= 5 else performance_history
        
        # Learning rate optimization
        if all('val_loss' in perf for perf in recent_performance):
            val_losses = [perf['val_loss'] for perf in recent_performance]
            if len(val_losses) > 1:
                loss_trend = np.polyfit(range(len(val_losses)), val_losses, 1)[0]
                
                if loss_trend > 0:  # Loss is increasing
                    suggestions['learning_rate'] = current_config.optimization.learning_rate * 0.5
                    suggestions['reason'] = 'Validation loss increasing, reducing learning rate'
                elif abs(loss_trend) < 0.001:  # Loss plateaued
                    suggestions['learning_rate'] = current_config.optimization.learning_rate * 1.2
                    suggestions['reason'] = 'Loss plateaued, slightly increasing learning rate'
        
        # Batch size optimization
        if 'memory_usage' in recent_performance[-1]:
            memory_usage = recent_performance[-1]['memory_usage']
            if memory_usage < 0.7:  # Less than 70% memory usage
                suggestions['batch_size'] = min(current_config.batch_size * 2, 128)
                suggestions['batch_size_reason'] = 'Low memory usage, increasing batch size'
        
        return suggestions


class ABTestManager:
    """Manager for A/B testing training strategies."""
    
    def __init__(self):
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_ab_test(self, config: ABTestConfig) -> str:
        """Create a new A/B test."""
        test_id = f"ab_test_{config.test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Validate traffic split
        if abs(sum(config.traffic_split) - 1.0) > 1e-6:
            raise ValueError("Traffic split must sum to 1.0")
        
        if len(config.traffic_split) != len(config.treatment_configs) + 1:
            raise ValueError("Traffic split must have one entry for control + each treatment")
        
        self.active_tests[test_id] = config
        self.test_results[test_id] = []
        
        logger.info(f"Created A/B test: {test_id}")
        return test_id
    
    def assign_treatment(self, test_id: str, user_id: str) -> Tuple[str, Dict[str, Any]]:
        """Assign a user to a treatment group."""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        config = self.active_tests[test_id]
        
        # Use hash of user_id for consistent assignment
        import hashlib
        hash_value = int(hashlib.md5(f"{test_id}_{user_id}".encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 10000.0
        
        # Determine treatment based on traffic split
        cumulative_split = 0
        for i, split in enumerate(config.traffic_split):
            cumulative_split += split
            if random_value <= cumulative_split:
                if i == 0:
                    return "control", config.control_config
                else:
                    return f"treatment_{i}", config.treatment_configs[i-1]
        
        # Fallback to control
        return "control", config.control_config
    
    def record_result(
        self,
        test_id: str,
        user_id: str,
        treatment: str,
        metric_value: float,
        additional_metrics: Optional[Dict[str, Any]] = None,
    ):
        """Record a result for an A/B test."""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        result = {
            'user_id': user_id,
            'treatment': treatment,
            'metric_value': metric_value,
            'timestamp': datetime.now(),
            'additional_metrics': additional_metrics or {}
        }
        
        self.test_results[test_id].append(result)
    
    def analyze_test_results(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results for statistical significance."""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        config = self.active_tests[test_id]
        results = self.test_results[test_id]
        
        if not results:
            return {'status': 'no_data', 'message': 'No results recorded yet'}
        
        # Group results by treatment
        treatment_groups = {}
        for result in results:
            treatment = result['treatment']
            if treatment not in treatment_groups:
                treatment_groups[treatment] = []
            treatment_groups[treatment].append(result['metric_value'])
        
        # Check minimum sample size
        for treatment, values in treatment_groups.items():
            if len(values) < config.minimum_sample_size:
                return {
                    'status': 'insufficient_data',
                    'message': f'Treatment {treatment} has only {len(values)} samples, need {config.minimum_sample_size}'
                }
        
        # Perform statistical analysis
        analysis = {
            'status': 'complete',
            'treatment_stats': {},
            'comparisons': [],
            'winner': None,
            'confidence': 0.0
        }
        
        # Calculate stats for each treatment
        for treatment, values in treatment_groups.items():
            analysis['treatment_stats'][treatment] = {
                'count': len(values),
                'mean': np.mean(values),
                'std': np.std(values),
                'median': np.median(values)
            }
        
        # Compare treatments to control
        if 'control' in treatment_groups:
            control_values = treatment_groups['control']
            control_mean = np.mean(control_values)
            
            for treatment, values in treatment_groups.items():
                if treatment == 'control':
                    continue
                
                # Perform t-test
                from scipy import stats
                t_stat, p_value = stats.ttest_ind(control_values, values)
                
                treatment_mean = np.mean(values)
                improvement = (treatment_mean - control_mean) / control_mean * 100
                
                comparison = {
                    'treatment': treatment,
                    'control_mean': control_mean,
                    'treatment_mean': treatment_mean,
                    'improvement_percent': improvement,
                    'p_value': p_value,
                    'significant': p_value < config.statistical_significance_threshold,
                    't_statistic': t_stat
                }
                
                analysis['comparisons'].append(comparison)
        
        # Determine winner
        significant_improvements = [
            comp for comp in analysis['comparisons'] 
            if comp['significant'] and comp['improvement_percent'] > 0
        ]
        
        if significant_improvements:
            best_treatment = max(significant_improvements, key=lambda x: x['improvement_percent'])
            analysis['winner'] = best_treatment['treatment']
            analysis['confidence'] = 1 - best_treatment['p_value']
        
        return analysis
    
    def stop_test(self, test_id: str) -> Dict[str, Any]:
        """Stop an A/B test and return final results."""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        final_analysis = self.analyze_test_results(test_id)
        
        # Archive the test
        archived_test = {
            'config': asdict(self.active_tests[test_id]),
            'results': self.test_results[test_id],
            'final_analysis': final_analysis,
            'stopped_at': datetime.now()
        }
        
        # Clean up active test
        del self.active_tests[test_id]
        del self.test_results[test_id]
        
        return archived_test


METADATA_FILENAME = "config_metadata.json"


@dataclass
class AdvancedTrainingConfigRecord:
    """Lightweight wrapper carrying configuration and metadata for API responses."""
    config_id: str
    config: AdvancedTrainingConfig
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        record = self.config.to_dict()
        record["config_id"] = self.config_id
        record["metadata"] = dict(self.metadata)
        return record


class AdvancedTrainingConfigManager:
    """Main manager for advanced training configuration system."""
    
    def __init__(self, config_dir: str = "config/training"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.ai_assistant = AITrainingAssistant()
        self.ab_test_manager = ABTestManager()
        self.active_sweeps: Dict[str, HyperparameterOptimizer] = {}
        self.training_metrics: Dict[str, TrainingMetrics] = {}
        self.metadata_index: Dict[str, Dict[str, Any]] = self._load_metadata_index()

    def _metadata_path(self) -> Path:
        return self.config_dir / METADATA_FILENAME

    def _load_metadata_index(self) -> Dict[str, Dict[str, Any]]:
        path = self._metadata_path()
        if not path.exists():
            return {}
        try:
            with open(path, "r") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                return raw
            logger.warning("Metadata index corrupted, resetting")
        except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover - resilience
            logger.warning(f"Failed to load metadata index: {exc}")
        return {}

    def _persist_metadata_index(self) -> None:
        path = self._metadata_path()
        with open(path, "w") as f:
            json.dump(self.metadata_index, f, indent=2)
    
    def create_advanced_config(self, base_config: Dict[str, Any]) -> AdvancedTrainingConfig:
        """Create an advanced training configuration."""
        config = AdvancedTrainingConfig(**base_config)
        config.updated_at = datetime.now()
        return config
    
    def save_config(
        self, config: AdvancedTrainingConfig, config_id: Optional[str] = None
    ) -> str:
        """Save training configuration to disk."""
        if not config_id:
            config_id = f"config_{config.model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config_path = self.config_dir / f"{config_id}.json"
        
        config_dict = asdict(config)
        # Convert datetime objects to strings
        config_dict['created_at'] = config.created_at.isoformat()
        config_dict['updated_at'] = config.updated_at.isoformat()
        
        # Convert enum values to strings for JSON serialization
        if 'optimization' in config_dict:
            opt = config_dict['optimization']
            if 'algorithm' in opt and hasattr(opt['algorithm'], 'value'):
                opt['algorithm'] = opt['algorithm'].value
            if 'scheduler_type' in opt and hasattr(opt['scheduler_type'], 'value'):
                opt['scheduler_type'] = opt['scheduler_type'].value
        
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Saved training config: {config_id}")
        return config_id
    
    def load_config(self, config_id: str) -> AdvancedTrainingConfig:
        """Load training configuration from disk."""
        config_path = self.config_dir / f"{config_id}.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config {config_id} not found")
        
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # Convert datetime strings back to datetime objects
        config_dict['created_at'] = datetime.fromisoformat(config_dict['created_at'])
        config_dict['updated_at'] = datetime.fromisoformat(config_dict['updated_at'])
        
        # Reconstruct nested dataclass objects
        if 'training_logic' in config_dict and isinstance(config_dict['training_logic'], dict):
            config_dict['training_logic'] = TrainingLogicConfig(**config_dict['training_logic'])
        
        if 'optimization' in config_dict and isinstance(config_dict['optimization'], dict):
            opt = config_dict['optimization']
            if 'algorithm' in opt and isinstance(opt['algorithm'], str):
                opt['algorithm'] = OptimizationAlgorithm(opt['algorithm'])
            if 'scheduler_type' in opt and isinstance(opt['scheduler_type'], str):
                opt['scheduler_type'] = SchedulerType(opt['scheduler_type'])
            config_dict['optimization'] = OptimizationConfig(**opt)
        
        if 'monitoring' in config_dict and isinstance(config_dict['monitoring'], dict):
            config_dict['monitoring'] = MonitoringConfig(**config_dict['monitoring'])
        
        if 'hyperparameter_sweep' in config_dict and config_dict['hyperparameter_sweep']:
            sweep_dict = config_dict['hyperparameter_sweep']
            if 'parameters' in sweep_dict:
                # Reconstruct HyperparameterRange objects
                for param_name, param_data in sweep_dict['parameters'].items():
                    if isinstance(param_data, dict):
                        sweep_dict['parameters'][param_name] = HyperparameterRange(**param_data)
            config_dict['hyperparameter_sweep'] = HyperparameterSweepConfig(**sweep_dict)
        
        if 'ab_test' in config_dict and config_dict['ab_test']:
            config_dict['ab_test'] = ABTestConfig(**config_dict['ab_test'])
        
        return AdvancedTrainingConfig(**config_dict)
    
    async def list_configs(self, user_id: str, tenant_id: str) -> List[AdvancedTrainingConfigRecord]:
        """List saved configurations, filtering by tenant/user metadata when available."""
        records: List[AdvancedTrainingConfigRecord] = []
        for config_file in sorted(self.config_dir.glob("config_*.json")):
            if config_file.name == METADATA_FILENAME:
                continue
            config_id = config_file.stem
            metadata = self.metadata_index.get(config_id, {})
            if metadata:
                tenant_match = metadata.get("tenant_id") == tenant_id
                user_match = metadata.get("created_by") == user_id
                if metadata.get("tenant_id") and not tenant_match:
                    continue
                if metadata.get("created_by") and not user_match:
                    continue
            config = self.load_config(config_id)
            records.append(AdvancedTrainingConfigRecord(config_id, config, metadata))
        return records

    async def create_config(
        self, config_data: Dict[str, Any], created_by: str, tenant_id: str
    ) -> str:
        """Create and persist an advanced training configuration."""
        config = self.create_advanced_config(config_data)
        config_id = self.save_config(config)
        metadata = {
            "config_id": config_id,
            "created_by": created_by,
            "tenant_id": tenant_id,
            "model_id": config.model_id,
            "dataset_id": config.dataset_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": config.updated_at.isoformat(),
        }
        self.metadata_index[config_id] = metadata
        self._persist_metadata_index()
        return config_id

    async def update_config(
        self, config_id: str, config_data: Dict[str, Any], updated_by: str
    ) -> bool:
        """Update an existing advanced training configuration."""
        config_path = self.config_dir / f"{config_id}.json"
        if not config_path.exists():
            return False

        existing = self.load_config(config_id)
        now = datetime.now()
        merged = asdict(existing)
        merged.update(config_data)
        merged["created_at"] = existing.created_at
        merged["updated_at"] = now

        updated_config = AdvancedTrainingConfig(**merged)
        updated_config.created_at = existing.created_at
        updated_config.updated_at = now

        self.save_config(updated_config, config_id=config_id)

        metadata = self.metadata_index.get(config_id, {})
        metadata.setdefault("created_by", updated_by)
        metadata.setdefault("created_at", existing.created_at.isoformat())
        metadata.update(
            {
                "updated_by": updated_by,
                "updated_at": now.isoformat(),
                "model_id": updated_config.model_id,
                "dataset_id": updated_config.dataset_id,
            }
        )
        self.metadata_index[config_id] = metadata
        self._persist_metadata_index()
        return True

    async def delete_config(self, config_id: str, deleted_by: str) -> bool:
        """Delete a saved advanced training configuration."""
        config_path = self.config_dir / f"{config_id}.json"
        if not config_path.exists():
            return False

        config_path.unlink()
        existed = self.metadata_index.pop(config_id, None) is not None
        if existed:
            self._persist_metadata_index()
        return True
    
    def get_ai_suggestions(self, model_type: str, dataset_size: int, 
                          hardware_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-assisted training suggestions."""
        return self.ai_assistant.suggest_training_strategy(model_type, dataset_size, hardware_specs)
    
    async def start_hyperparameter_sweep(self, config: AdvancedTrainingConfig) -> str:
        """Start a hyperparameter sweep."""
        if not config.hyperparameter_sweep:
            raise ValueError("No hyperparameter sweep configuration provided")
        
        sweep_id = f"sweep_{config.model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create optimizer based on search strategy
        if config.hyperparameter_sweep.search_strategy == "grid":
            optimizer = GridSearchOptimizer(config.hyperparameter_sweep)
        elif config.hyperparameter_sweep.search_strategy == "random":
            optimizer = RandomSearchOptimizer(config.hyperparameter_sweep)
        else:
            raise ValueError(f"Unsupported search strategy: {config.hyperparameter_sweep.search_strategy}")
        
        self.active_sweeps[sweep_id] = optimizer
        logger.info(f"Started hyperparameter sweep: {sweep_id}")
        return sweep_id
    
    def get_sweep_suggestion(self, sweep_id: str, trial_number: int) -> Dict[str, Any]:
        """Get parameter suggestion for next trial in sweep."""
        if sweep_id not in self.active_sweeps:
            raise ValueError(f"Sweep {sweep_id} not found")
        
        optimizer = self.active_sweeps[sweep_id]
        return optimizer.suggest_parameters(trial_number)
    
    def report_sweep_result(self, sweep_id: str, trial_number: int, 
                           parameters: Dict[str, Any], objective_value: float, 
                           metrics: Dict[str, Any]):
        """Report result for a sweep trial."""
        if sweep_id not in self.active_sweeps:
            raise ValueError(f"Sweep {sweep_id} not found")
        
        optimizer = self.active_sweeps[sweep_id]
        optimizer.report_result(trial_number, parameters, objective_value, metrics)
    
    def get_sweep_best_params(self, sweep_id: str) -> Tuple[Dict[str, Any], float]:
        """Get best parameters from sweep."""
        if sweep_id not in self.active_sweeps:
            raise ValueError(f"Sweep {sweep_id} not found")
        
        optimizer = self.active_sweeps[sweep_id]
        return optimizer.get_best_parameters()
    
    def create_ab_test(self, config: ABTestConfig) -> str:
        """Create an A/B test for training strategies."""
        return self.ab_test_manager.create_ab_test(config)
    
    def get_ab_test_assignment(self, test_id: str, user_id: str) -> Tuple[str, Dict[str, Any]]:
        """Get A/B test treatment assignment."""
        return self.ab_test_manager.assign_treatment(test_id, user_id)
    
    def record_ab_test_result(
        self,
        test_id: str,
        user_id: str,
        treatment: str,
        metric_value: float,
        additional_metrics: Optional[Dict[str, Any]] = None,
    ):
        """Record A/B test result."""
        self.ab_test_manager.record_result(test_id, user_id, treatment, metric_value, additional_metrics)
    
    def analyze_ab_test(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results."""
        return self.ab_test_manager.analyze_test_results(test_id)
    
    def initialize_training_metrics(self, training_id: str) -> TrainingMetrics:
        """Initialize metrics tracking for a training session."""
        metrics = TrainingMetrics()
        self.training_metrics[training_id] = metrics
        return metrics
    
    def update_training_metrics(self, training_id: str, epoch: int, metrics: Dict[str, Any]):
        """Update training metrics for an epoch."""
        if training_id not in self.training_metrics:
            self.training_metrics[training_id] = TrainingMetrics()
        
        self.training_metrics[training_id].add_epoch_metrics(epoch, metrics)
    
    def get_training_analysis(self, training_id: str) -> Dict[str, Any]:
        """Get AI analysis of training progress."""
        if training_id not in self.training_metrics:
            raise ValueError(f"Training {training_id} not found")
        
        metrics = self.training_metrics[training_id]
        return self.ai_assistant.analyze_training_progress(metrics)
    
    def get_loss_curve_data(self, training_id: str) -> Dict[str, List[float]]:
        """Get loss curve data for visualization."""
        if training_id not in self.training_metrics:
            raise ValueError(f"Training {training_id} not found")
        
        return self.training_metrics[training_id].get_loss_curve_data()
    
    def get_gradient_analysis(self, training_id: str) -> Dict[str, Any]:
        """Get gradient analysis for training session."""
        if training_id not in self.training_metrics:
            raise ValueError(f"Training {training_id} not found")
        
        return self.training_metrics[training_id].get_gradient_analysis()
    
    def cleanup_completed_sweeps(self, max_age_hours: int = 24):
        """Clean up completed hyperparameter sweeps."""
        # This would typically check for completed sweeps and archive them
        # For now, just log the cleanup attempt
        logger.info(f"Cleaning up sweeps older than {max_age_hours} hours")
    
    def export_training_report(self, training_id: str) -> Dict[str, Any]:
        """Export comprehensive training report."""
        if training_id not in self.training_metrics:
            raise ValueError(f"Training {training_id} not found")
        
        metrics = self.training_metrics[training_id]
        analysis = self.ai_assistant.analyze_training_progress(metrics)
        
        report = {
            'training_id': training_id,
            'generated_at': datetime.now().isoformat(),
            'metrics': {
                'loss_curve': metrics.get_loss_curve_data(),
                'gradient_analysis': metrics.get_gradient_analysis(),
                'final_metrics': {
                    'final_loss': metrics.loss_history[-1] if metrics.loss_history else None,
                    'final_val_loss': metrics.validation_loss_history[-1] if metrics.validation_loss_history else None,
                    'best_val_loss': min(metrics.validation_loss_history) if metrics.validation_loss_history else None,
                    'total_epochs': len(metrics.loss_history),
                    'total_training_time': sum(metrics.epoch_times) if metrics.epoch_times else 0
                }
            },
            'analysis': analysis,
            'recommendations': analysis.get('recommendations', [])
        }
        
        return report
