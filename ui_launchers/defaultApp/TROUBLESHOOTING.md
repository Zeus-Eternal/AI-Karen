# Troubleshooting Guide

## 🚨 Common Issues and Solutions

### Issue 1: OS File Watch Limit Reached

**Error**: `Turbopack Error: OS file watch limit reached`

**Root Cause**: The AI-Karen repository has many files, and the OS inotify watch limit is too low for Turbopack to watch all files.

**Solutions** (try in order):

#### Solution 1: Increase File Watch Limit (Recommended - requires sudo)

Run these commands in your terminal:

```bash
# Check current limit
cat /proc/sys/fs/inotify/max_user_watches

# Temporarily increase limit (until reboot)
sudo sysctl fs.inotify.max_user_watches=524288

# Make it permanent
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### Solution 2: Build and Run Production Mode

Skip development mode and use production build:

```bash
cd ui_launchers/defaultApp
npm run build
npm run start
```

The UI will be available at http://localhost:3000

**Note**: You'll need to rebuild after making changes.

#### Solution 3: Use a Separate Development Environment

Create a symlink to just the defaultApp directory and develop from there:

```bash
cd /tmp
mkdir karen-ui-dev
cd karen-ui-dev
cp -r /mnt/development/KIRO/AI-Karen/ui_launchers/defaultApp/* .
npm install
npm run dev
```

This isolates the development environment from the large AI-Karen repository.

#### Solution 4: Use Static Export

For UI-only development without backend connection:

```bash
cd ui_launchers/defaultApp
# Update next.config.ts to enable static export
npm run build
# Output will be in out/ directory
```

### Issue 2: Port Already in Use

**Error**: `Port 3000 is in use by an unknown process`

**Solution**:

```bash
# Find process using port 3000
lsof -ti:3000

# Kill the process
kill -9 $(lsof -ti:3000)

# Or use a different port
PORT=3001 npm run dev
```

### Issue 3: Backend Connection Failed

**Error**: `Failed to connect to backend API`

**Solutions**:

1. Check if backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify `.env.local` configuration:
   ```bash
   cat .env.local | grep NEXT_PUBLIC_API_URL
   ```

3. Check browser console for CORS errors

4. Test API endpoint directly:
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "test"}'
   ```

### Issue 4: Module Not Found Errors

**Error**: `Module not found: Can't resolve '@copilotkit/react-core'`

**Solution**:

```bash
cd ui_launchers/defaultApp
rm -rf node_modules package-lock.json
npm install
```

### Issue 5: TypeScript Errors

**Error**: TypeScript compilation errors

**Solution**:

```bash
# Check TypeScript errors
npm run build

# For development mode with type checking
npx next dev --experimental-app
```

## 🔍 Debug Mode

Enable debug logging by adding to `.env.local`:

```bash
NEXT_PUBLIC_DEBUG=true
```

This will log:
- API requests/responses
- State changes
- Error details
- Performance metrics

## 📊 Performance Issues

### UI is Slow or Laggy

1. Check React DevTools Profiler
2. Enable React Strict Mode (already enabled)
3. Check for unnecessary re-renders
4. Optimize image sizes
5. Enable gzip compression in production

### High Memory Usage

1. Close unused browser tabs
2. Clear browser cache
3. Restart development server
4. Check for memory leaks in custom hooks

## 🆘 Getting Help

If none of these solutions work:

1. Check Next.js documentation: https://nextjs.org/docs
2. Check the console and terminal output for specific errors
3. Review the error logs in `/tmp/nextjs-dev.log`
4. Create a minimal reproduction case
5. Report the issue with:
   - OS and version
   - Node.js version (`node --version`)
   - Next.js version (`npm list next`)
   - Full error message
   - Steps to reproduce

## 📝 Quick Reference

### Useful Commands

```bash
# Clean build
rm -rf .next node_modules package-lock.json
npm install

# Development with different port
PORT=3001 npm run dev

# Production build
npm run build
npm run start

# Check TypeScript
npx tsc --noEmit

# Lint code
npm run lint

# Check file watch limit
cat /proc/sys/fs/inotify/max_user_watches
```

### Important Files

- `.env.local` - Environment configuration
- `next.config.ts` - Next.js configuration
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.ts` - TailwindCSS configuration
