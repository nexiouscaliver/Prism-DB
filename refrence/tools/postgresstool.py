from agno.tools.postgres import PostgresTools
import psycopg2
from agents.db_agent import get_db_agent  # Import the db_agent creator function

def get_database_names():
    # Connect to the PostgreSQL server
    conn = psycopg2.connect(
        host="localhost",
        port=5532,
        user="prismdb",
        password="prismdb",
        dbname="postgres"  # connecting to postgres database by default
    )
    
    # Create a cursor object
    cur = conn.cursor()
    
    # Execute a query to get all databases
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    
    # Fetch all rows from the executed query
    rows = cur.fetchall()
    
    # Close the cursor and connection
    cur.close()
    conn.close()
    
    # Extract database names from the rows
    database_names = [row[0] for row in rows]
    
    return database_names

database_list = get_database_names()
unwanted_databases = ["postgres", "agent", "prismdb", 'externalsources']

database_list = [db for db in database_list if db not in unwanted_databases]
print(f"Found databases: {database_list}")

# Create database tools for internal use only (not to be exposed directly to agents)
postgres_tools = []
postgres_tool_names = []
db_agents = []  # This will hold our database-specific agents

for db in database_list:
    # Create a tool for each database - these tools will be used by db-specific agents only
    db_tool = PostgresTools(
        host="localhost",
        port=5532,
        db_name=db,
        user="prismdb",
        password="prismdb",
        run_queries=True,
        inspect_queries=True,
        summarize_tables=True,
        export_tables=True,
        table_schema="public"
    )
    postgres_tools.append(db_tool)
    
    # Create a valid agent name that follows OpenAI function calling requirements
    sanitized_db_name = db.replace(" ", "_").replace("-", "_")
    agent_name = f"{sanitized_db_name}_database_Postgres_Agent"
    postgres_tool_names.append(agent_name)

print(f"Created {len(postgres_tools)} PostgreSQL tools")

# Note: The actual db_agents will be created in prismagent.py using these tools
# This allows us to initialize the model properly before creating agents