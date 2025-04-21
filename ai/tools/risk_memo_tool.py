# ./backend/ai/tools/risk_memo_tool.py

import json
from typing import List
from agno.tools import Toolkit
from agno.utils.log import logger
import asyncio
from datetime import datetime, timedelta

from db.edgar_utils import (
    # download_cik_ticker_map,
    cik_from_ticker,
    download_all_cik_submissions,
    download_latest_filings,
    # download_financial_data
)
from db.utils import (
    parse_latest_filings,
    get_all_sections_from_risk_memo,
    get_filing_date_from_risk_memo,
)
from db.mongodb import check_document_exists_by_field, get_mongodb_client

if __package__:
    # If the script is run as part of a package, use relative imports.
    from .process_risk_memo import process_sections
    from .risk_memo_pdf_generator import RiskMemoGenerator
    from .market_data import get_company_profile, get_financial_overview
else:
    # If the script is run directly, use absolute imports.
    from process_risk_memo import process_sections
    from risk_memo_pdf_generator import RiskMemoGenerator
    from market_data import get_company_profile, get_financial_overview


class RiskMemoTool(Toolkit):
    def __init__(
        self,
        generate_risk_memo: bool = False,
    ):
        super().__init__(name="risk_memo_tool")

        if generate_risk_memo:
            self.register(self.generate_risk_memo)

    def _check_filings_freshness(self, ticker, cik):
        """
        Check if we have recent enough filings in the database.
        Returns True if filings need to be updated, False otherwise.

        Conditions for update:
        1. No risk memo exists in the database
        2. Missing any required sections
        3. New 10-K or 10-Q has been filed since our last update
        """
        today = datetime.now()
        ticker = ticker.lower()

        # Check if risk memo exists in database
        if not check_document_exists_by_field("risk_memos", "ticker", ticker):
            logger.info(f"No risk memo found for {ticker}. Need to download filings.")
            return True

        # Check for required sections and their content
        risk_memo = get_all_sections_from_risk_memo(ticker)

        # If there's an error getting sections, we need to refresh
        if "error" in risk_memo:
            logger.info(f"Error in risk memo for {ticker}. Need to download filings.")
            return True

        # Check if we have required sections
        required_sections = [
            "business",
            "risks and mitigation",
            "market risks",
            "management perspective",
            "legal proceedings",
            "supplementary financial data",
            "financial statements",
            "financial statement",
        ]

        for section in required_sections:
            # For financial statements, check for either "financial statements" or "financial statement"
            if (
                section == "financial statements"
                and "financial statement" in risk_memo
                and risk_memo.get("financial statement")
            ):
                continue
            if (
                section == "financial statement"
                and "financial statements" in risk_memo
                and risk_memo.get("financial statements")
            ):
                continue

            if section not in risk_memo or not risk_memo.get(section):
                logger.info(
                    f"Missing section {section} for {ticker}. Need to download filings."
                )
                return True

        # NEW: Check if new filings are available by querying the SEC submissions
        try:
            # Get the dates of our last stored filings
            last_10k_date = get_filing_date_from_risk_memo(ticker, "10-K")
            last_10q_date = get_filing_date_from_risk_memo(ticker, "10-Q")

            if not last_10k_date or not last_10q_date:
                logger.info(
                    f"Filing dates not found in database for {ticker}. Need to check for updates."
                )
                return True

            # Convert string dates to datetime objects for comparison
            if isinstance(last_10k_date, str):
                last_10k_date = datetime.strptime(last_10k_date, "%Y-%m-%d")
            if isinstance(last_10q_date, str):
                last_10q_date = datetime.strptime(last_10q_date, "%Y-%m-%d")

            # Get the latest submissions from MongoDB
            client = get_mongodb_client()
            db = client["company_eval"]
            submissions = db["submissions"].find_one({"_id": cik})

            if not submissions:
                logger.info(
                    f"No submissions found for {ticker} (CIK: {cik}). Need to download submissions."
                )
                return True

            # Check the recent filings for newer 10-K or 10-Q documents
            recent_filings = submissions["filings"]["recent"]

            # First check for quarterly updates (more frequent)
            latest_10q = None
            for i in range(len(recent_filings["form"])):
                if recent_filings["form"][i] == "10-Q":
                    filing_date = datetime.strptime(
                        recent_filings["filingDate"][i], "%Y-%m-%d"
                    )
                    if filing_date > last_10q_date:
                        latest_10q = filing_date
                        logger.info(
                            f"Found newer 10-Q filing from {filing_date.strftime('%Y-%m-%d')} for {ticker}"
                        )
                        return True

            # Then check for annual updates
            latest_10k = None
            for i in range(len(recent_filings["form"])):
                if recent_filings["form"][i] == "10-K":
                    filing_date = datetime.strptime(
                        recent_filings["filingDate"][i], "%Y-%m-%d"
                    )
                    if filing_date > last_10k_date:
                        latest_10k = filing_date
                        logger.info(
                            f"Found newer 10-K filing from {filing_date.strftime('%Y-%m-%d')} for {ticker}"
                        )
                        return True

            # If we're here, all filing dates are up to date
            logger.info(
                f"All filings for {ticker} are up to date. Using cached SEC filings."
            )
            return False

        except Exception as e:
            logger.error(f"Error checking filing dates for {ticker}: {str(e)}")
            # If we can't determine filing freshness, default to downloading fresh data
            return True

    def generate_risk_memo(self, ticker: str) -> str:
        try:
            ticker = ticker.upper()
            # STEP 1: Get Reference Data
            cik = cik_from_ticker(ticker)

            # STEP 2: Check if we need to download new filings
            need_filings_update = self._check_filings_freshness(ticker, cik)

            if need_filings_update:
                logger.info(f"Downloading CIK submissions for {ticker}")
                download_all_cik_submissions(cik)

                logger.info(f"Downloading latest filings for {ticker}")
                download_latest_filings(ticker)

                logger.info(f"Parsing latest filings for {ticker}")
                parse_latest_filings(cik)

                logger.info(f"Processing sections for {ticker}")
                process_response = process_sections(ticker)
                process_status = process_response["status"]
                logger.info(f"Process status: {process_status}")
            else:
                logger.info(
                    f"Using existing filings data for {ticker} - skipping section processing"
                )
                # Skip the section processing since we already have all the required sections in MongoDB
                # No need to call process_sections again which would regenerate drafts with LLM

            # STEP 3: Always refresh market data for up-to-date information
            logger.info(f"Refreshing company profile for {ticker}")
            get_company_profile(ticker)

            logger.info(f"Refreshing financial overview for {ticker}")
            get_financial_overview(ticker)

            # STEP 4: Generate Risk Memo PDF with latest data
            logger.info(
                f"Generating risk memo PDF with current market data and existing SEC filings"
            )
            generator = RiskMemoGenerator()
            file_name = generator.create_pdf(ticker)

            # STEP 5: adding a special character carat ^ to the file name and return
            rm_file_name = f"^{file_name}"
            logger.info(f"Risk memo generated: {rm_file_name}")
            return rm_file_name

        except Exception as e:
            response = f"error occurred: {str(e)}"
            logger.error(response)
            return response


# Example usage for RiskMemoTool
if __name__ == "__main__":
    risk_memo_tool = RiskMemoTool()
    file_name = risk_memo_tool.generate_risk_memo("AAPL")
    print(f"Generated risk memo file: {file_name}")
