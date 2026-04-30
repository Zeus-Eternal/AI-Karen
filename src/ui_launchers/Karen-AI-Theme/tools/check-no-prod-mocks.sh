#!/usr/bin/env bash
set -euo pipefail

forbidden_regex='\b(mock|dummy|demo)\b|mock-up|conceptual placeholder|synthetic output'

rg_args=(
  -n -i "$forbidden_regex"
  -g '!**/*.test.*'
  -g '!**/tests/**'
  -g '!**/test/**'
  -g '!**/__mocks__/**'
  -g '!**/plugin_repo_backups/**'
)

paths=(core api_routes services src/components src/lib src/app)

has_hits=0
for p in "${paths[@]}"; do
  if [[ -d "$p" ]]; then
    if rg "${rg_args[@]}" "$p"; then
      has_hits=1
    fi
  fi
done

if [[ "$has_hits" -ne 0 ]]; then
  echo "Forbidden mock/demo patterns found in production paths." >&2
  exit 1
fi

echo "No forbidden mock/demo patterns found in production paths."
