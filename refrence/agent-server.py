from agno.playground import Playground, serve_playground_app
import logging  # Import standard logging

from prismagent import get_prism_agents
from prism_scheduler import start_scheduler_thread
import agno.utils.log as agno_logging

logger = agno_logging.build_logger(__name__)

# Configure file logging
log_file = 'agent-server.log'
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG) # Set the desired log level

logger.info("Starting agent server")

# Create Prism agents with different LLM models
prism_agents_gpt4o = get_prism_agents(model_name="gpt-4o", debug_mode=True)
# prism_agents_gpt4o_mini = get_prism_agents(model_name="gpt-4o-mini", debug_mode=True)
prism_agents_gemini_flash = get_prism_agents(model_name="gemini-flash-2.0", debug_mode=True)
# prism_agents_deepseek_v3 = get_prism_agents(model_name="deepseek-v3", debug_mode=True)

# Initialize the Playground app with all agents
app = Playground(agents=[
    prism_agents_gpt4o,
    # prism_agents_gpt4o_mini, 
    prism_agents_gemini_flash, 
    # prism_agents_deepseek_v3
]).get_app()

# Start the prism scheduler in a separate thread
scheduler_thread = start_scheduler_thread()
logger.info("Prism scheduler started successfully")

if __name__ == "__main__":
    serve_playground_app("agent-server:app", reload=True)
