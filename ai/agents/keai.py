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

from agno.tools import Toolkit
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.exa import ExaTools
from agno.tools.yfinance import YFinanceTools
from agno.vectordb.pgvector import PgVector, SearchType

from ai.settings import ai_settings
from db.session import db_url
from workspace.settings import ws_settings
import os
from agno.utils.log import logger as logging
from agno.models.deepseek import DeepSeek  # import deepseek model
from agno.tools.firecrawl import FirecrawlTools
from agno.models.google import Gemini # import google model
from agno.tools.tavily import TavilyTools # import tavily tools

# Import the new Database Explorer Tool
from ..tools.database_explorer_tool import DatabaseExplorerTool
from ..agents.pgmcpagent import DatabaseExplorerAgent
# Import our new URL Research Agent
from ai.tools.url_search_pdf_agent import URLResearchAgent

# from agno.document.chunking.semantic import SemanticChunking
# import asyncio
# from agno.workflow import Workflow, Task
# from agno.tools.openbb_tools import OpenBBTools
# from .tools.sec import SecTool

from ai.tools.risk_memo_tool import RiskMemoTool
logging.info(f"DB URL USED : {db_url}")


def get_web_keai(
    model_name: str = None,
    google_search: bool = True,  # rename to google_search
    exa_search: bool = False,
    tavily_search: bool = False,
    finance_tools: bool = False,
    risk_memo_tool: bool = False,
    # openbb_tools: bool = False,
    firecrawl_tool: bool = False,
    research_agent: bool = False,
    url_research_agent: bool = False,  # New parameter for our enhanced URL research agent
    database_explorer_tool: bool = False,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    print("Using get_web_keai. model_name =  {}".format(model_name),f"DB URL USED : {db_url}")
    logging.debug(f"DB URL USED : {db_url}")

    # Initialize the model based on model_name
    if model_name == "claude-3-5-sonnet":
        model = Claude(id="anthropic.claude-3-5-sonnet-20240620-v1:0")
        
    elif model_name == "deepseek-v3":
        print("Using DeepSeek model called deepseek-chat")
        # print(os.getenv("DEEPSEEK_API_KEY"))
        model = DeepSeek(id="deepseek-chat")

    elif model_name == "gemini-flash-2.0":

        model = Gemini(id="gemini-2.0-flash")
    
    elif model_name == "o3-mini":
        model = OpenAIChat(id="o3-mini-2025-01-31")
        print(f"Using o3-mini model")

    else:
        # model = OpenAIChat(id=model_name)
        model_name = "gpt-4o-mini"
        model = OpenAIChat(id=model_name)
        print(f"Using {model_name} model in the absence of any other model.")

    # Add tools available to the Personalized Agent
    tools: List[Toolkit] = []
    
    # Extra instructions for using tools - converting to dictionary format
    extra_instructions: Dict[str, str] = {}

    if google_search:
        # tools.append(DuckDuckGoTools(fixed_max_results=5))
        tools.append(GoogleSearchTools(fixed_max_results=10, fixed_language="en"))
        extra_instructions["GoogleSearchTools"] = """
When the user's query requires general information retrieval or fact-finding, utilize the `GoogleSearchTools` tool.
Example: {"name": "google_search", "arguments": {"query": "your search term"}}
Example: {"name": "update_memory", "arguments": {"task": "Your task description"}}
Prioritize `GoogleSearchTools` for broad searches and diverse topics to ensure comprehensive results.
If the user's request involves in-depth analysis or research-oriented tasks, `ExaTools` is preferred over `GoogleSearchTools` due to its advanced search capabilities.
If you don't receive an answer from the `GoogleSearchTools` tool, you can use the `ExaTools` tool to get a search response.
"""

    if exa_search:
        # Updated for Agno compatibility - removed summary parameter
        tools.append(ExaTools(
            num_results=10,
            text=True,
            highlights=True
        ))
        extra_instructions["ExaTools"] = """
Employ the `ExaTools` tool for online searches, especially when needing structured data or specific document types.
If the user's request involves in-depth analysis or research-oriented tasks, `ExaTools` is preferred over `GoogleSearchTools` due to its advanced search capabilities.
If you don't receive an answer from the `GoogleSearchTools` tool, you can use the `ExaTools` tool to get more structured data and response.
Example: {"name": "exa_search", "arguments": {"query": "your search term"}}
Make sure to present the response in a clear and concise manner to the user.
"""

    if tavily_search:
        tools.append(TavilyTools(max_tokens=6000))
        extra_instructions["TavilyTools"] = """
Use the `TavilyTools` tool for online searches to get context-based results and an AI-generated summary of the search findings.
The `TavilyTools` provides both raw search results and a synthesized AI summary, making it excellent for complex queries that need condensed information.
If the user's request involves in-depth analysis or research-oriented tasks, `TavilyTools` is preferred over `GoogleSearchTools` due to its contextual understanding and summarization capabilities.
When you need the most relevant information quickly without having to process multiple search results manually, use `TavilyTools`.
Example: {"name": "tavily_search", "arguments": {"query": "your search term"}}
Make sure to present the response in a clear and concise manner to the user.
"""

    if finance_tools:
        tools.append(
            YFinanceTools(
                stock_price=True,
                company_info=True,
                analyst_recommendations=True,
                company_news=True,
                historical_prices=True,
                stock_fundamentals=True,
                key_financial_ratios=True,
            )
        )
        extra_instructions["YFinanceTools"] = "Utilize the `YFinanceTools` tool to answer any queries related to company financials, stock information, or financial news. Ensure accurate and up-to-date financial data is provided."

    if risk_memo_tool:
        tools.append(RiskMemoTool(generate_risk_memo=True))
        extra_instructions["RiskMemoTool"] = "Use the `RiskMemoTool` tool to generate risk memo for a given company by passing the ticker symbol. And **importantly** return the same response that you will receive from the tool without adding any additional text."

    if firecrawl_tool:
        # Updated for Agno compatibility
        tools.append(FirecrawlTools(crawl=True))
        extra_instructions["FirecrawlTools"] = """
If the user explicitly mentions a URL and requests crawling or scraping of that specific website, use the `FirecrawlTools` tool.
Provide the URL as an argument to the `FirecrawlTools` to extract relevant information from the website.
Example: {"name": "firecrawl", "arguments": {"url": "the website URL to crawl or scrape"}}
Ensure that the URL is valid and accessible before using the `FirecrawlTools`.
Only use `FirecrawlTools` when a URL is explicitly provided by the user for crawling or scraping purposes.
Save the extracted information in a structured format temporarily for the session for future reference.
Make sure to present the response in a clear and concise manner to the user.
"""

# if openbb_tools:
    #     tools.append(OpenBBTools(obb=obb, company_profile=True, company_news=True, price_targets=True))
    #     extra_instructions["OpenBBTools"] = "You can use the `openbb_search` tool to search the OpenBB database for finance related questions."

    # if sec_tools:
    #     tools.append(SecTool(get_reference_data=False, get_filing_data=False,
    #                          parse_filing_data=False, get_filing_section_in_kb=True))
    #     extra_instructions["SecTool"] = "You can use the `sec_tools` when asked to do a company eval or to get sec filing data in kb. You can work with this tool asynchronously and let user know you have delegated the task and it will get completed soon"

    # Add team members available to the keai
    team: List[Agent] = []

    if research_agent:
        _research_agent = Agent(
            model=model,
            name="Research Agent",
            role="Write a research report on a given topic",
            description="You are a Senior New York Times researcher tasked with writing a cover story research report.",
            instructions=[
                "For a given topic, use the `search_exa` to get the top 10 search results.",
                "Carefully read the results and generate a final - NYT cover story worthy report in the format provided below.",
                "Make your report engaging, informative, and well-structured.",
                "Remember: you are writing for the New York Times, so the quality of the report is important.",
                "Remember: At minimum your response needs 5000 characters or more for the report.",
            ],
            expected_output=dedent(
                """\
            An engaging, informative, and well-structured report in the following format:

            ## Title

            - **Overview** Brief introduction of the topic.
            - **Importance** Why is this topic significant now?

            ### Section 1
            - **Detail 1**
            - **Detail 2**
            - **Detail 3**

            ### Section 2
            - **Detail 1**
            - **Detail 2**
            - **Detail 3**
            
            ### Section 3
            - **Detail 1**
            - **Detail 2**
            - **Detail 3**
            
            ## Conclusion
            - **Summary of report:** Recap of the key findings from the report.
            - **Implications:** What these findings mean for the future.

            ## References
            - [Reference 1](Link to Source)
            - [Reference 2](Link to Source)
            """
            ),
            tools=[ExaTools(
                num_results=5,
                text=True,
                highlights=True
            )],
            # This setting tells the LLM to format messages in markdown
            markdown=True,
            show_tool_calls=False,
            add_datetime_to_instructions=True,
            save_response_to_file="scratch/{session_id}.md",
            debug_mode=debug_mode,
        )
        team.append(_research_agent)
        extra_instructions["Research Agent"] = "To write a research report, delegate the task to the `Research Agent`. Return the report in the <report_format> to the user as is, without any additional text like 'here is the report'."
    
    # Add our new URL Research Agent with PDF output
    if url_research_agent:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        GENERATED_FILES_DIR = os.path.join(base_dir, "..", "..", "generated_files")
        os.makedirs(GENERATED_FILES_DIR, exist_ok=True)
        _url_research_agent = URLResearchAgent.create(
            model=model,
            session_id=session_id,
            user_id=user_id,
            output_dir=GENERATED_FILES_DIR,
            max_pages=8,  # Changed from default to explicit 8
            debug_mode=debug_mode
        )
        team.append(_url_research_agent)
        extra_instructions["URL Search Agent"] = """
If the input prompt is: 'I need a report on this website: <URL>' or 'Generate report on this website: <URL>', delegate the task to the `URL Search Agent`.
This agent will generate an enterprise-grade research report based on website content and automatically save it as a properly formatted PDF document that preserves all markdown formatting.
The agent will return the paths to both the markdown and PDF files for easy access.
When you receive a response from the **URL Search Agent**, **always** return the response **exactly as received**, without adding any additional text or formatting.
Always return the response in the '^<report_name>' to the user as is, without any additional text like 'here is the report' or anything else. The ^ character is important.
"""

    if database_explorer_tool:
        # We need to create the database explorer agent synchronously since we're in a sync context
        async def create_db_agent():
            # Use the new DatabaseExplorerAgent.create method
            create_agent_func = DatabaseExplorerAgent.create(
                model=model,
                postgress_url=db_url,
                session_id=session_id,
                user_id=user_id,
                debug_mode=debug_mode
            )
            return await create_agent_func()
            
        # Create a new event loop to run the async function
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            agent = loop.run_until_complete(create_db_agent())
        finally:
            loop.close()
            
        team.append(agent)
        extra_instructions["DatabaseExplorerTool"] = """
Use the `explore_and_report` tool when the user asks for a database structure analysis, exploration, or report.
This tool will automatically run a deep scan of the connected database, generate a markdown report, convert it to PDF, and return the PDF filename.
Think about the user's request and decide what is the best way to explore the database.
Explore the database structure, generate a report, and attempt to reason with the user's request.
Example: {"name": "explore_and_report", "arguments": {}}
**IMPORTANT**: When you receive a response from this tool (it will start with '^'), you MUST return that response string *exactly* as is, with no modifications or additional text.
"""

    if model_name == "deepseek-v3":
        return Agent(
            model=model,
            name="keai",
            session_id=session_id,
            user_id=user_id,
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
                # chunking_strategy=SemanticChunking(),
                # 3 references are added to the prompt
                num_documents=3,
            ),
            description=dedent(
                """\
            You are the most advanced AI system in the world called `RegenAI`.
            You have access to a set of tools and a team of AI Agents at your disposal.
            Your goal is to assist the user in the best way possible.\
            """
            ),
            instructions=[
                "When the user sends a message, first **think** and determine if:\n"
                " - You can answer by using a tools available to you\n"
                " - You need to search the knowledge base\n"
                " - You need to search the internet using your own capabilities if you don't have browsing capabilities then use the `google_search` tool.\n"
                " - You need to use the 'risk_memo_tool' to create or generate risk memos\n",
                " - You need to delegate the task to a team member\n"
                " - You need to ask a clarifying question\n",
                "If the user asks about a topic, first ALWAYS search your knowledge base using the `search_knowledge_base` tool.\n",
                "If the user asks for a database structure analysis, exploration, or report or the user message starts with the word 'db', use the `explore_and_report` tool with the user message as the argument.\n",
                "If the user asks to generate or create 'risk memo' use the 'risk_memo_tool'.\n",
                "If the user asks for website analysis or research with a specific URL, delegate this task to the `URL Search Agent` which will generate a PDF report.",
                "When a response is received from the 'risk_memo_tool' there is file name in the response which you need to send back to the user as is without adding any more text. Return the received response as is.\n",
                "When a response is received from the 'url_search_tool' there is file name in the response which you need to send back to the user as is without adding any more text. Return the received response as is.\n",
                "When you receive a response from the **RiskMemoTool**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "When you receive a response from the **url_search_tool**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "When you receive a response from the **URLSearchTool**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "When you receive a response from the **research_website**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "When you receive a response from the **ResearchWebsite**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                # "When a response is received from the 'risk_memo_tool' the response is structured as json string which you need to send back to the user as is without altering anything. Return the received response as is.\n",
                "If you don't find relevant information in your knowledge base, see if you have ability to search internet, if not then use the `google_search` tool to search the internet.\n",
                "If the user asks to summarise the conversation, use the `get_chat_history` tool with None as the argument.\n",
                "If the users message is unclear, ask clarifying questions to get more information.\n",
                "Carefully read the information you have gathered and provide a clear and concise answer to the user.\n",
                "Do not use phrases like 'based on my knowledge' or 'depending on the information'.\n",
                "You can delegate tasks to an AI Agent in your team depending of their role and the tools available to them.",
                "When a user asks for website analysis or research with a specific URL, delegate this task to the `URL Search Agent` which will generate a PDF report.",
                "**ALYWAS STRICTLY FOLLOW THIS RULE** : When you receive a response from any **Agent** or **Tool** in the team and the response is a **File name** with .pdf extension, you need to send back the file name to the user as is without adding any more text or removing. Return the received response as is. If the response doesn't contain the special symbol '^' then you need to **add it before** the file name.",
                "**EXCEPTION TO ABOVE RULE**: If the response comes specifically from the `explore_and_report` tool (which already starts with '^'), return that response *exactly* as received."
            ],
            # Add extra instructions for using tools
            # add_context_instructions=True,  # Commented out to avoid adding extra instructions to the DeepSeek model
            #context_instructions=extra_instructions,
            # Add tools to the Agent
            # tools=tools,   # Commented out to avoid adding tools to the DeepSeek model
            # Add team members to the Agent
            # team=team,  # Commented out to avoid adding team members to the DeepSeek model
            # Show tool calls in the chat
            show_tool_calls=True,
            # Reasoning whcih can fail 20% of the time
            # reasoning=True,
            # This setting adds a tool to search the knowledge base for information
            search_knowledge=False,
            # Add a tool to read chat history.
            read_chat_history=False,
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
            Hi, I'm RegenAI your research agent.
            I have access to a set of tools to assist you.
            Let's get started!\
            """
            ),
            debug_mode=debug_mode,
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
                auto_upgrade_schema=True,
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
                # chunking_strategy=SemanticChunking(),
                # 3 references are added to the prompt
                num_documents=3,
            ),
            description=dedent(
                """\
        You are the most advanced AI system in the world called `RegenAI`.
        You have access to a set of tools and a team of AI Agents at your disposal.
        Your goal is to assist the user in the best way possible.\
        """
            ),
            instructions=[
                "When the user sends a message, first **think** and determine if:\n"
                " - You can answer by using a tools available to you\n"
                " - You need to search the knowledge base\n"
                " - You need to search the internet using your own capabilities if you don't have browsing capabilities then use the `google_search` tool.\n"
                " - You need to use the 'risk_memo_tool' to create or generate risk memos\n",
                " - You need to delegate the task to a team member\n"
                " - You need to ask a clarifying question\n",
                "If the user asks about a topic, first ALWAYS search your knowledge base using the `search_knowledge_base` tool.\n",
                "If the user asks for a database structure analysis, exploration, or report, use the `explore_and_report` tool.\n",
                "If the user asks to generate or create 'risk memo' use the 'risk_memo_tool'.\n",
                "If the user asks for website analysis or research with a specific URL, delegate this task to the `URL Search Agent` which will generate a PDF report.",
                "When a response is received from the 'risk_memo_tool' there is file name in the response which you need to send back to the user as is without adding any more text. Return the received response as is.\n",
                "When a response is received from the 'url_search_tool' there is file name in the response which you need to send back to the user as is without adding any more text. Return the received response as is.\n",
                "When you receive a response from the **RiskMemoTool**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "When you receive a response from the **url_search_tool**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "When you receive a response from the **URLSearchTool**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "When you receive a response from the **research_website**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "When you receive a response from the **ResearchWebsite**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                # "When a response is received from the 'risk_memo_tool' the response is structured as json string which you need to send back to the user as is without altering anything. Return the received response as is.\n",
                "If you don't find relevant information in your knowledge base, see if you have ability to search internet, if not then use the `google_search` tool to search the internet.\n",
                "If the user asks to summarise the conversation, use the `get_chat_history` tool with None as the argument.\n",
                "If the users message is unclear, ask clarifying questions to get more information.\n",
                "Carefully read the information you have gathered and provide a clear and concise answer to the user.\n",
                "Do not use phrases like 'based on my knowledge' or 'depending on the information'.\n",
                "You can delegate tasks to an AI Agent in your team depending of their role and the tools available to them.",
                "When a user asks for website analysis or research with a specific URL, delegate this task to the `URL Search Agent` which will generate a PDF report.",
                "**ALYWAS STRICTLY FOLLOW THIS RULE** : When you receive a response from any **Agent** or **Tool** in the team and the response is a **File name** with .pdf extension, you need to send back the file name to the user as is without adding any more text or removing. Return the received response as is. If the response doesn't contain the special symbol '^' then you need to **add it before** the file name.",
                "**EXCEPTION TO ABOVE RULE**: If the response comes specifically from the `explore_and_report` tool (which already starts with '^'), return that response *exactly* as received."
            ],
            # Add extra instructions for using tools
            # add_context_instructions=True,   comment out when migration to agno - not exist
            #context_instructions=extra_instructions,  comment out when migration to agno - not exist
            add_context=True,
            context=extra_instructions,
            # Add tools to the Agent
            tools=tools,
            # Add team members to the Agent
            team=team,
            # Show tool calls in the chat
            show_tool_calls=False,
            # Reasoning whcih can fail 20% of the time
            # reasoning=True,
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
        Hi, I'm RegenAI your research agent.
        I have access to a set of tools to assist you.
        Let's get started!\
        """
            ),
            debug_mode=debug_mode,
        )