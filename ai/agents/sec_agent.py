#  ai/sec_assitant.py
from textwrap import dedent
from typing import Optional, List, Dict
from agno.agent import Agent
from agno.knowledge import AgentKnowledge
from agno.vectordb.pgvector import PgVector
from agno.embedder.openai import OpenAIEmbedder
from ai.settings import ai_settings
from db.session import db_url
from agno.tools import Toolkit
# from workspace.settings import ws_settings
from agno.models.openai import OpenAIChat
from ..tools.sec import SecTool


def sec_agent(
    sec_tools: bool = True,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = True,
) -> Agent:

    # LLM to use for the Agent
    model = OpenAIChat(
        id="gpt-4o"
        # model = "gpt-4o-mini"
        # Uncomment and configure the following lines as needed
        # max_tokens=ai_settings.default_max_tokens,
        # temperature=ai_settings.default_temperature,
    )

    # Add tools available to the Personalized Agent
    tools: List[Toolkit] = []
    # Extra instructions for using tools - converting to dictionary format
    extra_instructions: Dict[str, str] = {}
    # Add team members
    team: List[Agent] = []

    if sec_tools:
        tools.append(
            SecTool(
                get_reference_data=False,
                get_filing_data=False,
                parse_filing_data=False,
                get_section=True,
            )
        )
        extra_instructions["SecTool"] = "Use `sec_tool' to get sec filing data to summarise section text."

    return Agent(
        model=model,
        name="sec_agent",
        session_id=session_id,
        user_id=user_id,
        # Store knowledge in a vector database
        knowledge=AgentKnowledge(
            vector_db=PgVector(
                db_url=db_url,
                table_name="keai_documents",
                embedder=OpenAIEmbedder(
                    id=ai_settings.embedding_model, dimensions=1536
                ),
            ),
            # 3 references are added to the prompt
            num_documents=3,
        ),
        description=dedent(
            """\
            You are the most advanced AI system in the world.
            Your current role is Chief Credit Risk Officer with Goldman Sachs.    
            You have access to a set of tools and a team of AI Agents at your disposal to analyse a company.
            Your goal is to get the sec filing data using sec_tools and summarise each section to assess risks.\
            """
        ),
        instructions=[
            "When youare called, first **think** and determine if:\n"
            " - the ticker (stock symbol) is given use that ticker to call sec_tools methods\n"
            " - You need to get the section text for for the section of the filing data asked by the user \n"
            " - You need to use appropriate available tools to download and parse the filing data\n"
            " - You need to summarise each section by keeping the oiriginal numbering, sub-topics and order\n"
            " - You need to adapt the language tone based on the context of the section.\n"
            " - You need to write filing type with year and quarter you are summarising.\n"
            " - If the section is about risk then write risk mitiastion with each risk item. Do not omit or drop any risk items\n"
            " - Write a long reports for each section with minimmum of 300 to 500 words. When not much text is avalaible then do a short sumary.\n"
            " - Adopt the tone of the document, write as a third person.\n"
            " - Format the text with bold for heading and sub topics. Maintain professional level of formatting.\n"
            "Do not use phrases like 'based on my knowledge' or 'depending on the information'.\n",
            "You can delegate tasks to an AI Agent in your team depending of their role and the tools available to them.",
        ],
        # Add extra instructions for using tools
        add_context_instructions=True,
        context_instructions=extra_instructions,
        # Add tools to the Agent
        tools=tools,
        # Add team members to the Agent
        team=team,
        # Show tool calls in the chat
        show_tool_calls=True,
        # This setting adds a tool to search the knowledge base for information
        search_knowledge=False,
        # This setting tells the LLM to format messages in markdown
        markdown=False,
        # This setting adds the current datetime to the instructions
        add_datetime_to_instructions=True,
        debug_mode=debug_mode,
    )
