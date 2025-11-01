# Extension System FAQ

## General Questions

### What are Kari Extensions?

Kari Extensions are modular add-ons that extend the functionality of the Kari platform. They can add new features, integrate with external services, provide custom UI components, and automate workflows. Extensions run in isolated environments and follow a standardized API for seamless integration.

### How do Extensions differ from Plugins?

Extensions are the next evolution of the plugin system, offering:
- **Better Isolation**: Each extension runs in its own process
- **Enhanced Security**: Granular permission system and sandboxing
- **UI Integration**: Full React component and page support
- **Data Management**: Built-in database and storage capabilities
- **Background Tasks**: Scheduled and event-driven task execution
- **Marketplace**: Centralized discovery and installation

### Are Extensions compatible with existing Plugins?

Yes, we provide migration tools to convert existing plugins to extensions. The migration process includes:
- Automatic manifest generation
- Code structure conversion
- Permission mapping
- Configuration migration
- Testing and validation

## Installation and Management

### How do I install Extensions?

Extensions can be installed through multiple methods:

**Web Interface:**
1. Navigate to Extensions > Marketplace
2. Browse or search for extensions
3. Click "Install" on desired extension
4. Configure settings if required

**Command Line:**
```bash
# From marketplace
kari extension install extension-name

# From local file
kari extension install ./my-extension.tar.gz

# From URL
kari extension install https://example.com/extension.tar.gz
```

### Can I install Extensions without internet access?

Yes, extensions can be installed offline:
1. Download extension packages on a connected machine
2. Transfer files to your Kari instance
3. Install using local file path
4. Configure any required settings

### How do I update Extensions?

**Automatic Updates:**
- Enable auto-updates in Settings > Extensions
- Extensions update during maintenance windows
- Critical security updates install immediately

**Manual Updates:**
```bash
# Update specific extension
kari extension update extension-name

# Update all extensions
kari extension update --all

# Check for available updates
kari extension check-updates
```

### Can I rollback Extension updates?

Yes, rollback is supported:
```bash
# Rollback to previous version
kari extension rollback extension-name

# Rollback to specific version
kari extension rollback extension-name --version 1.2.0

# List available versions
kari extension versions extension-name
```

## Development

### What programming languages can I use?

**Primary Languages:**
- **Python**: Backend logic, APIs, background tasks
- **TypeScript/JavaScript**: UI components and frontend logic
- **SQL**: Database queries and schema definitions

**Supported Frameworks:**
- FastAPI for REST APIs
- React for UI components
- SQLAlchemy for database operations
- Celery for background tasks

### Do I need to know React to create Extensions?

Not necessarily. Extensions can be:
- **Backend-only**: Pure API extensions without UI
- **Simple UI**: Basic HTML/CSS with minimal JavaScript
- **Advanced UI**: Full React components and pages

For complex UI features, React knowledge is recommended.

### How do I test my Extension?

**Development Testing:**
```bash
# Run extension in development mode
kari extension dev ./my-extension --watch

# Run unit tests
kari extension test ./my-extension

# Integration testing
kari extension test ./my-extension --integration
```

**Testing Framework:**
- Built-in test client for API testing
- Mock utilities for external dependencies
- UI component testing with React Testing Library
- Performance and security testing tools

### Can Extensions access the file system?

Extensions have limited file system access:
- **Extension Directory**: Full read/write access to extension files
- **Data Directory**: Dedicated storage space for extension data
- **Temp Directory**: Temporary file storage
- **System Files**: Requires special permissions (rarely granted)

### How do Extensions handle secrets and API keys?

Extensions use a secure configuration system:
```python
# Access encrypted configuration
api_key = self.config.get_secret("api_key")

# Store encrypted values
await self.config.set_secret("token", encrypted_token)
```

Secrets are:
- Encrypted at rest
- Never logged or exposed
- Isolated per extension
- Backed up securely

## Security and Permissions

### Are Extensions secure?

Extensions run in a secure, isolated environment with:
- **Process Isolation**: Separate processes prevent interference
- **Permission System**: Granular access controls
- **Resource Limits**: CPU, memory, and disk quotas
- **Network Restrictions**: Controlled external access
- **Code Signing**: Verified extension authenticity
- **Security Scanning**: Automated vulnerability detection

### What permissions do Extensions need?

Common permissions include:
- `data.read/write`: Access extension data
- `api.create_endpoints`: Create REST endpoints
- `ui.register_components`: Add UI components
- `system.background_tasks`: Run scheduled tasks
- `user.read_profile`: Access user information

Extensions request minimal necessary permissions.

### Can Extensions access my personal data?

Extensions can only access data they have explicit permission for:
- **Extension Data**: Data created by the extension
- **User Profile**: Only with `user.read_profile` permission
- **System Data**: Only with specific system permissions
- **Cross-Extension Data**: Not allowed without special permissions

### How do I review Extension permissions?

**Before Installation:**
- Review permission list on extension page
- Read extension documentation
- Check user reviews for security concerns

**After Installation:**
```bash
# View extension permissions
kari extension permissions extension-name

# Audit all extension permissions
kari extension permissions --audit
```

### Can I revoke Extension permissions?

Currently, permissions are set during installation. To change permissions:
1. Uninstall the extension
2. Reinstall with different permission settings
3. Or contact the extension developer for a version with fewer permissions

## Performance and Resources

### Do Extensions slow down Kari?

Extensions are designed for minimal performance impact:
- **Lazy Loading**: Extensions load only when needed
- **Resource Limits**: Prevent resource exhaustion
- **Efficient APIs**: Optimized for performance
- **Caching**: Built-in caching mechanisms
- **Monitoring**: Performance tracking and alerts

### How much resources do Extensions use?

Default resource limits per extension:
- **Memory**: 512MB
- **CPU**: 50% of one core
- **Disk**: 1GB storage
- **Network**: 100 requests/minute

Limits can be adjusted based on extension needs.

### Can I monitor Extension performance?

Yes, comprehensive monitoring is available:
```bash
# Real-time monitoring
kari extension monitor extension-name

# Performance metrics
kari extension metrics extension-name --last 24h

# Resource usage
kari extension resources extension-name
```

Web dashboard also provides visual performance metrics.

### What happens if an Extension crashes?

Extensions have automatic recovery:
- **Auto-restart**: Crashed extensions restart automatically
- **Circuit Breaker**: Prevents cascading failures
- **Graceful Degradation**: Core Kari functionality continues
- **Error Reporting**: Automatic crash reports to developers
- **Rollback**: Automatic rollback to stable version if needed

## Data and Storage

### Where is Extension data stored?

Extension data is stored in isolated databases:
- **PostgreSQL**: Structured data with full SQL support
- **Redis**: Caching and session data
- **File Storage**: Documents and binary files
- **Configuration**: Encrypted configuration data

Each extension has its own isolated storage space.

### Can Extensions share data?

Extensions are isolated by default, but can share data through:
- **Public APIs**: Extensions can expose APIs for others
- **Event System**: Extensions can publish/subscribe to events
- **Shared Services**: Common services like user management
- **Explicit Permissions**: Special permissions for data sharing

### How is Extension data backed up?

Extension data is included in regular Kari backups:
- **Automatic Backups**: Daily incremental backups
- **Manual Backups**: On-demand backup creation
- **Point-in-time Recovery**: Restore to specific timestamps
- **Cross-region Replication**: For enterprise deployments

### What happens to data when I uninstall an Extension?

Data handling depends on uninstall options:
- **Keep Data**: Data preserved for potential reinstallation
- **Delete Data**: All extension data permanently removed
- **Export Data**: Data exported before deletion
- **Archive Data**: Data archived for compliance

## Marketplace and Distribution

### How do I publish my Extension?

**Publishing Process:**
1. Develop and test your extension
2. Create comprehensive documentation
3. Submit to marketplace for review
4. Address any review feedback
5. Extension goes live after approval

**Requirements:**
- Complete manifest file
- Security review passed
- Documentation provided
- Terms of service accepted

### Can I sell my Extensions?

Yes, the marketplace supports both free and paid extensions:
- **Free Extensions**: No cost to users
- **Paid Extensions**: One-time purchase or subscription
- **Freemium**: Basic features free, premium features paid
- **Enterprise**: Custom pricing for enterprise features

Revenue sharing applies to paid extensions.

### How do I get support for marketplace Extensions?

**Support Channels:**
- **Extension Documentation**: Built-in help and guides
- **Developer Support**: Contact extension developer directly
- **Community Forums**: User community discussions
- **Marketplace Support**: For installation and billing issues

### Can I request custom Extensions?

Yes, custom extension development is available:
- **Community Requests**: Post feature requests in forums
- **Paid Development**: Hire developers for custom work
- **Enterprise Services**: Custom development for enterprise customers
- **Open Source**: Contribute to open source extensions

## Troubleshooting

### My Extension won't install. What should I do?

**Common Solutions:**
1. Check system requirements and compatibility
2. Verify sufficient disk space and permissions
3. Clear extension cache: `kari extension cache --clear`
4. Try installing with verbose logging: `--verbose`
5. Check network connectivity and proxy settings

### Extension is installed but not working. How do I fix it?

**Troubleshooting Steps:**
1. Check extension status: `kari extension status extension-name`
2. Review logs: `kari extension logs extension-name`
3. Validate configuration: `kari extension config extension-name --validate`
4. Restart extension: `kari extension restart extension-name`
5. Check for conflicts with other extensions

### How do I report Extension bugs?

**Bug Reporting:**
1. **Extension Issues**: Contact extension developer through marketplace
2. **Platform Issues**: Submit to Kari support team
3. **Security Issues**: Email security@kari.ai immediately
4. **Feature Requests**: Post in community forums

Include diagnostic information when reporting bugs.

### Can I get help developing Extensions?

**Development Support:**
- **Documentation**: Comprehensive development guides
- **Examples**: Sample extensions and code snippets
- **Community**: Developer forums and discussions
- **Office Hours**: Regular developer Q&A sessions
- **Professional Services**: Paid development assistance

## Enterprise Features

### Are there enterprise-specific Extension features?

**Enterprise Extensions include:**
- **Advanced Security**: Enhanced isolation and monitoring
- **Compliance**: SOC 2, GDPR, HIPAA compliance features
- **Custom Deployment**: Private marketplace and repositories
- **Priority Support**: Dedicated support team
- **SLA Guarantees**: Uptime and performance guarantees

### Can I host a private Extension marketplace?

Yes, enterprise customers can deploy private marketplaces:
- **On-premises**: Fully isolated marketplace
- **Hybrid**: Mix of public and private extensions
- **Custom Approval**: Internal review processes
- **Enterprise Catalog**: Curated extension collections

### How do Extensions work with SSO and RBAC?

Extensions integrate with enterprise authentication:
- **SSO Integration**: Support for SAML, OIDC, LDAP
- **RBAC**: Role-based access control for extension features
- **Audit Logging**: Comprehensive access and usage logs
- **Compliance**: Meet regulatory requirements

## Migration and Compatibility

### How do I migrate from the old Plugin system?

**Migration Process:**
1. **Assessment**: Analyze existing plugins
2. **Planning**: Create migration timeline
3. **Conversion**: Use migration tools
4. **Testing**: Validate converted extensions
5. **Deployment**: Gradual rollout

Migration tools handle most conversion automatically.

### Are there breaking changes between versions?

We maintain backward compatibility:
- **API Versioning**: Multiple API versions supported
- **Deprecation Notices**: Advance warning of changes
- **Migration Guides**: Step-by-step upgrade instructions
- **Legacy Support**: Extended support for older versions

### Can I run old Plugins alongside new Extensions?

Yes, during the transition period:
- **Parallel Operation**: Plugins and extensions coexist
- **Gradual Migration**: Migrate at your own pace
- **Feature Parity**: Extensions provide all plugin functionality
- **Support Timeline**: Plugin support continues for 12 months

## Future Roadmap

### What new features are planned?

**Upcoming Features:**
- **AI-Powered Development**: AI assistance for extension creation
- **Visual Builder**: Drag-and-drop extension builder
- **Mobile Extensions**: Extensions for mobile apps
- **Edge Computing**: Extensions running at edge locations
- **Blockchain Integration**: Decentralized extension distribution

### How can I influence the Extension roadmap?

**Community Input:**
- **Feature Requests**: Submit ideas through forums
- **User Surveys**: Participate in regular feedback surveys
- **Beta Testing**: Join beta testing programs
- **Developer Advisory**: Join developer advisory board
- **Open Source**: Contribute to open source components

### Will Extensions work with future Kari versions?

Yes, we're committed to long-term compatibility:
- **Stable APIs**: Core APIs remain stable across versions
- **Migration Tools**: Automated migration for major updates
- **Deprecation Policy**: 12-month notice for breaking changes
- **LTS Versions**: Long-term support for enterprise customers

## Getting Started

### I'm new to Extensions. Where should I start?

**For Users:**
1. Browse the marketplace to see what's available
2. Install a simple extension like "Task Manager"
3. Explore extension settings and configuration
4. Join the community forums for tips and tricks

**For Developers:**
1. Read the [Development Guide](development-guide.md)
2. Follow the quick start tutorial
3. Study example extensions
4. Join developer community discussions

### What are some popular Extensions to try?

**Productivity:**
- Task Manager Pro
- Smart Calendar
- Note Taking Assistant
- Time Tracker

**Integrations:**
- Slack Connector
- GitHub Integration
- Google Workspace Sync
- Salesforce CRM

**Analytics:**
- Advanced Dashboard
- Performance Monitor
- User Analytics
- Custom Reports

### How do I stay updated on Extension news?

**Stay Informed:**
- **Newsletter**: Subscribe to extension newsletter
- **Blog**: Follow the Kari blog for updates
- **Social Media**: Follow @KariAI on Twitter
- **Community**: Join Discord and forums
- **Documentation**: Bookmark documentation site

---

*Have a question not covered here? Visit our [community forums](https://community.kari.ai) or [contact support](mailto:support@kari.ai).*