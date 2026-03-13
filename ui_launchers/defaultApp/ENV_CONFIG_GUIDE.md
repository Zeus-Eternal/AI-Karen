# Environment Configuration Guide

## ⚠️ Important Note

The `.env.local` file is gitignored for security reasons. You need to create it manually.

## 📝 Steps to Create `.env.local`

Run this command in your terminal:

```bash
cd ui_launchers/defaultApp
```

Then create the `.env.local` file with this content:

```bash
# AI-Karen Backend API Configuration
# Update this with your backend server URL

NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: API Key if your backend requires authentication
# NEXT_PUBLIC_API_KEY=your_api_key_here

# Optional: Enable debug mode for development
# NEXT_PUBLIC_DEBUG=true
```

## 🔍 Finding Your Backend URL

The AI-Karen backend typically runs on:
- **Development**: http://localhost:8000
- **Production**: Your deployed backend URL

Check your backend configuration to confirm the correct port and URL.

## 🚀 After Creating `.env.local`

1. Restart the development server: `npm run dev`
2. The UI will connect to your backend at the specified URL
3. You can test the chat functionality

## 📋 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | - | Your AI-Karen backend server URL |
| `NEXT_PUBLIC_API_KEY` | No | - | API key for authentication (if required) |
| `NEXT_PUBLIC_DEBUG` | No | false | Enable debug logging in console |

## 🔒 Security Notes

- Never commit `.env.local` to version control
- Use different values for development and production
- Rotate API keys regularly in production
- Use environment-specific files (`.env.development`, `.env.production`)
