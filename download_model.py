#!/usr/bin/env python3
"""
Download Qwen3.5-0.8B model to local models directory.
This approach downloads model weights to models/transformers/ where both
Transformers and vLLM can use them.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    print("=" * 60)
    print("Downloading Qwen3.5-0.8B Model")
    print("=" * 60)

    # Model configuration
    model_name = "Qwen/Qwen3.5-0.8B"
    models_dir = project_root / "models" / "transformers"

    # Ensure models directory exists
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nModel: {model_name}")
    print(f"Target directory: {models_dir}")
    print(f"Expected size: ~1.75 GB")
    print("\nStarting download...")

    try:
        from huggingface_hub import snapshot_download

        # Download model to local directory
        downloaded_path = snapshot_download(
            repo_id=model_name,
            cache_dir=str(models_dir),
            local_dir=str(models_dir / model_name.replace("/", "--")),
            local_dir_use_symlinks=False,
            resume_download=True,
        )

        print(f"\n✅ Model downloaded successfully!")
        print(f"Location: {downloaded_path}")

        # Show disk usage
        import shutil
        total_size = sum(f.stat().st_size for f in Path(downloaded_path).rglob('*') if f.is_file())
        size_gb = total_size / (1024**3)
        print(f"Total size: {size_gb:.2f} GB")

        print("\n" + "=" * 60)
        print("Download Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Model is now available for Transformers provider")
        print("2. Model is ready for vLLM server (when started)")
        print("3. You can enable offline mode in .env after download")

    except Exception as e:
        print(f"\n❌ Error downloading model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
