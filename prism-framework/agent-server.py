"""
PrismDB Agent Server

This module initializes and starts the PrismDB agent server, which provides 
a playground interface for interacting with the database agents.

The server:
1. Initializes multiple agents with different LLM backends (GPT-4o-mini, Gemini Flash)
2. Creates a playground interface for these agents
3. Applies authentication middleware for security
4. Serves the playground app on a local server

Usage:
    python agent-server.py

This starts the agent server on the default port (7777).
"""

from agno.playground import Playground, serve_playground_app
import logging  # Import standard logging

from agents.prismagent import get_prism_agent, get_prism_agents
import agno.utils.log as agno_logging
from agents.auth_middleware import apply_auth_middleware

logger = agno_logging.build_logger(__name__)

# Configure file logging
log_file = 'agent-server.log'
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG) # Set the desired log level

logger.info("Starting agent server")


# prism_agent = get_prism_agent()
# prism_agents_gpt4o = get_prism_agents(model_name="gpt-4o", debug_mode=True)
prism_agents_gpt4o_mini = get_prism_agents(model_name="gpt-4o-mini", debug_mode=True)
prism_agents_gemini_flash = get_prism_agents(model_name="gemini-flash-2.0", debug_mode=True)
# prism_agents_deepseek_v3 = get_prism_agents(model_name="deepseek-v3", debug_mode=True)

# app = Playground(agents=[prism_agent]).get_app()
# app = Playground(agents=[prism_agents_gpt4o,prism_agents_gpt4o_mini,prism_agents_gemini_flash,prism_agents_deepseek_v3]).get_app()
app_raw = Playground(agents=[prism_agents_gpt4o_mini,prism_agents_gemini_flash]).get_app()

# Apply authentication middleware
app = apply_auth_middleware(app_raw)

if __name__ == "__main__":
    serve_playground_app("agent-server:app", reload=True)
