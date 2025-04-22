from textwrap import dedent
from typing import Optional, List, Dict

from agno.agent import Agent
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory import AgentMemory
from agno.memory.db.postgres import PgMemoryDb
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge import AgentKnowledge
from agno.models.openai import OpenAIChat
from agno.models.anthropic.claude import Claude
from agno.models.deepseek import DeepSeek
from agno.models.google import Gemini
from agno.vectordb.pgvector import PgVector, SearchType
import agno.utils.log as agno_logging
import logging
from tools.postgresstool import postgres_tools, postgres_tool_names, database_list
from agno.tools import Toolkit
from agno.tools.postgres import PostgresTools
import os
import dotenv

# Import agent modules
from agents.schema_agent import get_schema_agent
from agents.query_builder_agent import get_query_builder_agent
from agents.read_agent import get_read_agent
from agents.write_agent import get_write_agent
from agents.admin_agent import get_admin_agent
from agents.prism_db_agent import get_prism_db_agent
from agents.coordinator_agent import get_coordinator_agent
from agents.db_agent import get_db_agent

dotenv.load_dotenv(dotenv_path=".env.agent")

db_url = os.getenv("AGENT_DB_URL")
embedding_model = os.getenv("EMBEDDING_MODEL")

logger = agno_logging.team_logger
logger.info("Starting Prism Agent Team")
log_file = 'prismagent.log'
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG) # Set the desired log level

def get_prism_agent(
    name: str = None,
    model_name: str = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = False,
    tools: List[Toolkit] = None,
    extra_team_members: List[Agent] = None
) -> Agent:
    """
    Create and return a Prism Data Extraction Agent with specialized database operation capabilities.
    
    Args:
        name: Name for the agent
        model_name: The name/id of the LLM model to use
        session_id: Optional session identifier
        user_id: Optional user identifier
        debug_mode: Whether to enable debug mode
        tools: List of tools to provide to the agent
        extra_team_members: Additional team members to add
        
    Returns:
        Agent: The configured Prism Data Extraction Agent
    """
    logger.info(f"Creating Prism Agent with model_name = {model_name}, DB URL = {db_url}")
    
    # Initialize the model based on model_name
    if model_name == "claude-3-5-sonnet":
        model = Claude(id="anthropic.claude-3-5-sonnet-20240620-v1:0")
        logger.info("Using Claude 3.5 Sonnet model")
        
    elif model_name == "deepseek-v3":
        model = DeepSeek(id="deepseek-chat")
        logger.info("Using DeepSeek model")

    elif model_name == "gemini-flash-2.0":
        model = Gemini(id="gemini-2.0-flash")
        logger.info("Using Gemini 2.0 Flash model")
    
    elif model_name == "gpt-4o":
        model = OpenAIChat(id="gpt-4o")
        logger.info("Using GPT-4o model")
    
    elif model_name == "gpt-4o-mini":
        model = OpenAIChat(id="gpt-4o-mini")
        logger.info("Using GPT-4o-mini model")
        
    else:
        # Default to GPT-4o if no specific model is provided
        model_name = "gpt-4o"
        model = OpenAIChat(id="gpt-4o")
        logger.info(f"Using {model_name} model as default")

    # Extra instructions for specialized agents
    extra_instructions: Dict[str, str] = {}

    # Create team members
    team_members = [
        get_schema_agent(model=model, tools=None),  # No direct database tools
        get_query_builder_agent(model=model, tools=None),  # No direct database tools
        get_read_agent(model=model, tools=None),  # No direct database tools
        get_write_agent(model=model, tools=None),  # No direct database tools
        get_admin_agent(model=model, tools=None),  # No direct database tools
        get_prism_db_agent(model=model, tools=None),  # No direct database tools
    ]
    
    # Add extra team members if provided
    if extra_team_members is not None:
        team_members.extend(extra_team_members)

    # Get the coordinator agent
    agent = get_coordinator_agent(
        model=model,
        team_members=team_members,
        tools=tools,  # Only non-database tools here
        extra_instructions=extra_instructions
    )
    
    # Configure memory, storage, and knowledge base
    agent.memory = AgentMemory(
        db=PgMemoryDb(db_url=db_url, table_name="prism_agent_memory", schema="agent"),
        create_user_memories=True,
        update_user_memories_after_run=True,
        create_session_summary=True,
        update_session_summary_after_run=True,
    )
    
    agent.storage = PostgresAgentStorage(
        table_name="prism_agent_storage",
        schema="agent",
        db_url=db_url,
        auto_upgrade_schema=True,
    )
    
    agent.knowledge = AgentKnowledge(
        vector_db=PgVector(
            db_url=db_url,
            table_name="prism_agent_knowledge",
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(
                id=embedding_model, dimensions=1536
            ),
            auto_upgrade_schema=True,
            schema="agent"
        ),
        num_documents=3,
    )
    
    # Set additional agent configurations
    agent.session_id = session_id
    agent.user_id = user_id
    agent.debug_mode = debug_mode
    agent.name = "Prism Agent" if name is None else name
    
    return agent

def get_prism_agents(
    model_name: str = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    """
    Create and return Prism agents with database-specific agents as team members.
    
    Args:
        model_name: The name/id of the LLM model to use
        session_id: Optional session identifier
        user_id: Optional user identifier
        debug_mode: Whether to enable debug mode
        
    Returns:
        Agent: The configured Prism Agent with database-specific agents
    """
    if model_name.startswith("gpt"):
        modelprefix = "OpenAI"
    elif model_name.startswith("gemini"):
        modelprefix = "Gemini"
    elif model_name.startswith("claude"):
        modelprefix = "Claude"
    elif model_name.startswith("groq"):
        modelprefix = "Groq"
    elif model_name.startswith("mistral"):
        modelprefix = "Mistral"
    elif model_name.startswith("deepseek"):
        modelprefix = "DeepSeek"
    
    # Initialize the model
    if model_name == "claude-3-5-sonnet":
        model = Claude(id="anthropic.claude-3-5-sonnet-20240620-v1:0")
    elif model_name == "deepseek-v3":
        model = DeepSeek(id="deepseek-chat")
    elif model_name == "gemini-flash-2.0":
        model = Gemini(id="gemini-2.0-flash")
    elif model_name == "gpt-4o":
        model = OpenAIChat(id="gpt-4o")
    elif model_name == "gpt-4o-mini":
        model = OpenAIChat(id="gpt-4o-mini")
    else:
        # Default to GPT-4o if no specific model is provided
        model = OpenAIChat(id="gpt-4o")
        
    # Create database-specific agents
    db_agents = []
    for i, postgres_tool in enumerate(postgres_tools):
        db_name = database_list[i]
        # Create a dedicated database agent using get_db_agent from db_agent.py
        db_agent = get_db_agent(
            model=model,
            db_name=db_name,
            db_tools=postgres_tool
        )
        db_agents.append(db_agent)
        logger.info(f"Created database agent for {db_name}")
    
    # Create a special prism database tool and agent
    # This is critical for managing schema tables and agent data
    prism_db_tool = PostgresTools(
        host="localhost",
        port=5532,
        db_name="agent",  # Connect to the agent database
        user="prismdb",
        password="prismdb",
        run_queries=True,
        inspect_queries=True,
        summarize_tables=True,
        export_tables=True,
        table_schema="agent"  # Use the agent schema
    )
    
    # Create the prism database agent
    prism_db_agent = get_db_agent(
        model=model,
        db_name="prism",
        db_tools=prism_db_tool
    )
    logger.info("Created special prism database agent")
    
    # Add the prism database agent to the list of database agents
    db_agents.append(prism_db_agent)
    
    # Create main coordinator agent with all database agents as team members
    # But WITHOUT direct database tools
    agent = get_prism_agent(
        f'Prism Agent [{modelprefix}]',
        model_name, 
        session_id, 
        user_id, 
        debug_mode, 
        tools=None,  # No direct database tools
        extra_team_members=db_agents
    )

    return agent
