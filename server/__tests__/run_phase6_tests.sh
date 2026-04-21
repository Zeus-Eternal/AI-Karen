#!/bin/bash

# Quick Start Script for Phase 6 Integration Tests
# This script provides an easy way to run the comprehensive integration tests

set -e

echo "🚀 Starting Phase 6 Integration Tests..."
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is required but not installed"
    echo "Please install pytest: pip install pytest pytest-asyncio"
    exit 1
fi

# Set up Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../../src"

# Create test results directory
mkdir -p test_results

# Default test category
CATEGORY="all"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --category)
            CATEGORY="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --category CATEGORY    Run specific test category (copilotkit_alignment, runtime_integration, boundary_layer, end_to_end_workflow, all)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Run all tests"
            echo "  $0 --category copilotkit_alignment  # Run only CopilotKit alignment tests"
            echo "  $0 --category runtime_integration   # Run only runtime integration tests"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate category
VALID_CATEGORIES=("copilotkit_alignment" "runtime_integration" "boundary_layer" "end_to_end_workflow" "all")
if [[ ! " ${VALID_CATEGORIES[@]} " =~ " $CATEGORY " ]]; then
    echo "❌ Invalid category: $CATEGORY"
    echo "Valid categories: ${VALID_CATEGORIES[*]}"
    exit 1
fi

echo "📋 Test Category: $CATEGORY"
echo "📁 Test Results Directory: test_results/"
echo ""

# Run tests based on category
case $CATEGORY in
    "copilotkit_alignment")
        echo "🔍 Running CopilotKit Alignment Tests..."
        pytest test_copilotkit_integration_phase6.py -v --tb=short
        ;;
    "runtime_integration")
        echo "🔍 Running Runtime Integration Tests..."
        pytest test_runtime_integration_phase6.py -v --tb=short
        ;;
    "boundary_layer")
        echo "🔍 Running Boundary Layer Tests..."
        pytest test_boundary_layer_phase6.py -v --tb=short
        ;;
    "end_to_end_workflow")
        echo "🔍 Running End-to-End Workflow Tests..."
        pytest test_end_to_end_workflow_phase6.py -v --tb=short
        ;;
    "all")
        echo "🔍 Running All Phase 6 Integration Tests..."
        echo ""
        
        # Run each test category with summary
        echo "📊 Running CopilotKit Alignment Tests..."
        pytest test_copilotkit_integration_phase6.py -v --tb=short --cov=src/ai_karen_engine/copilotkit --cov-report=term-missing
        echo ""
        
        echo "📊 Running Runtime Integration Tests..."
        pytest test_runtime_integration_phase6.py -v --tb=short --cov=src/ai_karen_engine/agents/adapters --cov-report=term-missing
        echo ""
        
        echo "📊 Running Boundary Layer Tests..."
        pytest test_boundary_layer_phase6.py -v --tb=short --cov=src/ai_karen_engine/copilotkit/safety_middleware --cov-report=term-missing
        echo ""
        
        echo "📊 Running End-to-End Workflow Tests..."
        pytest test_end_to_end_workflow_phase6.py -v --tb=short --cov=src/ai_karen_engine/copilotkit --cov-report=term-missing
        echo ""
        
        # Generate comprehensive report
        echo "📈 Generating Comprehensive Test Report..."
        python run_phase6_tests.py --generate-report
        ;;
esac

echo ""
echo "✅ Tests completed successfully!"
echo "📁 Test results available in: test_results/"
echo "📖 For detailed documentation, see: PHASE6_TESTING_GUIDE.md"

# Show summary if all tests were run
if [[ "$CATEGORY" == "all" ]]; then
    echo ""
    echo "📊 Test Summary:"
    echo "================"
    
    # Count test files
    TOTAL_TESTS=$(find test_results -name "*.json" -type f | wc -l)
    echo "Total Test Files: $TOTAL_TESTS"
    
    # Check for test results
    if [[ -f test_results/phase6_test_report.json ]]; then
        echo "📋 Detailed report available: test_results/phase6_test_report.json"
    fi
    
    # Check for coverage reports
    if [[ -d htmlcov ]]; then
        echo "📊 Coverage report available: htmlcov/index.html"
    fi
fi

echo ""
echo "🎉 Phase 6 Integration Tests completed!"