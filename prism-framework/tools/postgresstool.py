from agno.tools.postgres import PostgresTools
import psycopg2

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
print(database_list)

postgres_tools = []
postgres_tool_names = []

for db in database_list:
    postgres_tools.append(PostgresTools(
        # name=f'{db} database Postgres Tool',
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
    ))
    postgres_tool_names.append(f'{db} database Postgres Agent')

print(postgres_tools)