# PrismDB 🗄️🤖📂

**Transform Natural Language into Data Insights, Like Light into a Rainbow**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/AI-Gemini%202.0-brightgreen)](https://ai.google.dev/)

---

## **Why PrismDB?**  
Data analysts shouldn't need to wrestle with query syntax or juggle multiple tools. **PrismDB** is a multi-agent framework that acts as a *contextual prism* for databases, transforming raw natural language queries into structured insights, visual reports, and actionable diagrams.  

Just as a prism splits light into vibrant colors, PrismDB:  
1. **Refracts** ambiguous user intents into precise queries.  
2. **Harmonizes** context from databases, schemas, and user history.  
3. **Synthesizes** outputs like charts, summaries, and dashboards.  

---

## **Features**  
✨ **Natural Language Interface** – "Show monthly sales trends for APAC region" instead of SQL.  
✨ **Multi-Model Database Support** – Connect to PostgreSQL, MySQL, and other SQL databases.  
✨ **Context-Aware Agents** – Understands schemas, user behavior, and domain semantics.  
✨ **Parallel Processing** – Agent swarms generate reports **5x faster** than manual workflows.  
✨ **Low-Code Integration** – REST API and Python SDK.  
✨ **Visualization Engine** - Automatically generates charts and visualizations from query results.

---

## **How It Works**  
```mermaid
graph LR
  A[Natural Language Input] --> B(NLU Agent)
  B --> C{{PrismDB Framework}}
  C --> D[Schema Lens]
  C --> E[Query Forge]
  C --> F[Viz Engine]
  D --> G[(Database)]
  E --> G
  F --> H[Output Spectrum]
  G --> H
  H --> I[📈 Charts]
  H --> J[📊 Reports]
  H --> K[📂 Structured Data]
```

1. **Input**: Users describe tasks in plain language.  
2. **Prism Layers**:  
   - **NLU Agent**: Parses intent and entities.  
   - **Schema Lens**: Maps queries to database structures.  
   - **Query Forge**: Generates optimized SQL queries.  
   - **Viz Engine**: Renders charts, graphs, or markdown reports.  
3. **Output**: Clean data, visualizations, or shareable documents.  

---

## **Architecture Overview**

PrismDB uses a multi-agent architecture powered by multiple LLM providers including Google's Gemini and OpenAI's models:

### Agent System
* **Base Agent**: Foundation class for all specialized agents
* **Schema Agent**: Extracts and understands database schema information
* **Query Builder Agent**: Generates optimized SQL queries based on natural language and schema
* **Read Agent**: Handles data retrieval operations safely and efficiently
* **Write Agent**: Manages data modification operations with proper validations
* **Admin Agent**: Handles database administration tasks
* **Orchestrator**: Coordinates all agents to process requests end-to-end

### Components
* **Backend**: Python-based API server handling request processing and agent orchestration
* **Frontend**: Next.js application providing the user interface and visualization capabilities
* **Agent UI**: Specialized chat interface for direct interaction with database agents
* **API Layer**: RESTful API endpoints for integration with external systems

### Services
* **Database Service**: Manages connections to multiple databases
* **Execution Service**: Executes SQL queries securely and efficiently
* **Visualization Service**: Renders charts and visualizations
* **Authentication Service**: Handles user authentication and authorization

### Security & Authentication
* **JWT-based authentication**: Secure access with fine-grained permissions
* **Role-based access control**: Control which databases users can access

---

## **Project Structure**

```
prismdb/
├── api/                 # API endpoints and routing
├── app/                 # Core application logic
├── frontend/            # Main user interface (Next.js)
├── prism-framework/     # Agent framework
│   ├── agent-ui/        # Specialized chat interface
│   ├── agents/          # Agent implementations
│   │   ├── prismagent.py   # Main orchestration agent
│   │   ├── schema_agent.py # Schema handling agent
│   │   └── ...
│   └── tools/           # Agent tools and utilities
├── sampledata/          # Example datasets for demonstration
└── requirements.txt     # Python dependencies
```

---

## **Step-by-Step Installation Guide**

### Prerequisites
- Python 3.9+
- PostgreSQL (for database storage)
- Node.js 18+ (for frontend and agent-ui)
- Google Gemini API key or OpenAI API key

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/prismdb
cd prismdb
```

### 2. Set Up a Virtual Environment
```bash
# On Linux/macOS
python3 -m venv prism.venv
source prism.venv/bin/activate

# On Windows
python -m venv prism.venv
prism.venv\Scripts\activate
```

### 3. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file and edit it with your settings:
```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:
```
# Required API keys
GOOGLE_API_KEY=your_google_api_key_here
# Or for OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Database configuration
DATABASE_URL=postgresql://username:password@localhost:5432/prismdb

# Application configuration
SECRET_KEY=your_secure_random_string_here
JWT_SECRET_KEY=another_secure_random_string_here
```

### 5. Set Up the Database
Install PostgreSQL:
```bash
# On Ubuntu
sudo apt update
sudo apt install postgresql postgresql-contrib

# On macOS with Homebrew
brew install postgresql
brew services start postgresql
```

Create a database for PrismDB:
```bash
sudo -u postgres psql
```

In the PostgreSQL prompt:
```sql
CREATE DATABASE prismdb;
CREATE USER prismuser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE prismdb TO prismuser;
\q
```

### 6. Install Frontend Dependencies

```bash
# For the main frontend
cd frontend
npm install
# or with pnpm
pnpm install

# For the agent UI
cd ../prism-framework/agent-ui
npm install
# or with pnpm
pnpm install
```

### 7. Start the Application

Start the backend:
```bash
# From the project root
python app/main.py
```

Start the frontend:
```bash
# In the frontend directory
cd frontend
npm run dev
# or with pnpm
pnpm dev
```

Start the agent UI (optional):
```bash
# In the agent-ui directory
cd prism-framework/agent-ui
npm run dev
# or with pnpm
pnpm dev
```

The main application will be running at `http://localhost:8000`
The agent UI will be running at `http://localhost:3000`

---

## **Setting Up With Sample Data**

To quickly get started with PrismDB and test its capabilities, you can use sample databases:

### Option 1: Pagila - DVD Rental Database

This is a sample database for a fictional DVD rental store with films, actors, customers, and rentals.

1. **Download the Pagila SQL file**:
```bash
wget https://raw.githubusercontent.com/neondatabase/postgres-sample-dbs/main/pagila.sql
```

2. **Create a database for Pagila**:
```bash
sudo -u postgres psql -c "CREATE DATABASE pagila;"
```

3. **Load the sample data**:
```bash
psql -U postgres -d pagila -f pagila.sql
```

4. **Configure PrismDB to use this database**:
   Add this to your `.env` file:
```
DATABASE_1_URL=postgresql://postgres:your_password@localhost:5432/pagila
DATABASE_1_NAME=DVD Rental Database
DATABASE_1_TYPE=postgres
DATABASE_1_ENABLED=true
DATABASE_1_READONLY=false
```

5. **Example Queries to Try**:
   - "Show me the top 5 most rented movies"
   - "List all customers who spent more than $150"
   - "What are the most popular film categories?"
   - "Show the rental history for customer Jane Doe"

### Option 2: Chinook - Digital Media Store

A sample database for a digital media store with artists, albums, tracks, and sales.

1. **Download the Chinook SQL file**:
```bash
wget https://raw.githubusercontent.com/neondatabase/postgres-sample-dbs/main/chinook.sql
```

2. **Create a database for Chinook**:
```bash
sudo -u postgres psql -c "CREATE DATABASE chinook;"
```

3. **Load the sample data**:
```bash
psql -U postgres -d chinook -f chinook.sql
```

4. **Configure PrismDB to use this database**:
   Add this to your `.env` file:
```
DATABASE_2_URL=postgresql://postgres:your_password@localhost:5432/chinook
DATABASE_2_NAME=Digital Media Store
DATABASE_2_TYPE=postgres
DATABASE_2_ENABLED=true
DATABASE_2_READONLY=false
```

5. **Example Queries to Try**:
   - "Show total sales by country"
   - "Who are the top 10 best-selling artists?"
   - "Which tracks have never been purchased?"
   - "List all albums by rock artists"

### Option 3: Netflix Dataset

A dataset with information about Netflix shows and movies.

1. **Download the Netflix SQL file**:
```bash
wget https://raw.githubusercontent.com/neondatabase/postgres-sample-dbs/main/netflix.sql
```

2. **Create a database for Netflix data**:
```bash
sudo -u postgres psql -c "CREATE DATABASE netflix;"
```

3. **Load the sample data**:
```bash
psql -U postgres -d netflix -f netflix.sql
```

4. **Configure PrismDB to use this database**:
   Add this to your `.env` file:
```
DATABASE_3_URL=postgresql://postgres:your_password@localhost:5432/netflix
DATABASE_3_NAME=Netflix Content Database
DATABASE_3_TYPE=postgres
DATABASE_3_ENABLED=true
DATABASE_3_READONLY=false
```

5. **Example Queries to Try**:
   - "Show the distribution of content by rating"
   - "Which directors have the most titles?"
   - "What is the trend of Netflix content over the years?"
   - "Compare TV shows vs movies by country of origin"

---

## **Usage Guide**

### Authentication

1. **Register a User**
   - Not implemented in demo version (uses hardcoded demo/demo_password credentials)

2. **Login to Get JWT Tokens**
   ```bash
   curl -X POST http://localhost:5000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "demo", "password": "demo_password"}'
   ```

   The response will contain:
   ```json
   {
     "access_token": "...",
     "refresh_token": "...",
     "expires_at": 1715183836,
     "token_type": "Bearer"
   }
   ```

3. **Use the Access Token for API Requests**
   ```bash
   curl -X GET http://localhost:5000/api/v1/agents \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Natural Language Queries

1. **Generate SQL from Natural Language**
   ```bash
   curl -X POST http://localhost:5000/api/v1/query/generate \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Show me the top 5 customers by sales in 2023",
       "prism_id": "sales_db",
       "max_tokens": 2048
     }'
   ```

   The response will contain:
   ```json
   {
     "status": "success",
     "result": {
       "sql": "SELECT c.customer_name, SUM(s.sales_amount) AS total_sales FROM customers c JOIN sales s ON c.customer_id = s.customer_id WHERE EXTRACT(YEAR FROM s.sale_date) = 2023 GROUP BY c.customer_name ORDER BY total_sales DESC LIMIT 5",
       "explanation": "This query finds the top 5 customers by total sales in 2023...",
       "confidence": 0.95,
       "intent": "get_top_customers",
       "entities": [{"type": "time_period", "value": "2023"}, {"type": "limit", "value": 5}],
       "visualization": {
         "chart_type": "bar",
         "chart_data": { ... },
         "chart_options": { ... }
       }
     }
   }
   ```

2. **Execute a Generated SQL Query**
   ```bash
   curl -X POST http://localhost:5000/api/v1/query/execute \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "sql": "SELECT customer_name, SUM(sales_amount) AS total_sales FROM customers JOIN sales USING (customer_id) WHERE EXTRACT(YEAR FROM sale_date) = 2023 GROUP BY customer_name ORDER BY total_sales DESC LIMIT 5",
       "prism_id": "sales_db"
     }'
   ```

### Managing Agents

1. **List Available Agents**
   ```bash
   curl -X GET http://localhost:5000/api/v1/agents \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

2. **Get Agent Configuration**
   ```bash
   curl -X GET http://localhost:5000/api/v1/agents/nlu \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

3. **Update Agent Configuration**
   ```bash
   curl -X POST http://localhost:5000/api/v1/agents/nlu/config \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "config": {
         "temperature": 0.3,
         "model": "gemini-2.0-flash-exp"
       }
     }'
   ```

### **Testing Guide**

PrismDB includes a comprehensive test suite using pytest to ensure code quality and functionality.

#### Running Tests

1. **Setup Test Environment**
   ```bash
   # Make sure you have all dependencies installed
   pip install -r requirements.txt
   
   # Set PYTHONPATH to include the project root
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

2. **Run All Tests**
   ```bash
   pytest
   ```

3. **Run Specific Test Categories**
   ```bash
   # Run only unit tests
   pytest tests/unit/
   
   # Run only integration tests
   pytest tests/integration/
   ```

4. **Generate Test Coverage Report**
   ```bash
   # Generate coverage report
   pytest --cov=.
   
   # Generate detailed HTML coverage report
   pytest --cov=. --cov-report=html
   ```

#### Test Structure

The test suite is organized into:
- **Unit Tests**: Test individual components in isolation 
- **Integration Tests**: Test components working together
- **Fixtures**: Reusable test components defined in `tests/conftest.py`

For more details on writing and running tests, see the [tests/README.md](tests/README.md) file.

---

## JWT Claim Structure for Prism Access Control

The PrismDB authentication system uses JWT (JSON Web Tokens) with a carefully designed claim structure to implement fine-grained access control to database resources (prisms).

### Token Types

PrismDB uses two types of tokens:

1. **Access Tokens**: Short-lived tokens (1 hour expiry) that grant access to API endpoints
2. **Refresh Tokens**: Long-lived tokens (7 days expiry) used only to obtain new access tokens

### Claim Structure

```json
{
  "sub": "user_123",           // User ID (subject)
  "prisms": [                  // Array of database access permissions
    "sales_db::read",          // Format: "db_name::permission"
    "inventory_db::write"      // Permissions: read, write, admin
  ],
  "role": "analyst",           // User role (analyst, admin, etc.)
  "type": "access",            // Token type (access or refresh)
  "jti": "unique_token_id",    // Unique token identifier (for revocation)
  "exp": 1715187436,           // Expiration timestamp
  "iat": 1715183836,           // Issued at timestamp
  "nbf": 1715183836            // Not valid before timestamp
}
```

---

## **Troubleshooting**

### Redis Connection Issues
- Make sure Redis is running with `redis-cli ping` (should return PONG)
- Check your Redis URL in the .env file
- The application has circuit breakers for Redis, so it will continue to function without Redis

### Database Connection Issues
- Verify PostgreSQL is running with `pg_isready`
- Check your DATABASE_URL in the .env file
- Make sure the database and user exist with the correct permissions

### API Key Issues
- Ensure your Google API key is correctly set in the .env file
- Test the key with a simple request to the Google Generative AI API

### JWT Token Issues
- If you're getting authentication errors, try logging in again to get a fresh token
- Make sure you're setting the Authorization header correctly

### Common Error Codes

PrismDB uses standardized error codes to help troubleshoot issues:

- `connection_error`: Unable to connect to the specified database
- `query_syntax_error`: The generated SQL has syntax errors
- `nl_parsing_error`: The NLU agent couldn't understand the natural language query
- `chart_generation_error`: Unable to generate a visualization

---

## **Contributing**

We welcome contributions to PrismDB! Here are ways you can help:

1. **Report bugs** by opening an issue
2. **Suggest new features** through the issues page
3. **Submit pull requests** with bug fixes or enhancements
4. **Improve documentation**

Please follow our coding standards and include tests with your submissions.

---

## **License**  
Distributed under the MIT License. See [LICENSE](LICENSE) for details.  

---

**PrismDB** isn't just a tool—it's a **new lens for data interaction**.  
Let's make databases as intuitive as a conversation. ⚡️

