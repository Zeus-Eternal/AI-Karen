#!/usr/bin/env bash
# Run Playwright test with a 40 second timeout and forward exit code.
# Usage: ./run_playwright_with_timeout.sh [additional playwright args]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
CMD=(npx playwright test e2e/chat-math-response.spec.ts --project=chromium --config=ui_launchers/web_ui/playwright.config.ts)

# Allow extra args to be appended
if [ "$#" -gt 0 ]; then
  CMD+=("$@")
fi

TIMEOUT_SECONDS=40

echo "Running Playwright with timeout ${TIMEOUT_SECONDS}s from ${ROOT_DIR}"
cd "${ROOT_DIR}"

# Use timeout(1) if available to kill the entire process group on expiry
if command -v timeout >/dev/null 2>&1; then
  # Run in its own process group so timeout can kill it and children (GNU timeout handles --kill-after)
  timeout --kill-after=5s ${TIMEOUT_SECONDS}s "${CMD[@]}"
  EXIT_CODE=$?
else
  # Portable fallback: run command in background, wait, then kill if needed
  "${CMD[@]}" &
  PID=$!
  ( sleep ${TIMEOUT_SECONDS}; kill -TERM -${PID} >/dev/null 2>&1 || true ) &
  WATCHER=$!
  wait ${PID} || EXIT_CODE=$?
  kill -9 ${WATCHER} >/dev/null 2>&1 || true
fi

if [ "${EXIT_CODE:-0}" -eq 124 ] || [ "${EXIT_CODE:-0}" -eq 137 ]; then
  echo "Playwright timed out after ${TIMEOUT_SECONDS}s (exit ${EXIT_CODE})"
  exit 124
fi

exit ${EXIT_CODE:-0}
