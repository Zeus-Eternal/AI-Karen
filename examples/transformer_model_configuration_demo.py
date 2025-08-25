#!/usr/bin/env python3
"""
Transformer Model Configuration System Demo

This demo showcases the enhanced transformer model configuration system including:
- Precision settings with hardware validation
- Dynamic batch size recommendations based on available memory
- Multi-GPU device allocation and load balancing
- Optimization flags interface for attention and mixed precision

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
"""

import json
import logging
from dataclasses import asdict
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_transformer_configuration():
    """Demonstrate transformer model configuration capabilities."""
    print("=" * 80)
    print("TRANSFORMER MODEL CONFIGURATION SYSTEM DEMO")
    print("=" * 80)
    
    try:
        from ai_karen_engine.services.system_model_manager import (
            get_system_model_manager,
            TransformerConfig
        )
        
        # Get system model manager
        manager = get_system_model_manager()
        model_id = "distilbert-base-uncased"
        
        print(f"\n1. CURRENT SYSTEM MODELS")
        print("-" * 40)
        
        models = manager.get_system_models()
        for model in models:
            if model["id"] == model_id:
                print(f"Model: {model['name']}")
                print(f"Family: {model['family']}")
                print(f"Format: {model['format']}")
                print(f"Status: {model['status']}")
                print(f"Parameters: {model['parameters']}")
                break
        
        print(f"\n2. HARDWARE RECOMMENDATIONS")
        print("-" * 40)
        
        recommendations = manager.get_hardware_recommendations(model_id)
        if "system_info" in recommendations:
            sys_info = recommendations["system_info"]
            print(f"System RAM: {sys_info['memory_gb']:.1f}GB")
            print(f"CPU Cores: {sys_info['cpu_count']}")
            print(f"GPU Available: {sys_info['gpu_available']}")
            if sys_info['gpu_available']:
                print(f"GPU Memory: {sys_info['gpu_memory_gb']:.1f}GB")
                print(f"GPU Count: {sys_info['gpu_count']}")
                print(f"BF16 Supported: {sys_info['bf16_supported']}")
            
            print(f"\nRecommended Settings:")
            if "recommended_device" in recommendations:
                print(f"  Device: {recommendations['recommended_device']}")
            if "recommended_precision" in recommendations:
                print(f"  Precision: {recommendations['recommended_precision']}")
            if "recommended_batch_size" in recommendations:
                print(f"  Batch Size: {recommendations['recommended_batch_size']}")
            
            if "dynamic_batch_sizes" in recommendations:
                print(f"\nDynamic Batch Sizes:")
                for scenario, batch_size in recommendations["dynamic_batch_sizes"].items():
                    print(f"  {scenario}: {batch_size}")
        
        print(f"\n3. CURRENT CONFIGURATION")
        print("-" * 40)
        
        current_config = manager.get_model_configuration(model_id)
        if current_config:
            print("Current transformer configuration:")
            for key, value in current_config.items():
                print(f"  {key}: {value}")
        
        print(f"\n4. PRECISION SETTINGS DEMO")
        print("-" * 40)
        
        # Demo different precision configurations
        precision_configs = [
            {"precision": "fp32", "description": "Full precision (highest quality, most memory)"},
            {"precision": "fp16", "description": "Half precision (balanced quality/memory)"},
            {"precision": "bf16", "description": "Brain float (good for training)"},
            {"precision": "int8", "description": "8-bit quantization (lower memory)"},
            {"precision": "int4", "description": "4-bit quantization (lowest memory)"}
        ]
        
        for config in precision_configs:
            test_config = TransformerConfig(
                precision=config["precision"],
                device="auto",
                batch_size=4
            )
            
            # Set quantization flags based on precision
            if config["precision"] == "int8":
                test_config.load_in_8bit = True
            elif config["precision"] == "int4":
                test_config.load_in_4bit = True
            
            validation = manager._validate_transformer_config(test_config)
            status = "✓ Valid" if validation["valid"] else "✗ Invalid"
            
            print(f"{config['precision'].upper():>6}: {status} - {config['description']}")
            if not validation["valid"]:
                print(f"        Error: {validation['error']}")
            elif validation.get("warnings"):
                print(f"        Warnings: {len(validation['warnings'])} warning(s)")
        
        print(f"\n5. MULTI-GPU CONFIGURATION")
        print("-" * 40)
        
        multi_gpu_config = manager.get_multi_gpu_configuration(model_id)
        if "error" in multi_gpu_config:
            print(f"Multi-GPU not available: {multi_gpu_config['error']}")
        else:
            print(f"GPU Count: {multi_gpu_config['gpu_count']}")
            print(f"Total GPU Memory: {multi_gpu_config['total_memory_gb']:.1f}GB")
            print(f"Recommended Strategy: {multi_gpu_config['recommended_strategy']}")
            
            print(f"\nGPU Details:")
            for gpu in multi_gpu_config['gpu_info']:
                print(f"  GPU {gpu['device_id']}: {gpu['name']} ({gpu['memory_gb']:.1f}GB)")
        
        print(f"\n6. ADVANCED CONFIGURATION DEMO")
        print("-" * 40)
        
        # Create an advanced configuration
        advanced_config = TransformerConfig(
            # Precision settings
            precision="fp16",
            torch_dtype="auto",
            load_in_8bit=False,
            load_in_4bit=False,
            
            # Device settings
            device="auto",
            device_map="auto",
            low_cpu_mem_usage=True,
            
            # Batch and sequence settings
            batch_size=8,
            max_length=1024,
            dynamic_batch_size=True,
            
            # Performance optimizations
            use_cache=True,
            attention_implementation="flash_attention_2",
            use_flash_attention=True,
            gradient_checkpointing=False,
            mixed_precision=True,
            compile_model=False,
            
            # Multi-GPU settings
            multi_gpu_strategy="auto",
            gpu_memory_fraction=0.9,
            enable_cpu_offload=False,
            
            # Advanced optimizations
            use_bettertransformer=False,
            optimize_for_inference=True,
            enable_xformers=False
        )
        
        print("Advanced Configuration Example:")
        config_dict = asdict(advanced_config)
        for key, value in config_dict.items():
            if value is not None:
                print(f"  {key}: {value}")
        
        # Validate the advanced configuration
        validation = manager._validate_transformer_config(advanced_config)
        print(f"\nValidation Result: {'✓ Valid' if validation['valid'] else '✗ Invalid'}")
        if not validation["valid"]:
            print(f"Error: {validation['error']}")
        if validation.get("warnings"):
            print(f"Warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
        
        print(f"\n7. CONFIGURATION UPDATE DEMO")
        print("-" * 40)
        
        # Demo updating configuration
        new_config = {
            "precision": "fp16",
            "batch_size": 16,
            "device": "auto",
            "use_flash_attention": True,
            "mixed_precision": True,
            "attention_implementation": "flash_attention_2"
        }
        
        print("Updating configuration with:")
        for key, value in new_config.items():
            print(f"  {key}: {value}")
        
        # Note: In a real scenario, this would save to disk
        print("\n✓ Configuration update would be saved to disk")
        print("✓ Hardware validation would be performed")
        print("✓ Model would be reloaded with new settings")
        
        print(f"\n8. PERFORMANCE METRICS")
        print("-" * 40)
        
        metrics = manager.get_performance_metrics(model_id)
        print("Current Performance Metrics:")
        for key, value in metrics.items():
            if key != "model_id":
                if isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        
        print(f"\n" + "=" * 80)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        print(f"\nKey Features Demonstrated:")
        print("✓ Hardware-aware precision settings (fp16, bf16, int8, int4)")
        print("✓ Dynamic batch size recommendations based on available memory")
        print("✓ Multi-GPU device allocation and load balancing")
        print("✓ Optimization flags for attention and mixed precision")
        print("✓ Comprehensive hardware validation")
        print("✓ Real-time configuration validation with warnings")
        print("✓ Performance monitoring and metrics collection")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required dependencies are installed.")
    except Exception as e:
        print(f"❌ Demo Error: {e}")
        logger.exception("Demo failed")

def demo_batch_size_optimization():
    """Demonstrate dynamic batch size optimization."""
    print(f"\n" + "=" * 60)
    print("DYNAMIC BATCH SIZE OPTIMIZATION DEMO")
    print("=" * 60)
    
    try:
        from ai_karen_engine.services.system_model_manager import SystemModelManager
        
        manager = SystemModelManager()
        
        # Test different memory scenarios
        scenarios = [
            {"memory_gb": 4, "gpu_available": False, "gpu_memory_gb": 0, "desc": "Low-end CPU"},
            {"memory_gb": 8, "gpu_available": False, "gpu_memory_gb": 0, "desc": "Mid-range CPU"},
            {"memory_gb": 16, "gpu_available": False, "gpu_memory_gb": 0, "desc": "High-end CPU"},
            {"memory_gb": 8, "gpu_available": True, "gpu_memory_gb": 4, "desc": "Entry GPU"},
            {"memory_gb": 16, "gpu_available": True, "gpu_memory_gb": 8, "desc": "Mid-range GPU"},
            {"memory_gb": 32, "gpu_available": True, "gpu_memory_gb": 16, "desc": "High-end GPU"},
            {"memory_gb": 64, "gpu_available": True, "gpu_memory_gb": 24, "desc": "Workstation GPU"}
        ]
        
        print(f"{'Scenario':<20} {'Optimal':<8} {'Training':<8} {'Inference':<9} {'Fine-tune':<10} {'Performance':<11}")
        print("-" * 75)
        
        for scenario in scenarios:
            optimal = manager._calculate_optimal_batch_size(
                scenario["memory_gb"], 
                scenario["gpu_available"], 
                scenario["gpu_memory_gb"]
            )
            
            dynamic = manager._get_dynamic_batch_sizes(
                scenario["memory_gb"], 
                scenario["gpu_available"], 
                scenario["gpu_memory_gb"]
            )
            
            print(f"{scenario['desc']:<20} {optimal:<8} {dynamic['training']:<8} {dynamic['inference']:<9} {dynamic['fine_tuning']:<10} {dynamic['performance_optimized']:<11}")
        
        print(f"\nBatch Size Optimization Rules:")
        print("• Training uses ~50% of optimal (more memory for gradients)")
        print("• Fine-tuning uses ~25% of optimal (most memory intensive)")
        print("• Inference uses full optimal batch size")
        print("• Performance mode uses 2x optimal (when possible)")
        print("• Memory constrained always uses batch size 1")
        
    except Exception as e:
        print(f"❌ Batch Size Demo Error: {e}")

if __name__ == "__main__":
    demo_transformer_configuration()
    demo_batch_size_optimization()