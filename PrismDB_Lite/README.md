# PrismDB Lite

A natural language to SQL multi-agent system combining OpenAI GPT-4 Turbo and Google Gemini Pro for complex reasoning and query validation. The system features real-time thought process visualization and automatic error recovery mechanisms.

## Architecture

PrismDB Lite leverages a multi-agent architecture to convert natural language queries into SQL:

1. **NLU Agent** - Natural language understanding with OpenAI GPT-4 Turbo and Google Gemini Pro
2. **Schema Agent** - Database schema analysis and relationship mapping
3. **SQL Agent** - SQL generation with syntax validation using Google Gemini Pro
4. **Execution Agent** - Safe query execution with timeout controls
5. **Visualization Agent** - Data visualization and insight generation
6. **Monitor Agent** - Real-time thought process streaming

All agents are coordinated by an **Orchestrator** that implements three collaboration modes:

- **Route Mode** - Direct queries to specialized agents
- **Coordinate Mode** - Parallel task execution
- **Collaborate Mode** - Consensus-based complex query handling

## Setup

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Redis server (optional, for real-time event streaming)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/PrismDB-Lite.git
cd PrismDB-Lite
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp env.example .env
```

Edit the `.env` file with your API keys and database connection details.

### Database Configuration

PrismDB Lite requires a PostgreSQL database. You can set up the database connection in the `.env` file or directly in the `config/agent_teams.yaml` file.

Example database connection string:
```
postgresql://username:password@localhost:5432/dbname
```

## Usage

### Starting the Server

Start the server with default settings:

```bash
python main.py
```

Advanced options:

```bash
python main.py --config config/agent_teams.yaml --env production --mode collaborate --host 0.0.0.0 --port 8000 --debug
```

Command line options:
- `--config`: Path to agent team configuration file (default: `config/agent_teams.yaml`)
- `--env`: Environment to use, either `development` or `production` (default: `development`)
- `--mode`: Agent team processing mode, either `route`, `coordinate`, or `collaborate` (default: from config)
- `--host`: Host for the API server (default: `127.0.0.1`)
- `--port`: Port for the API server (default: `5000`)
- `--debug`: Enable debug mode (default: `False`)
- `--log-level`: Logging level, one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: from config)

### API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/health` | GET | Health check, returns status and available agents |
| `/api/query` | POST | Process a natural language query through the orchestrator |
| `/api/nlu` | POST | Natural language understanding |
| `/api/sql-gen` | POST | Generate SQL from natural language |
| `/api/execute` | POST | Execute a SQL query |
| `/api/visualize` | POST | Generate visualizations for query results |
| `/api/schema` | GET | Get database schema information |
| `/api/agent-events` | GET | Stream agent events (SSE) |
| `/api/execution-graph` | GET | Get agent execution graph |
| `/api/agent-stats` | GET | Get statistics for all agents |

### Example Query

```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all users who joined in the last month"}'
```

### Real-Time Thought Process Visualization

The system provides real-time visualization of agent thought processes using Server-Sent Events (SSE). To view this in a browser:

```javascript
const eventSource = new EventSource('/api/agent-events');
eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log(data);
  // Update UI with agent thoughts
};
```

## Configuration

Agent configuration is defined in `config/agent_teams.yaml`. This file contains:

- Team configurations
- Agent definitions
- Environment-specific settings (development, production)

Example configuration structure:

```yaml
teams:
  prismdb_team:
    description: "PrismDB Multi-Agent Team for NL to SQL Conversion"
    modes:
      - route
      - coordinate
      - collaborate
    agents:
      orchestrator:
        type: "Orchestrator"
        description: "Coordinates agent workflow"
      nlu_agent:
        type: "NLUAgent"
        description: "Natural language understanding"

environments:
  development:
    logging_level: "DEBUG"
    apis:
      openai:
        api_key: "${OPENAI_API_KEY}"
  production:
    logging_level: "INFO"
    # Production settings
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

This project was built using the following technologies:
- [OpenAI API](https://openai.com)
- [Google Gemini API](https://ai.google.dev/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Flask](https://flask.palletsprojects.com/)
- [Chart.js](https://www.chartjs.org/)
- [D3.js](https://d3js.org/) 