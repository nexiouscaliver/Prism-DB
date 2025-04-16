"""
SchemaAgent for PrismDB.

This agent is responsible for providing schema information for database contexts.
It retrieves table structures, relationships, and other metadata needed for SQL generation.
"""
from typing import Dict, Any, List

from agents.base import PrismAgent


class SchemaAgent(PrismAgent):
    """Agent for retrieving and analyzing database schema information.
    
    This agent is responsible for providing contextual information about
    database schemas, including tables, columns, relationships, and constraints.
    This information is used by the QueryAgent to generate accurate SQL.
    """
    
    def __init__(self):
        """Initialize the SchemaAgent with appropriate tools and instructions."""
        super().__init__(
            name="SchemaAgent",
            system_prompt="""You are a SchemaAgent responsible for analyzing database schemas
            and providing contextual information about tables, columns, relationships, and constraints.
            Your job is to provide accurate schema information that can be used to generate SQL queries.""",
            instructions=[
                "Analyze database schema structures accurately",
                "Detect table relationships and foreign keys",
                "Identify primary keys and constraints",
                "Provide detailed column information including data types",
                "Format all responses as JSON with consistent structure"
            ]
        )
        
    def process(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a schema request and return database structural information.
        
        Args:
            input_text: Natural language request for schema information
            context: Additional context, including prism_id to identify the database
            
        Returns:
            Dictionary with schema information including tables and relationships
        """
        try:
            # In a real implementation, this would query the database for schema information
            # For now, we'll return mock data
            
            prism_id = context.get("prism_id", "default_db")
            
            # Mock schema data for demonstration
            mock_tables = [
                {
                    "name": "customers",
                    "description": "Customer information",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "is_primary": True},
                        {"name": "name", "type": "VARCHAR(100)"},
                        {"name": "email", "type": "VARCHAR(100)"},
                        {"name": "created_at", "type": "TIMESTAMP"}
                    ]
                },
                {
                    "name": "orders",
                    "description": "Customer orders",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "is_primary": True},
                        {"name": "customer_id", "type": "INTEGER", "is_foreign_key": True},
                        {"name": "order_date", "type": "TIMESTAMP"},
                        {"name": "total_amount", "type": "DECIMAL(10,2)"}
                    ]
                }
            ]
            
            mock_relationships = [
                {
                    "from_table": "orders",
                    "from_column": "customer_id",
                    "to_table": "customers",
                    "to_column": "id",
                    "relationship_type": "many-to-one"
                }
            ]
            
            return self.success_response(
                f"Schema information retrieved for {prism_id}",
                {
                    "tables": mock_tables,
                    "relationships": mock_relationships
                }
            )
        except Exception as e:
            return self.error_response(f"Failed to retrieve schema: {str(e)}") 