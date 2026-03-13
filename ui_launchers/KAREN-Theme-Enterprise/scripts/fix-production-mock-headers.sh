#!/bin/bash
# Fix production mock headers in copilot API routes

echo "🔧 Fixing mock user headers for production..."

FILES=(
  "src/app/api/copilot/assist/route.ts"
  "src/app/api/copilot/lnm/list/route.ts"
  "src/app/api/copilot/lnm/select/route.ts"
  "src/app/api/copilot/plugins/execute/route.ts"
  "src/app/api/copilot/plugins/list/route.ts"
  "src/app/api/copilot/security/context/route.ts"
)

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Processing $file..."
    # Remove X-Mock-User-ID header from development section
    sed -i "/h.set('X-Mock-User-ID'/d" "$file"
    echo "  ✓ Removed X-Mock-User-ID header"
  else
    echo "  ✗ File not found: $file"
  fi
done

echo ""
echo "✅ Production mock header fixes complete!"
echo ""
echo "Changed files:"
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  - $file"
  fi
done
