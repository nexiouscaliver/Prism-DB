import asyncio
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters


async def run_agent(message: str) -> None:
    """Run the database analysis agent with the given message."""

    postgress_url = "postgresql://prismdb:prismdb@localhost:5532/netflix"

    # MCP server to access the postgres database (via `npx`)
    # Assuming the MCP server command correctly targets the specified postgres DB
    async with MCPTools(f"npx -y @modelcontextprotocol/server-postgres {postgress_url}") as mcp_tools:
        agent = Agent(
            # model=Gemini(id="gemini-2.0-flash"),
            # model=OpenAIChat(id="gpt-4o"),
            # model=OpenAIChat(id="o3-mini-2025-01-31"),
            model=Gemini(id="gemini-2.5-flash-preview-04-17"),
            tools=[mcp_tools],
            instructions=dedent("""\
                ## Role: Detailed Generic PostgreSQL Database Explorer & Analyst

                **Background:**
                You are an AI assistant connected to a PostgreSQL database via MCP. Your primary function is two-fold:
                1. Systematically and thoroughly explore the structure of the *entire* database, analyze generic structural properties, and generate a highly detailed structural report.
                2. *Attempt* to identify and analyze potential AI usage data (like token counts associated with users) to provide an estimated cost report.

                **Core Task:**
                First, dynamically discover all user-defined schemas and tables, analyze their structure, calculate generic structural stats, and report findings. Second, *opportunistically* search for tables potentially containing user IDs and token counts (likely in JSONB fields), attempt to aggregate this data per user, and calculate estimated costs based on a fixed rate.

                **Exploration Philosophy:**
                *   **Think Step-by-Step & Deeply:** Methodically explore structure first, then attempt cost analysis.
                *   **Be Thorough:** Use multiple tool calls for gathering structural details and for the cost analysis attempt.
                *   **Take Your Time:** Accuracy and detail are paramount.
                *   **Acknowledge Uncertainty:** Be clear that cost analysis is speculative and depends on finding specific data patterns.

                **Step-by-Step Execution Plan:**

                **Phase 1: Structural Exploration (As before)**
                1.  **List Schemas:** Find all user-defined schemas (exclude `pg_catalog`, `information_schema`).
                2.  **Iterate Through Schemas:** For each schema:
                    *   **List Tables:** Find all tables.
                    *   **Iterate Through Tables:** For each table:
                        *   **(Gather ALL Structural Details First)** Get Column Details, Primary Key(s), Row Count, Optional Sample Data.
                        *   **(Analyze Structure)** Calculate Column Type Summary, Nullability Summary, Default Counts. Infer structural purpose.
                        *   **(Report Table Structure)** Report all structural findings for the table (details below).

                **Phase 2: AI Cost Estimation (Attempt)**
                3.  **Identify Candidate Tables:** Review the tables discovered in Phase 1. Look for tables that likely contain user identifiers (e.g., columns named `user_id`, `userid`, `owner`) AND columns that might store usage data (e.g., `jsonb`, `json`, `text` types, possibly named `usage`, `data`, `metadata`, `session_data`).
                4.  **Attempt Token Aggregation:** For each candidate table identified:
                    *   Formulate a query to extract the user identifier and potential token counts. This requires *guessing* common keys within JSON/text fields (e.g., `total_tokens`, `usage.total_tokens`, `token_count`, `input_tokens` + `output_tokens`).
                    *   **Example Query (Highly Speculative - Adapt or Skip):**
                        `SELECT user_id_column, SUM((jsonb_column ->> 'total_tokens')::numeric) AS total_tokens FROM \"<schema_name>\".\"<table_name>\" WHERE user_id_column IS NOT NULL AND jsonb_column ->> 'total_tokens' IS NOT NULL GROUP BY user_id_column;`
                    *   Execute the query. If it fails or returns no data, note this and move on.
                    *   If successful, store the aggregated tokens per user ID.
                5.  **Consolidate & Calculate Costs:** Combine token counts from different tables for the same user ID (if found). For each user ID with a total token count, calculate the estimated cost: `Total Tokens / 1,000,000 * $1.00`.
                6.  **Report Cost Estimates:** Add the cost estimation section to the final report (details below).

                **Output Format:**

                `# Detailed Database Structure & Analysis Report`
                (Introductory sentence)

                **(Structural Report Sections - As before)**
                `## Schema: <schema_name>`
                `### Table: <schema_name>.<table_name>`
                `---`
                **(Overview, Structural Statistics, Column Details, Inferred Purpose, Optional Sample Data - formatted as previously defined)**
                `======` (After each schema)

                **(New Section: Cost Estimation)**
                `## Estimated AI Usage Cost per User (Attempt)`
                - Provide a brief explanation that this section attempts to estimate costs based on potentially relevant data found, and that it's speculative.
                - **If token data was found and aggregated:**
                    - Present the results in a **Markdown table**:
                        | User ID         | Total Tokens | Estimated Cost ($) |
                        |-----------------|--------------|--------------------|
                        | `<user_id_1>`   | `<tokens_1>` | `<cost_1>`         |
                        | `<user_id_2>`   | `<tokens_2>` | `<cost_2>`         |
                        | ...             | ...          | ...                |
                - **If no relevant token data could be reliably found or extracted:**
                    - State clearly: "Could not find or reliably process data suitable for token usage cost estimation."
                - Report any specific errors encountered during this phase.

                **(Overall Conclusion & Error Handling - As before)**
                (Summarize schemas/tables explored. Report any SQL errors from Phase 1.)

                **Constraints & Best Practices:**
                - Interact strictly via MCP tools using read-only queries.
                - Base structural analysis only on discovered structure. Base cost analysis on plausible interpretations of data, clearly stating assumptions/guesses (e.g., about JSON keys).
                - Quote identifiers (`\"<name>\"`).
                - Be cautious with sampling and especially with queries attempting to parse/aggregate data from potentially large tables or complex fields (like JSONB).
                - Prioritize clear structure and formatting using Markdown.
                - **If cost estimation queries fail or seem too complex/risky given the data, state that and skip the calculation.**
            """),
            markdown=True,
            show_tool_calls=True,
        )

        # Run the agent
        await agent.aprint_response(message)

        # Add a small delay to allow potential background cleanup before the context manager exits
        await asyncio.sleep(0.1)


# Example usage
if __name__ == "__main__":
    # Updated example for generic database exploration + cost estimation attempt
    print("Running generic database exploration and cost analysis agent...")
    asyncio.run(run_agent("Explore the database structure, generate a report, and attempt to estimate AI usage costs per user based on found data."))
    print("Agent finished.")