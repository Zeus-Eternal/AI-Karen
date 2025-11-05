#!/bin/bash

echo "🔒 Fixing file permissions for security..."

# Fix environment file permissions
if [ -f ".env.local" ]; then
    chmod 600 .env.local
    echo "✅ Fixed .env.local permissions (600)"
fi

if [ -f ".env" ]; then
    chmod 600 .env
    echo "✅ Fixed .env permissions (600)"
fi

if [ -f ".env.production" ]; then
    chmod 600 .env.production
    echo "✅ Fixed .env.production permissions (600)"
fi

# Fix configuration file permissions (644 is appropriate for config files)
for file in "next.config.js" "tsconfig.json" "playwright.config.ts" "package.json"; do
    if [ -f "$file" ]; then
        chmod 644 "$file"
        echo "✅ Fixed $file permissions (644)"
    fi
done

# Clean up backup files
echo "🧹 Cleaning up backup files..."
find . -name "*.bak" -o -name "*.backup" -o -name "*.old" -o -name "*~" | while read file; do
    if [[ "$file" != *"node_modules"* ]]; then
        echo "🗑️  Removing backup file: $file"
        rm -f "$file"
    fi
done

echo "✅ Permission fixes complete!"