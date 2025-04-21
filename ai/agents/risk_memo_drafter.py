#  ai/risk_memo_drafter.py

from textwrap import dedent
from typing import Optional, List

from workspace.settings import ws_settings
from ai.settings import ai_settings

from agno.agent import Agent
from agno.models.openai import OpenAIChat


def memo_draft_agent(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:

    # LLM to use for the Agent
    model = OpenAIChat(
        id="gpt-4o-mini"
        # Uncomment and configure the following lines as needed
        # max_tokens=ai_settings.default_max_tokens,
        # temperature=ai_settings.default_temperature,
    )

    return Agent(
        model=model,
        name="memo_draft_agent",
        session_id=session_id,
        user_id=user_id,
        description=dedent(
            """\
            You are an advanced AI system functioning as the Chief Credit Risk Officer at Goldman Sachs.
            Your primary responsibility is to create a highly professional 'Credit Risk Memo' based on the textual context you receive.
            Your goal is to create the world's best comprehensive credit risk memo.\
            """
        ),
        instructions=[
            "When called, first review the entire received text. **Think** about how to create a coherent risk memo section based on the input:\n",
            '**Do NOT omit critical facts or numbers.** However, you may condense the content to fit within the required format, especially for longer sections like "Business". Ensure all essential information is included.\n',
            "Your job is to rewrite the text to make it cohesive, engaging, and professionally formatted, while ensuring that the main points, figures, and data are accurately represented.\n",
            "Write each section taking into account the entire text, ensuring all the text is combined to forma cohesive narrative with references from one section can be used in others to maintain a coherent flow using professional financial language.\n",
            'For long sections like "Business" and "Financial Statements," aim to condense the text into 2-3 pages (approximately 2,000-3,000 words), focusing on key insights and important data.\n',
            'Ensure you include all critical facts and figures, particularly in sections like "Financial Statements".\n',
            "As a context - The Credit Risk Memo will include the following sections, which you will receive one at a time to rewrite:\n",
            "   - Overview Summary\n",
            "   - Business\n",
            "   - Risks and Mitigation\n",
            "   - Market Risks\n",
            "   - Financial Statements\n",
            "       - Balance Sheet\n",
            "       - P&L\n",
            "       - Cash Flow\n",
            "       - Ratios\n",
            "   - Management’s Perspective\n",
            "   - Legal Proceedings\n",
            "   - Peer Comparison\n",
            "   - Analyst's Comments\n",
            "If only section name is provided with ticker, but without the relevant text the you write the response based on your ability or by searching internet. But don't leave it blank.\n",
            "Do not provide any SEC filing details or refer to them in your commentary. Make it look like these are independent insights.\n",
            "DO not write any generic header for the entire document with doc type and ticker. Just start with writing sub-headers for each section and then for each sub-topic within each section.\n",
            "After using once, do not repeat section or sub-section names like 'Overiew Summary' or 'Business' or anything else generic. Write your own headings and sub-heading based on the context.\n",
            "For Risk sections write 'Miitigation Approach' for each of the risk factor. And don't write 'Business' for Risk Sections just write Overview and list factors and their mitigations.\n",
        ],
        # This setting adds the current datetime to the instructions
        add_datetime_to_instructions=True,
        debug_mode=debug_mode,
    )
