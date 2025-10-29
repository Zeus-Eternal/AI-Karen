#!/bin/bash
# Activate AI-Karen Environment Script
#
# This script ensures you're using the correct .env_karen virtual environment
# and sets up the proper environment variables.

echo "🚀 Activating AI-Karen Environment (.env_karen)"
echo "================================================"

# Check if .env_karen exists
if [ ! -d ".env_karen" ]; then
    echo "❌ .env_karen virtual environment not found!"
    echo "💡 Please create it first with: python -m venv .env_karen"
    exit 1
fi

# Activate the virtual environment
echo "📦 Activating .env_karen virtual environment..."
source .env_karen/bin/activate

# Verify activation
if [[ "$VIRTUAL_ENV" == *".env_karen"* ]]; then
    echo "✅ Successfully activated .env_karen"
    echo "📍 Virtual environment: $VIRTUAL_ENV"
else
    echo "⚠️ Virtual environment activation may have failed"
    echo "📍 Current VIRTUAL_ENV: $VIRTUAL_ENV"
fi

# Load environment variables from .env
if [ -f ".env" ]; then
    echo "📋 Loading environment variables from .env..."
    set -a  # automatically export all variables
    source .env
    set +a  # stop automatically exporting
    echo "✅ Environment variables loaded"
else
    echo "⚠️ .env file not found"
fi

# Show Python version and location
echo "🐍 Python information:"
echo "   Version: $(python --version)"
echo "   Location: $(which python)"

# Show key environment variables
echo "🔧 Key environment variables:"
echo "   MODELS_ROOT: ${MODELS_ROOT:-not set}"
echo "   HUGGINGFACE_CACHE_DIR: ${HUGGINGFACE_CACHE_DIR:-not set}"
echo "   LLAMACPP_MODELS_PATH: ${LLAMACPP_MODELS_PATH:-not set}"

echo ""
echo "✅ Environment ready! You can now:"
echo "   • Run: python download_essential_models.py"
echo "   • Run: python verify_model_setup.py"
echo "   • Start your backend server"
echo ""
echo "💡 To deactivate later, run: deactivate"