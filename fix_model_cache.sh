#!/bin/bash

# Fix DistilBERT model cache structure for Hugging Face transformers
# This script creates the proper directory structure that transformers expects

echo "Fixing DistilBERT model cache structure..."

# Base directories
MODELS_DIR="./models/transformers"
HF_CACHE_DIR="./models/transformers/hub"
MODEL_NAME="distilbert-base-uncased"

# Create Hugging Face hub directory structure
mkdir -p "${HF_CACHE_DIR}"

# Create the proper Hugging Face cache directory name with double dashes
HF_MODEL_DIR="${HF_CACHE_DIR}/models--${MODEL_NAME}"

# Copy model files to proper Hugging Face cache location
if [ -d "${MODELS_DIR}/${MODEL_NAME}" ] && [ ! -d "${HF_MODEL_DIR}" ]; then
    echo "Copying model files to Hugging Face cache structure..."
    cp -r "${MODELS_DIR}/${MODEL_NAME}" "${HF_MODEL_DIR}"
    echo "✓ Model files copied to: ${HF_MODEL_DIR}"
elif [ -d "${HF_MODEL_DIR}" ]; then
    echo "✓ Hugging Face cache directory already exists: ${HF_MODEL_DIR}"
else
    echo "✗ Source model directory not found: ${MODELS_DIR}/${MODEL_NAME}"
    exit 1
fi

# Create symbolic links for alternative cache locations
ln -sf "${HF_MODEL_DIR}" "${MODELS_DIR}/models--${MODEL_NAME}"

echo "✓ Model cache structure fixed"
echo ""
echo "Cache directories created:"
echo "  - Hugging Face hub: ${HF_MODEL_DIR}"
echo "  - Symlink: ${MODELS_DIR}/models--${MODEL_NAME}"
echo ""
echo "The DistilBERT model should now be accessible in offline mode."