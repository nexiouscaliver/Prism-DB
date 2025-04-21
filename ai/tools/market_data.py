import requests
from dotenv import load_dotenv
import os
from db.utils import add_section_to_risk_memo
import logging
import pandas as pd
import numpy as np
import markdown
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_company_profile(ticker):
    load_dotenv()
    api_key = os.getenv("FMP_API")
    ticker = ticker.lower()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        logger.info(f"Fetching real-time company profile for {ticker} at {timestamp}")
        # Fetch financial profile data from the API
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker.upper()}?apikey={api_key}"
        profile_response = requests.get(profile_url)
        profile_response.raise_for_status()  # Raise an error for bad status codes
        profile = profile_response.json()[0]

        # Extract the logo URL and other market data
        logo_url = profile["image"]
        company_name = profile["companyName"]
        industry = profile["industry"]
        description = profile["description"]
        price = profile["price"]
        beta = profile["beta"]
        vol_avg = profile["volAvg"]
        mkt_cap = profile["mktCap"]
        last_div = profile["lastDiv"]

        # Prepare the overview data as a plain text string with Markdown formatting
        profile_data = (
            f"### Profile\n"
            f"- **Company Name**: {company_name}\n"
            f"- **Industry**: {industry}\n"
            f"- **Description**: {description}\n"
            f"- ![Logo]({logo_url})\n\n"
            f"### Market Data (REAL-TIME as of {timestamp})\n"
            f"- **Price**: ${price:,.2f}\n"
            f"- **Beta**: {beta}\n"
            f"- **Volume Average**: {vol_avg:,}\n"
            f"- **Market Cap**: ${mkt_cap:,.2f}\n"
            f"- **Last Dividend**: ${last_div:,.2f}\n"
        )

        # Add the overview section to the risk_memos collection
        response = add_section_to_risk_memo(ticker, "profile", profile_data)
        # Store timestamp to know when market data was last updated
        add_section_to_risk_memo(ticker, "market_data_timestamp", timestamp)

        logger.info(
            f"Real-time market data for {ticker} successfully added to the database."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching market data: {e}")
    except Exception as e:
        logger.error(f"Error processing market data for {ticker}: {e}")
    finally:
        logger.info(f"Finished processing market data for {ticker}.")

    return response


def get_financial_overview(ticker):
    load_dotenv()
    api = os.getenv("FMP_API")
    ticker = ticker.lower()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Fetching real-time financial overview for {ticker} at {timestamp}")

    millions = 1000000
    dates = [2023, 2022, 2021, 2020, 2019]

    # API Endpoints
    urls = {
        "income_statement": f"https://financialmodelingprep.com/api/v3/income-statement/{ticker.upper()}?apikey={api}",
        "balance_sheet": f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker.upper()}?apikey={api}",
        "cash_flow": f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker.upper()}?apikey={api}",
        "ratios": f"https://financialmodelingprep.com/api/v3/ratios/{ticker.upper()}?apikey={api}",
        "key_metrics": f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker.upper()}?apikey={api}",
        "profile": f"https://financialmodelingprep.com/api/v3/profile/{ticker.upper()}?apikey={api}",
    }

    # Fetch data from APIs
    data = {key: requests.get(url).json() for key, url in urls.items()}

    # Create a dictionary to hold financial data
    financials = {}

    for item in range(5):
        year = dates[item]
        financials[year] = {
            "Mkt Cap": data["key_metrics"][item]["marketCap"] / millions,
            "Debt to Equity": data["key_metrics"][item]["debtToEquity"],
            "Debt to Assets": data["key_metrics"][item]["debtToAssets"],
            "Revenue per Share": data["key_metrics"][item]["revenuePerShare"],
            "NI per Share": data["key_metrics"][item]["netIncomePerShare"],
            "Revenue": data["income_statement"][item]["revenue"] / millions,
            "Gross Profit": data["income_statement"][item]["grossProfit"] / millions,
            "R&D Expenses": data["income_statement"][item][
                "researchAndDevelopmentExpenses"
            ]
            / millions,
            "Op Expenses": data["income_statement"][item]["operatingExpenses"]
            / millions,
            "Op Income": data["income_statement"][item]["operatingIncome"] / millions,
            "Net Income": data["income_statement"][item]["netIncome"] / millions,
            "Cash": data["balance_sheet"][item]["cashAndCashEquivalents"] / millions,
            "Inventory": data["balance_sheet"][item]["inventory"] / millions,
            "Cur Assets": data["balance_sheet"][item]["totalCurrentAssets"] / millions,
            "LT Assets": data["balance_sheet"][item]["totalNonCurrentAssets"]
            / millions,
            "Int Assets": data["balance_sheet"][item]["intangibleAssets"] / millions,
            "Total Assets": data["balance_sheet"][item]["totalAssets"] / millions,
            "Cur Liab": data["balance_sheet"][item]["totalCurrentLiabilities"]
            / millions,
            "LT Debt": data["balance_sheet"][item]["longTermDebt"] / millions,
            "LT Liab": data["balance_sheet"][item]["totalNonCurrentLiabilities"]
            / millions,
            "Total Liab": data["balance_sheet"][item]["totalLiabilities"] / millions,
            "SH Equity": data["balance_sheet"][item]["totalStockholdersEquity"]
            / millions,
            "CF Operations": data["cash_flow"][item][
                "netCashProvidedByOperatingActivities"
            ]
            / millions,
            "CF Investing": data["cash_flow"][item]["netCashUsedForInvestingActivites"]
            / millions,
            "CF Financing": data["cash_flow"][item][
                "netCashUsedProvidedByFinancingActivities"
            ]
            / millions,
            "CAPEX": data["cash_flow"][item]["capitalExpenditure"] / millions,
            "FCF": data["cash_flow"][item]["freeCashFlow"] / millions,
            "Dividends Paid": data["cash_flow"][item]["dividendsPaid"] / millions,
            "Gross Profit Margin": data["ratios"][item]["grossProfitMargin"],
            "Op Margin": data["ratios"][item]["operatingProfitMargin"],
            "Int Coverage": data["ratios"][item]["interestCoverage"],
            "Net Profit Margin": data["ratios"][item]["netProfitMargin"],
            "Dividend Yield": data["ratios"][item]["dividendYield"],
            "Current Ratio": data["ratios"][item]["currentRatio"],
            "Operating Cycle": data["ratios"][item]["operatingCycle"],
            "Days of AP Outstanding": data["ratios"][item]["daysOfPayablesOutstanding"],
            "Cash Conversion Cycle": data["ratios"][item]["cashConversionCycle"],
            "ROA": data["ratios"][item]["returnOnAssets"],
            "ROE": data["ratios"][item]["returnOnEquity"],
            "ROCE": data["ratios"][item]["returnOnCapitalEmployed"],
            "PE": data["ratios"][item]["priceEarningsRatio"],
            "PS": data["ratios"][item]["priceToSalesRatio"],
            "PB": data["ratios"][item]["priceToBookRatio"],
            "Price To FCF": data["ratios"][item]["priceToFreeCashFlowsRatio"],
            "PEG": data["ratios"][item]["priceEarningsToGrowthRatio"],
            "EPS": data["income_statement"][item]["eps"],
        }

    # Transform the dictionary into a Pandas DataFrame with columns orientation
    fundamentals = pd.DataFrame.from_dict(financials, orient="index")

    # Replace inf, -inf, and NaN with 0
    fundamentals.replace([np.inf, -np.inf, np.nan], 0, inplace=True)

    # Generate HTML output for financial overview
    upper_ticker = ticker.upper()
    html_str = (
        f"<h3>{upper_ticker} Financial Overview (REAL-TIME as of {timestamp})</h3>\n\n"
    )

    html_str += """
        <table border="1" cellpadding="3" cellspacing="0">
            <thead>
                <tr>
                    <th style="color: #0000FF; font-weight: normal; width: 120px; padding: 5px; font-size: smaller;">Metric</th>
                    <th style="color: #0000FF; font-weight: normal; width: 100px; padding: 5px; font-size: smaller;">2023</th>
                    <th style="color: #0000FF; font-weight: normal; width: 100px; padding: 5px; font-size: smaller;">2022</th>
                    <th style="color: #0000FF; font-weight: normal; width: 100px; padding: 5px; font-size: smaller;">2021</th>
                    <th style="color: #0000FF; font-weight: normal; width: 100px; padding: 5px; font-size: smaller;">2020</th>
                    <th style="color: #0000FF; font-weight: normal; width: 100px; padding: 5px; font-size: smaller;">2019</th>
                </tr>
            </thead>
            <tbody>
        \n\n"""

    # Adjust each row
    for key in fundamentals.columns[:-5]:  # Exclude calculated growth metrics
        html_str += "<tr>"
        html_str += f'<td style="color: #8B4513; width: 150px; padding: 5px; font-size: smaller;">{key}</td>'
        for year in dates:
            html_str += f'<td style="width: 100px; padding: 5px; font-size: smaller;">{fundamentals.loc[year, key]:,.2f}</td>'
        html_str += "</tr>"

    html_str += "</tbody></table>"

    # Store the financial overview HTML string to the database (MongoDB)
    response = add_section_to_risk_memo(ticker, "financial_overview", html_str)
    logger.info(f"Real-time financial overview for {ticker} successfully updated.")
    return response
