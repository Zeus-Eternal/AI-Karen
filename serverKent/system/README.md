Native llama.cpp in App Directory
=================================

Overview
--------
- This sets up a local build of `llama.cpp` inside the repo under `serverKent/system`.
- The server binary is placed in `serverKent/system/bin/llama-server`.
- Configs are updated so the manager uses this binary.
- Models live at the repo root under `models/`.

Layout
------
- Source: `serverKent/system/llama.cpp` (cloned)
- Binary: `serverKent/.bin/llama-server`
- Configs:
  - Dev: `configs/llamacpp/config.json`
  - System: `serverKent/system/config.json`
- Models: `models/` (place `.gguf` files here)

Install (native)
----------------
- CPU build (default):
  - `bash serverKent/system/install_native_llamacpp.sh`
- GPU builds:
  - Auto-detect: `bash serverKent/system/install_native_llamacpp.sh --gpu auto`
  - CUDA/cuBLAS:  `bash serverKent/system/install_native_llamacpp.sh --gpu cuda`
  - ROCm/HIPBLAS: `bash serverKent/system/install_native_llamacpp.sh --gpu rocm`
  - Metal (macOS):`bash serverKent/system/install_native_llamacpp.sh --gpu metal`
  - Vulkan:       `bash serverKent/system/install_native_llamacpp.sh --gpu vulkan`
  - OpenCL/CLBlast:`bash serverKent/system/install_native_llamacpp.sh --gpu opencl`

Advanced:
- Choose branch: `--branch <ref>`
- Skip pull: `--no-pull`
- Clean build: `--clean`
- Jobs: `--jobs N`

The installer will:
- Clone/pull `ggerganov/llama.cpp`
- Build the `server` target with the chosen backend
- Copy to `serverKent/system/bin/llama-server`
- Update `server_bin` in both configs to the absolute path

Run
---
- Via manager (recommended):
  - `bash serverKent/system/run_manager.sh`
- Bare server (no monitoring):
  - `bash serverKent/system/run_bare.sh`

Notes
-----
- CPU build is used by default; for GPU builds, customize the Make invocation in `install_native_llamacpp.sh`.
- Ensure your model exists at `models/llama-cpp` or update the config.
