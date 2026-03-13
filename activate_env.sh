#!/bin/bash
# Activation script for AI-Karen virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if the virtual environment exists
if [ ! -d "$SCRIPT_DIR/.env_karen" ]; then
    echo "Error: Virtual environment .env_karen not found in $SCRIPT_DIR"
    exit 1
fi

# Activate the virtual environment
echo "Activating AI-Karen virtual environment..."
source "$SCRIPT_DIR/.env_karen/bin/activate"

# Set PYTHONPATH to include src directory for imports
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Verify activation
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✓ Virtual environment activated: $VIRTUAL_ENV"
    
    # Check if Python is correctly pointing to the virtual environment
    PYTHON_PATH=$(which python3)
    if [[ "$PYTHON_PATH" == "$VIRTUAL_ENV/bin/python3" ]]; then
        echo "✓ Python: $PYTHON_PATH (correctly using venv Python)"
    else
        echo "⚠ Warning: Python is not correctly pointing to venv: $PYTHON_PATH"
        echo "  Expected: $VIRTUAL_ENV/bin/python3"
    fi
    
    # Check if pip is correctly pointing to the virtual environment
    PIP_PATH=$(which pip3)
    if [[ "$PIP_PATH" == "$VIRTUAL_ENV/bin/pip3" ]]; then
        echo "✓ Pip: $PIP_PATH (correctly using venv pip)"
    else
        echo "⚠ Warning: Pip is not correctly pointing to venv: $PIP_PATH"
        echo "  Expected: $VIRTUAL_ENV/bin/pip3"
    fi
    
    # Check Python version compatibility
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    echo "✓ Python version: $(python3 --version)"
    
    # Verify Python version meets project requirements
    if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        echo "✓ Python version $PYTHON_VERSION meets project requirements (>=3.11)"
    else
        echo "⚠ Warning: Python version $PYTHON_VERSION may not meet project requirements (>=3.11)"
    fi
    
    echo "✓ PYTHONPATH: $PYTHONPATH"
    
    # Set the environment file path
    export ENV_FILE="$SCRIPT_DIR/.env"
    echo "✓ Environment file: $ENV_FILE"
    
    echo ""
    echo "You can now run the project with:"
    echo "  python3 start.py"
    echo ""
    echo "Or install packages with:"
    echo "  pip install <package>"
    echo ""
    echo "Or start an interactive shell with:"
    echo "  bash"
else
    echo "Error: Failed to activate virtual environment"
    exit 1
fi