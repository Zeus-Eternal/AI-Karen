# Multi-Database Setup Guide

AI-Karen supports multiple database backends to fit your infrastructure needs:
- **MySQL** (Default) - Popular open-source relational database
- **MongoDB** - NoSQL document database
- **Firestore** - Google Cloud NoSQL database

## Quick Start

### Interactive Setup (Recommended)

Run the interactive setup script:

```bash
python scripts/setup_database.py
```

This will guide you through:
1. Choosing your database type
2. Configuring connection parameters
3. Testing the connection
4. Saving configuration to `.env.database`

### Manual Configuration

1. Copy the template:
```bash
cp .env.multi-database.template .env.database
```

2. Edit `.env.database` and set `DB_TYPE` to your choice:
   - `mysql` (default)
   - `mongodb`
   - `firestore`

3. Configure database-specific settings (see sections below)

## Database-Specific Configuration

### MySQL (Default)

#### Requirements
```bash
pip install sqlalchemy pymysql aiomysql
```

#### Docker Setup
```bash
docker run -d --name mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=password \
  -e MYSQL_DATABASE=ai_karen \
  mysql:8.0
```

#### Environment Variables
```bash
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_karen
MYSQL_POOL_SIZE=10
MYSQL_MAX_OVERFLOW=20
```

#### Example Usage
```python
from ai_karen_engine.database import (
    load_multi_database_config,
    DatabaseConnectionFactory
)

# Load configuration
config = load_multi_database_config()

# Create factory
factory = DatabaseConnectionFactory(config)

# Get MySQL engine
engine = factory.get_mysql_engine()

# Use with session
with factory.get_session() as session:
    # Perform database operations
    result = session.execute("SELECT 1")
    print(result.scalar())
```

#### Async Usage
```python
async def example():
    config = load_multi_database_config()
    factory = DatabaseConnectionFactory(config)

    # Get async engine
    async_engine = factory.get_mysql_engine(async_mode=True)

    # Use async session
    async with factory.get_async_session() as session:
        result = await session.execute("SELECT 1")
        print(result.scalar())
```

---

### MongoDB (NoSQL)

#### Requirements
```bash
pip install pymongo motor
```

#### Docker Setup
```bash
docker run -d --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:7.0
```

#### Environment Variables
```bash
DB_TYPE=mongodb
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=your_password
MONGO_DATABASE=ai_karen
MONGO_AUTH_SOURCE=admin
MONGO_MAX_POOL_SIZE=100
```

#### Example Usage
```python
from ai_karen_engine.database import (
    load_multi_database_config,
    DatabaseConnectionFactory
)

# Load configuration
config = load_multi_database_config()

# Create factory
factory = DatabaseConnectionFactory(config)

# Get MongoDB client
client = factory.get_mongodb_client()

# Access database
db = client[config.mongodb_config.database]

# Insert document
collection = db["users"]
result = collection.insert_one({
    "name": "Alice",
    "email": "alice@example.com"
})

print(f"Inserted document ID: {result.inserted_id}")

# Find documents
for doc in collection.find({"name": "Alice"}):
    print(doc)
```

#### Async Usage
```python
async def example():
    config = load_multi_database_config()
    factory = DatabaseConnectionFactory(config)

    # Get async MongoDB client (Motor)
    client = factory.get_mongodb_client(async_mode=True)
    db = client[config.mongodb_config.database]

    # Insert document
    collection = db["users"]
    result = await collection.insert_one({
        "name": "Bob",
        "email": "bob@example.com"
    })

    print(f"Inserted document ID: {result.inserted_id}")

    # Find documents
    async for doc in collection.find({"name": "Bob"}):
        print(doc)
```

#### Using Session Context Manager
```python
config = load_multi_database_config()
factory = DatabaseConnectionFactory(config)

with factory.get_session() as db:
    # db is the database object
    collection = db["users"]
    collection.insert_one({"name": "Charlie"})
```

---

### Firestore (Google Cloud)

#### Requirements
```bash
pip install google-cloud-firestore
```

#### Environment Variables (Production)
```bash
DB_TYPE=firestore
FIRESTORE_PROJECT_ID=your-gcp-project-id
FIRESTORE_CREDENTIALS_PATH=/path/to/service-account.json
FIRESTORE_DATABASE_ID=(default)
```

#### Environment Variables (Emulator)
```bash
DB_TYPE=firestore
FIRESTORE_PROJECT_ID=demo-project
FIRESTORE_USE_EMULATOR=true
FIRESTORE_EMULATOR_HOST=localhost
FIRESTORE_EMULATOR_PORT=8080
```

#### Emulator Setup
```bash
# Install gcloud SDK first
gcloud emulators firestore start --host-port=localhost:8080
```

#### Example Usage
```python
from ai_karen_engine.database import (
    load_multi_database_config,
    DatabaseConnectionFactory
)

# Load configuration
config = load_multi_database_config()

# Create factory
factory = DatabaseConnectionFactory(config)

# Get Firestore client
client = factory.get_firestore_client()

# Create document
doc_ref = client.collection("users").document("alice")
doc_ref.set({
    "name": "Alice",
    "email": "alice@example.com",
    "created_at": firestore.SERVER_TIMESTAMP
})

print(f"Document created: {doc_ref.id}")

# Read document
doc = doc_ref.get()
if doc.exists:
    print(f"Document data: {doc.to_dict()}")

# Query collection
users_ref = client.collection("users")
for doc in users_ref.where("name", "==", "Alice").stream():
    print(f"{doc.id} => {doc.to_dict()}")
```

#### Using Session Context Manager
```python
config = load_multi_database_config()
factory = DatabaseConnectionFactory(config)

with factory.get_session() as client:
    # client is the Firestore client
    doc_ref = client.collection("users").document("bob")
    doc_ref.set({"name": "Bob"})
```

---

## Testing Connection

### Using the Setup Script
```bash
python scripts/setup_database.py
```
Follow prompts and choose "Yes" when asked to test connection.

### Using Python
```python
from ai_karen_engine.database import (
    load_multi_database_config,
    DatabaseConnectionFactory
)

# Load config
config = load_multi_database_config()

# Validate configuration
if not config.is_valid():
    print("Configuration errors:")
    for error in config.validation_errors:
        print(f"  - {error}")
    exit(1)

# Create factory
factory = DatabaseConnectionFactory(config)

# Test connection
import asyncio
result = asyncio.run(factory.test_connection())

if result["success"]:
    print(f"✓ Connected to {result['db_type']}")
    print(f"Details: {result['details']}")
else:
    print(f"✗ Connection failed: {result['error']}")
```

---

## Advanced Configuration

### Connection Pooling (MySQL)

```bash
# Adjust pool size based on your application load
MYSQL_POOL_SIZE=20           # Base pool size
MYSQL_MAX_OVERFLOW=50        # Additional connections allowed
MYSQL_POOL_TIMEOUT=30        # Timeout waiting for connection (seconds)
MYSQL_POOL_RECYCLE=3600      # Recycle connections after 1 hour
```

### SSL/TLS (MySQL)

```bash
MYSQL_SSL_CA=/path/to/ca-cert.pem
MYSQL_SSL_CERT=/path/to/client-cert.pem
MYSQL_SSL_KEY=/path/to/client-key.pem
```

### Replica Set (MongoDB)

```bash
MONGO_REPLICA_SET=rs0
MONGO_HOST=mongo1.example.com:27017,mongo2.example.com:27017
```

### Multiple Databases (Firestore)

```bash
# Use a non-default database
FIRESTORE_DATABASE_ID=my-custom-db

# Add collection prefix for multi-tenancy
FIRESTORE_COLLECTION_PREFIX=tenant1_
```

---

## Migration from PostgreSQL

If you're currently using PostgreSQL and want to switch:

1. **Keep existing PostgreSQL configuration** - The new multi-database system works alongside the existing PostgreSQL setup.

2. **Gradual migration** - You can use both systems simultaneously:
   ```python
   # Old PostgreSQL system
   from ai_karen_engine.database import MultiTenantPostgresClient
   pg_client = MultiTenantPostgresClient()

   # New multi-database system
   from ai_karen_engine.database import DatabaseConnectionFactory, load_multi_database_config
   config = load_multi_database_config()
   factory = DatabaseConnectionFactory(config)
   ```

3. **Data migration** - Create migration scripts specific to your data:
   - Export data from PostgreSQL
   - Transform to target database schema
   - Import to new database

---

## Best Practices

### 1. Use Environment Variables
Never hardcode credentials in code. Always use environment variables or secrets management.

### 2. Connection Pooling
Configure appropriate pool sizes based on your application load:
- **Low traffic**: pool_size=5-10
- **Medium traffic**: pool_size=10-20
- **High traffic**: pool_size=20-50

### 3. Error Handling
Always handle connection errors gracefully:
```python
try:
    config = load_multi_database_config()
    factory = DatabaseConnectionFactory(config)
except Exception as e:
    logger.error(f"Database setup failed: {e}")
    # Implement fallback or retry logic
```

### 4. Resource Cleanup
Always close connections when done:
```python
factory = DatabaseConnectionFactory(config)
try:
    # Use database
    pass
finally:
    factory.close()
```

Or use context manager:
```python
with DatabaseConnectionFactory(config) as factory:
    # Use database
    pass
# Automatically closed
```

### 5. Health Checks
Implement database health checks in your application:
```python
async def health_check():
    factory = DatabaseConnectionFactory(config)
    result = await factory.test_connection()
    return result["success"]
```

---

## Troubleshooting

### MySQL Connection Issues

**Error: "Access denied for user"**
```bash
# Check credentials
MYSQL_USER=correct_username
MYSQL_PASSWORD=correct_password

# Grant permissions in MySQL
GRANT ALL PRIVILEGES ON ai_karen.* TO 'username'@'%';
FLUSH PRIVILEGES;
```

**Error: "Can't connect to MySQL server"**
- Ensure MySQL is running: `docker ps` or `systemctl status mysql`
- Check firewall: MySQL uses port 3306
- Verify host/port configuration

### MongoDB Connection Issues

**Error: "Authentication failed"**
```bash
# Ensure auth source is correct
MONGO_AUTH_SOURCE=admin

# Create user in MongoDB
use admin
db.createUser({
  user: "username",
  pwd: "password",
  roles: [{role: "readWrite", db: "ai_karen"}]
})
```

**Error: "Connection timeout"**
- Increase timeout: `MONGO_CONNECT_TIMEOUT=30000`
- Check network connectivity
- Verify MongoDB is listening: `netstat -an | grep 27017`

### Firestore Connection Issues

**Error: "Project not found"**
- Verify project ID: `gcloud projects list`
- Ensure Firestore is enabled: `gcloud services enable firestore.googleapis.com`

**Error: "Permission denied"**
- Check service account permissions
- Required roles: `roles/datastore.user` or `roles/datastore.owner`

**Emulator not connecting**
```bash
# Start emulator
gcloud emulators firestore start --host-port=localhost:8080

# Set environment variable
export FIRESTORE_EMULATOR_HOST=localhost:8080
```

---

## Performance Tuning

### MySQL
```bash
# Production settings
MYSQL_POOL_SIZE=50
MYSQL_MAX_OVERFLOW=100
MYSQL_POOL_RECYCLE=3600
MYSQL_POOL_PRE_PING=true
```

### MongoDB
```bash
# Production settings
MONGO_MAX_POOL_SIZE=200
MONGO_MIN_POOL_SIZE=20
MONGO_SERVER_SELECTION_TIMEOUT=30000
MONGO_CONNECT_TIMEOUT=10000
```

### Firestore
```bash
# Optimize for high throughput
FIRESTORE_TIMEOUT=120.0

# Use collection groups for cross-collection queries
# Use composite indexes for complex queries
```

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `tail -f logs/database.log`
3. Open an issue on GitHub with:
   - Database type
   - Configuration (sanitized)
   - Error messages
   - Steps to reproduce

---

## Examples

See working examples in:
- `examples/database_mysql.py` - MySQL examples
- `examples/database_mongodb.py` - MongoDB examples
- `examples/database_firestore.py` - Firestore examples
