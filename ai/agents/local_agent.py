from textwrap import dedent
from typing import Optional, List, Dict
from agno.agent import Agent
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory import AgentMemory
from agno.memory.db.postgres import PgMemoryDb
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge import AgentKnowledge
# from agno.models.openai import OpenAIChat
# from agno.models.anthropic.claude import Claude
from agno.tools import Toolkit
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools
from agno.tools.yfinance import YFinanceTools
from agno.vectordb.pgvector import PgVector, SearchType
from agno.tools.googlesearch import GoogleSearchTools

from ai.settings import ai_settings
from db.session import db_url
from workspace.settings import ws_settings
from agno.models.ollama import Ollama
from agno.models.ollama import OllamaTools


def get_local_keai(
    model_name: str = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = False,
    use_google_search: bool = True,  # Renamed parameter
) -> Agent:
    # print(f"db_url: {db_url}")
    if model_name is None:
        model_name = "llama3.3:70b-instruct-q5_K_M"

    model = OllamaTools(id=model_name)

    # Add tools available to the Personalized Agent
    tools: List[Toolkit] = []

    # Extra instructions for using tools - converting to dictionary format
    extra_instructions: Dict[str, str] = {}

    if use_google_search:
        tools.append(GoogleSearchTools(fixed_max_results=10, fixed_language="en"))

        extra_instructions["GoogleSearchTools"] = """
Use the `GoogleSearch` tool to search the internet to find answers for the user's queries.
Example: {"name": "google_search", "arguments": {"query": "your search term"}}
Example: {"name": "update_memory", "arguments": {"task": "Your task description"}}
"""

    if "deepseek" in model_name:
        print("Removing DeepSeek tools")
        return Agent(
        model=model,
        name="keai",
        session_id=session_id,
        user_id=user_id,
        # Store the memories in a database
        # memory=AgentMemory(
        #     db=PgMemoryDb(table_name="keai_memory", db_url=db_url),
        #     create_user_memories=True,
        #     update_user_memories_after_run=True,
        #     create_session_summary=True,
        #     update_session_summary_after_run=True,
        # ),
        # # Store runs in a database
        # storage=PgAgentStorage(
        #     table_name="regenai_sessions",
        #     schema="ai",
        #     db_url=db_url,
        # ),
        # # Store knowledge in a vector database
        # knowledge=AgentKnowledge(
        #     vector_db=PgVector(
        #         db_url=db_url,
        #         table_name="keai_documents",
        #         search_type=SearchType.hybrid,
        #         embedder=OpenAIEmbedder(
        #             model=ai_settings.embedding_model, dimensions=1536
        #         ),
        #     ),
        #     # 3 references are added to the prompt
        #     num_documents=3,
        # ),
        description="You are a chatbot that talks to users. Do not use tools. Do not print <think> data.",
        instructions=[
            "When the user sends a message, first **think** but do not think for more than 5 seconds. The points to remember:\n"
            " - You can answer by using your own knowledge from training you received\n"
            # " - You need to search the knowledge base\n"
            # " - You need to search internet using the `GoogleSearch` tool.\n"
            # "If the user asks about a topic with a keyword 'kb', first ALWAYS search your knowledge base using the `search_knowledge_base` tool.\n",
            "If the users message is unclear, ask clarifying questions to get more information.\n",
            "Carefully read the information you have gathered and provide a clear and concise answer to the user.\n",
            "Do not use phrases like 'based on my knowledge' or 'depending on the information'.\n",
            "If you don't know the answer then apologise and say that you don't have the knowledge, but don't make-up the answer.\n",
            "Ensure that when using tools, you provide all required arguments.",
            "You can understand and respond to queries in any language, including Hindi.",
            # "When calling tools, ensure you use the correct function names and provide all required arguments.",
            # "For the `GoogleSearch` tool, use the `google_search` function with the 'query' argument.",
            # 'Example: {"name": "google_search", "arguments": {"query": "your search term"}}',
            # "When using `update_memory`, always include the 'task' argument with a description.",
            # 'Example: {"name": "update_memory", "arguments": {"task": "Your task description"}}',
        ],
        # Add extra instructions for using tools
        # add_context_instructions=True, # Removed tools from the Agent
        # context_instructions=extra_instructions,
        # Add tools to the Agent
        # tools=tools,  # Removed tools from the Agent
        # Add team members to the Agent
        # team=team,
        # Show tool calls in the chatg
        show_tool_calls=False,
        # This setting adds a tool to search the knowledge base for information
        search_knowledge=False,
        # Add a tool to read chat history.
        read_chat_history=False,
        # This setting tells the LLM to format messages in markdown
        markdown=True,
        # This setting adds chat history to the messages
        # read_chat_history=True,
        add_history_to_messages=False,
        # This setting adds 6 previous messages from chat history to the messages sent to the LLM
        num_history_responses=5,
        # This setting adds the current datetime to the instructions
        add_datetime_to_instructions=True,
        # Add an introductory Agent message
        introduction=dedent(
            """\
        Hi, I'm RegenAI your AI agent.
        Let's get started!\
        """
        ),
        debug_mode=debug_mode,
        add_function_descriptions=False,
    )
    else:
        return Agent(
            model=model,
            name="keai",
            session_id=session_id,
            user_id=user_id,
            # Store the memories in a database
            memory=AgentMemory(
                db=PgMemoryDb(table_name="keai_memory", db_url=db_url),
                create_user_memories=True,
                update_user_memories_after_run=True,
                create_session_summary=True,
                update_session_summary_after_run=True,
            ),
            # Store runs in a database
            storage=PostgresAgentStorage(
                table_name="regenai_sessions",
                schema="ai",
                db_url=db_url,
            ),
            # Store knowledge in a vector database
            knowledge=AgentKnowledge(
                vector_db=PgVector(
                    db_url=db_url,
                    table_name="keai_documents",
                    search_type=SearchType.hybrid,
                    embedder=OpenAIEmbedder(
                        id=ai_settings.embedding_model, dimensions=1536
                    ),
                ),
                # 3 references are added to the prompt
                num_documents=3,
            ),
            description="You are a news agent that helps users find the latest news.",
            instructions=[
                "When the user sends a message, first **think** and determine if:\n"
                " - You can answer by using your own knowledge from training you received and tools available to you\n"
                " - You need to search the knowledge base\n"
                " - You need to search internet using the `GoogleSearch` tool.\n"
                "If the user asks about a topic with a keyword 'kb', first ALWAYS search your knowledge base using the `search_knowledge_base` tool.\n",
                "If the users message is unclear, ask clarifying questions to get more information.\n",
                "Carefully read the information you have gathered and provide a clear and concise answer to the user.\n",
                "Do not use phrases like 'based on my knowledge' or 'depending on the information'.\n",
                "If you don't know the answer then apologise and say that you don't have the knowledge, but don't make-up the answer.\n",
                "Ensure that when using tools, you provide all required arguments.",
                "You can understand and respond to queries in any language, including Hindi.",
                "When calling tools, ensure you use the correct function names and provide all required arguments.",
                "For the `GoogleSearch` tool, use the `google_search` function with the 'query' argument.",
                'Example: {"name": "google_search", "arguments": {"query": "your search term"}}',
                "When using `update_memory`, always include the 'task' argument with a description.",
                'Example: {"name": "update_memory", "arguments": {"task": "Your task description"}}',
            ],
            # Add extra instructions for using tools
            add_context_instructions=True,
            context_instructions=extra_instructions,
            # Add tools to the Agent
            tools=tools,
            # Add team members to the Agent
            # team=team,
            # Show tool calls in the chatg
            show_tool_calls=False,
            # This setting adds a tool to search the knowledge base for information
            search_knowledge=True,
            # Add a tool to read chat history.
            read_chat_history=True,
            # This setting tells the LLM to format messages in markdown
            markdown=True,
            # This setting adds chat history to the messages
            # read_chat_history=True,
            add_history_to_messages=True,
            # This setting adds 6 previous messages from chat history to the messages sent to the LLM
            num_history_responses=5,
            # This setting adds the current datetime to the instructions
            add_datetime_to_instructions=True,
            # Add an introductory Agent message
            introduction=dedent(
                """\
            Hi, I'm RegenAI your AI agent.
            I have access to a set of tools to assist you.
            Let's get started!\
            """
            ),
            debug_mode=debug_mode,
            add_function_descriptions=True,
        )
