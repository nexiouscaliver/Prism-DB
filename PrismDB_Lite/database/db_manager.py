from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger("prismdb.database")

class DatabaseError(Exception):
    """Base class for all database-related errors."""
    pass

class ConnectionError(DatabaseError):
    """Error that occurs when a connection to the database fails."""
    pass

class ExecutionError(DatabaseError):
    """Error that occurs when a SQL query execution fails."""
    pass

class PostgresManager:
    """Manager for PostgreSQL database operations."""
    
    def __init__(self, connection_str, pool_size=5, max_overflow=10):
        """
        Initialize the PostgreSQL manager.
        
        Args:
            connection_str (str): Database connection string
            pool_size (int, optional): Size of the connection pool
            max_overflow (int, optional): Maximum number of overflow connections
        """
        try:
            self.engine = create_engine(
                connection_str, 
                pool_size=pool_size, 
                max_overflow=max_overflow
            )
            self.Session = sessionmaker(bind=self.engine)
            self.inspector = inspect(self.engine)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise ConnectionError(f"Failed to connect to database: {str(e)}")

    def execute_sql(self, sql, timeout=30, params=None):
        """
        Execute a SQL query and return the results.
        
        Args:
            sql (str): SQL query to execute
            timeout (int, optional): Query timeout in seconds
            params (dict, optional): Parameters for the SQL query
            
        Returns:
            dict: Results with columns and data
        """
        with self.Session() as session:
            try:
                # Set the timeout for the query
                session.execute(text(f"SET statement_timeout = {timeout * 1000}"))
                
                # Execute the query with parameters if provided
                if params:
                    result = session.execute(text(sql), params)
                else:
                    result = session.execute(text(sql))
                
                # Reset the timeout
                session.execute(text("SET statement_timeout = 0"))
                
                return {
                    "columns": list(result.keys()),
                    "data": [dict(row) for row in result.mappings()]
                }
            except SQLAlchemyError as e:
                logger.error(f"SQL Error: {str(e)}")
                raise ExecutionError(f"SQL Error: {str(e)}")
    
    def get_schema_metadata(self):
        """
        Get metadata about the database schema.
        
        Returns:
            dict: Schema metadata including tables, columns, and relationships
        """
        try:
            schema = {}
            
            # Get all tables
            tables = self.inspector.get_table_names()
            schema["tables"] = tables
            
            # Get columns for each table
            schema["columns"] = {}
            for table in tables:
                columns = self.inspector.get_columns(table)
                schema["columns"][table] = [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": col.get("default", None),
                    }
                    for col in columns
                ]
            
            # Get primary keys for each table
            schema["primary_keys"] = {}
            for table in tables:
                pk = self.inspector.get_pk_constraint(table)
                schema["primary_keys"][table] = pk.get("constrained_columns", [])
            
            # Get foreign keys for each table
            schema["foreign_keys"] = {}
            for table in tables:
                fks = self.inspector.get_foreign_keys(table)
                schema["foreign_keys"][table] = [
                    {
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"],
                    }
                    for fk in fks
                ]
            
            return schema
        except Exception as e:
            logger.error(f"Error retrieving schema metadata: {str(e)}")
            raise DatabaseError(f"Error retrieving schema metadata: {str(e)}")
    
    def test_connection(self):
        """
        Test the database connection.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            with self.Session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False 