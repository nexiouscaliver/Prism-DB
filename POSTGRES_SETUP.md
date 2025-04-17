# PostgreSQL Database Setup and Configuration

This guide explains how to set up and configure PostgreSQL databases with PrismDB, including dynamic database connection and schema extraction.

## Overview

PrismDB now supports PostgreSQL as the primary database system. The architecture includes:

1. A default PostgreSQL database (`prismdb`) that stores metadata about other databases
2. Support for multiple additional PostgreSQL databases
3. Dynamic database selection for queries
4. Schema extraction from additional databases to the default database

## Configuration

### 1. Environment Configuration

To configure PostgreSQL databases, you need to set up your `.env` file with the appropriate database connection strings. Here's an example:

```
# Default database - This is the main PrismDB database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/prismdb

# Additional databases
DATABASE_1_URL=postgresql://postgres:postgres@localhost:5432/employees
DATABASE_1_NAME=Employees Database
DATABASE_1_TYPE=postgres
DATABASE_1_ENABLED=true
DATABASE_1_READONLY=false

DATABASE_2_URL=postgresql://postgres:postgres@localhost:5432/sales
DATABASE_2_NAME=Sales Database
DATABASE_2_TYPE=postgres
DATABASE_2_ENABLED=true
DATABASE_2_READONLY=false
```

You can add as many databases as needed by incrementing the number in the environment variable names.

### 2. Default Database Setup

The default `prismdb` database needs to be created before starting the application:

```bash
# Create the default database
createdb -U postgres prismdb

# If you want to initialize with schema tables immediately:
psql -U postgres -d prismdb -c "
CREATE TABLE IF NOT EXISTS database_metadata (
    db_id VARCHAR(50) PRIMARY KEY,
    db_name VARCHAR(100) NOT NULL,
    db_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS table_metadata (
    id SERIAL PRIMARY KEY,
    db_id VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    CONSTRAINT table_metadata_unique UNIQUE (db_id, table_name),
    FOREIGN KEY (db_id) REFERENCES database_metadata(db_id)
);

CREATE TABLE IF NOT EXISTS column_metadata (
    id SERIAL PRIMARY KEY,
    db_id VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    is_nullable BOOLEAN NOT NULL,
    column_default TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    CONSTRAINT column_metadata_unique UNIQUE (db_id, table_name, column_name),
    FOREIGN KEY (db_id, table_name) REFERENCES table_metadata(db_id, table_name)
);

CREATE TABLE IF NOT EXISTS primary_key_metadata (
    id SERIAL PRIMARY KEY,
    db_id VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    CONSTRAINT pk_metadata_unique UNIQUE (db_id, table_name, column_name),
    FOREIGN KEY (db_id, table_name, column_name) REFERENCES column_metadata(db_id, table_name, column_name)
);

CREATE TABLE IF NOT EXISTS foreign_key_metadata (
    id SERIAL PRIMARY KEY,
    db_id VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    referenced_table VARCHAR(100) NOT NULL,
    referenced_column VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    CONSTRAINT fk_metadata_unique UNIQUE (db_id, table_name, column_name, referenced_table, referenced_column),
    FOREIGN KEY (db_id, table_name, column_name) REFERENCES column_metadata(db_id, table_name, column_name)
);
"
```

## API Endpoints

### Database Management

PrismDB provides several API endpoints for managing databases:

- **List Databases**: `GET /api/v1/databases`
- **Get Database Schema**: `GET /api/v1/databases/{db_id}/schema`
- **Extract Schema**: `POST /api/v1/databases/{db_id}/extract-schema`
- **Extract All Schemas**: `POST /api/v1/databases/extract-all-schemas`
- **Get Merged Schema**: `GET /api/v1/databases/merged-schema`
- **Select Database**: `POST /api/v1/databases/select` (with JSON body: `{"db_id": "database_id"}`)
- **Get Selected Database**: `GET /api/v1/databases/selected`

### Schema Extraction

Schema extraction is the process of retrieving schema information from additional databases and storing it in the default database. This allows PrismDB to have a centralized repository of schema information for all connected databases.

To extract the schema from all databases after starting the application:

```bash
curl -X POST http://localhost:5000/api/v1/databases/extract-all-schemas \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

This will populate the metadata tables in the default database with information about all connected databases.

## Dynamic Database Selection

PrismDB supports dynamically selecting a database for operations. When executing a query, you can specify which database to use:

```bash
curl -X POST http://localhost:5000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM employees LIMIT 10",
    "database_id": "db_1"
  }'
```

If no database_id is provided, the default database is used.

## Multi-Database Queries

To execute the same query across all databases:

```bash
curl -X POST http://localhost:5000/api/v1/query/execute-all \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT COUNT(*) FROM users"
  }'
```

This will return results from all databases that have a `users` table.

## Programmatic Usage

You can also use the `DatabaseService` class programmatically in your code:

```python
from services.database_service import DatabaseService

# Initialize the service
db_service = DatabaseService()

# Get a list of available databases
databases = db_service.get_available_databases()

# Execute a query against a specific database
result = await db_service.execute_query(
    "SELECT * FROM users LIMIT 10", 
    db_id="db_1"
)

# Extract schema information to the default database
extraction_result = await db_service.extract_schema_to_default("db_1")

# Get merged schema information
schema = await db_service.get_merged_schema_from_default()
```

## Troubleshooting

- **Connection Issues**: Ensure your PostgreSQL server is running and accessible using the connection strings in your `.env` file.
- **Permission Issues**: Make sure the database users have the appropriate permissions to read schema information.
- **Schema Extraction Failures**: Check that the PostgreSQL user has permission to access system catalogs.

For additional help, please consult the PostgreSQL documentation or open an issue on the PrismDB GitHub repository. 