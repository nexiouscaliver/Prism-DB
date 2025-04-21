## Testing of risk memo pdf generator
# from ai.tools.risk_memo_pdf_generator import RiskMemoGenerator

# generator = RiskMemoGenerator()
# response = generator.create_pdf("AAPL")

# print(response)


# # Testing of risk memto tool end-to-end
# from risk_memo_tool import RiskMemoTool

# tool = RiskMemoTool(generate_risk_memo=True)
# file_name = tool.generate_risk_memo("TSLA")

# print(file_name)


# # Testing of parse_latest_filings
# from db.utils import parse_latest_filings, get_section_text
# from db.edgar_utils import cik_from_ticker

# cik = cik_from_ticker("NVDA")
# resposne = parse_latest_filings(cik)
# print(resposne)


# from db.mongodb import check_document_exists_by_field
# response = check_document_exists_by_field("risk_memos","ticker", "tsla")
# print (response)

# from importlib import reload
# import db.edgar_utils as edgar_utils
# reload(edgar_utils)

# response = edgar_utils.download_latest_filings("AAPL")
# print(response)


# Test pdf formats:
from importlib import reload
import ai.tools.risk_memo_pdf_generator as risk_memo_pdf_generator
from ai.tools.risk_memo_pdf_generator import RiskMemoGenerator

reload(risk_memo_pdf_generator)

generator = RiskMemoGenerator()
pdf_path = generator.create_pdf("AAPL")

print(pdf_path)
