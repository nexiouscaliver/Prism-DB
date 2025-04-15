# PrismDB Architecture

This document provides a detailed overview of PrismDB's architecture, explaining how the various components work together to transform natural language into SQL queries and visualizations.

## System Overview

PrismDB is a multi-agent system built on the following principles:
1. **Separation of concerns**: Each agent has a specific responsibility
2. **Composability**: Agents can be combined to create complex workflows
3. **Extensibility**: New agents and capabilities can be added easily
4. **Fault tolerance**: The system can recover from individual component failures

The high-level architecture consists of:
- A core multi-agent framework
- Database connectivity services
- API endpoints for client interaction
- Security and authentication layers
- Visualization and rendering services

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Flask Application                          │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   API v1    │  │  JWT Auth   │  │Redis Circuit│  │Database │ │
│  │  Endpoints  │  │   Service   │  │   Breaker   │  │ Models  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────┘ │
└─────────┼───────────────┼───────────────┼──────────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestration Layer                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Agent Orchestrator                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │  NLU     │   │  Schema  │   │  Query   │   │   Viz    │     │
│  │  Agent   │   │  Agent   │   │  Agent   │   │  Agent   │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
          │               │               │               │
          ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ Database │   │Execution │   │   Viz    │   │ Caching  │     │
│  │ Service  │   │ Service  │   │ Service  │   │ Service  │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
          │               │               │
          ▼               ▼               ▼
┌──────────────────┐ ┌──────────┐ ┌───────────────┐
│    Multiple      │ │  Query   │ │ Visualization │
│    Database      │ │ Results  │ │    Output     │
│   Connections    │ │          │ │               │
└──────────────────┘ └──────────┘ └───────────────┘
```

## Core Components

### 1. Agents

All agents inherit from the `PrismAgent` base class, which provides:
- Standardized input/output interfaces
- Error handling and telemetry
- Configuration management
- Integration with the Gemini LLM

#### NLU Agent

**Location:** `agents/nlu_agent.py`

The Natural Language Understanding agent:
- Parses user queries to extract intents and entities
- Identifies database operations (select, aggregate, filter, etc.)
- Recognizes time periods, quantities, and categories
- Detects ambiguities and suggests clarifications

#### Schema Agent

**Location:** `agents/schema_agent.py`

The Schema agent:
- Extracts and processes database schema information
- Identifies tables, columns, relationships, and data types
- Maps natural language concepts to database entities
- Handles schema caching for performance

#### Query Agent

**Location:** `agents/query_agent.py`

The Query agent:
- Generates SQL based on intent and schema
- Optimizes queries for performance
- Validates query safety and prevents injection attacks
- Explains generated queries in natural language

#### Visualization Agent

**Location:** `agents/visualization_agent.py`

The Visualization agent:
- Analyzes query results to suggest appropriate visualizations
- Generates charts (bar, line, pie, scatter plots, etc.)
- Formats labels and styling based on data characteristics
- Provides explanations for visualization choices

### 2. Orchestrator

**Location:** `agents/orchestrator.py`

The Orchestrator:
- Coordinates the multi-agent workflow
- Manages agent execution order and dependencies
- Handles parallel processing for improved response time
- Implements circuit breakers and fallback strategies
- Aggregates results from all agents into a coherent response

### 3. Services

#### Database Service

**Location:** `services/database_service.py`

The Database service:
- Manages connections to multiple databases
- Implements connection pooling and retry logic
- Handles database credentials and security
- Provides a unified interface for different database types

#### Execution Service

**Location:** `services/execution_service.py`

The Execution service:
- Securely executes SQL queries
- Implements query timeouts and resource limitations
- Formats query results into standardized structures
- Caches results for frequently executed queries

#### Visualization Service

**Location:** `services/visualization_service.py`

The Visualization service:
- Renders charts and visualizations
- Implements different output formats (SVG, PNG, HTML)
- Applies theme settings and styling
- Optimizes visualizations for different display sizes

### 4. API Endpoints

The Flask application exposes RESTful endpoints in `app/api/v1/`:

- **Authentication**: Login and token management
- **Query**: Generation and execution of SQL from natural language
- **Visualization**: Chart generation from query results
- **Agents**: Configuration and management of agents
- **Database**: Management of database connections

### 5. Security Model

PrismDB implements a comprehensive security model:

- **JWT Authentication**: Secure token-based access
- **Database Access Control**: Fine-grained permissions for databases
- **Query Validation**: Prevention of SQL injection attacks
- **Rate Limiting**: Protection against abuse
- **Circuit Breakers**: Resilience against cascading failures

## Data Flow

### Natural Language to SQL Flow

1. User sends a natural language query through the API
2. NLU Agent extracts intent, entities, and query parameters
3. Schema Agent identifies relevant tables and relationships
4. Query Agent generates SQL based on intent and schema
5. SQL is returned to the user or passed to the execution service
6. Execution Service runs the SQL against the target database
7. Results are formatted and returned to the user

### Visualization Flow

1. User requests visualization for a query result
2. Visualization Agent analyzes the data characteristics
3. Agent suggests appropriate chart types and configurations
4. Visualization Service renders the selected chart
5. Chart is returned to the user in the requested format

## Concurrent Processing

PrismDB uses asyncio for concurrent processing:

- Parallel agent execution where possible
- Non-blocking database and API operations
- Task queuing and prioritization
- Background processing for long-running tasks

## Extensibility

PrismDB is designed to be extensible:

- New agents can be added by extending the PrismAgent base class
- Additional database types can be supported by implementing connectors
- New visualization types can be added to the visualization service
- Custom workflows can be created by configuring the orchestrator

## Configuration Management

The system configuration is managed through:

- Environment variables for deployment settings
- Database records for user and agent configurations
- In-memory caching for frequently accessed settings
- Dynamic configuration updates through the API

## Performance Considerations

PrismDB implements several optimizations:

- Schema caching to reduce database access
- Connection pooling for efficient resource utilization
- Result caching for common queries
- Parallel agent execution for improved response time
- Lightweight visualizations for faster rendering

## Error Handling

The error handling strategy includes:

- Standardized error codes and messages
- Graceful degradation of services
- Circuit breakers for external dependencies
- Comprehensive logging for troubleshooting
- Retry mechanisms for transient failures

## Monitoring and Telemetry

PrismDB includes built-in monitoring:

- Request timing and throughput metrics
- Agent performance tracking
- Error rate monitoring
- Resource utilization tracking
- Health check endpoints

## Deployment Architecture

PrismDB can be deployed in various configurations:

- Single-server deployment for development
- Multi-server deployment for production
- Container-based deployment with Docker
- Orchestrated deployment with Kubernetes

## Future Directions

Planned architectural enhancements include:

- Streaming responses for large result sets
- Enhanced caching strategies
- Support for additional database types
- Advanced visualization capabilities
- Collaborative features for team environments 