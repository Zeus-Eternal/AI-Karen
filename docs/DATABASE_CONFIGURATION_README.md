# Multi-Database Configuration System

This document provides a quick overview of the multi-database support system in AI-Karen.

## Overview

AI-Karen now supports multiple database backends:
- **MySQL** (Default) - Relational database, widely supported
- **MongoDB** - NoSQL document database for flexible schemas
- **Firestore** - Google Cloud NoSQL database with real-time capabilities

## Quick Start

### 1. Run Interactive Setup

```bash
python scripts/setup_database.py
```

This interactive wizard will:
- Guide you through database selection
- Configure connection parameters
- Test the connection
- Save configuration to `.env.database`

### 2. Install Dependencies

Based on your database choice:

```bash
# MySQL (Default)
pip install sqlalchemy pymysql aiomysql

# MongoDB
pip install pymongo motor

# Firestore
pip install google-cloud-firestore

# Or install all
pip install -r requirements-database.txt
```

### 3. Use in Your Application

```python
from ai_karen_engine.database import (
    load_multi_database_config,
    DatabaseConnectionFactory
)

# Load configuration from environment
config = load_multi_database_config()

# Create database connection factory
factory = DatabaseConnectionFactory(config)

# Get database connection (auto-detects type)
db = factory.get_database()

# Or use with context manager
with factory.get_session() as session:
    # Perform database operations
    pass
```

## Configuration Files

- **`.env.multi-database.template`** - Template with all configuration options
- **`DATABASE_SETUP.md`** - Comprehensive setup guide with examples
- **`requirements-database.txt`** - Python dependencies for all database types

## File Structure

```
AI-Karen/
├── .env.multi-database.template    # Configuration template
├── .env.database                   # Your configuration (created by setup)
├── requirements-database.txt       # Database dependencies
├── DATABASE_CONFIGURATION_README.md # This file
├── docs/
│   └── DATABASE_SETUP.md          # Detailed setup guide
├── scripts/
│   └── setup_database.py          # Interactive setup wizard
└── src/ai_karen_engine/database/
    ├── multi_db_config.py         # Database configuration classes
    ├── multi_db_factory.py        # Connection factory
    └── __init__.py                # Exports all database modules
```

## Database Type Selection

Set the `DB_TYPE` environment variable to choose your database:

```bash
# MySQL (Default)
DB_TYPE=mysql

# MongoDB
DB_TYPE=mongodb

# Firestore
DB_TYPE=firestore
```

## Features

### ✓ Multiple Database Support
- MySQL, MongoDB, Firestore
- Easy switching between databases
- Consistent API across all types

### ✓ Connection Management
- Connection pooling (MySQL, MongoDB)
- Automatic reconnection
- Health checks and monitoring

### ✓ Configuration Validation
- Environment variable validation
- Clear error messages
- Sensible defaults

### ✓ Production Ready
- SSL/TLS support
- Connection timeouts
- Resource cleanup
- Error handling

### ✓ Developer Friendly
- Interactive setup wizard
- Comprehensive documentation
- Type hints and docstrings
- Example code

## Quick Examples

### MySQL

```bash
# Configuration
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=ai_karen
```

```python
# Usage
config = load_multi_database_config()
factory = DatabaseConnectionFactory(config)
engine = factory.get_mysql_engine()
```

### MongoDB

```bash
# Configuration
DB_TYPE=mongodb
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=password
MONGO_DATABASE=ai_karen
```

```python
# Usage
config = load_multi_database_config()
factory = DatabaseConnectionFactory(config)
client = factory.get_mongodb_client()
db = client[config.mongodb_config.database]
collection = db["users"]
```

### Firestore

```bash
# Configuration
DB_TYPE=firestore
FIRESTORE_PROJECT_ID=my-project
FIRESTORE_CREDENTIALS_PATH=/path/to/service-account.json
```

```python
# Usage
config = load_multi_database_config()
factory = DatabaseConnectionFactory(config)
client = factory.get_firestore_client()
doc_ref = client.collection("users").document("user1")
```

## Documentation

- **Full Setup Guide**: See [`docs/DATABASE_SETUP.md`](docs/DATABASE_SETUP.md)
- **Configuration Template**: See [`.env.multi-database.template`](.env.multi-database.template)
- **Setup Script**: Run `python scripts/setup_database.py`

## Migration from PostgreSQL

The new multi-database system works **alongside** the existing PostgreSQL setup. You can:

1. Use both systems simultaneously
2. Gradually migrate data and code
3. Switch between databases easily

No breaking changes to existing PostgreSQL code.

## Support

### Common Issues

**Connection Failed**
- Check database is running
- Verify host, port, credentials
- Check firewall settings
- Review error logs

**Import Errors**
- Install required dependencies: `pip install -r requirements-database.txt`
- Verify Python version (3.8+)

**Configuration Errors**
- Use the setup wizard: `python scripts/setup_database.py`
- Check environment variables are set
- Validate configuration: See [DATABASE_SETUP.md](docs/DATABASE_SETUP.md)

### Getting Help

1. Check [DATABASE_SETUP.md](docs/DATABASE_SETUP.md) troubleshooting section
2. Review configuration template: `.env.multi-database.template`
3. Run setup wizard with verbose output
4. Open GitHub issue with details

## What's Next?

After setting up your database:

1. **Test Connection**: Use `python scripts/setup_database.py` or the test examples
2. **Configure Application**: Update your application to use the new configuration
3. **Run Migrations**: Apply any necessary database migrations
4. **Monitor Performance**: Use built-in health checks and monitoring

## Key Benefits

- **Flexibility**: Choose the best database for your needs
- **Simplicity**: One configuration system for all databases
- **Reliability**: Production-tested connection management
- **Developer Experience**: Interactive setup, clear documentation

---

**Ready to get started?** Run:

```bash
python scripts/setup_database.py
```

For detailed information, see [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md).
