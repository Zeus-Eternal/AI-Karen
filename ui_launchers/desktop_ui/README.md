# AI Karen Desktop Application

A native desktop application for AI Karen built with Tauri 2.5.0, providing a secure, performant, and feature-rich desktop experience with deep system integration capabilities.

## Overview

The AI Karen Desktop Application combines the power of Rust for the backend with modern web technologies for the frontend, delivering a native desktop experience with web-based UI flexibility. Built on Tauri 2.5.0, it provides secure system access, efficient resource usage, and seamless integration with the AI Karen backend services.

## Features

### Core Desktop Features
- **Native Performance**: Rust-based backend with optimized resource usage
- **Cross-Platform**: Support for Windows, macOS, and Linux
- **System Integration**: Native file system access, notifications, and system tray
- **Secure Architecture**: Sandboxed execution with controlled API access
- **Auto-Updates**: Built-in update mechanism for seamless maintenance
- **Offline Capabilities**: Local data storage and offline functionality

### AI Karen Integration
- **Backend Connectivity**: Full integration with AI Karen FastAPI backend
- **Real-time Communication**: WebSocket support for live updates
- **Plugin System**: Native plugin execution with system-level access
- **Memory Management**: Local memory caching and synchronization
- **Security**: Encrypted local storage and secure API communication

### User Interface
- **Modern Web UI**: React-based frontend with Vite build system
- **Responsive Design**: Adaptive layout for different window sizes
- **Native Menus**: Platform-specific menu bars and context menus
- **Keyboard Shortcuts**: Comprehensive keyboard navigation
- **Accessibility**: Full accessibility support with screen readers

## Technology Stack

### Backend (Rust)
- **Tauri**: 2.5.0 (Desktop application framework)
- **Serde**: JSON serialization and deserialization
- **Tokio**: Async runtime for concurrent operations
- **Reqwest**: HTTP client for backend communication

### Frontend (Web Technologies)
- **Vite**: Modern build tool with fast HMR
- **React**: UI library for component-based development
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework

### Plugins and Extensions
- **tauri-plugin-http**: HTTP client for API communication
- **tauri-plugin-shell**: Secure shell command execution
- **tauri-plugin-log**: Comprehensive logging system
- **Custom Plugins**: Extensible plugin architecture

## Prerequisites

### System Requirements

#### Windows
- **OS**: Windows 10 version 1903 or higher
- **Architecture**: x64, ARM64
- **WebView2**: Microsoft Edge WebView2 (auto-installed)
- **Visual Studio**: Build Tools or Community Edition

#### macOS
- **OS**: macOS 10.15 (Catalina) or higher
- **Architecture**: Intel x64, Apple Silicon (M1/M2)
- **Xcode**: Command Line Tools or full Xcode

#### Linux
- **OS**: Ubuntu 18.04+, Debian 10+, or equivalent
- **Architecture**: x64, ARM64
- **Dependencies**: webkit2gtk, libgtk-3, libayatana-appindicator3

### Development Tools
- **Rust**: 1.77.2 or higher
- **Node.js**: 18.x or higher
- **npm/yarn**: Package manager for frontend dependencies
- **Tauri CLI**: Latest version for development commands

## Quick Start

### Installation

#### Install Rust
```bash
# Install Rust via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Verify installation
rustc --version
cargo --version
```

#### Install Node.js and Dependencies
```bash
# Install Node.js (via nvm recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Verify installation
node --version
npm --version
```

#### Install Tauri CLI
```bash
# Install Tauri CLI
cargo install tauri-cli

# Verify installation
cargo tauri --version
```

### Development Setup

```bash
# Navigate to desktop UI directory
cd ui_launchers/desktop_ui

# Install frontend dependencies (if package.json exists)
npm install

# Start AI Karen backend (required)
# From project root:
cd ../..
python main.py  # or uvicorn main:create_app --factory

# Start development server
cargo tauri dev
```

The application will launch as a native desktop window with the frontend served from `http://localhost:3000`.

### Build Commands

```bash
# Development build with hot reload
cargo tauri dev

# Production build
cargo tauri build

# Build for specific platform
cargo tauri build --target x86_64-pc-windows-msvc  # Windows
cargo tauri build --target x86_64-apple-darwin     # macOS Intel
cargo tauri build --target aarch64-apple-darwin    # macOS Apple Silicon
cargo tauri build --target x86_64-unknown-linux-gnu # Linux

# Build with debug symbols
cargo tauri build --debug
```

## Configuration

### Environment Variables

Create a `.env` file in the desktop UI directory:

```env
# Development server URL for frontend
TAURI_DEV_SERVER_URL=http://localhost:3000

# AI Karen backend configuration
KAREN_BACKEND_URL=http://localhost:8000
KAREN_API_KEY=your_api_key_here

# Application configuration
APP_NAME=AI Karen Desktop
APP_VERSION=1.0.0
APP_IDENTIFIER=com.aikaren.desktop

# Security configuration
ENABLE_DEVTOOLS=false
ALLOW_EXTERNAL_URLS=false
CSP_POLICY=default-src 'self'

# Logging configuration
LOG_LEVEL=info
LOG_FILE=karen-desktop.log
```

### Tauri Configuration

The application is configured through `src-tauri/Cargo.toml`:

```toml
[package]
name = "ai-karen-desktop"
version = "1.0.0"
edition = "2021"
rust-version = "1.77.2"

[dependencies]
tauri = { version = "2.5.0", features = ["api-all"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.0", features = ["full"] }
reqwest = { version = "0.11", features = ["json"] }

# Plugins
tauri-plugin-http = "2.0.0"
tauri-plugin-shell = "2.0.0"
tauri-plugin-log = "2.0.0-rc"
```

### Frontend Configuration

The frontend uses Vite for development and building:

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'esnext'
  }
})
```

## Architecture

### Directory Structure

```
ui_launchers/desktop_ui/
├── src-tauri/                 # Rust backend
│   ├── src/
│   │   ├── main.rs           # Application entry point
│   │   ├── commands.rs       # Tauri commands
│   │   ├── menu.rs           # Application menus
│   │   ├── plugins/          # Custom plugins
│   │   └── utils/            # Utility functions
│   ├── Cargo.toml            # Rust dependencies
│   ├── Cargo.lock            # Dependency lock file
│   ├── build.rs              # Build script
│   └── icons/                # Application icons
├── src/                      # Frontend source (if exists)
│   ├── components/           # React components
│   ├── pages/                # Application pages
│   ├── hooks/                # Custom React hooks
│   ├── services/             # API services
│   ├── utils/                # Utility functions
│   └── styles/               # CSS styles
├── public/                   # Static assets
├── dist/                     # Build output
├── package.json              # Frontend dependencies
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
├── .env                      # Environment variables
└── README.md                 # This documentation
```

### Application Architecture

#### Rust Backend (`src-tauri/`)
- **Main Process**: Application lifecycle and window management
- **Commands**: Exposed functions callable from frontend
- **Plugins**: System integration and extended functionality
- **Security**: Sandboxed execution with controlled API access
- **IPC**: Inter-process communication with frontend

#### Frontend (Web Technologies)
- **React Components**: Modular UI components
- **State Management**: Application state and data flow
- **API Integration**: Communication with AI Karen backend
- **Routing**: Client-side navigation and page management
- **Styling**: Modern CSS with responsive design

### Security Model

- **Sandboxed Frontend**: Web content runs in isolated context
- **Controlled API Access**: Only exposed commands are accessible
- **CSP (Content Security Policy)**: Strict content security policies
- **HTTPS Only**: Secure communication with external services
- **Code Signing**: Signed binaries for distribution

## Development

### Frontend Development

If using a separate frontend build process:

```bash
# Install frontend dependencies
npm install

# Start frontend development server
npm run dev

# Build frontend for production
npm run build

# Type checking
npm run typecheck

# Linting
npm run lint
```

### Rust Development

```bash
# Check Rust code
cargo check

# Run tests
cargo test

# Format code
cargo fmt

# Lint code
cargo clippy

# Build Rust backend only
cargo build
```

### Tauri Commands

Custom commands for frontend-backend communication:

```rust
// src-tauri/src/commands.rs
use tauri::command;

#[command]
async fn process_message(message: String) -> Result<String, String> {
    // Process message with AI Karen backend
    Ok(format!("Processed: {}", message))
}

#[command]
async fn get_system_info() -> Result<SystemInfo, String> {
    // Get system information
    Ok(SystemInfo::new())
}
```

### Plugin Development

Create custom plugins for extended functionality:

```rust
// src-tauri/src/plugins/karen_plugin.rs
use tauri::{plugin::Plugin, Runtime};

pub fn init<R: Runtime>() -> impl Plugin<R> {
    tauri::plugin::Builder::new("karen")
        .invoke_handler(tauri::generate_handler![
            karen_command
        ])
        .build()
}

#[tauri::command]
async fn karen_command() -> Result<String, String> {
    Ok("Karen plugin response".to_string())
}
```

## Building and Distribution

### Development Builds

```bash
# Debug build with console
cargo tauri dev

# Debug build without console (Windows)
cargo tauri dev --no-dev-server-wait
```

### Production Builds

```bash
# Release build
cargo tauri build

# Build with custom configuration
cargo tauri build --config tauri.prod.conf.json

# Build for distribution
cargo tauri build --bundles all
```

### Platform-Specific Builds

#### Windows
```bash
# Build MSI installer
cargo tauri build --bundles msi

# Build NSIS installer
cargo tauri build --bundles nsis

# Build portable executable
cargo tauri build --bundles portable
```

#### macOS
```bash
# Build DMG
cargo tauri build --bundles dmg

# Build App Bundle
cargo tauri build --bundles app

# Build for App Store
cargo tauri build --bundles app --target universal-apple-darwin
```

#### Linux
```bash
# Build DEB package
cargo tauri build --bundles deb

# Build RPM package
cargo tauri build --bundles rpm

# Build AppImage
cargo tauri build --bundles appimage
```

### Code Signing

#### Windows
```bash
# Sign with certificate
cargo tauri build --bundles msi -- --sign-tool signtool --certificate-thumbprint THUMBPRINT
```

#### macOS
```bash
# Sign and notarize
cargo tauri build --bundles dmg -- --sign --notarize
```

## Backend Integration

### AI Karen API Integration

```rust
// src-tauri/src/karen_client.rs
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct MessageRequest {
    pub message: String,
    pub user_id: String,
    pub session_id: String,
}

#[derive(Serialize, Deserialize)]
pub struct MessageResponse {
    pub response: String,
    pub metadata: serde_json::Value,
}

pub struct KarenClient {
    client: Client,
    base_url: String,
    api_key: String,
}

impl KarenClient {
    pub fn new(base_url: String, api_key: String) -> Self {
        Self {
            client: Client::new(),
            base_url,
            api_key,
        }
    }

    pub async fn send_message(&self, request: MessageRequest) -> Result<MessageResponse, Box<dyn std::error::Error>> {
        let response = self
            .client
            .post(&format!("{}/api/chat", self.base_url))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&request)
            .send()
            .await?;

        let message_response: MessageResponse = response.json().await?;
        Ok(message_response)
    }
}
```

### WebSocket Integration

```rust
// Real-time communication with backend
use tokio_tungstenite::{connect_async, tungstenite::Message};

pub async fn connect_websocket() -> Result<(), Box<dyn std::error::Error>> {
    let (ws_stream, _) = connect_async("ws://localhost:8000/ws").await?;
    
    // Handle WebSocket messages
    Ok(())
}
```

## Troubleshooting

### Common Issues

#### Build Errors

**Rust Compilation Errors**
```bash
# Update Rust toolchain
rustup update

# Clean build cache
cargo clean

# Rebuild dependencies
cargo build --release
```

**Frontend Build Errors**
```bash
# Clear node modules
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf dist .vite
npm run build
```

#### Runtime Issues

**Backend Connection Issues**
```bash
# Check backend status
curl http://localhost:8000/health

# Verify environment variables
echo $KAREN_BACKEND_URL

# Check network connectivity
netstat -an | grep 8000
```

**WebView Issues (Windows)**
```bash
# Install/update WebView2
# Download from Microsoft Edge WebView2 page
# Or use automatic installer in Tauri build
```

#### Platform-Specific Issues

**Windows**
- **Missing Visual Studio Build Tools**: Install Visual Studio Build Tools
- **WebView2 Not Found**: Install Microsoft Edge WebView2 Runtime
- **Code Signing Issues**: Verify certificate installation and permissions

**macOS**
- **Xcode Command Line Tools**: `xcode-select --install`
- **Gatekeeper Issues**: Sign and notarize the application
- **Permissions**: Grant necessary permissions in System Preferences

**Linux**
- **Missing Dependencies**: Install webkit2gtk-4.0-dev libgtk-3-dev
- **AppImage Issues**: Ensure FUSE is installed and configured
- **Permissions**: Set executable permissions on built binaries

### Debug Mode

```bash
# Enable debug logging
RUST_LOG=debug cargo tauri dev

# Enable frontend debugging
TAURI_DEBUG=true cargo tauri dev

# Enable all debugging
RUST_LOG=debug TAURI_DEBUG=true cargo tauri dev
```

### Performance Optimization

- **Bundle Size**: Optimize frontend bundle size with tree shaking
- **Memory Usage**: Monitor Rust memory usage and optimize allocations
- **Startup Time**: Lazy load components and defer initialization
- **Resource Usage**: Profile CPU and memory usage during development

## Contributing

### Development Guidelines

1. **Setup Development Environment**: Follow the quick start guide
2. **Code Style**: Use `cargo fmt` for Rust and Prettier for frontend
3. **Testing**: Add tests for new functionality
4. **Documentation**: Update documentation for changes
5. **Pull Requests**: Submit well-documented pull requests

### Code Standards

- **Rust**: Follow Rust conventions and use Clippy for linting
- **TypeScript**: Use strict typing and ESLint for code quality
- **Git**: Use conventional commit messages
- **Security**: Follow security best practices for desktop applications

### Testing

```bash
# Run Rust tests
cargo test

# Run frontend tests
npm test

# Integration tests
cargo tauri test
```

## License

This project is part of the AI-Karen system. See the main project LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Tauri documentation: https://tauri.app/
3. Submit issues through the project's issue tracker
4. Join the community discussions for support and feature requests
