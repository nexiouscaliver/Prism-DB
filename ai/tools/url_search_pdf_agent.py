"""URL Research Agent - Enterprise-grade website analysis agent"""
import os
import logging
from typing import Optional, Dict, Any, Union
from textwrap import dedent
from datetime import datetime
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic.claude import Claude
from .url_search_pdf_tool import URLSearchPDFTool, GENERATED_FILES_DIR

logger = logging.getLogger(__name__)

class URLResearchAgent:
    """Factory class for creating URL Research Agents with PDF output capabilities."""
    
    @staticmethod
    def create(
        model: Union[str, OpenAIChat, Claude],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None, 
        output_dir: str = GENERATED_FILES_DIR,
        max_pages: int = 8,  # Changed default
        debug_mode: bool = False
    ) -> Agent:
        """
        Create a URL Research Agent instance configured for enterprise-grade 
        website analysis with PDF output.
        
        Args:
            model: LLM model to use (string ID or model instance)
            session_id: Optional session identifier 
            user_id: Optional user identifier
            output_dir: Directory to save generated files
            max_pages: Maximum number of pages to crawl
            debug_mode: Enable debug logging
            
        Returns:
            Agent: Fully configured URL Research Agent
        """
        # Handle model input
        if isinstance(model, str):
            if model.startswith("claude"):
                model = Claude(id=model)
            else:
                model = OpenAIChat(id=model)
        
        # Ensure output directory is absolute and exists
        if not os.path.isabs(output_dir):
            output_dir = GENERATED_FILES_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        # Create and configure the URL search tool
        url_search_tool = URLSearchPDFTool(
            max_pages=max_pages,
            save_to_pdf=True,
            output_dir=output_dir
        )
        
        # Configure simple post-processing to format the response correctly
        def post_process_response(response, agent_session_id=session_id):
            try:
                # Simply ensure the response is properly formatted
                # No need to generate PDFs here as it's done directly in the tool
                if "PDF: ^" not in response:
                    logger.warning("Response does not contain PDF path marker - PDF generation may have failed")
                return response
            except Exception as e:
                logger.error(f"Error in post-processing: {str(e)}", exc_info=True)
                return response
        
        # Create the agent configuration
        agent_config = {
            "model": model,
            "name": "website_research_agent",
            "role": "Generate comprehensive research reports from websites using tools",
            "description": "Analyze websites and create detailed research reports with PDF output using the tools given",
            "instructions": [
                "For a given website URL, use the url_search_tool tool and crawl up to 8 pages of the site.",
                # "The tool will automatically generate both a Markdown report and PDF version for you.",
                # "Review the tool output and present the results to the user with proper formatting.",
                # "Be sure to include the paths to both the Markdown and PDF files in your response.",
                "When you receive a response from the **url_search_tool**, **always** return the response **exactly as received**, without adding any additional text or formatting.",
                "The response will contain ONLY this format : `^<path_to_pdf>`",
                "do not respond anything else. ONLY THE RETURN VALUE RECIEVED FROM THE TOOL.",
                "ALWAYS RETURN THE RESPONSE in format `^<path_to_pdf>` , where `<path_to_pdf>` is the path to the generated PDF file , ^ is important.",
                "Ensure to handle any potential issues with response formatting. Response format : `^<path_to_pdf>` "
            ],
            "tools": [url_search_tool],
            "markdown": True,
            "show_tool_calls": False,
            "add_datetime_to_instructions": True,
            "save_response_to_file": f"{output_dir}/{session_id}.md" if session_id else None,
            "debug_mode": debug_mode,
        }
        
        return Agent(**agent_config)