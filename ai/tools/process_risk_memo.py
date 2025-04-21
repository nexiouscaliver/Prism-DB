# ai/tool/process_risk_memo.py

from ai.agents.risk_memo_drafter import memo_draft_agent
from db.utils import (
    get_section_text,
    add_section_to_risk_memo,
)
from typing import List
from db.mongodb import check_document_exists_by_field
import logging
import json
import traceback

from ai.tools.market_data import get_company_profile, get_financial_overview

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# LLM Call: Draft the risk memo sections
def draft_risk_memo(sections_commentary) -> str:
    try:
        draft_assistant = memo_draft_agent()
        memo_draft = draft_assistant.run(sections_commentary, stream=False)  # type: ignore
        # Extract content from RunResponse object
        if hasattr(memo_draft, "content"):
            return memo_draft.content
        return str(memo_draft)
    except Exception as e:
        logger.error(f"Error in draft_risk_memo: {e}")
        logger.error(traceback.format_exc())
        return f"Error generating draft: {str(e)}"


# Helper function to switch section names
def switch_section_name(section):
    section_name_switcher = {
        "business": "Business",
        "risk factors": "Risks and Mitigation",
        "quantitative and qualitative disclosures about market risk": "Market Risks",
        "management's discussion and analysis of financial condition and results of operations": "Management Perspective",
        "legal proceedings": "Legal Proceedings",
        "financial statements and supplementary data": "Supplementary Financial Data",
        "financial statement": "Financial Statements",
        "Peer Comparison": "Peer Comparison",
        "Analyst's Comments": "Analysts Comments",
    }
    return section_name_switcher.get(
        section, section
    )  # Default to original if not found


# RH: Writing this new method to process the sections in one go
def process_sections(ticker):
    ticker = ticker.lower()
    logger.info(f"Starting process_sections for ticker: {ticker}")

    # Initialize sections dictionary
    sections = {}

    # Check if the document already exists in parsed_documents
    if check_document_exists_by_field("risk_memos", "ticker", ticker):
        logger.info(
            f"Document with ticker {ticker} already exists in risk_memos. Checking for missing sections."
        )

        from db.utils import get_all_sections_from_risk_memo

        sections = get_all_sections_from_risk_memo(ticker)
        logger.info(f"Current sections in MongoDB: {list(sections.keys())}")

    # List of relevant sections
    relevant_sections = [
        "business",
        "risk factors",
        "quantitative and qualitative disclosures about market risk",
        "management's discussion and analysis of financial condition and results of operations",
        "legal proceedings",
        "financial statements and supplementary data",  # 10-k
        "financial statement",  # 10-Q
    ]

    total_sections = len(relevant_sections)
    successful_sections = 0

    for section in relevant_sections:
        try:
            # Check if this section already exists in the risk_memos collection
            section_name = switch_section_name(section).lower()

            # If section already exists in MongoDB and has content, skip processing
            if sections and section_name in sections and sections.get(section_name):
                logger.info(
                    f"Section '{section_name}' already exists with content. Skipping processing."
                )
                successful_sections += 1
                continue

            logger.info(f"Processing section: {section}")

            # 1. Get the text for the current section
            section_text = get_section_text(ticker, section)
            logger.info(
                f"Retrieved section text length: {len(section_text) if section_text else 0}"
            )

            # Parse section text to check if it's valid
            try:
                section_data = json.loads(section_text)
                if (
                    section_data.get("section_texts")
                    == "No sections found for the provided ticker and section name."
                ):
                    logger.warning(
                        f"No content found for section '{section}' in SEC filings"
                    )
                    continue
            except Exception as e:
                logger.error(f"Failed to parse section text: {e}")

            # 2. Generate the draft for each section ** LLM Call 2 ** LLM Memo drafter
            logger.info(f"Generating draft for section: {section}")
            draft_memo_response = draft_risk_memo(section_text)
            logger.info(
                f"Generated draft length: {len(draft_memo_response) if draft_memo_response else 0}"
            )

            if not draft_memo_response or (
                isinstance(draft_memo_response, str)
                and draft_memo_response.startswith("Error")
            ):
                logger.error(
                    f"Failed to generate draft for section {section}: {draft_memo_response}"
                )
                continue

            # 3. Add the summary to the risk_memos collection of MongoDB with the new section name
            # 3 a. Switch the section name to the new format
            new_section_name = switch_section_name(section)
            logger.info(f"Mapped section name: {section} -> {new_section_name}")

            # 3 b. DB Insertion
            response = add_section_to_risk_memo(
                ticker, new_section_name.lower(), draft_memo_response
            )
            logger.info(f"DB insertion response: {response}")

            successful_sections += 1

        except Exception as e:
            logger.error(f"Error processing section {section}: {e}")
            logger.error(traceback.format_exc())

    # 4. Process additional sections after relevant sections are done
    process_additional_section(ticker)

    # 5. Market data is now handled in the risk_memo_tool main function
    # We removed this section to avoid duplicate market data updates
    # and ensure real-time data is only fetched once right before PDF generation

    # Return a simple success message
    logger.info(
        f"Process completed with {successful_sections}/{total_sections} sections processed"
    )
    return {
        "status": "done",
        "message": f"Risk Memo for {ticker} successfully saved in db. {successful_sections}/{total_sections} sections processed.",
    }


# Generate text for sections that are not in SEC filings
def process_additional_section(ticker):
    logger.info(f"Processing additional sections for {ticker}")
    # List of additional sections to be processed directly
    additional_sections = ["Peer Comparison", "Analyst's Comments"]

    successful_sections = 0
    total_sections = len(additional_sections)

    for section in additional_sections:
        try:
            logger.info(f"Processing additional section: {section}")

            prompt = f"Write the {section} section for ticker {ticker} using your own knowledge and searching the web."
            logger.info(f"Using prompt: {prompt}")

            # Generate the draft directly using the section name ** LLM Call **
            draft_memo_response = draft_risk_memo(prompt)
            logger.info(
                f"Generated additional section length: {len(draft_memo_response) if draft_memo_response else 0}"
            )

            if not draft_memo_response or (
                isinstance(draft_memo_response, str)
                and draft_memo_response.startswith("Error")
            ):
                logger.error(
                    f"Failed to generate draft for additional section {section}: {draft_memo_response}"
                )
                continue

            # Add the draft to the risk_memos collection of MongoDB using the section name directly
            new_section_name = switch_section_name(section)
            logger.info(f"Mapped section name: {section} -> {new_section_name}")

            response = add_section_to_risk_memo(
                ticker, new_section_name.lower(), draft_memo_response
            )
            logger.info(f"DB insertion response for additional section: {response}")
            successful_sections += 1

        except Exception as e:
            logger.error(f"Error processing additional section {section}: {e}")
            logger.error(traceback.format_exc())

    logger.info(
        f"Additional section processing completed with {successful_sections}/{total_sections} sections processed"
    )
    return {
        "status": "done",
        "message": f"Additional sections for {ticker} successfully saved in db. {successful_sections}/{total_sections} sections processed.",
    }
