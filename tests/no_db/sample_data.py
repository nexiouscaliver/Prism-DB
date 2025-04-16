"""
Sample data for tests that don't require a database connection.

This module contains mock data structures that represent database schemas,
natural language queries, SQL outputs, query results, and visualization
recommendations that can be used in tests.
"""

# Sample database configurations
SAMPLE_DB_CONFIGS = [
    {
        "id": "db1",
        "name": "Test PostgreSQL Database",
        "db_type": "postgresql",
        "connection_string": "postgresql://user:password@localhost:5432/testdb",
        "is_enabled": True,
        "is_read_only": False
    },
    {
        "id": "db2",
        "name": "Test MySQL Database",
        "db_type": "mysql",
        "connection_string": "mysql://user:password@localhost:3306/testdb",
        "is_enabled": True,
        "is_read_only": True
    }
]

# Sample database schema
SAMPLE_DB_SCHEMA = {
    "tables": [
        {
            "name": "customers",
            "columns": [
                {"name": "customer_id", "type": "INTEGER", "primary_key": True},
                {"name": "first_name", "type": "TEXT"},
                {"name": "last_name", "type": "TEXT"},
                {"name": "email", "type": "TEXT"},
                {"name": "sign_up_date", "type": "DATE"},
                {"name": "status", "type": "TEXT"}
            ]
        },
        {
            "name": "orders",
            "columns": [
                {"name": "order_id", "type": "INTEGER", "primary_key": True},
                {"name": "customer_id", "type": "INTEGER", "foreign_key": "customers.customer_id"},
                {"name": "order_date", "type": "DATE"},
                {"name": "total_amount", "type": "DECIMAL(10,2)"},
                {"name": "status", "type": "TEXT"}
            ]
        },
        {
            "name": "products",
            "columns": [
                {"name": "product_id", "type": "INTEGER", "primary_key": True},
                {"name": "name", "type": "TEXT"},
                {"name": "description", "type": "TEXT"},
                {"name": "price", "type": "DECIMAL(10,2)"},
                {"name": "category", "type": "TEXT"},
                {"name": "inventory_count", "type": "INTEGER"}
            ]
        },
        {
            "name": "order_items",
            "columns": [
                {"name": "order_item_id", "type": "INTEGER", "primary_key": True},
                {"name": "order_id", "type": "INTEGER", "foreign_key": "orders.order_id"},
                {"name": "product_id", "type": "INTEGER", "foreign_key": "products.product_id"},
                {"name": "quantity", "type": "INTEGER"},
                {"name": "unit_price", "type": "DECIMAL(10,2)"},
                {"name": "subtotal", "type": "DECIMAL(10,2)"}
            ]
        }
    ],
    "relationships": [
        {
            "from_table": "orders",
            "from_column": "customer_id",
            "to_table": "customers",
            "to_column": "customer_id"
        },
        {
            "from_table": "order_items",
            "from_column": "order_id",
            "to_table": "orders",
            "to_column": "order_id"
        },
        {
            "from_table": "order_items",
            "from_column": "product_id",
            "to_table": "products",
            "to_column": "product_id"
        }
    ]
}

# Sample natural language queries
SAMPLE_NL_QUERIES = [
    {
        "id": 1,
        "query_text": "Show me all active customers",
        "category": "customer"
    },
    {
        "id": 2,
        "query_text": "What are the total sales by month?",
        "category": "sales"
    },
    {
        "id": 3,
        "query_text": "List the top 5 products by revenue",
        "category": "product"
    },
    {
        "id": 4,
        "query_text": "What is the average order value for each customer?",
        "category": "customer"
    },
    {
        "id": 5,
        "query_text": "Show orders placed in the last 30 days",
        "category": "order"
    }
]

# Sample SQL outputs corresponding to the natural language queries
SAMPLE_SQL_OUTPUTS = [
    {
        "query_id": 1,
        "sql_text": "SELECT customer_id, first_name, last_name, email FROM customers WHERE status = 'active';"
    },
    {
        "query_id": 2,
        "sql_text": """
            SELECT 
                DATE_TRUNC('month', order_date) AS month,
                SUM(total_amount) AS total_sales
            FROM orders
            GROUP BY DATE_TRUNC('month', order_date)
            ORDER BY month;
        """
    },
    {
        "query_id": 3,
        "sql_text": """
            SELECT 
                p.product_id,
                p.name,
                SUM(oi.subtotal) AS revenue
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            GROUP BY p.product_id, p.name
            ORDER BY revenue DESC
            LIMIT 5;
        """
    },
    {
        "query_id": 4,
        "sql_text": """
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                AVG(o.total_amount) AS avg_order_value
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id, c.first_name, c.last_name
            ORDER BY avg_order_value DESC;
        """
    },
    {
        "query_id": 5,
        "sql_text": """
            SELECT 
                order_id,
                customer_id,
                order_date,
                total_amount,
                status
            FROM orders
            WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY order_date DESC;
        """
    }
]

# Sample query results
SAMPLE_QUERY_RESULTS = [
    {
        "sql_text": "SELECT customer_id, first_name, last_name, email FROM customers WHERE status = 'active';",
        "result_data": [
            {"customer_id": 1, "first_name": "John", "last_name": "Doe", "email": "john.doe@example.com"},
            {"customer_id": 2, "first_name": "Jane", "last_name": "Smith", "email": "jane.smith@example.com"},
            {"customer_id": 3, "first_name": "Robert", "last_name": "Johnson", "email": "robert.j@example.com"},
            {"customer_id": 4, "first_name": "Emily", "last_name": "Brown", "email": "emily.b@example.com"},
            {"customer_id": 5, "first_name": "Michael", "last_name": "Wilson", "email": "michael.w@example.com"}
        ]
    },
    {
        "sql_text": """
            SELECT 
                DATE_TRUNC('month', order_date) AS month,
                SUM(total_amount) AS total_sales
            FROM orders
            GROUP BY DATE_TRUNC('month', order_date)
            ORDER BY month;
        """,
        "result_data": [
            {"month": "2023-01-01", "total_sales": 12500.75},
            {"month": "2023-02-01", "total_sales": 15320.50},
            {"month": "2023-03-01", "total_sales": 18750.25},
            {"month": "2023-04-01", "total_sales": 14980.00},
            {"month": "2023-05-01", "total_sales": 22340.75}
        ]
    },
    {
        "sql_text": """
            SELECT 
                p.product_id,
                p.name,
                SUM(oi.subtotal) AS revenue
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            GROUP BY p.product_id, p.name
            ORDER BY revenue DESC
            LIMIT 5;
        """,
        "result_data": [
            {"product_id": 1, "name": "Laptop Pro", "revenue": 25000.00},
            {"product_id": 3, "name": "Smartphone X", "revenue": 18500.50},
            {"product_id": 5, "name": "Wireless Headphones", "revenue": 12750.25},
            {"product_id": 2, "name": "Tablet Ultra", "revenue": 10800.75},
            {"product_id": 8, "name": "Smart Watch", "revenue": 9500.00}
        ]
    },
    {
        "sql_text": """
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                AVG(o.total_amount) AS avg_order_value
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id, c.first_name, c.last_name
            ORDER BY avg_order_value DESC;
        """,
        "result_data": [
            {"customer_id": 3, "first_name": "Robert", "last_name": "Johnson", "avg_order_value": 850.25},
            {"customer_id": 1, "first_name": "John", "last_name": "Doe", "avg_order_value": 750.50},
            {"customer_id": 5, "first_name": "Michael", "last_name": "Wilson", "avg_order_value": 625.75},
            {"customer_id": 2, "first_name": "Jane", "last_name": "Smith", "avg_order_value": 580.00},
            {"customer_id": 4, "first_name": "Emily", "last_name": "Brown", "avg_order_value": 490.25}
        ]
    },
    {
        "sql_text": """
            SELECT 
                order_id,
                customer_id,
                order_date,
                total_amount,
                status
            FROM orders
            WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY order_date DESC;
        """,
        "result_data": [
            {"order_id": 101, "customer_id": 3, "order_date": "2023-05-15", "total_amount": 950.25, "status": "completed"},
            {"order_id": 102, "customer_id": 1, "order_date": "2023-05-12", "total_amount": 750.50, "status": "completed"},
            {"order_id": 103, "customer_id": 4, "order_date": "2023-05-10", "total_amount": 490.75, "status": "completed"},
            {"order_id": 104, "customer_id": 2, "order_date": "2023-05-05", "total_amount": 820.00, "status": "completed"},
            {"order_id": 105, "customer_id": 5, "order_date": "2023-04-30", "total_amount": 675.25, "status": "completed"}
        ]
    }
]

# Sample visualization recommendations
SAMPLE_VIZ_RECOMMENDATIONS = [
    {
        "type": "table",
        "config": {
            "columns": ["customer_id", "first_name", "last_name", "email"],
            "sortable": True,
            "pagination": True
        }
    },
    {
        "type": "bar_chart",
        "config": {
            "x_field": "month",
            "y_field": "total_sales",
            "title": "Monthly Sales",
            "x_axis_label": "Month",
            "y_axis_label": "Total Sales ($)"
        }
    },
    {
        "type": "horizontal_bar_chart",
        "config": {
            "x_field": "revenue",
            "y_field": "name",
            "title": "Top 5 Products by Revenue",
            "x_axis_label": "Revenue ($)",
            "y_axis_label": "Product"
        }
    },
    {
        "type": "line_chart",
        "config": {
            "x_field": "month",
            "y_field": "total_sales",
            "title": "Sales Trend",
            "x_axis_label": "Month",
            "y_axis_label": "Sales ($)"
        }
    },
    {
        "type": "pie_chart",
        "config": {
            "value_field": "avg_order_value",
            "label_field": "last_name",
            "title": "Average Order Value by Customer"
        }
    }
] 