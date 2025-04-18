import logging
import json
import time
import asyncio
from functools import wraps
from typing import Dict, Any, Callable

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import flask_sse  # Server-Sent Events for real-time updates

logger = logging.getLogger("prismdb.api")

def async_route(route_function):
    """
    Decorator to handle async routes with Flask.
    """
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        return asyncio.run(route_function(*args, **kwargs))
    return decorated_function

def create_app(agents=None):
    """
    Create and configure the Flask application.
    
    Args:
        agents (dict, optional): Dictionary of initialized agents
        
    Returns:
        Flask: The Flask application
    """
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    app.config['REDIS_URL'] = "redis://localhost:6379"
    
    # Enable CORS
    CORS(app)
    
    # Register the SSE Blueprint
    app.register_blueprint(flask_sse.sse, url_prefix='/stream')
    
    # Store agents in app context
    app.agents = agents or {}
    
    # Request timing middleware
    @app.before_request
    def start_timer():
        request.start_time = time.time()
    
    @app.after_request
    def log_request(response):
        if request.path != '/stream':  # Don't log SSE requests
            duration = time.time() - request.start_time
            logger.info(
                f"{request.method} {request.path} {response.status_code} ({duration:.2f}s)"
            )
        return response
    
    # Error handler
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f"Error: {str(error)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500
    
    # Routes
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "agents": list(app.agents.keys()) if app.agents else []
        })
    
    @app.route('/api/nlu', methods=['POST'])
    @async_route
    async def nlu_process():
        """Natural language understanding endpoint."""
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"status": "error", "message": "No query provided"}), 400
        
        # Get the NLU agent
        nlu_agent = app.agents.get('nlu_agent')
        if not nlu_agent:
            return jsonify({"status": "error", "message": "NLU agent not available"}), 503
        
        # Process the query
        result = await nlu_agent.process({"query": query})
        
        return jsonify({
            "status": "success",
            "result": result
        })
    
    @app.route('/api/sql-gen', methods=['POST'])
    @async_route
    async def sql_generate():
        """SQL generation endpoint."""
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"status": "error", "message": "No query provided"}), 400
        
        # Get the SQL agent
        sql_agent = app.agents.get('sql_agent')
        if not sql_agent:
            return jsonify({"status": "error", "message": "SQL agent not available"}), 503
        
        # Process the query
        result = await sql_agent.process({"query": query})
        
        return jsonify({
            "status": "success",
            "result": result
        })
    
    @app.route('/api/execute', methods=['POST'])
    @async_route
    async def execute_sql():
        """SQL execution endpoint."""
        data = request.json
        sql = data.get('sql', '')
        
        if not sql:
            return jsonify({"status": "error", "message": "No SQL provided"}), 400
        
        # Get the execution agent
        execution_agent = app.agents.get('execution_agent')
        if not execution_agent:
            return jsonify({"status": "error", "message": "Execution agent not available"}), 503
        
        # Execute the SQL
        result = await execution_agent.process({"sql": sql})
        
        return jsonify({
            "status": "success",
            "result": result
        })
    
    @app.route('/api/visualize', methods=['POST'])
    @async_route
    async def visualize_data():
        """Data visualization endpoint."""
        data = request.json
        result_data = data.get('data', {})
        
        if not result_data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Get the visualization agent
        visualization_agent = app.agents.get('visualization_agent')
        if not visualization_agent:
            return jsonify({"status": "error", "message": "Visualization agent not available"}), 503
        
        # Generate visualization
        result = await visualization_agent.process({"data": result_data})
        
        return jsonify({
            "status": "success",
            "result": result
        })
    
    @app.route('/api/query', methods=['POST'])
    @async_route
    async def process_query():
        """Process a natural language query through the orchestrator."""
        data = request.json
        query = data.get('query', '')
        mode = data.get('mode')  # Optional processing mode
        
        if not query:
            return jsonify({"status": "error", "message": "No query provided"}), 400
        
        # Get the orchestrator
        orchestrator = app.agents.get('orchestrator')
        if not orchestrator:
            return jsonify({"status": "error", "message": "Orchestrator not available"}), 503
        
        # Set processing mode if specified
        original_mode = None
        if mode:
            original_mode = orchestrator.processing_mode
            orchestrator.set_mode(mode)
        
        try:
            # Process the query
            result = await orchestrator.process({"query": query})
            
            # Notify monitor about the processed query
            monitor_agent = app.agents.get('monitor_agent')
            if monitor_agent:
                await monitor_agent.process({
                    "type": "query",
                    "agent": "api",
                    "message": query,
                    "metadata": {
                        "mode": orchestrator.processing_mode,
                        "timestamp": time.time()
                    }
                })
            
            return jsonify({
                "status": "success",
                "result": result,
                "mode": orchestrator.processing_mode
            })
        finally:
            # Restore original mode if changed
            if original_mode:
                orchestrator.set_mode(original_mode)
    
    @app.route('/api/schema', methods=['GET'])
    @async_route
    async def get_schema():
        """Get database schema information."""
        # Get the schema agent
        schema_agent = app.agents.get('schema_agent')
        if not schema_agent:
            return jsonify({"status": "error", "message": "Schema agent not available"}), 503
        
        # Get schema information
        result = await schema_agent.process({})
        
        return jsonify({
            "status": "success",
            "schema": result.get("schema", {})
        })
    
    @app.route('/api/agent-events', methods=['GET'])
    def stream_agent_events():
        """Stream agent events using Server-Sent Events."""
        def generate():
            # Get the monitor agent
            monitor_agent = app.agents.get('monitor_agent')
            if not monitor_agent:
                yield f"data: {json.dumps({'error': 'Monitor agent not available'})}\n\n"
                return
            
            # Stream events
            for event in monitor_agent.get_event_stream():
                if event.get("type") == "keepalive":
                    yield f": keepalive\n\n"
                else:
                    yield f"data: {json.dumps(event)}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    @app.route('/api/execution-graph', methods=['GET'])
    def get_execution_graph():
        """Get the agent execution graph."""
        # Get the monitor agent
        monitor_agent = app.agents.get('monitor_agent')
        if not monitor_agent:
            return jsonify({"status": "error", "message": "Monitor agent not available"}), 503
        
        # Get the execution graph
        graph = monitor_agent.get_execution_graph()
        
        return jsonify({
            "status": "success",
            "graph": graph
        })
    
    @app.route('/api/agent-stats', methods=['GET'])
    def get_agent_stats():
        """Get statistics for all agents."""
        # Get the monitor agent
        monitor_agent = app.agents.get('monitor_agent')
        if not monitor_agent:
            return jsonify({"status": "error", "message": "Monitor agent not available"}), 503
        
        # Get agent statistics
        stats = monitor_agent.get_agent_statistics()
        
        return jsonify({
            "status": "success",
            "stats": stats
        })
    
    return app 