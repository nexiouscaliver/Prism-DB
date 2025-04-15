# PrismDB Setup Guide

This guide provides comprehensive instructions for setting up PrismDB, configuring it with sample data, and getting started with your first natural language queries.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Setting Up Sample Databases](#setting-up-sample-databases)
4. [Running Your First Queries](#running-your-first-queries)
5. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)

## Prerequisites

Before installing PrismDB, ensure your system meets the following requirements:

- **Python**: Version 3.9 or higher
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Database**: PostgreSQL 12 or higher
- **Cache**: Redis 6 or higher
- **API Key**: Google Gemini API key (get one at [Google AI Studio](https://ai.google.dev/))
- **Disk Space**: At least 500MB for the application and 100MB+ for each sample database

## Installation Steps

### 1. System Preparation

#### For Ubuntu/Debian:
```bash
# Update package lists
sudo apt update

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv git curl

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Start services
sudo systemctl start postgresql
sudo systemctl start redis
sudo systemctl enable postgresql
sudo systemctl enable redis
```

#### For macOS:
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python postgresql redis

# Start services
brew services start postgresql
brew services start redis
```

### 2. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/prismdb
cd prismdb
```

### 3. Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Database Setup

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Inside PostgreSQL prompt, create a database and user
CREATE DATABASE prismdb;
CREATE USER prismuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE prismdb TO prismuser;
\q
```

### 5. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your preferred editor
nano .env  # or vi .env, or any editor you prefer
```

Update the following fields in your `.env` file:

```
# API Keys
GOOGLE_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=postgresql://prismuser:your_secure_password@localhost:5432/prismdb

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=generate_a_random_string_here
JWT_SECRET_KEY=generate_another_random_string_here

# Application Settings
FLASK_ENV=development  # Change to 'production' for production use
PORT=5000
```

You can generate secure random strings for the SECRET_KEY and JWT_SECRET_KEY using:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Start the Application

```bash
python run.py
```

Your PrismDB instance should now be running at `http://localhost:5000`

## Setting Up Sample Databases

PrismDB becomes more useful when you connect it to databases with interesting data. Here's how to set up several sample databases that will showcase PrismDB's capabilities.

### Option 1: Pagila (DVD Rental Database)

A comprehensive database for a fictional DVD rental store with films, actors, customers, and more.

```bash
# Create a new database
sudo -u postgres psql -c "CREATE DATABASE pagila;"

# Download the sample database
wget https://raw.githubusercontent.com/neondatabase/postgres-sample-dbs/main/pagila.sql

# Load the data
psql -U postgres -d pagila -f pagila.sql
```

Add this configuration to your `.env` file:
```
DATABASE_1_URL=postgresql://postgres:your_postgres_password@localhost:5432/pagila
DATABASE_1_NAME=DVD Rental Store
DATABASE_1_TYPE=postgres
DATABASE_1_ENABLED=true
DATABASE_1_READONLY=false
```

### Option 2: Chinook (Digital Media Store)

A sample database for a digital media store, including artists, albums, tracks, and invoices.

```bash
# Create a new database
sudo -u postgres psql -c "CREATE DATABASE chinook;"

# Download the sample database
wget https://raw.githubusercontent.com/neondatabase/postgres-sample-dbs/main/chinook.sql

# Load the data
psql -U postgres -d chinook -f chinook.sql
```

Add this configuration to your `.env` file:
```
DATABASE_2_URL=postgresql://postgres:your_postgres_password@localhost:5432/chinook
DATABASE_2_NAME=Digital Media Store
DATABASE_2_TYPE=postgres
DATABASE_2_ENABLED=true
DATABASE_2_READONLY=false
```

### Option 3: Netflix Shows Database

A dataset containing information about Netflix movies and TV shows.

```bash
# Create a new database
sudo -u postgres psql -c "CREATE DATABASE netflix;"

# Download the sample database
wget https://raw.githubusercontent.com/neondatabase/postgres-sample-dbs/main/netflix.sql

# Load the data
psql -U postgres -d netflix -f netflix.sql
```

Add this configuration to your `.env` file:
```
DATABASE_3_URL=postgresql://postgres:your_postgres_password@localhost:5432/netflix
DATABASE_3_NAME=Netflix Content
DATABASE_3_TYPE=postgres
DATABASE_3_ENABLED=true
DATABASE_3_READONLY=false
```

After adding any new database configurations, restart PrismDB for the changes to take effect:

```bash
# Stop the current process (Ctrl+C) and restart
python run.py
```

## Running Your First Queries

Now that you have PrismDB up and running with sample data, let's try some queries:

### 1. Authentication

First, you need to get access tokens to use the API:

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo_password"}'
```

Save the returned `access_token` for subsequent requests.

### 2. List Available Databases (Prisms)

```bash
curl -X GET http://localhost:5000/api/v1/databases \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

This will show you all the databases connected to PrismDB.

### 3. Sample Natural Language Queries

Replace `DATABASE_ID` with the ID of one of your sample databases (e.g., "db_1" for the first additional database):

#### For the Pagila (DVD Rental) Database:

```bash
curl -X POST http://localhost:5000/api/v1/query/generate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the top 5 most rented movies?",
    "prism_id": "db_1",
    "max_tokens": 2048
  }'
```

#### For the Chinook (Digital Media Store) Database:

```bash
curl -X POST http://localhost:5000/api/v1/query/generate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the top 10 best-selling tracks",
    "prism_id": "db_2",
    "max_tokens": 2048
  }'
```

#### For the Netflix Database:

```bash
curl -X POST http://localhost:5000/api/v1/query/generate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many movies vs TV shows are in the database?",
    "prism_id": "db_3",
    "max_tokens": 2048
  }'
```

### 4. Execute a Generated SQL Query

Once you've generated a SQL query, you can execute it:

```bash
curl -X POST http://localhost:5000/api/v1/query/execute \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "YOUR_GENERATED_SQL",
    "prism_id": "db_1"
  }'
```

### 5. Generate Visualizations

To create a visualization from your query results:

```bash
curl -X POST http://localhost:5000/api/v1/visualize \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "YOUR_GENERATED_SQL",
    "prism_id": "db_1",
    "chart_type": "bar"  // Options: bar, line, pie, scatter
  }'
```

## Common Issues and Troubleshooting

### Database Connection Issues

**Symptom**: Error messages like "could not connect to server" or "connection refused"

**Solutions**:
1. Check if PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify your connection string in `.env` has the correct host, port, username, and password
3. Ensure the database exists: `sudo -u postgres psql -c "\l"`
4. Check that your PostgreSQL user has proper permissions

### Redis Connection Issues

**Symptom**: Warnings about Redis connectivity, token issues

**Solutions**:
1. Check if Redis is running: `sudo systemctl status redis`
2. Verify your Redis URL in `.env`
3. PrismDB can function without Redis, but performance will be affected

### API Key Issues

**Symptom**: Error messages related to the Google API key

**Solutions**:
1. Verify your API key is correctly set in the `.env` file
2. Ensure you've created an API key with proper permissions at [Google AI Studio](https://ai.google.dev/)
3. Check that you haven't exceeded your API quota

### Application Won't Start

**Symptom**: Error messages when running `python run.py`

**Solutions**:
1. Verify all dependencies are installed: `pip install -r requirements.txt`
2. Check Python version: `python --version` (should be 3.9+)
3. Make sure your `.env` file contains all required variables
4. Check for port conflicts: try changing the PORT in `.env`

### Authentication Issues

**Symptom**: "Unauthorized" or token-related errors

**Solutions**:
1. Get a fresh token by logging in again
2. Ensure you're using the access token with "Bearer " prefix
3. Check that your token hasn't expired (default expiry is 1 hour)

## Next Steps

Once you have PrismDB running successfully with sample data, you might want to:

1. **Connect your own database**: Add your production or development databases
2. **Customize agent behaviors**: Update agent configurations via the API
3. **Integrate with your applications**: Use the API to integrate with your existing apps
4. **Contributing**: Consider contributing to the project if you find it useful

For more detailed information, refer to the main [README.md](README.md) file. 