#!/usr/bin/env bash
set -euo pipefail

# Native install of llama.cpp server into the app directory
# Layout:
#   <repo_root>/serverKent/.llama.cpp          (source)
#   <repo_root>/serverKent/.bin/llama-server   (built binary)
#   <repo_root>/configs/llamacpp/config.json (updated server_bin)
#   <repo_root>/serverKent/system/config.json (updated server_bin)

REPO_ROOT="$(cd "$(dirname "$0")"/../.. && pwd)"
SYS_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$REPO_ROOT/serverKent/.llama.cpp"
BIN_DIR="$REPO_ROOT/serverKent/.bin"
BIN_PATH="$BIN_DIR/llama-server"

usage() {
  cat <<'EOF'
Native llama.cpp installer (in-repo)

Options:
  --gpu [auto|cuda|rocm|metal|vulkan|opencl]  Enable GPU backend (default: cpu)
  --branch <ref>                               Checkout a specific llama.cpp ref
  --no-pull                                    Do not git pull if repo exists
  --clean                                      Run 'make clean' before build
  --jobs N                                     Parallel build jobs (default: nproc)
  -h, --help                                   Show help

Examples:
  bash serverKent/system/install_native_llamacpp.sh --gpu auto
  bash serverKent/system/install_native_llamacpp.sh --gpu cuda --jobs 8
  bash serverKent/system/install_native_llamacpp.sh --gpu metal --branch master
EOF
}

GPU_BACKEND="cpu"
CUDA_COMPILER=""
BRANCH=""
DO_PULL=1
CLEAN=0
JOBS="$(command -v nproc >/dev/null 2>&1 && nproc || echo 2)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu)
      GPU_BACKEND="$2"; shift 2 ;;
    --cuda-compiler)
      CUDA_COMPILER="$2"; shift 2 ;;
    --branch)
      BRANCH="$2"; shift 2 ;;
    --no-pull)
      DO_PULL=0; shift ;;
    --clean)
      CLEAN=1; shift ;;
    --jobs)
      JOBS="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

echo "==> Native llama.cpp install into: $SRC_DIR (gpu=$GPU_BACKEND)"

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
command -v cmake >/dev/null 2>&1 || { echo "cmake is required" >&2; exit 1; }

mkdir -p "$BIN_DIR"

if [[ ! -d "$SRC_DIR/.git" ]]; then
  echo "Cloning llama.cpp into $SRC_DIR"
  git clone --depth 1 https://github.com/ggerganov/llama.cpp.git "$SRC_DIR"
else
  if [[ $DO_PULL -eq 1 ]]; then
    echo "Updating llama.cpp in $SRC_DIR"
    git -C "$SRC_DIR" pull --ff-only || true
  else
    echo "Skipping git pull (per --no-pull)"
  fi
fi

if [[ -n "$BRANCH" ]]; then
  echo "Checking out ref: $BRANCH"
  git -C "$SRC_DIR" checkout "$BRANCH"
fi

# Determine GPU CMake variables
CMAKE_VARS=()
detect_gpu_backend() {
  # Simple auto-detection heuristics
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo metal; return
  fi
  if command -v nvcc >/dev/null 2>&1 || [[ -d "/usr/local/cuda" ]]; then
    echo cuda; return
  fi
  if command -v hipcc >/dev/null 2>&1 || [[ -d "/opt/rocm" ]]; then
    echo rocm; return
  fi
  if pkg-config --exists vulkan 2>/dev/null || command -v vkcube >/dev/null 2>&1; then
    echo vulkan; return
  fi
  if pkg-config --exists clblast 2>/dev/null || pkg-config --exists OpenCL 2>/dev/null; then
    echo opencl; return
  fi
  echo cpu
}

BACKEND_CHOSEN="$GPU_BACKEND"
if [[ "$GPU_BACKEND" == "auto" ]]; then
  BACKEND_CHOSEN="$(detect_gpu_backend)"
  echo "Auto-detected GPU backend: $BACKEND_CHOSEN"
fi

case "$BACKEND_CHOSEN" in
  cuda)
    CMAKE_VARS+=( -DGGML_CUDA=ON )
    # Prefer provided compiler, else discover nvcc
    if [[ -n "$CUDA_COMPILER" ]]; then
      CMAKE_VARS+=( -DCMAKE_CUDA_COMPILER="$CUDA_COMPILER" )
    else
      if command -v nvcc >/dev/null 2>&1; then
        CMAKE_VARS+=( -DCMAKE_CUDA_COMPILER="$(command -v nvcc)" )
      elif [[ -x "/usr/local/cuda/bin/nvcc" ]]; then
        CMAKE_VARS+=( -DCMAKE_CUDA_COMPILER="/usr/local/cuda/bin/nvcc" )
      else
        echo "[native] CUDA selected but 'nvcc' not found. Falling back to CPU build." >&2
        BACKEND_CHOSEN="cpu"
        # reset to CPU
        CMAKE_VARS=()
      fi
    fi
    ;;
  rocm)
    CMAKE_VARS+=( -DGGML_HIPBLAS=ON ) ;;
  metal)
    CMAKE_VARS+=( -DGGML_METAL=ON ) ;;
  vulkan)
    CMAKE_VARS+=( -DGGML_VULKAN=ON ) ;;
  opencl)
    CMAKE_VARS+=( -DGGML_CLBLAST=ON ) ;;
  cpu|*)
    ;; # no extra vars
esac

BUILD_DIR="$SRC_DIR/build"
# Auto-clean if deprecated LLAMA_* cache entries are present
if [[ -f "$BUILD_DIR/CMakeCache.txt" ]] && grep -qE '^LLAMA_(CUBLAS|HIPBLAS|METAL|VULKAN|CLBLAST)' "$BUILD_DIR/CMakeCache.txt" 2>/dev/null; then
  echo "Detected deprecated LLAMA_* flags in existing CMake cache; cleaning $BUILD_DIR"
  CLEAN=1
fi

if [[ $CLEAN -eq 1 ]]; then
  echo "Cleaning previous build directory: $BUILD_DIR"
  rm -rf "$BUILD_DIR" || true
fi

echo "Configuring (CMake) backend=$BACKEND_CHOSEN"
cmake -S "$SRC_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release "${CMAKE_VARS[@]}"

echo "Building llama.cpp server (CMake)"
# Prefer the CMake target name 'llama-server'; fall back to default build if not present
if ! cmake --build "$BUILD_DIR" --target llama-server -j"$JOBS"; then
  echo "Target 'llama-server' not found; building default targets"
  cmake --build "$BUILD_DIR" -j"$JOBS"
fi

# Prefer the built artifact named 'server'; copy to our bin as 'llama-server'
if [[ -x "$BUILD_DIR/bin/llama-server" ]]; then
  cp -f "$BUILD_DIR/bin/llama-server" "$BIN_PATH"
elif [[ -x "$BUILD_DIR/bin/server" ]]; then
  cp -f "$BUILD_DIR/bin/server" "$BIN_PATH"
elif [[ -x "$SRC_DIR/server" ]]; then
  cp -f "$SRC_DIR/server" "$BIN_PATH"
elif [[ -x "$SRC_DIR/bin/server" ]]; then
  cp -f "$SRC_DIR/bin/server" "$BIN_PATH"
else
  echo "Build did not produce a 'server' binary. Please check CMake build output in $BUILD_DIR." >&2
  exit 1
fi
chmod +x "$BIN_PATH"

echo "Built server: $BIN_PATH"

# Update configs to use the absolute server_bin
ABS_BIN="$(readlink -f "$BIN_PATH" 2>/dev/null || realpath "$BIN_PATH" 2>/dev/null || echo "$BIN_PATH")"

update_json_server_bin() {
  local file="$1"
  if [[ -f "$file" ]]; then
    # Use jq if available for robust edits; fallback to sed
    if command -v jq >/dev/null 2>&1; then
      tmp="$(mktemp)"
      jq --arg p "$ABS_BIN" '.server_bin = $p' "$file" > "$tmp" && mv "$tmp" "$file"
      echo "Updated server_bin in $file"
    else
      # naive replace: if key exists, replace its value; else append before closing brace
      if grep -q '"server_bin"' "$file"; then
        sed -i "s#\("server_bin"\s*:\s*\)\"[^\"]*\"#\1\"$ABS_BIN\"#" "$file"
      else
        sed -i "s#}\s*
#  , \"server_bin\": \"$ABS_BIN\"\n}#" "$file"
      fi
      echo "Updated server_bin in $file (sed)"
    fi
  fi
}

update_json_server_bin "$REPO_ROOT/configs/llamacpp/config.json"
update_json_server_bin "$REPO_ROOT/serverKent/system/config.json"
update_json_server_bin "$REPO_ROOT/serverKent/configs/llamacpp/config.json"

echo "\nNative install complete. Next steps:"
echo "- Models directory: $REPO_ROOT/models (place your .gguf files here)"
echo "- Config (dev):     $REPO_ROOT/configs/llamacpp/config.json"
echo "- Config (system):  $REPO_ROOT/serverKent/system/config.json"
echo "- server_bin set to: $ABS_BIN"
echo "\nRun via launcher:"
echo "  python3 $REPO_ROOT/serverKent/llamacpp_launcher.py"
echo "Then select 1) Manager: Start."
