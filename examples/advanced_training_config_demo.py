"""
Advanced Training Configuration System Demo

Demonstrates sophisticated hyperparameter optimization, training logic editing,
AI-assisted training strategy suggestions, A/B testing capabilities, and comprehensive
training monitoring with gradient analysis and loss curves.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
"""

import asyncio
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import tempfile
import shutil
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    SchedulerType
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def simulate_training_epoch(epoch: int, config: dict, base_performance: float = 0.7) -> dict:
    """Simulate training metrics for one epoch."""
    # Simulate learning curve with some noise
    progress = (epoch + 1) / 50  # Assuming 50 epochs max
    
    # Base loss decreases with training
    loss = 1.0 * (1 - progress * 0.8) + np.random.normal(0, 0.05)
    val_loss = loss * 1.1 + np.random.normal(0, 0.03)  # Validation slightly higher
    
    # Accuracy increases with training
    accuracy = base_performance + progress * 0.25 + np.random.normal(0, 0.02)
    val_accuracy = accuracy - 0.02 + np.random.normal(0, 0.02)
    
    # Learning rate might decay
    lr = config.get('learning_rate', 1e-4) * (0.95 ** epoch)
    
    # Gradient norm with occasional spikes
    gradient_norm = 0.5 + np.random.normal(0, 0.1)
    if np.random.random() < 0.05:  # 5% chance of gradient spike
        gradient_norm *= 5
    
    return {
        'loss': max(0.01, loss),
        'val_loss': max(0.01, val_loss),
        'accuracy': min(0.99, max(0.1, accuracy)),
        'val_accuracy': min(0.99, max(0.1, val_accuracy)),
        'learning_rate': lr,
        'gradient_norm': gradient_norm,
        'epoch_time': 120 + np.random.normal(0, 20),
        'memory_usage': 0.7 + np.random.normal(0, 0.1)
    }


async def demo_basic_configuration():
    """Demonstrate basic advanced training configuration."""
    print_section("Basic Advanced Training Configuration")
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    try:
        manager = AdvancedTrainingConfigManager(config_dir=temp_dir)
        
        # Create advanced training configuration
        config = AdvancedTrainingConfig(
            model_id="demo_transformer",
            dataset_id="demo_dataset",
            training_logic=TrainingLogicConfig(
                gradient_accumulation_steps=4,
                gradient_clipping=1.0,
                mixed_precision=True,
                early_stopping_patience=10
            ),
            optimization=OptimizationConfig(
                algorithm=OptimizationAlgorithm.ADAMW,
                learning_rate=2e-4,
                weight_decay=0.01,
                scheduler_type=SchedulerType.COSINE,
                scheduler_params={"T_max": 100, "eta_min": 1e-6}
            ),
            monitoring=MonitoringConfig(
                track_gradients=True,
                track_weights=True,
                gradient_histogram_frequency=10,
                tensorboard_logging=True
            ),
            max_epochs=100,
            batch_size=32,
            validation_split=0.2
        )
        
        # Save configuration
        config_id = manager.save_config(config)
        print(f"✓ Created and saved configuration: {config_id}")
        
        # Load and verify
        loaded_config = manager.load_config(config_id)
        print(f"✓ Successfully loaded configuration")
        print(f"  Model ID: {loaded_config.model_id}")
        print(f"  Optimizer: {loaded_config.optimization.algorithm.value}")
        print(f"  Learning Rate: {loaded_config.optimization.learning_rate}")
        print(f"  Mixed Precision: {loaded_config.training_logic.mixed_precision}")
        
    finally:
        shutil.rmtree(temp_dir)


async def demo_ai_assistance():
    """Demonstrate AI-assisted training strategy suggestions."""
    print_section("AI-Assisted Training Strategy Suggestions")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = AdvancedTrainingConfigManager(config_dir=temp_dir)
        
        # Get AI suggestions for different scenarios
        scenarios = [
            {
                "name": "Large Transformer on High-End GPU",
                "model_type": "transformer",
                "dataset_size": 100000,
                "hardware_specs": {"gpu_memory_gb": 24, "has_gpu": True, "cpu_cores": 16}
            },
            {
                "name": "CNN on Mid-Range GPU",
                "model_type": "cnn",
                "dataset_size": 10000,
                "hardware_specs": {"gpu_memory_gb": 8, "has_gpu": True, "cpu_cores": 8}
            },
            {
                "name": "RNN on CPU Only",
                "model_type": "rnn",
                "dataset_size": 5000,
                "hardware_specs": {"gpu_memory_gb": 0, "has_gpu": False, "cpu_cores": 4}
            }
        ]
        
        for scenario in scenarios:
            print(f"\n--- {scenario['name']} ---")
            suggestions = manager.get_ai_suggestions(
                scenario["model_type"],
                scenario["dataset_size"],
                scenario["hardware_specs"]
            )
            
            print(f"Recommended Learning Rate: {suggestions['optimization_config'].get('learning_rate', 'N/A')}")
            print(f"Recommended Batch Size: {suggestions['optimization_config'].get('batch_size', 'N/A')}")
            print(f"Mixed Precision: {suggestions['training_logic'].get('mixed_precision', False)}")
            print(f"Potential Issues: {', '.join(suggestions['potential_issues'])}")
            
            if suggestions['mitigation_strategies']:
                print("Mitigation Strategies:")
                for strategy in suggestions['mitigation_strategies'][:2]:  # Show first 2
                    print(f"  - {strategy['issue']}: {', '.join(strategy['solutions'])}")
    
    finally:
        shutil.rmtree(temp_dir)


async def demo_hyperparameter_optimization():
    """Demonstrate hyperparameter optimization with grid and random search."""
    print_section("Hyperparameter Optimization")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = AdvancedTrainingConfigManager(config_dir=temp_dir)
        
        # Create configuration with hyperparameter sweep
        config = AdvancedTrainingConfig(
            model_id="hyperopt_demo",
            dataset_id="demo_dataset",
            hyperparameter_sweep=HyperparameterSweepConfig(
                parameters={
                    "learning_rate": HyperparameterRange(
                        min_value=1e-5,
                        max_value=1e-3,
                        log_scale=True
                    ),
                    "batch_size": HyperparameterRange(
                        discrete_values=[16, 32, 64, 128]
                    ),
                    "weight_decay": HyperparameterRange(
                        min_value=0.0,
                        max_value=0.1,
                        step=0.01
                    )
                },
                search_strategy="random",
                max_trials=10,
                objective_metric="validation_loss",
                objective_direction="minimize"
            )
        )
        
        # Start hyperparameter sweep
        sweep_id = manager.start_hyperparameter_sweep(config)
        print(f"✓ Started hyperparameter sweep: {sweep_id}")
        
        # Simulate trials
        print("\nRunning hyperparameter optimization trials...")
        best_score = float('inf')
        best_params = None
        
        for trial in range(8):  # Run 8 out of 10 trials
            try:
                # Get parameter suggestion
                params = manager.get_sweep_suggestion(sweep_id, trial)
                
                # Simulate training with these parameters
                # Better performance with certain parameter ranges
                lr_score = 1.0 if params['learning_rate'] > 5e-4 else 0.8
                batch_score = 1.0 if params['batch_size'] == 32 else 0.9
                wd_score = 1.0 if 0.01 <= params['weight_decay'] <= 0.05 else 0.85
                
                base_score = lr_score * batch_score * wd_score
                objective_value = 0.3 / base_score + np.random.normal(0, 0.05)
                objective_value = max(0.1, objective_value)  # Ensure positive
                
                metrics = {
                    "accuracy": 1.0 - objective_value,
                    "f1_score": 0.9 - objective_value * 0.8
                }
                
                # Report result
                manager.report_sweep_result(sweep_id, trial, params, objective_value, metrics)
                
                print(f"  Trial {trial + 1}: Loss = {objective_value:.4f}, "
                      f"LR = {params['learning_rate']:.2e}, "
                      f"BS = {params['batch_size']}, "
                      f"WD = {params['weight_decay']:.3f}")
                
                if objective_value < best_score:
                    best_score = objective_value
                    best_params = params
                    
            except StopIteration:
                print(f"  Completed all parameter combinations at trial {trial}")
                break
        
        # Get best parameters from sweep
        sweep_best_params, sweep_best_score = manager.get_sweep_best_params(sweep_id)
        
        print(f"\n✓ Hyperparameter optimization completed!")
        print(f"Best parameters found:")
        for param, value in sweep_best_params.items():
            if isinstance(value, float) and value < 1e-3:
                print(f"  {param}: {value:.2e}")
            else:
                print(f"  {param}: {value}")
        print(f"Best validation loss: {sweep_best_score:.4f}")
        
    finally:
        shutil.rmtree(temp_dir)


async def demo_ab_testing():
    """Demonstrate A/B testing for training strategies."""
    print_section("A/B Testing Training Strategies")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = AdvancedTrainingConfigManager(config_dir=temp_dir)
        
        # Create A/B test configuration
        ab_config = ABTestConfig(
            test_name="optimizer_comparison",
            control_config={
                "optimizer": "adam",
                "learning_rate": 1e-4,
                "weight_decay": 0.0
            },
            treatment_configs=[
                {
                    "optimizer": "adamw",
                    "learning_rate": 1e-4,
                    "weight_decay": 0.01
                },
                {
                    "optimizer": "sgd",
                    "learning_rate": 1e-3,
                    "momentum": 0.9
                }
            ],
            traffic_split=[0.4, 0.4, 0.2],  # 40% control, 40% AdamW, 20% SGD
            success_metric="final_accuracy",
            minimum_sample_size=30,
            statistical_significance_threshold=0.05
        )
        
        # Create A/B test
        test_id = manager.create_ab_test(ab_config)
        print(f"✓ Created A/B test: {test_id}")
        print(f"Testing: Adam (control) vs AdamW vs SGD")
        
        # Simulate users and training sessions
        print("\nSimulating training sessions...")
        treatment_counts = {"control": 0, "treatment_1": 0, "treatment_2": 0}
        
        np.random.seed(42)  # For reproducible demo
        
        for user_id in range(100):
            # Get treatment assignment
            treatment, config = manager.get_ab_test_assignment(test_id, f"user_{user_id}")
            treatment_counts[treatment] += 1
            
            # Simulate training performance based on treatment
            if treatment == "control":  # Adam
                base_performance = 0.82
            elif treatment == "treatment_1":  # AdamW - slightly better
                base_performance = 0.85
            else:  # SGD - more variable
                base_performance = 0.80
            
            # Add noise and ensure realistic range
            final_accuracy = base_performance + np.random.normal(0, 0.05)
            final_accuracy = max(0.6, min(0.95, final_accuracy))
            
            # Record result
            manager.record_ab_test_result(
                test_id, f"user_{user_id}", treatment, final_accuracy,
                {"training_time": np.random.uniform(300, 600)}
            )
        
        print(f"Treatment distribution: {treatment_counts}")
        
        # Analyze results
        analysis = manager.analyze_ab_test(test_id)
        
        print(f"\n✓ A/B Test Analysis:")
        print(f"Status: {analysis['status']}")
        
        if analysis['status'] == 'complete':
            print("\nTreatment Statistics:")
            for treatment, stats in analysis['treatment_stats'].items():
                print(f"  {treatment}: {stats['count']} users, "
                      f"mean accuracy = {stats['mean']:.4f} ± {stats['std']:.4f}")
            
            print("\nComparisons to Control:")
            for comparison in analysis['comparisons']:
                improvement = comparison['improvement_percent']
                significant = "✓" if comparison['significant'] else "✗"
                print(f"  {comparison['treatment']}: {improvement:+.2f}% improvement, "
                      f"p-value = {comparison['p_value']:.4f} {significant}")
            
            if analysis.get('winner'):
                print(f"\n🏆 Winner: {analysis['winner']} "
                      f"(confidence: {analysis['confidence']:.1%})")
            else:
                print("\n📊 No statistically significant winner found")
        
    finally:
        shutil.rmtree(temp_dir)


async def demo_training_monitoring():
    """Demonstrate comprehensive training monitoring with gradient analysis."""
    print_section("Training Monitoring & Gradient Analysis")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = AdvancedTrainingConfigManager(config_dir=temp_dir)
        
        # Initialize training metrics
        training_id = "monitoring_demo"
        metrics = manager.initialize_training_metrics(training_id)
        print(f"✓ Initialized training metrics for: {training_id}")
        
        # Simulate training with different phases
        print("\nSimulating training epochs...")
        
        config = {"learning_rate": 1e-4, "optimizer": "adamw"}
        
        # Phase 1: Normal training (epochs 0-15)
        for epoch in range(16):
            epoch_metrics = simulate_training_epoch(epoch, config, base_performance=0.7)
            manager.update_training_metrics(training_id, epoch, epoch_metrics)
            
            if epoch % 5 == 0:
                print(f"  Epoch {epoch}: Loss = {epoch_metrics['loss']:.4f}, "
                      f"Val Loss = {epoch_metrics['val_loss']:.4f}, "
                      f"Accuracy = {epoch_metrics['accuracy']:.4f}")
        
        # Phase 2: Introduce gradient explosion (epochs 16-18)
        print("  [Simulating gradient explosion...]")
        for epoch in range(16, 19):
            epoch_metrics = simulate_training_epoch(epoch, config)
            epoch_metrics['gradient_norm'] = 15.0 + np.random.normal(0, 2)  # High gradient norm
            manager.update_training_metrics(training_id, epoch, epoch_metrics)
        
        # Phase 3: Recovery with gradient clipping (epochs 19-25)
        print("  [Applying gradient clipping...]")
        for epoch in range(19, 26):
            epoch_metrics = simulate_training_epoch(epoch, config)
            epoch_metrics['gradient_norm'] = min(1.0, epoch_metrics['gradient_norm'])  # Clipped
            manager.update_training_metrics(training_id, epoch, epoch_metrics)
        
        # Get training analysis
        analysis = manager.get_training_analysis(training_id)
        
        print(f"\n✓ Training Analysis:")
        print(f"Status: {analysis['status']}")
        print(f"Issues detected: {', '.join(analysis['issues_detected']) if analysis['issues_detected'] else 'None'}")
        
        if analysis['recommendations']:
            print("Recommendations:")
            for rec in analysis['recommendations']:
                print(f"  - {rec['issue']}: {rec['suggestion']}")
        
        # Get gradient analysis
        gradient_analysis = manager.get_gradient_analysis(training_id)
        
        print(f"\n✓ Gradient Analysis:")
        print(f"Mean gradient norm: {gradient_analysis['mean_gradient_norm']:.4f}")
        print(f"Gradient explosion detected: {gradient_analysis['gradient_explosion_detected']}")
        print(f"Gradient vanishing detected: {gradient_analysis['gradient_vanishing_detected']}")
        
        # Get loss curve data
        loss_data = manager.get_loss_curve_data(training_id)
        
        print(f"\n✓ Loss Curves:")
        print(f"Training epochs: {len(loss_data['train_loss'])}")
        print(f"Final training loss: {loss_data['train_loss'][-1]:.4f}")
        print(f"Final validation loss: {loss_data['val_loss'][-1]:.4f}")
        print(f"Best validation loss: {min(loss_data['val_loss']):.4f}")
        
        # Export comprehensive report
        report = manager.export_training_report(training_id)
        
        print(f"\n✓ Training Report Generated:")
        print(f"Total training time: {report['metrics']['final_metrics']['total_training_time']:.1f} seconds")
        print(f"Total epochs: {report['metrics']['final_metrics']['total_epochs']}")
        print(f"Best validation loss: {report['metrics']['final_metrics']['best_val_loss']:.4f}")
        
        # Create simple visualization if matplotlib is available
        try:
            plt.figure(figsize=(12, 4))
            
            # Loss curves
            plt.subplot(1, 3, 1)
            epochs = loss_data['epochs']
            plt.plot(epochs, loss_data['train_loss'], label='Training Loss', alpha=0.8)
            plt.plot(epochs, loss_data['val_loss'], label='Validation Loss', alpha=0.8)
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.title('Loss Curves')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Gradient norms
            plt.subplot(1, 3, 2)
            gradient_norms = gradient_analysis['gradient_norm_history']
            plt.plot(range(len(gradient_norms)), gradient_norms, alpha=0.8, color='red')
            plt.axhline(y=10.0, color='red', linestyle='--', alpha=0.5, label='Explosion threshold')
            plt.axhline(y=1e-6, color='blue', linestyle='--', alpha=0.5, label='Vanishing threshold')
            plt.xlabel('Epoch')
            plt.ylabel('Gradient Norm')
            plt.title('Gradient Analysis')
            plt.yscale('log')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Training metrics
            plt.subplot(1, 3, 3)
            training_metrics = manager.training_metrics[training_id]
            if training_metrics.accuracy_history:
                plt.plot(range(len(training_metrics.accuracy_history)), 
                        training_metrics.accuracy_history, label='Training Accuracy', alpha=0.8)
            if training_metrics.validation_accuracy_history:
                plt.plot(range(len(training_metrics.validation_accuracy_history)), 
                        training_metrics.validation_accuracy_history, label='Validation Accuracy', alpha=0.8)
            plt.xlabel('Epoch')
            plt.ylabel('Accuracy')
            plt.title('Accuracy Curves')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            plot_path = Path(temp_dir) / "training_analysis.png"
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            print(f"✓ Training visualization saved to: {plot_path}")
            
            # Show plot if in interactive environment
            try:
                plt.show()
            except:
                pass  # Non-interactive environment
                
        except ImportError:
            print("📊 Matplotlib not available - skipping visualization")
        
    finally:
        shutil.rmtree(temp_dir)


async def demo_complete_workflow():
    """Demonstrate a complete advanced training workflow."""
    print_section("Complete Advanced Training Workflow")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = AdvancedTrainingConfigManager(config_dir=temp_dir)
        
        print("🚀 Starting complete advanced training workflow...")
        
        # Step 1: Get AI suggestions
        print("\n1. Getting AI training suggestions...")
        suggestions = manager.get_ai_suggestions(
            model_type="transformer",
            dataset_size=50000,
            hardware_specs={"gpu_memory_gb": 12, "has_gpu": True, "cpu_cores": 8}
        )
        
        suggested_lr = suggestions['optimization_config'].get('learning_rate', 1e-4)
        suggested_bs = suggestions['optimization_config'].get('batch_size', 32)
        
        print(f"   AI suggested LR: {suggested_lr:.2e}, Batch Size: {suggested_bs}")
        
        # Step 2: Create advanced configuration
        print("\n2. Creating advanced training configuration...")
        config = AdvancedTrainingConfig(
            model_id="workflow_demo",
            dataset_id="large_dataset",
            training_logic=TrainingLogicConfig(
                gradient_accumulation_steps=2,
                gradient_clipping=1.0,
                mixed_precision=True,
                early_stopping_patience=15
            ),
            optimization=OptimizationConfig(
                algorithm=OptimizationAlgorithm.ADAMW,
                learning_rate=suggested_lr,
                weight_decay=0.01,
                scheduler_type=SchedulerType.COSINE
            ),
            monitoring=MonitoringConfig(
                track_gradients=True,
                track_weights=True,
                gradient_histogram_frequency=5
            ),
            batch_size=suggested_bs,
            max_epochs=50
        )
        
        config_id = manager.save_config(config)
        print(f"   ✓ Configuration saved: {config_id}")
        
        # Step 3: Run training with monitoring
        print("\n3. Running training with comprehensive monitoring...")
        training_id = "workflow_training"
        manager.initialize_training_metrics(training_id)
        
        # Simulate training
        for epoch in range(20):
            epoch_metrics = simulate_training_epoch(epoch, {"learning_rate": suggested_lr})
            manager.update_training_metrics(training_id, epoch, epoch_metrics)
            
            # Check for issues every 5 epochs
            if epoch > 0 and epoch % 5 == 0:
                analysis = manager.get_training_analysis(training_id)
                if analysis['issues_detected']:
                    print(f"   ⚠️  Epoch {epoch}: Issues detected - {', '.join(analysis['issues_detected'])}")
                    if analysis['early_stopping_suggestion']:
                        print(f"   🛑 Early stopping suggested at epoch {epoch}")
                        break
                else:
                    print(f"   ✓ Epoch {epoch}: Training healthy")
        
        # Step 4: Generate final report
        print("\n4. Generating comprehensive training report...")
        report = manager.export_training_report(training_id)
        
        final_metrics = report['metrics']['final_metrics']
        print(f"   Final training loss: {final_metrics['final_loss']:.4f}")
        print(f"   Best validation loss: {final_metrics['best_val_loss']:.4f}")
        print(f"   Total training time: {final_metrics['total_training_time']:.1f}s")
        print(f"   Training epochs completed: {final_metrics['total_epochs']}")
        
        # Step 5: AI analysis and recommendations
        analysis = report['analysis']
        print(f"\n5. AI Analysis Results:")
        print(f"   Training status: {analysis['status']}")
        
        if analysis['recommendations']:
            print("   Recommendations for future training:")
            for rec in analysis['recommendations'][:3]:  # Show top 3
                print(f"     - {rec['suggestion']}")
        
        print(f"\n🎉 Complete workflow finished successfully!")
        print(f"   Configuration ID: {config_id}")
        print(f"   Training ID: {training_id}")
        print(f"   Report generated at: {report['generated_at']}")
        
    finally:
        shutil.rmtree(temp_dir)


async def main():
    """Run all advanced training configuration demos."""
    print("🧠 Advanced Training Configuration System Demo")
    print("=" * 60)
    print("This demo showcases sophisticated hyperparameter optimization,")
    print("AI-assisted training strategies, A/B testing, and comprehensive")
    print("training monitoring with gradient analysis and loss curves.")
    print()
    
    demos = [
        ("Basic Configuration", demo_basic_configuration),
        ("AI Assistance", demo_ai_assistance),
        ("Hyperparameter Optimization", demo_hyperparameter_optimization),
        ("A/B Testing", demo_ab_testing),
        ("Training Monitoring", demo_training_monitoring),
        ("Complete Workflow", demo_complete_workflow)
    ]
    
    for name, demo_func in demos:
        try:
            await demo_func()
            print(f"\n✅ {name} demo completed successfully!")
        except Exception as e:
            print(f"\n❌ {name} demo failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-" * 60)
    
    print("\n🎯 All demos completed!")
    print("\nKey Features Demonstrated:")
    print("✓ Sophisticated hyperparameter optimization (grid & random search)")
    print("✓ AI-assisted training strategy suggestions")
    print("✓ A/B testing for training strategies")
    print("✓ Comprehensive training monitoring")
    print("✓ Gradient analysis and anomaly detection")
    print("✓ Loss curve visualization and analysis")
    print("✓ Complete training workflow integration")


if __name__ == "__main__":
    asyncio.run(main())