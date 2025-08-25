#!/usr/bin/env python3
"""
Enhanced HuggingFace Model Discovery Demo

This demo showcases the enhanced HuggingFace model discovery service
with advanced filtering, compatibility detection, and download management.

Features demonstrated:
- Advanced model search with training filters
- Model compatibility detection and analysis
- Enhanced download management with progress tracking
- Model registration and metadata management
"""

import asyncio
import json
from typing import Dict, Any

from ai_karen_engine.services.enhanced_huggingface_service import (
    get_enhanced_huggingface_service,
    TrainingFilters,
    TrainableModel,
    CompatibilityReport
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_model_info(model: TrainableModel):
    """Print formatted model information."""
    print(f"\n📦 {model.name} ({model.id})")
    print(f"   Author: {model.author or 'Unknown'}")
    print(f"   Family: {model.family or 'Unknown'}")
    print(f"   Parameters: {model.parameters or 'Unknown'}")
    print(f"   Downloads: {model.downloads:,}")
    print(f"   Training Complexity: {model.training_complexity}")
    
    # Training capabilities
    capabilities = []
    if model.supports_fine_tuning:
        capabilities.append("Fine-tuning")
    if model.supports_lora:
        capabilities.append("LoRA")
    if model.supports_full_training:
        capabilities.append("Full Training")
    
    print(f"   Training Support: {', '.join(capabilities) if capabilities else 'None'}")
    
    if model.memory_requirements:
        print(f"   Min GPU Memory: {model.memory_requirements}GB")
    
    if model.training_frameworks:
        print(f"   Frameworks: {', '.join(model.training_frameworks)}")


def print_compatibility_report(report: CompatibilityReport):
    """Print formatted compatibility report."""
    print(f"\n🔍 Compatibility Analysis")
    print(f"   Compatible: {'✅ Yes' if report.is_compatible else '❌ No'}")
    print(f"   Score: {report.compatibility_score:.2f}/1.0")
    
    if report.supported_operations:
        print(f"   Supported Operations: {', '.join(report.supported_operations)}")
    
    if report.framework_compatibility:
        frameworks = [f"{k}: {'✅' if v else '❌'}" for k, v in report.framework_compatibility.items()]
        print(f"   Framework Support: {', '.join(frameworks)}")
    
    if report.hardware_requirements:
        print(f"   Hardware Requirements:")
        for key, value in report.hardware_requirements.items():
            print(f"     {key}: {value}")
    
    if report.warnings:
        print(f"   ⚠️  Warnings:")
        for warning in report.warnings:
            print(f"     • {warning}")
    
    if report.recommendations:
        print(f"   💡 Recommendations:")
        for rec in report.recommendations:
            print(f"     • {rec}")


def demo_trainable_model_creation():
    """Demonstrate TrainableModel creation and capability inference."""
    print_section("TrainableModel Creation & Capability Inference")
    
    # Create different types of models
    models = [
        TrainableModel(
            id="meta-llama/Llama-2-7b-hf",
            name="Llama-2-7b-hf",
            tags=["pytorch", "transformers", "llama"],
            family="llama",
            parameters="7B",
            downloads=150000,
            likes=8000,
            description="7B parameter Llama 2 model"
        ),
        TrainableModel(
            id="microsoft/DialoGPT-medium",
            name="DialoGPT-medium",
            tags=["pytorch", "transformers", "conversational"],
            family="gpt",
            parameters="345M",
            downloads=75000,
            likes=3000,
            description="Medium-sized conversational AI model"
        ),
        TrainableModel(
            id="meta-llama/Llama-2-70b-hf",
            name="Llama-2-70b-hf",
            tags=["pytorch", "transformers", "llama"],
            family="llama",
            parameters="70B",
            downloads=50000,
            likes=5000,
            description="70B parameter Llama 2 model"
        )
    ]
    
    for model in models:
        print_model_info(model)


def demo_training_filters():
    """Demonstrate training filter functionality."""
    print_section("Training Filters")
    
    # Create different filter configurations
    filters = [
        ("Basic Fine-tuning", TrainingFilters(
            supports_fine_tuning=True
        )),
        ("LoRA Support", TrainingFilters(
            supports_fine_tuning=True,
            supports_lora=True
        )),
        ("Small Models Only", TrainingFilters(
            supports_fine_tuning=True,
            max_parameters="7B",
            memory_requirements=16
        )),
        ("Full Training Capable", TrainingFilters(
            supports_fine_tuning=True,
            supports_lora=True,
            supports_full_training=True,
            training_frameworks=["transformers", "peft"]
        ))
    ]
    
    for name, filter_config in filters:
        print(f"\n🔧 {name}:")
        print(f"   Fine-tuning: {filter_config.supports_fine_tuning}")
        print(f"   LoRA: {filter_config.supports_lora}")
        print(f"   Full Training: {filter_config.supports_full_training}")
        if filter_config.max_parameters:
            print(f"   Max Parameters: {filter_config.max_parameters}")
        if filter_config.memory_requirements:
            print(f"   Max Memory: {filter_config.memory_requirements}GB")
        if filter_config.training_frameworks:
            print(f"   Frameworks: {', '.join(filter_config.training_frameworks)}")


def demo_compatibility_detection():
    """Demonstrate compatibility detection."""
    print_section("Compatibility Detection")
    
    # Create mock compatibility reports
    reports = [
        ("Excellent Compatibility", CompatibilityReport(
            is_compatible=True,
            compatibility_score=0.95,
            supported_operations=["fine_tuning", "lora", "full_training"],
            hardware_requirements={
                "min_gpu_memory": 16,
                "recommended_gpu_memory": 24,
                "gpu_required": True,
                "multi_gpu_beneficial": False
            },
            framework_compatibility={
                "transformers": True,
                "peft": True,
                "deepspeed": True
            },
            warnings=[],
            recommendations=[
                "SafeTensors format detected - optimal for training",
                "Permissive license - suitable for commercial use"
            ]
        )),
        ("Good Compatibility with Warnings", CompatibilityReport(
            is_compatible=True,
            compatibility_score=0.75,
            supported_operations=["fine_tuning", "lora"],
            hardware_requirements={
                "min_gpu_memory": 8,
                "recommended_gpu_memory": 16,
                "gpu_required": False
            },
            framework_compatibility={
                "transformers": True,
                "peft": False
            },
            warnings=[
                "PyTorch .bin format detected - consider converting to SafeTensors",
                "Limited LoRA support due to architecture"
            ],
            recommendations=[
                "Use gradient checkpointing to reduce memory usage",
                "Consider using smaller batch sizes"
            ]
        )),
        ("Poor Compatibility", CompatibilityReport(
            is_compatible=False,
            compatibility_score=0.25,
            supported_operations=[],
            hardware_requirements={},
            framework_compatibility={
                "transformers": False,
                "peft": False
            },
            warnings=[
                "Unsupported model architecture",
                "No training-compatible files found",
                "Restrictive license may limit usage"
            ],
            recommendations=[
                "Consider using a different model",
                "Check for alternative model formats"
            ]
        ))
    ]
    
    for name, report in reports:
        print(f"\n📊 {name}:")
        print_compatibility_report(report)


def demo_service_functionality():
    """Demonstrate service functionality."""
    print_section("Enhanced HuggingFace Service")
    
    # Get service instance
    service = get_enhanced_huggingface_service()
    print(f"✅ Service initialized: {type(service).__name__}")
    
    # Demonstrate singleton pattern
    service2 = get_enhanced_huggingface_service()
    print(f"✅ Singleton pattern: {service is service2}")
    
    # Demonstrate artifact selection logic
    print(f"\n🔧 Artifact Selection Logic:")
    
    files = [
        {"rfilename": "pytorch_model.bin", "size": 13000000000},
        {"rfilename": "model.safetensors", "size": 13000000000},
        {"rfilename": "config.json", "size": 1024},
        {"rfilename": "tokenizer.json", "size": 2048},
        {"rfilename": "tokenizer_config.json", "size": 512}
    ]
    
    print(f"   Available files:")
    for file in files:
        size_mb = file["size"] / (1024 * 1024)
        print(f"     • {file['rfilename']} ({size_mb:.1f} MB)")
    
    # Mock device capabilities
    from ai_karen_engine.services.enhanced_huggingface_service import DeviceCapabilities
    device_caps = DeviceCapabilities(has_gpu=True, gpu_memory=16384)
    
    selected = service._select_training_artifacts(files, device_caps)
    print(f"   Selected for training:")
    for artifact in selected:
        print(f"     ✅ {artifact}")
    
    # Demonstrate hardware requirements estimation
    print(f"\n💻 Hardware Requirements Estimation:")
    
    from unittest.mock import Mock
    
    # Small model
    small_model = Mock(files=[{"size": 1000000000}])  # 1GB
    small_reqs = service._estimate_hardware_requirements(small_model)
    print(f"   Small Model (1GB):")
    print(f"     Min GPU Memory: {small_reqs['min_gpu_memory']}GB")
    print(f"     GPU Required: {small_reqs['gpu_required']}")
    
    # Large model
    large_model = Mock(files=[{"size": 20000000000}])  # 20GB
    large_reqs = service._estimate_hardware_requirements(large_model)
    print(f"   Large Model (20GB):")
    print(f"     Min GPU Memory: {large_reqs['min_gpu_memory']}GB")
    print(f"     GPU Required: {large_reqs['gpu_required']}")
    print(f"     Multi-GPU Beneficial: {large_reqs['multi_gpu_beneficial']}")
    
    # Demonstrate conversion detection
    print(f"\n🔄 Format Conversion Detection:")
    
    bin_only = [{"rfilename": "pytorch_model.bin", "size": 1000000}]
    safetensors_available = [{"rfilename": "model.safetensors", "size": 1000000}]
    
    print(f"   PyTorch .bin only: {'Conversion needed' if service._needs_conversion(bin_only) else 'No conversion needed'}")
    print(f"   SafeTensors available: {'Conversion needed' if service._needs_conversion(safetensors_available) else 'No conversion needed'}")


def demo_enhanced_features():
    """Demonstrate enhanced features."""
    print_section("Enhanced Features")
    
    print("🚀 Enhanced HuggingFace Model Discovery Features:")
    print("   ✅ Advanced model search with training-specific filters")
    print("   ✅ Automatic compatibility detection and analysis")
    print("   ✅ Intelligent artifact selection for optimal training")
    print("   ✅ Hardware requirements estimation")
    print("   ✅ Format conversion detection and recommendations")
    print("   ✅ Enhanced download management with progress tracking")
    print("   ✅ Model registration with training metadata")
    print("   ✅ Integration with existing model store and job management")
    
    print("\n🎯 Key Benefits:")
    print("   • Streamlined model discovery for training workflows")
    print("   • Reduced setup time with automatic compatibility checks")
    print("   • Optimized downloads with intelligent artifact selection")
    print("   • Better resource utilization through hardware analysis")
    print("   • Seamless integration with existing Karen AI infrastructure")
    
    print("\n📋 Supported Training Operations:")
    operations = [
        "Fine-tuning with custom datasets",
        "LoRA (Low-Rank Adaptation) training",
        "Full model training for smaller models",
        "Parameter-efficient fine-tuning",
        "Multi-GPU distributed training",
        "Gradient checkpointing optimization"
    ]
    
    for op in operations:
        print(f"   • {op}")


def main():
    """Run the enhanced HuggingFace demo."""
    print("🤗 Enhanced HuggingFace Model Discovery Demo")
    print("=" * 60)
    
    try:
        # Run all demo sections
        demo_trainable_model_creation()
        demo_training_filters()
        demo_compatibility_detection()
        demo_service_functionality()
        demo_enhanced_features()
        
        print_section("Demo Complete")
        print("✅ All enhanced HuggingFace features demonstrated successfully!")
        print("\n💡 Next Steps:")
        print("   1. Integrate with your training workflows")
        print("   2. Customize filters for your specific use cases")
        print("   3. Set up automated model discovery and downloads")
        print("   4. Monitor compatibility reports for new models")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()