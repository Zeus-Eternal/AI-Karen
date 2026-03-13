#!/bin/bash
# AI-Karen Project Runner
# This script properly sets up the environment and runs the project

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "🚀 Starting AI-Karen Project..."
echo "📁 Project directory: $SCRIPT_DIR"

# Set environment file path
export ENV_FILE="$SCRIPT_DIR/.env"
echo "📄 Environment file: $ENV_FILE"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    echo "Please ensure the .env file exists in the project root directory."
    exit 1
fi

# Change to project directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d ".virEnv" ]; then
    echo "🐍 Virtual environment found: .virEnv"
    
    # Check if virtual environment has proper Python
    if [ -f ".virEnv/bin/python3" ]; then
        echo "✓ Using virtual environment Python"
        
        # Check if fastapi is available in virtual environment
        if .virEnv/bin/python3 -c "import fastapi" 2>/dev/null; then
            echo "✓ Dependencies available in virtual environment"
            
            # Run with virtual environment Python
            exec .virEnv/bin/python3 start.py "$@"
        else
            echo "⚠️  Dependencies not installed in virtual environment"
            echo "💡 Run ./setup_venv.sh to fix this issue"
            echo "🔄 Attempting to run with system Python..."
            
            # Fallback to system Python
            if python3 -c "import fastapi" 2>/dev/null; then
                echo "✓ Using system Python with dependencies"
                exec python3 start.py "$@"
            else
                echo "❌ Error: Required packages not found in system Python"
                echo "Please run: ./setup_venv.sh"
                exit 1
            fi
        fi
    else
        echo "⚠️  Virtual environment Python not found, using system Python"
        exec python3 start.py "$@"
    fi
else
    echo "⚠️  Virtual environment not found, using system Python"
    
    # Check if system Python has required packages
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo "❌ Error: Required packages not found in system Python"
        echo "Please run: ./setup_venv.sh"
        exit 1
    fi
    
    exec python3 start.py "$@"
fi