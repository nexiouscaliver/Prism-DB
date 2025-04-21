# ./backend/ai/sec.py

import json
from typing import List, Union, Optional
from pymongo import MongoClient
from agno.tools import Toolkit
from agno.utils.log import logger
from .string_reader import StringReader
# from agno.knowledge.base import AssistantKnowledge
from pydantic import BaseModel

from db.edgar_utils import (
    download_cik_ticker_map,
    cik_from_ticker,
    download_all_cik_submissions,
    download_latest_filings,
    download_financial_data,
)
from db.utils import parse_latest_filings, get_section_text


class SecTool(Toolkit):
    def __init__(
        self,
        get_reference_data: bool = False,
        get_filing_data: bool = False,
        parse_filing_data: bool = False,
        get_section: bool = False,
        # get_filing_section_in_kb: bool = True,
    ):
        super().__init__(name="sec_tool")

        if get_reference_data:
            self.register(self.get_reference_data)
        if get_filing_data:
            self.register(self.get_filing_data)
        if parse_filing_data:
            self.register(self.parse_filing_data)
        if get_section:
            self.register(self.get_section)
        # if get_filing_section_in_kb:
        # self.register(self.get_filing_section_in_kb)

        # knowledge_base=AssistantKnowledge(
        #     vector_db=PgVector2(
        #         db_url=db_url,
        #         collection="llm_os_documents",
        #         embedder=OpenAIEmbedder(model=ai_settings.embedding_model, dimensions=1536),
        #     )
        # knowledge_base

    #     # Get agent for KB without any tools
    #     def get_kb_agent(
    #         agent_type: AgentType,
    #         session_id: Optional[str] = None,
    #         user_id: Optional[str] = None,
    #     ):
    #         """Return the agent"""

    #         agent = agent(
    #     llm=OpenAIChat(model="gpt-4o"),
    #     description="You help people with their health and fitness goals.",
    #     instructions=["Recipes should be under 5 ingredients"],
    # )
    #         if agent == "LLM_OS":
    #             return get_llm_os(
    #                 calculator=False,
    #                 ddg_search=False,
    #                 file_tools=False,
    #                 finance_tools=False,
    #                 python_assistant=False,
    #                 research_assistant=False,
    #                 openbb_tools=False,
    #                 session_id=session_id,
    #                 user_id=user_id
    #             )

    #     class LoadStringRequest(BaseModel):
    #         assistant: AssistantType = "LLM_OS"
    #         session_id: Optional[str] = None
    #         user_id: Optional[str] = None
    #         doc_name: Optional[str] = None
    #         document: Optional[str] = None

    #     async def load_string(body: LoadStringRequest ) -> str:
    #         """Loads a string as a document into the knowledge base for an Assistant and returns a JSON string with a status update."""

    #         try:
    #             assistant = get_kb_assistant(assistant_type=body.assistant, session_id=body.session_id, user_id=body.user_id)
    #             if not hasattr(assistant, 'knowledge_base'):
    #                 return json.dumps({"error": "This assistant does not support a knowledge base."})

    #             document = body.document

    #             print(f"Document Received inside load_string: {document[:500]}...")

    #             # Use the StringReader to read the content
    #             reader = StringReader()
    #             doc_name = body.doc_name

    #             try:
    #                 file_documents = reader.read(document, doc_name)
    #             except Exception as e:
    #                 return json.dumps({"error": f"Failed to read text content: {str(e)}"})

    #             if file_documents:
    #                 assistant.knowledge_base.load_documents(file_documents, upsert=True)
    #                 response = {"operation": "string_load", "status": "success", "doc_name": body.doc_name}
    #                 return json.dumps(response)
    #             else:
    #                 return json.dumps({"error": f"Could not read text from string content: {body.doc_name}"})

    #         except Exception as e:
    #             return json.dumps({"error": str(e)})

    def get_reference_data(self, tickers: List[str]) -> str:
        download_cik_ticker_map()
        for ticker in tickers:
            cik = cik_from_ticker(ticker)
            download_all_cik_submissions(cik)
        return json.dumps({"operation": "get_reference_data", "status": "success"})

    def get_filing_data(self, tickers: List[str]) -> str:
        for ticker in tickers:
            download_latest_filings(ticker)
            cik = cik_from_ticker(ticker)
            download_financial_data(cik)
        return json.dumps({"operation": "get_filing_data", "status": "success"})

    def parse_filing_data(self, tickers: List[str]) -> str:
        for ticker in tickers:
            try:
                cik = cik_from_ticker(ticker)
                if cik:
                    parse_latest_filings(cik)
                else:
                    logger.error(f"CIK not found for {ticker}")
            except Exception as e:
                logger.error(f"Failed to parse filings for {ticker}. Error: {e}")
        return json.dumps({"operation": "parse_filing_data", "status": "success"})

    def get_section(self, ticker: str, section_name: str) -> str:
        section_name = section_name.lower()
        # Parse the JSON response to a Python dictionary
        response = get_section_text(ticker, section_name)

        extracted_section_text = response.get("section_text", None)

        if extracted_section_text:
            return extracted_section_text
        else:
            return f"No section text found for {ticker} {section_name}."

    # async def get_filing_section_in_kb(self, ticker: str, section_name: str) -> str:
    #     # tickers = [ticker]
    #     # section_names = [section_name]

    #     # self.get_reference_data(tickers)
    #     # self.get_filing_data(tickers)
    #     # self.parse_filing_data(tickers)

    #     # Parse the JSON response to a Python dictionary
    #     response = await asyncio.to_thread(get_section_text, ticker, section_name)

    #     extracted_section_text = response.get("section_text", None)

    #     if extracted_section_text:
    #         if not isinstance(extracted_section_text, str):
    #             raise TypeError(f"Expected extracted_section_text to be str, got {type(extracted_section_text)}")

    #         # not needed aymore because we've written a string reader class - delete this later on
    #         # binary_data = extracted_section_text.encode('utf-8')

    #         body = LoadStringRequest(
    #             assistant="LLM_OS",
    #             session_id=None,
    #             user_id="rhytik",
    #             doc_name=f"{ticker}_{section_name.replace(' ', '_')}",
    #             document=extracted_section_text,
    #         )
    #         return await load_string(body)
    #     else:
    #         return json.dumps({"message": "No section text extracted to load into knowledge base."})


# Example usage
if __name__ == "__main__":
    import asyncio

    sec_tool = SecTool()
    asyncio.run(sec_tool.get_filing_section_in_kb("AAPL", "business"))
