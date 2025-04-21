"""URL Search PDF Tool - Enterprise-grade website research report generator with PDF output"""

import os
import json  # Added json import
import logging
from typing import Optional, Dict, Any, Union, List  # Added List import
from datetime import datetime
import uuid
from agno.tools import Toolkit
from agno.tools.firecrawl import FirecrawlTools
from firecrawl import FirecrawlApp
import re
import openai
from json import JSONDecodeError

from ..tools.markdown_pdf_converter import MarkdownPDFConverter

logger = logging.getLogger(__name__)

# Define output directory
base_dir = os.path.dirname(os.path.abspath(__file__))
GENERATED_FILES_DIR = os.path.join(base_dir, "..", "..", "generated_files")
os.makedirs(GENERATED_FILES_DIR, exist_ok=True)

class URLSearchPDFTool(Toolkit):
    """Enhanced URL Search Tool with PDF output capabilities."""
    
    def __init__(
        self,
        max_pages: int = 8,  # Changed from 12 to 8
        save_to_pdf: bool = True,
        enable_analytics: bool = True,
        add_metadata: bool = True,
        output_dir: str = GENERATED_FILES_DIR,
        content_preview_length: int = 2500,  # Configurable content preview length
        max_urls_to_display: int = 15,      # Configurable URL display limit
        max_pages_to_analyze: int = 15,     # Configurable page analysis limit
        model_name: str = "gpt-4o-mini",    # Configurable model, defaulting to gpt-4o-mini
        fallback_model_name: str = "gpt-4o"  # Fallback model if primary fails
    ):
        """Initialize the URL Search PDF Tool."""
        super().__init__(name="url_search_tool")
        
        # Store configuration
        self.config = {
            "max_pages": max_pages,
            "save_to_pdf": save_to_pdf,
            "enable_analytics": enable_analytics,
            "add_metadata": add_metadata,
            "output_dir": output_dir if os.path.isabs(output_dir) else GENERATED_FILES_DIR,
            "content_preview_length": content_preview_length,
            "max_urls_to_display": max_urls_to_display,
            "max_pages_to_analyze": max_pages_to_analyze,
            "model_name": model_name,
            "fallback_model_name": fallback_model_name
        }
        
        # Initialize components
        self._firecrawl = FirecrawlTools(crawl=True)
        
        # Register the main research function
        self.register(self.research_website)
    
    def research_website(
        self,
        url: str,
        session_id: Optional[str] = None,
        depth: int = 1,
        max_pages: Optional[int] = None,
    ) -> str:
        """Generate a comprehensive research report from a website URL and save it as PDF."""
        try:
            start_time = datetime.now()
            
            # Generate session ID if not provided
            session_id = session_id or str(uuid.uuid4())
            max_pages = max_pages or self.config["max_pages"]
            
            logger.info(f"Starting website research for URL: {url} (session_id: {session_id})")
            
            # Crawl the website
            pages, sitemap, links_list, crawl_result, num_pages_crawled = self._crawl_website(url, max_pages)
            
            # Always analyze the website content with GPT-4o-mini
            try:
                logger.info(f"Analyzing website content with {self.config['model_name']}...")
                gpt_analysis = self._analyze_website_content_with_gpt(url, pages, links_list, crawl_result)
                logger.info(f"GPT analysis completed: {gpt_analysis['success']}")
            except Exception as gpt_error:
                logger.warning(f"Error during GPT analysis: {str(gpt_error)}")
                gpt_analysis = {
                    "success": False,
                    "error": str(gpt_error),
                    "analysis": {}
                }
            
            # Generate filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_base = f"website_report_{session_id}_{timestamp}"
            pdf_filename = f"{filename_base}.pdf"
            md_filename = f"{filename_base}.md"
            
            # Ensure output paths
            output_dir = self.config["output_dir"]
            os.makedirs(output_dir, exist_ok=True)
            
            pdf_path = os.path.join(output_dir, pdf_filename)
            md_path = os.path.join(output_dir, md_filename)
            
            # Create a detailed markdown report with structured content and GPT insights
            if gpt_analysis and gpt_analysis.get("success", False):
                # Use GPT's insights for enhanced report
                logger.info("Using GPT-generated insights for website report")
                markdown_report = self._generate_markdown_report_with_gpt(url, pages, links_list, num_pages_crawled, gpt_analysis["analysis"])
            else:
                # Fallback to standard template-based report
                logger.info("Using standard template-based report generation")
                markdown_report = self._generate_markdown_report(url, pages, sitemap, num_pages_crawled, crawl_result)
            
            # Write markdown report to file
            with open(md_path, 'w', encoding='utf-8') as md_file:
                md_file.write(markdown_report)
            logger.info(f"Saved markdown report to: {md_path}")
            
            # Generate PDF from the markdown report
            try:
                # Extract title from markdown content
                title = "Website Research Report"
                lines = markdown_report.split('\n')
                if lines and len(lines) > 0:
                    first_line = lines[0].strip()
                    if (first_line.startswith("# ")):
                        title = first_line.replace("# ", "").strip()
                
                # Generate PDF
                pdf_path = self.generate_pdf_from_markdown(
                    filename=pdf_filename,
                    markdown_content=markdown_report,
                    output_path=pdf_path,
                    title=title
                )
                logger.info(f"Successfully generated PDF report: {pdf_path}")
                
                # Important: To maintain compatibility with url_search_pdf_agent.py
                # We need to ensure we return the proper format with the ^ marker
                # full_pdf_path = os.path.join(output_dir, pdf_path)
                # return f"^{full_pdf_path}"
                return f"^{pdf_path}"
                
            except Exception as pdf_error:
                logger.error(f"Error generating PDF: {str(pdf_error)}", exc_info=True)
                # Return error message with the right format
                return f"Error: Failed to generate PDF: {str(pdf_error)}"
            
        except Exception as e:
            error_msg = f"Error researching website {url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def _crawl_website(self, url: str, max_pages: int) -> tuple:
        """
        Crawl a website and extract page data.
        
        Args:
            url: The URL to crawl
            max_pages: Maximum number of pages to crawl
            
        Returns:
            tuple: (pages, sitemap, links_list, crawl_result, num_pages_crawled)
        """
        try:
            logger.info(f"Calling FirecrawlTools.crawl_website with URL: {url}, limit: {max_pages}")
            # Make sure the FirecrawlTools instance has crawl=True
            if not hasattr(self._firecrawl, 'app'):
                self._firecrawl = FirecrawlTools(crawl=True)
                
            # Crawl the website
            crawl_response = self._firecrawl.crawl_website(url=url, limit=max_pages)
            logger.info(f"Raw crawl response received, length: {len(crawl_response) if crawl_response else 0}")
            
            # Try to get sitemap from map function in FirecrawlApp
            try:
                firecrawl_api = os.getenv("FIRECRAWL_API_KEY")
                firecrawl = FirecrawlApp(api_key=firecrawl_api)
                sitemap_list = firecrawl.map_url(url)
                links_list = sitemap_list.get('links', [])
                logger.info(f"Additional sitemap data received, length: {len(links_list) if links_list else 0}")
            except Exception as sitemap_error:
                logger.warning(f"Could not get additional sitemap data: {str(sitemap_error)}")
                links_list = []
                
            # Parse the JSON response
            try:
                crawl_result = json.loads(crawl_response)
                logger.info(f"Crawl result parsed successfully: {type(crawl_result)}")
            except json.JSONDecodeError as json_error:
                logger.error(f"Failed to parse crawl response: {str(json_error)}")
                logger.error(f"Raw response: {crawl_response[:500]}")
                raise ValueError(f"Error parsing crawl results: {str(json_error)}")
            
            # Check for success field first
            if not crawl_result.get('success', False):
                error_msg = crawl_result.get('message', 'Unknown error')
                logger.error(f"Crawl operation failed: {error_msg}")
                raise ValueError(f"Failed to crawl website: {url} - {error_msg}")
                
            # Extract pages and sitemap from the crawl result
            pages, sitemap = self._extract_page_data(url, crawl_result)
            
            # Ensure we have at least one page
            if not pages:
                logger.error("No pages extracted from crawl result")
                raise ValueError(f"Failed to extract any page data from {url}")
                
            num_pages_crawled = len(pages)
            logger.info(f"Successfully extracted data for {num_pages_crawled} pages from {url}")
            
            return pages, sitemap, links_list, crawl_result, num_pages_crawled
            
        except Exception as e:
            logger.error(f"Error during website crawling: {str(e)}", exc_info=True)
            raise ValueError(f"Error while crawling website {url}: {str(e)}")
            
    def _extract_page_data(self, url: str, crawl_result: Dict) -> tuple:
        """
        Extract page data from crawl result.
        
        Args:
            url: The URL that was crawled
            crawl_result: The parsed crawl result
            
        Returns:
            tuple: (pages, sitemap)
        """
        pages = []
        sitemap = []
        
        # Handle different response formats
        if 'data' in crawl_result:
            logger.info("Found 'data' key in response - processing FirecrawlApp response format")
            
            # For API/pricing pages, the data might be directly in the response
            if isinstance(crawl_result['data'], dict):
                # Single page result - typically for direct scrapes
                pages = [crawl_result['data']]
                
                # Extract URL if available
                if 'url' in crawl_result['data']:
                    pages[0]['url'] = crawl_result['data']['url']
                    sitemap = [crawl_result['data']['url']]
                else:
                    # If URL not in data, use the requested URL
                    pages[0]['url'] = url
                    sitemap = [url]
                
                # Ensure we have page title
                if 'title' not in pages[0] and 'pageTitle' not in pages[0]:
                    title_parts = url.split('/')
                    page_title = title_parts[-1] if title_parts[-1] else title_parts[-2]
                    page_title = page_title.replace('-', ' ').replace('_', ' ').title()
                    pages[0]['title'] = page_title
                    
            elif isinstance(crawl_result['data'], list):
                # Multiple pages in the response
                pages = crawl_result['data']
                # Extract URLs for sitemap
                sitemap = [item.get('url', '') for item in pages if 'url' in item]
                
                # Ensure all pages have titles
                for i, page in enumerate(pages):
                    if 'title' not in page and 'pageTitle' not in page:
                        # Extract title from URL if available
                        if 'url' in page and page['url']:
                            url_parts = page['url'].split('/')
                            page_title = url_parts[-1] if url_parts[-1] else url_parts[-2]
                            page_title = page_title.replace('-', ' ').replace('_', ' ').title()
                            pages[i]['title'] = page_title
                        else:
                            pages[i]['title'] = f"Page {i+1}"
            
            # Handle missing content in pages
            for i, page in enumerate(pages):
                if 'content' not in page and 'text' not in page:
                    pages[i]['content'] = "Content could not be extracted. The page may use JavaScript rendering or require authentication."
        
        elif 'pages' in crawl_result:
            logger.info("Found 'pages' key in response - using standard response format")
            pages = crawl_result.get('pages', [])
            sitemap = crawl_result.get('sitemap', [])
            
            # Add the requested URL to sitemap if empty
            if not sitemap:
                sitemap = [url]
                
            # Handle missing content in pages
            for i, page in enumerate(pages):
                if 'content' not in page and 'text' not in page:
                    pages[i]['content'] = "Content could not be extracted. The page may use JavaScript rendering or require authentication."
        else:
            # If we don't have pages data but have successful response
            logger.warning("No standard page data format found. Attempting to reconstruct from raw result.")
            
            # Try to extract useful information from the response
            if 'status' in crawl_result and crawl_result['status'] == 'completed':
                # This is likely a FirecrawlApp result with non-standard structure
                if 'url' in crawl_result:
                    page_url = crawl_result['url']
                else:
                    page_url = url
                    
                # Create a synthetic page
                synthetic_page = {
                    'url': page_url,
                    'title': page_url.split('/')[-1].replace('-', ' ').replace('_', ' ').title() or 'Website Page',
                    'content': "This page requires specialized rendering or authentication to access complete content."
                }
                
                pages = [synthetic_page]
                sitemap = [page_url]
            else:
                # Log available keys for debugging
                available_keys = list(crawl_result.keys())
                logger.error(f"Neither 'pages' nor 'data' key found in response. Available keys: {available_keys}")
                
                # Create a fallback synthetic page for analysis
                synthetic_page = {
                    'url': url,
                    'title': 'Website Page',
                    'content': "Unable to extract content from this website."
                }
                pages = [synthetic_page]
                sitemap = [url]
        
        return pages, sitemap

    def _analyze_website_content_with_gpt(self, url: str, pages: List[Dict[str, Any]], sitemap: List[str], crawl_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use GPT to analyze website content and extract structured insights with enhanced business focus.
        
        Args:
            url: The website URL.
            pages: List of page data dictionaries.
            sitemap: List of URLs from the sitemap.
            crawl_result: The original crawl result.
            
        Returns:
            Dictionary with analysis results.
        """
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found in environment variables")
            
            # Create OpenAI client
            client = openai.OpenAI(api_key=api_key)
            
            # Ensure sitemap is a list
            if not isinstance(sitemap, list):
                sitemap = list(sitemap) if sitemap else []
                
            # Prepare pages data with limited content to control token usage
            processed_pages = []
            max_pages_for_analysis = min(5, len(pages))  # Limit number of pages to analyze
            
            # Extract domain for better context
            domain = url.split('//')[1].split('/')[0] if '//' in url else url.split('/')[0]
            
            # Detect website type for better analysis
            is_ecommerce = any(term in url.lower() for term in ['shop', 'store', 'product', 'pricing', 'buy'])
            is_blog = any(term in url.lower() for term in ['blog', 'news', 'article', 'post'])
            is_corporate = any(term in url.lower() for term in ['about', 'company', 'team', 'career', 'contact'])
            is_api_documentation = any(term in url.lower() for term in ['api', 'docs', 'documentation', 'developer'])
            
            for page in pages[:max_pages_for_analysis]:
                page_data = {
                    "url": page.get("url", ""),
                    "title": page.get("title", page.get("pageTitle", "")),
                }
                
                # Extract OG meta tags specifically for title and description
                meta = page.get("meta", page.get("metadata", {}))
                if meta:
                    # Try to get OG:Title and OG:Description
                    if isinstance(meta, dict):
                        og_title = meta.get("og:title", "")
                        og_description = meta.get("og:description", "")
                        if og_title:
                            page_data["og_title"] = og_title
                        if og_description:
                            page_data["og_description"] = og_description
                    page_data["metadata"] = meta
                
                # Extract content with configurable preview length
                content = page.get("content", page.get("text", ""))
                if content:
                    preview_length = min(1200, self.config["content_preview_length"])
                    page_data["content_preview"] = content[:preview_length] + "..." if len(content) > preview_length else content
                
                # Extract page structure info if available
                if 'headings' in page and page['headings']:
                    page_data["headings"] = [
                        {"level": h.get("tag", "h1")[-1] if h.get("tag", "h1")[-1].isdigit() else "1", 
                         "text": h.get("text", "")} 
                        for h in page['headings'][:10]
                    ]
                
                # Extract link information if available
                if 'links' in page and page['links']:
                    internal_links = [link for link in page['links'] if domain in link]
                    external_links = [link for link in page['links'] if domain not in link]
                    page_data["link_summary"] = {
                        "total_links": len(page['links']),
                        "internal_links": len(internal_links),
                        "external_links": len(external_links)
                    }
                
                processed_pages.append(page_data)
            
            # Build a summary of website data for context
            website_data = {
                "url": url,
                "domain": domain,
                "sitemap_size": len(sitemap),
                "sitemap": sitemap[:self.config["max_urls_to_display"]],
                "pages": processed_pages,
                "total_pages_crawled": len(pages),
                "website_type": {
                    "appears_to_be_ecommerce": is_ecommerce,
                    "appears_to_be_blog": is_blog,
                    "appears_to_be_corporate": is_corporate,
                    "appears_to_be_api_documentation": is_api_documentation
                }
            }

            # Construct an enhanced structured prompt with more user-friendly focus
            prompt = f"""
You are an expert analyst tasked with producing a clear, user-friendly website report. Your audience is a typical user who wants to understand what this website is about without technical jargon. Focus on explaining the website's contents, purpose, and offerings in clear, plain language.

Please return your analysis strictly as a JSON object with the following keys:

- "website_overview": Provide a clear, jargon-free summary of what the website is about, what it offers, and who it's for. Include 2-3 paragraphs that explain:
  * What this website contains
  * Who would find this website useful
  * What services or information it provides
  * Any unique features or content that stand out

- "main_topics": Identify 3-6 main topics or themes the website covers. For each, provide:
  * "topic_name": The name of the topic or theme
  * "topic_summary": A brief 1-2 sentence explanation of what information is provided
  * "user_benefit": How this information would help a typical visitor

- "key_content_areas": List the primary content areas or sections of the website (like Products, Services, Blog, etc.) with a brief description of what each contains

- "user_journey": Describe in plain language how a visitor would likely use this website:
  * What information they would find first
  * What actions they could take
  * What resources are available
  * How they would navigate between sections

- "technical_details": This section needs to be comprehensive and will contain detailed analysis including:
  * "content_analysis": In-depth analysis of website content quality, comprehensiveness, relevance, organization, and clarity. Include specific strengths and weaknesses.
  * "user_experience_evaluation": Detailed assessment of site navigation, information architecture, mobile friendliness, accessibility considerations, loading speed impressions, and overall usability.
  * "competitive_analysis": Compare the website to industry standards and likely competitors. Examine differentiators, strengths relative to competitors, and areas where competitors may have advantages.
  * "seo_and_discoverability": Thorough analysis of SEO elements including URL structure, keyword usage, meta descriptions, heading structure, internal linking, image optimization, and search engine visibility factors.
  * "strategic_recommendations": Provide 5-7 detailed, actionable recommendations for website improvement, prioritized by potential impact. Each should include implementation guidance.
  * "improvement_suggestions": 3-4 additional practical suggestions to improve the website

Website Data:
---------------------------
URL: {url}
Domain: {domain}
Total Pages Crawled: {len(pages)}
Sitemap Size: {len(sitemap)}
Website Type: {"E-commerce" if is_ecommerce else "Blog/Content" if is_blog else "Corporate/Business" if is_corporate else "API/Documentation" if is_api_documentation else "General/Other"}

Page Analysis:
{json.dumps(processed_pages, indent=2)}

Instructions:
- Focus on what the website contains and says, not technical aspects in the main sections
- Use clear, simple language a non-technical person would understand in the user-focused sections
- Reserve technical terminology and detailed analysis for the technical_details section
- Format all responses as valid JSON with the exact keys specified above
- If you're uncertain about specific details, make reasonable inferences based on the available content
- Keep the tone conversational and helpful throughout
- Be comprehensive and detailed in the technical_details section
"""
            # Make API call with better control parameters
            try:
                response = client.chat.completions.create(
                    model=self.config["model_name"],
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at explaining websites in user-friendly language for general sections, while providing detailed technical analysis in the technical sections. Produce comprehensive reports with both accessible explanations and expert insights."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,  # More focused responses
                    response_format={"type": "json_object"},  # Ensure JSON output
                    max_tokens=4000,  # Allow for comprehensive analysis
                )
                analysis_text = response.choices[0].message.content.strip()

                # Parse the GPT response as JSON with enhanced error handling
                try:
                    analysis_json = json.loads(analysis_text)
                    return {"success": True, "analysis": analysis_json}
                except JSONDecodeError as json_error:
                    logger.error(f"Failed to parse GPT response as JSON: {str(json_error)}")
                    logger.error(f"Response text: {analysis_text[:500]}...")
                    
                    # Try extracting JSON code block if available
                    json_match = re.search(r'```(?:json)?\n([\s\S]*?)\n```', analysis_text)
                    if json_match:
                        try:
                            analysis_json = json.loads(json_match.group(1))
                            return {"success": True, "analysis": analysis_json}
                        except JSONDecodeError:
                            pass
                    
                    # Fallback: Return the raw text as analysis
                    return {"success": True, "analysis": {"raw_analysis": analysis_text}}
                
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}")
                # Attempt to use the fallback model if specified
                if self.config["fallback_model_name"] != self.config["model_name"]:
                    logger.info(f"Attempting analysis with fallback model: {self.config['fallback_model_name']}")
                    try:
                        # Try again with the fallback model
                        fallback_response = client.chat.completions.create(
                            model=self.config["fallback_model_name"],
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are an expert at explaining websites in user-friendly language for general sections, while providing detailed technical analysis in the technical sections. Produce comprehensive reports with both accessible explanations and expert insights."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,  # Slightly higher temperature for fallback model
                            response_format={"type": "json_object"},
                            max_tokens=2500,  # Reduced tokens for fallback model
                        )
                        fallback_text = fallback_response.choices[0].message.content.strip()
                        
                        # Parse the fallback response
                        try:
                            fallback_json = json.loads(fallback_text)
                            logger.info("Successfully used fallback model for analysis")
                            return {"success": True, "analysis": fallback_json, "used_fallback": True}
                        except JSONDecodeError:
                            # Try to extract JSON if in code block format
                            json_match = re.search(r'```(?:json)?\n([\s\S]*?)\n```', fallback_text)
                            if json_match:
                                try:
                                    fallback_json = json.loads(json_match.group(1))
                                    logger.info("Successfully used fallback model for analysis (extracted from code block)")
                                    return {"success": True, "analysis": fallback_json, "used_fallback": True}
                                except JSONDecodeError:
                                    pass
                            
                            # If we still can't parse JSON, use raw text
                            logger.info("Using fallback model raw text as analysis")
                            return {"success": True, "analysis": {"raw_analysis": fallback_text}, "used_fallback": True}
                    except Exception as fallback_error:
                        logger.error(f"Fallback model error: {str(fallback_error)}")
                
                # If fallback also fails or isn't configured, return error
                return {"success": False, "error": str(api_error), "analysis": {"error_message": str(api_error)}}

        except Exception as e:
            logger.error(f"Error analyzing website content with GPT: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "analysis": {}}

    def _generate_markdown_report_with_gpt(self, url: str, pages: List[Dict[str, Any]], sitemap: List[str], num_pages_crawled: int, gpt_analysis: Dict[str, Any]) -> str:
        """
        Generate an enhanced markdown report using the GPT analysis insights with improved user focus.
        
        Args:
            url: The website URL.
            pages: List of page data dictionaries.
            sitemap: List of URLs from the sitemap.
            num_pages_crawled: Number of pages crawled.
            gpt_analysis: GPT analysis results.
            
        Returns:
            Markdown report content.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        website_title = (pages[0].get("title", pages[0].get("pageTitle", "")) if pages else url.split("//")[-1].split("/")[0]) or url
        domain = url.split('//')[1].split('/')[0] if '//' in url else url.split('/')[0]
        
        # Start with title
        markdown = f"# Website Report\n\n"
        
        # Basic website info
        markdown += f"**Website:** {url}\n"
        markdown += f"**Date:** {timestamp}\n\n"
        
        # Helper function to convert any data type to proper markdown
        def format_to_markdown(data, indent_level=0):
            indent = "  " * indent_level
            
            # Handle None values
            if data is None:
                return "None"
                
            # Handle string values
            elif isinstance(data, str):
                # Check if it's already a formatted markdown paragraph with line breaks
                if "\n" in data:
                    # Preserve paragraphs by adding proper indentation and line breaks
                    paragraphs = data.split("\n")
                    return "\n".join([f"{indent}{p}" for p in paragraphs if p.strip()])
                return data
                
            # Handle list values - render as markdown list with proper indentation
            elif isinstance(data, list):
                if not data:  # Empty list
                    return "None"
                    
                result = ""
                for item in data:
                    if isinstance(item, dict):
                        # For dictionaries in a list, format as nested content
                        result += f"\n{indent}- "
                        nested_content = format_to_markdown(item, indent_level + 1)
                        # For simple key-value dictionaries, put on same line
                        if "\n" not in nested_content:
                            result += f"{nested_content}"
                        else:
                            result += f"\n{indent}  {nested_content.replace(indent+'  ', indent+'    ')}"
                    else:
                        # For simple items, format as bullet points
                        result += f"\n{indent}- {format_to_markdown(item, indent_level + 1)}"
                return result.strip()
                
            # Handle dictionary values - render as markdown with keys as headers
            elif isinstance(data, dict):
                if not data:  # Empty dict
                    return "None"
                    
                result = ""
                for key, value in data.items():
                    formatted_key = key.replace('_', ' ').title() if isinstance(key, str) else str(key)
                    
                    # Format the value appropriately based on its type
                    formatted_value = format_to_markdown(value, indent_level + 1)
                    
                    # Handle different value types for better formatting
                    if isinstance(value, dict):
                        result += f"\n{indent}**{formatted_key}**:\n{formatted_value}"
                    elif isinstance(value, list):
                        if not value:  # Empty list
                            result += f"\n{indent}**{formatted_key}**: None"
                        else:
                            result += f"\n{indent}**{formatted_key}**:{formatted_value}"
                    else:
                        # Simple values
                        result += f"\n{indent}**{formatted_key}**: {formatted_value}"
                return result.strip()
                
            # Handle numeric and boolean values directly
            elif isinstance(data, (int, float, bool)):
                return str(data)
                
            # Fallback for any other data types
            else:
                return str(data)
        
        # Process GPT analysis with improved formatting focused on website content
        if "raw_analysis" in gpt_analysis:
            raw_text = gpt_analysis["raw_analysis"]
            if re.search(r'(#+)\s+', raw_text):
                markdown += raw_text + "\n\n"
            else:
                markdown += "## Website Summary\n\n" + raw_text + "\n\n"
        else:
            # First section: Website Overview - what the site is about
            if "website_overview" in gpt_analysis:
                markdown += "## Website Summary\n\n"
                content = gpt_analysis["website_overview"]
                formatted_content = format_to_markdown(content)
                markdown += f"{formatted_content}\n\n"
            
            # Second section: Main Topics/Themes with special handling for better formatting
            if "main_topics" in gpt_analysis:
                markdown += "## Main Topics & Themes\n\n"
                content = gpt_analysis["main_topics"]
                
                # Special handling for main topics to ensure they're well formatted
                if isinstance(content, list):
                    for topic in content:
                        if isinstance(topic, dict):
                            topic_name = topic.get("topic_name", "")
                            summary = topic.get("topic_summary", "")
                            benefit = topic.get("user_benefit", "")
                            
                            if topic_name:
                                markdown += f"### {topic_name}\n\n"
                            
                            if summary:
                                markdown += f"{summary}\n\n"
                                
                            if benefit:
                                markdown += f"**Benefit to users**: {benefit}\n\n"
                        else:
                            # If not a dict, fall back to standard formatting
                            markdown += f"- {format_to_markdown(topic)}\n"
                else:
                    # Fall back to standard formatting for non-list content
                    formatted_content = format_to_markdown(content)
                    markdown += f"{formatted_content}\n\n"
            
            # Third section: Key Content Areas
            if "key_content_areas" in gpt_analysis:
                markdown += "## Key Content Areas\n\n"
                content = gpt_analysis["key_content_areas"]
                formatted_content = format_to_markdown(content)
                markdown += f"{formatted_content}\n\n"
            
            # Fourth section: User Journey
            if "user_journey" in gpt_analysis:
                markdown += "## How to Use This Website\n\n"
                content = gpt_analysis["user_journey"]
                formatted_content = format_to_markdown(content)
                markdown += f"{formatted_content}\n\n"
            
            # Website Structure & Sitemap Section
            markdown += "## Website Structure\n\n"
            markdown += f"The website contains {len(sitemap)} pages. Here are the main pages:\n\n"
            
            if sitemap:
                max_urls_to_display = min(self.config["max_urls_to_display"], len(sitemap))
                
                for i, site_url in enumerate(sitemap[:max_urls_to_display]):
                    try:
                        # Get page name from URL for better readability
                        parts = site_url.split('//')[1].split('/') if '//' in site_url else site_url.split('/')
                        path_parts = [part for part in parts if part]
                        page_name = path_parts[-1].replace('-', ' ').replace('_', ' ').title() if path_parts else "Homepage"
                        markdown += f"- [{page_name}]({site_url})  \n"
                    except Exception:
                        # Fallback to plain URL if parsing fails
                        markdown += f"- {site_url}\n"
                
                if len(sitemap) > max_urls_to_display:
                    markdown += f"\n*...and {len(sitemap) - max_urls_to_display} more pages*\n\n"
            
            # Content Preview Section with enhanced display of all pages
            markdown += "## Content Preview\n\n"
            
            # Show all available pages in the report with structured format
            max_pages_to_display = min(self.config["max_pages_to_analyze"], len(pages))
            markdown += f"Displaying {max_pages_to_display} pages from the website:\n\n"
            
            for i, page in enumerate(pages[:max_pages_to_display]):
                page_num = i + 1
                
                # Use structured page header with page number
                markdown += f"### Page {page_num}:\n\n"
                
                # Use OG:Title as Page Title if available
                title = None
                meta = page.get("meta", page.get("metadata", {}))
                if meta and isinstance(meta, dict):
                    og_title = meta.get("og:title", "")
                    if og_title:
                        title = og_title
                
                # Fallback to standard title if no OG:Title
                if not title:
                    title = page.get("title", page.get("pageTitle", f"Page {page_num}"))
                
                # Add page title in structured format
                markdown += f"**Title:** {title}\n\n"
                
                page_url = page.get("url", "")
                if page_url:
                    markdown += f"**URL:** [{page_url}]({page_url})\n\n"
                
                # Add OG:Description as Description if available
                description = None
                if meta and isinstance(meta, dict):
                    og_description = meta.get("og:description", "")
                    if og_description:
                        description = og_description
                        markdown += f"**Description:** {description}\n\n"
                    else:
                        # Try to extract a description from the content
                        content = page.get("content", page.get("text", ""))
                        if content and len(content) > 50:
                            # Use the first paragraph as description
                            paragraphs = content.split('\n\n')
                            first_para = paragraphs[0].strip() if paragraphs else content[:200]
                            if len(first_para) > 200:
                                first_para = first_para[:200] + "..."
                            markdown += f"**Description:** {first_para}\n\n"
                        else:
                            markdown += "**Description:** *No description available*\n\n"
                else:
                    markdown += "**Description:** *No description available*\n\n"
                
                # Extract headings if available for better content structure overview
                headings = page.get('headings', [])
                if headings and len(headings) > 0:
                    markdown += "**Content Structure:**\n\n"
                    for heading in headings[:5]:  # Show top 5 headings per page
                        heading_text = heading.get('text', '')
                        if heading_text:
                            markdown += f"- {heading_text}\n"
                    
                    if len(headings) > 5:
                        markdown += f"*...and {len(headings) - 5} more headings*\n\n"
                    else:
                        markdown += "\n"
                
                # Include a brief content preview
                content = page.get("content", page.get("text", ""))
                if content:
                    content_preview = content[:self.config["content_preview_length"]] + "..." if len(content) > self.config["content_preview_length"] else content
                    markdown += f"**Content Preview:**\n\n{content_preview}\n\n"
                else:
                    markdown += "**Content Preview:** *Content not available for this page*\n\n"
                
                # # Add additional page metrics for more comprehensive report
                # links = page.get('links', [])
                # images = page.get('images', [])
                
                # markdown += "**Page Metrics:**\n\n"
                
                # # Word count if content is available
                # if content:
                #     word_count = len(content.split())
                #     markdown += f"- Word Count: {word_count}\n"
                
                # # Link count
                # if links:
                #     internal_links = [link for link in links if domain in link]
                #     external_links = [link for link in links if domain not in link]
                #     markdown += f"- Total Links: {len(links)} (Internal: {len(internal_links)}, External: {len(external_links)})\n"
                
                # # Image count
                # if images:
                #     markdown += f"- Images: {len(images)}\n"
                
                markdown += "\n---\n\n"
            
            # Technical Details Section with expanded sections
            markdown += "## Technical Details\n\n"
            markdown += "*This section contains comprehensive technical information about the website that may be of interest to web developers and digital marketers.*\n\n"
            
            # Process all the required technical sections
            if "technical_details" in gpt_analysis:
                tech_details = gpt_analysis["technical_details"]
                
                # Content Analysis Section
                if isinstance(tech_details, dict) and "content_analysis" in tech_details:
                    markdown += "### Content Analysis\n\n"
                    content = tech_details["content_analysis"]
                    formatted_content = format_to_markdown(content)
                    markdown += f"{formatted_content}\n\n"
                
                # User Experience Evaluation Section
                if isinstance(tech_details, dict) and "user_experience_evaluation" in tech_details:
                    markdown += "### User Experience (UX) Evaluation\n\n"
                    content = tech_details["user_experience_evaluation"]
                    formatted_content = format_to_markdown(content)
                    markdown += f"{formatted_content}\n\n"
                
                # Competitive Analysis Section
                if isinstance(tech_details, dict) and "competitive_analysis" in tech_details:
                    markdown += "### Competitive Analysis\n\n"
                    content = tech_details["competitive_analysis"]
                    formatted_content = format_to_markdown(content)
                    markdown += f"{formatted_content}\n\n"
                
                # SEO and Discoverability Section
                if isinstance(tech_details, dict) and "seo_and_discoverability" in tech_details:
                    markdown += "### SEO and Discoverability\n\n"
                    content = tech_details["seo_and_discoverability"]
                    formatted_content = format_to_markdown(content)
                    markdown += f"{formatted_content}\n\n"
                
                # Strategic Recommendations Section
                if isinstance(tech_details, dict) and "strategic_recommendations" in tech_details:
                    markdown += "### Strategic Recommendations\n\n"
                    content = tech_details["strategic_recommendations"]
                    formatted_content = format_to_markdown(content)
                    markdown += f"{formatted_content}\n\n"
                
                # Improvement Suggestions
                if isinstance(tech_details, dict) and "improvement_suggestions" in tech_details:
                    markdown += "### Improvement Suggestions\n\n"
                    content = tech_details["improvement_suggestions"]
                    formatted_content = format_to_markdown(content)
                    markdown += f"{formatted_content}\n\n"
                
                # If tech_details is not a dict or doesn't have the specific sections, format it as a whole
                if not isinstance(tech_details, dict) or not any(key in tech_details for key in [
                    "content_analysis", "user_experience_evaluation", "competitive_analysis", 
                    "seo_and_discoverability", "strategic_recommendations", "improvement_suggestions"
                ]):
                    formatted_content = format_to_markdown(tech_details)
                    markdown += f"{formatted_content}\n\n"
            
            # Handle legacy data structure for backward compatibility
            # These sections will appear if they exist at the root level of the analysis
            technical_sections = [
                ("content_analysis", "Content Analysis"),
                ("user_experience_evaluation", "User Experience (UX) Evaluation"),
                ("competitive_analysis", "Competitive Analysis"),
                ("competitor_positioning", "Competitive Analysis"),
                ("seo_and_discoverability", "SEO and Discoverability"),
                ("strategic_recommendations", "Strategic Recommendations")
            ]
            
            has_technical_sections = False
            for key, title in technical_sections:
                if key in gpt_analysis:
                    if not has_technical_sections:
                        markdown += "## Additional Technical Analysis\n\n"
                        markdown += "*The following sections contain technical details about the website's design and implementation.*\n\n"
                        has_technical_sections = True
                        
                    markdown += f"### {title}\n\n"
                    content = gpt_analysis[key]
                    formatted_content = format_to_markdown(content)
                    markdown += f"{formatted_content}\n\n"
            
            # Strategic Recommendations Section - if available at root level
            if "strategic_recommendations" in gpt_analysis or "strategic_roadmap_opportunities" in gpt_analysis:
                markdown += "## Recommendations\n\n"
                
                # Try both potential key names
                recommendations = gpt_analysis.get("strategic_recommendations", gpt_analysis.get("strategic_roadmap_opportunities", None))
                
                if recommendations:
                    formatted_recommendations = format_to_markdown(recommendations)
                    
                    # Special handling for recommendation items if they're in a list format
                    if isinstance(recommendations, list) and all(isinstance(rec, dict) for rec in recommendations):
                        for i, rec in enumerate(recommendations, 1):
                            title = rec.get("title", f"Recommendation {i}")
                            desc = rec.get("description", "")
                            impact = rec.get("business_impact", "")
                            complexity = rec.get("implementation_complexity", "")
                            
                            markdown += f"### {i}. {title}\n\n"
                            markdown += f"{desc}\n\n"
                            
                            if impact or complexity:
                                markdown += "**Implementation Details**:\n\n"
                                if impact:
                                    markdown += f"- **Business Impact**: {impact}\n"
                                if complexity:
                                    markdown += f"- **Implementation Complexity**: {complexity}\n"
                                markdown += "\n"
                    else:
                        # Use general formatting for other recommendation structures
                        markdown += f"{formatted_recommendations}\n\n"
        
        # Conclusion
        markdown += "## Conclusion\n\n"
        markdown += f"This report provides an overview of {url}, focusing primarily on what the website contains and offers to visitors. "
        markdown += "The information aims to help you understand the website's purpose, content, and structure without technical jargon.\n\n"
        
        # New Technical Considerations section
        markdown += "---\n\n"
        markdown += "## Technical Considerations\n\n"
        
        # Extract domain information
        server_info = {}
        try:
            # Generate some basic technical info from the domain
            if domain:
                protocol = "https" if url.startswith("https://") else "http"
                server_info = {
                    "Domain": domain,
                    "Protocol": protocol
                }
        except Exception:
            pass
        
        # Count internal/external links
        internal_links_count = 0
        external_links_count = 0
        for page in pages:
            if 'links' in page and page['links']:
                for link in page['links']:
                    if domain in link:
                        internal_links_count += 1
                    else:
                        external_links_count += 1
        
        # Count images
        image_count = sum(len(page.get('images', [])) for page in pages)
        
        markdown += "### Website Infrastructure\n\n"
        markdown += f"- **Domain**: {domain}\n"
        markdown += f"- **Protocol**: {server_info.get('Protocol', 'https/http')}\n"
        markdown += f"- **Pages Analyzed**: {num_pages_crawled}\n\n"
        
        markdown += "### Technical Structure\n\n"
        markdown += f"- **Internal Links**: {internal_links_count}\n"
        markdown += f"- **External Links**: {external_links_count}\n"
        markdown += f"- **Media Elements**: {image_count} images/visual elements\n\n"
        
        # Footer with generation details and branding
        markdown += "*This website report was automatically generated using RegenAI advanced AI analytics.*\n"
        markdown += f"*Generated on: {timestamp}*\n"
        
        return markdown

    def _generate_markdown_report(self, url: str, pages: List[Dict], sitemap: List[str], num_pages_crawled: int, crawl_result: Dict) -> str:
        """Generate a structured markdown report from crawled website data with enhanced content analysis."""
        
        # Create the report header with more professional formatting
        report = f"# Website Research Report: {url}\n\n"
        report += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by RegenAI*\n\n"
        
        # Extract domain for better context
        domain = url.split('//')[1].split('/')[0] if '//' in url else url.split('/')[0]
        
        # Detect website type for better analysis
        is_ecommerce = any(term in url.lower() for term in ['shop', 'store', 'product', 'pricing', 'buy'])
        is_blog = any(term in url.lower() for term in ['blog', 'news', 'article', 'post'])
        is_corporate = any(term in url.lower() for term in ['about', 'company', 'team', 'career', 'contact'])
        is_api_documentation = any(term in url.lower() for term in ['api', 'docs', 'documentation', 'developer'])
        
        # Website Overview Section - Enhanced with more details
        report += "## Website Overview\n\n"
        
        # Try to extract site title and description from the crawl result or pages
        site_title = "Unknown Website"
        site_description = "No description available."
        
        if pages and len(pages) > 0:
            # Use the first page (usually homepage) for title and description
            home_page = pages[0]
            page_title = home_page.get('title', home_page.get('pageTitle', ''))
            if page_title:
                site_title = page_title
            else:
                # Extract title from URL
                title_parts = url.split('/')
                site_title = title_parts[-1].replace('-', ' ').replace('_', ' ').title() if title_parts[-1] else title_parts[-2].replace('-', ' ').replace('_', ' ').title()
            
            # Try to find a description in meta tags or content
            meta_description = home_page.get('description', '')
            meta_tags = home_page.get('meta', home_page.get('metadata', {}))
            if isinstance(meta_tags, dict) and 'description' in meta_tags:
                meta_description = meta_tags['description']
                
            content = home_page.get('content', home_page.get('text', ''))
            
            if meta_description:
                site_description = meta_description
            elif content and len(content) > 200:
                # Extract first paragraph for description
                paragraphs = content.split('\n\n')
                if paragraphs:
                    first_para = paragraphs[0].strip()
                    if len(first_para) > 30:  # Ensure it's a real paragraph
                        site_description = first_para[:self.config["content_preview_length"]] + "..." if len(first_para) > self.config["content_preview_length"] else first_para
                    else:
                        site_description = content[:self.config["content_preview_length"]] + "..." if len(content) > self.config["content_preview_length"] else content
        
        # Add domain and website type information with enhanced business context
        report += f"**Site Name:** {site_title}\n\n"
        report += f"**Domain:** {domain}\n\n"
        report += f"**URL:** {url}\n\n"
        report += f"**Description:** {site_description}\n\n"
        
        # Add website type with business context
        report += "**Website Type:** "
        if is_ecommerce:
            report += "E-commerce / Product Information"
        elif is_blog:
            report += "Blog / News / Content Publisher"
        elif is_corporate:
            report += "Corporate / Business Information"
        elif is_api_documentation:
            report += "API Documentation / Developer Resource"
        else:
            report += "General Information"
        report += "\n\n"
        
        # Add summary of findings section with more details and business focus
        report += "**Executive Summary:**\n\n"
        
        report += f"This enterprise-grade analysis examines {num_pages_crawled} page(s) from {url}. "
        
        # Add tailored business context based on site type
        if is_ecommerce:
            report += f"The website appears to be focused on selling products or services related to {site_title.split(' - ')[0] if ' - ' in site_title else site_title}. "
            report += "The content has been analyzed to assess the effectiveness of product presentation, pricing strategy, and conversion paths. "
        elif is_blog:
            report += f"The website appears to be a content publishing platform focused on {site_title.split(' - ')[0] if ' - ' in site_title else site_title}. "
            report += "The content has been analyzed to evaluate content quality, audience engagement potential, and topic relevance. "
        elif is_corporate:
            report += f"The website appears to be a corporate presence for {site_title.split(' - ')[0] if ' - ' in site_title else site_title}. "
            report += "The content has been analyzed to assess brand messaging, company information clarity, and stakeholder communication effectiveness. "
        elif is_api_documentation:
            report += f"The website appears to be a technical resource providing API or developer documentation for {site_title.split(' - ')[0] if ' - ' in site_title else site_title}. "
            report += "The content has been analyzed to evaluate technical documentation quality, developer experience, and implementation guidance. "
        else:
            report += f"The website appears to be focused on {site_title.split(' - ')[0] if ' - ' in site_title else site_title}. "
            report += "The content has been analyzed to provide insights into the website's purpose, structure, and key information. "
        
        report += "\n\n"
        
        # Sitemap Summary Section - improved formatting
        report += "## Sitemap Summary\n\n"
        report += f"**Total Pages Crawled:** {num_pages_crawled}\n\n"
        
        if sitemap:
            report += "**Pages:**\n\n"
            # Use a more readable list format with indentation
            max_urls_to_display = min(self.config["max_urls_to_display"], len(sitemap))
            for i, site_url in enumerate(sitemap[:max_urls_to_display]):
                # Extract domain and path for better presentation
                try:
                    parsed_url = site_url.split('//')[1] if '//' in site_url else site_url
                    domain_part = parsed_url.split('/')[0]
                    path_part = '/'.join(parsed_url.split('/')[1:])
                    url_name = path_part.replace('-', ' ').replace('_', ' ').title() if path_part else "Homepage"
                    report += f"- [{url_name}]({site_url})  \n"
                except Exception:
                    # Fallback to simple list if parsing fails
                    report += f"- {site_url}\n"
            
            if len(sitemap) > max_urls_to_display:
                report += f"\n*...and {len(sitemap) - max_urls_to_display} more pages*\n"
        else:
            report += "*No explicit sitemap available. Analysis is based on directly crawled pages.*\n"
            
        report += "\n"
        
        # Enhanced Content Analysis Section - New comprehensive analysis
        report += "## Content Analysis\n\n"
        
        # Analyze overall content across all pages
        all_content = " ".join([page.get('content', page.get('text', '')) for page in pages])
        total_word_count = len(all_content.split())
        
        # Extract all headings across pages
        all_headings = []
        for page in pages:
            if 'headings' in page and page['headings']:
                all_headings.extend([h.get('text', '') for h in page['headings'] if h.get('text', '')])
        
        # Content type detection
        content_types = []
        if any("price" in page.get('content', '').lower() for page in pages):
            content_types.append("Pricing information")
        if any("contact" in page.get('content', '').lower() for page in pages):
            content_types.append("Contact information")
        if any("about" in page.get('content', '').lower() for page in pages):
            content_types.append("About/Company information")
        if any("blog" in page.get('content', '').lower() or "article" in page.get('content', '').lower() for page in pages):
            content_types.append("Blog/Article content")
        if any("product" in page.get('content', '').lower() for page in pages):
            content_types.append("Product descriptions")
        if any("api" in page.get('content', '').lower() or "documentation" in page.get('content', '').lower() for page in pages):
            content_types.append("API/Technical documentation")
        
        if not content_types:
            content_types.append("General information")
        
        # Extract and analyze keywords from all content
        words = [w.lower() for w in all_content.split() if len(w) > 4]
        word_freq = {}
        for word in words:
            if word not in word_freq:
                word_freq[word] = 0
            word_freq[word] += 1
        
        # Get top keywords
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        
        # Evaluate content quality based on various metrics
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1) if words else 0
        content_quality = "High" if avg_word_length > 5.5 else "Medium" if avg_word_length > 4.5 else "Basic"
        
        # Analyze content density
        content_density = "High" if total_word_count > 3000 else "Medium" if total_word_count > 1000 else "Low"
        
        # Check for visual content
        has_images = any('images' in page and page['images'] for page in pages)
        total_images = sum(len(page.get('images', [])) for page in pages)
        
        # Check for external links - indicates references and authority
        has_external_links = False
        external_link_count = 0
        for page in pages:
            if 'links' in page and page['links']:
                for link in page['links']:
                    if domain not in link:
                        has_external_links = True
                        external_link_count += 1
        
        # Output content analysis
        report += "**Content Types:** " + str(content_types) + "\n\n"
        
        report += "**Content Overview:**\n\n"
        report += f"- **Total Words:** {total_word_count}\n"
        report += f"- **Content Quality:** {content_quality}\n"
        report += f"- **Content Density:** {content_density}\n"
        report += f"- **Visual Elements:** {'Yes - ' + str(total_images) + ' images' if has_images else 'Limited or None'}\n"
        report += f"- **External References:** {'Yes - ' + str(external_link_count) + ' links' if has_external_links else 'Limited or None'}\n\n"
        
        # Add keyword analysis
        report += "**Key Topics and Terminology:**\n\n"
        for word, freq in top_keywords:
            report += f"- {word} ({freq} occurrences)\n"
        report += "\n"
        
        # Add content structure analysis
        if all_headings:
            report += "**Content Structure Highlights:**\n\n"
            for heading in all_headings[:10]:  # Show top 10 headings
                report += f"- {heading}\n"
            if len(all_headings) > 10:
                report += f"\n*...and {len(all_headings) - 10} more section headings*\n\n"
        
        # Add content strengths and gaps analysis
        report += "**Content Strengths:**\n\n"
        
        # Analyze content strengths based on metrics
        if total_word_count > 2000:
            report += "- **Comprehensive Information**: The website provides substantial content, suggesting a commitment to thorough information.\n"
        if has_images and total_images > 5:
            report += "- **Visual Engagement**: Multiple visual elements enhance the content and improve user engagement.\n"
        if has_external_links and external_link_count > 3:
            report += "- **Well-Referenced**: Content includes external references, which can enhance credibility and authority.\n"
        if len(content_types) >= 3:
            report += "- **Diverse Content Mix**: The website offers various content types to serve different user needs.\n"
        if content_quality == "High":
            report += "- **Professional Writing**: Content appears professionally written with industry-appropriate terminology.\n"
        
        report += "\n**Content Gaps and Opportunities:**\n\n"
        
        # Analyze content gaps based on metrics
        if total_word_count < 1000:
            report += "- **Limited Content Volume**: The website may benefit from expanding its content to provide more comprehensive information.\n"
        if not has_images or total_images < 3:
            report += "- **Visual Enhancement Opportunity**: Adding more visual elements could improve engagement and clarify concepts.\n"
        if not has_external_links or external_link_count < 3:
            report += "- **Authority Building**: Adding references to authoritative sources could enhance credibility.\n"
        if len(content_types) < 2:
            report += "- **Content Diversity**: Expanding to include more content types could serve wider audience needs.\n"
        if content_quality != "High":
            report += "- **Content Quality Enhancement**: The writing quality could be improved to appear more professional and authoritative.\n"
        
        # Add a catch-all recommendation for any website
        report += "- **Audience Targeting**: Content could be further refined to more precisely address specific audience segments and their needs.\n\n"
        
        # Technical Analysis Section - Enhanced with more details
        report += "## Technical Analysis\n\n"
        
        # Check for common technologies and features
        has_links = any('links' in page and page['links'] for page in pages)
        
        report += "**Website Technologies and Features:**\n\n"
        report += f"- **Number of Pages:** {num_pages_crawled}\n"
        report += f"- **Images:** {'Present - ' + str(total_images) + ' total' if has_images else 'Limited or None'}\n"
        report += f"- **External Links:** {'Present - ' + str(external_link_count) + ' total' if has_external_links else 'Limited or None'}\n"
        
        # Check if the URL contains API endpoints or documentation indicators
        if is_api_documentation:
            report += "- **Type:** API Documentation or Developer Resource\n"
        
        # Add content type based on URL patterns
        if is_blog:
            report += "- **Content Type:** Blog or Article Collection\n"
        elif is_ecommerce:
            report += "- **Content Type:** E-commerce or Product Information\n"
        elif is_corporate:
            report += "- **Content Type:** Company Information\n"
        
        report += "\n"
        
        # Detailed Page Analysis Section - Improved with better formatting
        report += "## Detailed Analysis by Page\n\n"
        
        max_pages_to_analyze = min(self.config["max_pages_to_analyze"], len(pages))
        for i, page in enumerate(pages[:max_pages_to_analyze]):
            # Get page details with fallbacks for different API formats
            page_title = page.get('title', page.get('pageTitle', f"Page {i+1}"))
            page_url = page.get('url', url)
            page_content = page.get('content', page.get('text', ''))
            
            # Extract headings if available
            headings = page.get('headings', [])
            
            # Page header with number for better organization
            report += f"### Page {i+1}: {page_title}\n\n"
            report += f"**URL:** [{page_url}]({page_url})\n\n"
            
            # Page Overview with more comprehensive content
            report += "**Overview:**\n\n"
            if page_content:
                # Use configurable preview length
                overview = page_content[:self.config["content_preview_length"]] + "..." if len(page_content) > self.config["content_preview_length"] else page_content
                report += f"{overview}\n\n"
            else:
                report += "This page appears to be dynamically generated or requires authentication. The content structure suggests it contains information related to this domain.\n\n"
            
            # Add headings analysis if available with improved nested list formatting
            if headings and len(headings) > 0:
                report += "**Page Structure:**\n\n"
                last_level = 0
                for heading in headings[:10]:
                    heading_text = heading.get('text', '')
                    heading_tag = heading.get('tag', 'h')
                    if heading_text:
                        level = int(heading_tag[-1]) if heading_tag[-1].isdigit() else 1
                        # Create properly nested bullets
                        indent = '  ' * (level - 1)
                        report += f"{indent}- {heading_text}\n"
                if len(headings) > 10:
                    report += f"\n*...and {len(headings) - 10} more headings*\n"
                report += "\n"
                
            # Key Insights with more detailed analysis and improved list formatting
            report += "**Key Insights:**\n\n"
            
            # Add more detailed content analysis with structured lists
            if page_content:
                # Word count analysis
                words = page_content.split()
                word_count = len(words)
                
                # Content length analysis with more helpful context
                content_length = len(page_content)
                if content_length > 5000:
                    content_size = "Very detailed page with extensive content"
                elif content_length > 2000:
                    content_size = "Comprehensive page with substantial content"
                elif content_length > 1000:
                    content_size = "Standard content page"
                elif content_length > 500:
                    content_size = "Brief content page"
                else:
                    content_size = "Minimal content page"
                
                report += f"- **Content Analysis:** {content_size} ({word_count} words, {content_length} characters)\n"
                
                # Text complexity measure
                avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
                if avg_word_length > 6.5:
                    complexity = "Technical/Academic"
                elif avg_word_length > 5.5:
                    complexity = "Professional"
                elif avg_word_length > 4.5:
                    complexity = "Standard"
                else:
                    complexity = "Conversational"
                    
                report += f"- **Content Complexity:** {complexity} (avg word length: {avg_word_length:.1f} characters)\n"
            
                # Link analysis with more detail and improved nested list formatting
                links = page.get('links', [])
                if links:
                    internal_links = [link for link in links if domain in link]
                    external_links = [link for link in links if domain not in link]
                    report += f"- **Link Analysis:** {len(links)} total links\n"
                    report += f"  - **Internal Links:** {len(internal_links)}\n"
                    report += f"  - **External Links:** {len(external_links)}\n"
                    
                    # List important external links with proper nesting
                    if external_links and len(external_links) > 0:
                        report += "  - **Key External Resources:**\n"
                        for ext_link in external_links[:3]:  # List up to 3 external links
                            domain = ext_link.split('//')[1].split('/')[0] if '//' in ext_link else ext_link.split('/')[0]
                            report += f"    - [{domain}]({ext_link})\n"
                        if len(external_links) > 3:
                            report += f"    - *...and {len(external_links) - 3} more external links*\n"
                
                # Image analysis with improved formatting
                images = page.get('images', [])
                if images:
                    report += f"- **Visual Content:** {len(images)} images/visual elements\n"
                    # Show sample image types if available
                    image_types = {}
                    for img in images[:10]:
                        img_url = img.get('src', '')
                        ext = img_url.split('.')[-1].lower() if '.' in img_url else 'unknown'
                        if ext in image_types:
                            image_types[ext] += 1
                        else:
                            image_types[ext] = 1
                    
                    if image_types:
                        report += "  - **Image Types:**\n"
                        for ext, count in image_types.items():
                            report += f"    - {ext}: {count}\n"
                
                # Add keyword analysis with improved formatting
                # Simple keyword extraction (could be enhanced with NLP)
                words = [w.lower() for w in page_content.split() if len(w) > 4]
                word_freq = {}
                for word in words:
                    if word not in word_freq:
                        word_freq[word] = 0
                    word_freq[word] += 1
                
                # Get top keywords
                top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                if top_keywords:
                    report += "- **Key Topics:**\n"
                    for word, freq in top_keywords:
                        report += f"  - {word} ({freq} occurrences)\n"
                
                # Add business purpose analysis - new section
                report += "- **Business Purpose:** "
                if "pricing" in page_url.lower() or "price" in page_content.lower():
                    report += "This page appears to serve conversion goals by providing pricing information.\n"
                elif "contact" in page_url.lower() or "contact" in page_content.lower():
                    report += "This page facilitates customer engagement through contact information and communication channels.\n"
                elif "about" in page_url.lower() or "about" in page_content.lower():
                    report += "This page builds brand trust by providing company information and background.\n"
                elif "blog" in page_url.lower() or "article" in page_content.lower() or "post" in page_url.lower():
                    report += "This page appears to support content marketing and thought leadership goals.\n"
                elif "product" in page_url.lower() or "service" in page_content.lower():
                    report += "This page appears to be focused on showcasing products or services for potential customers.\n"
                else:
                    report += "This page appears to provide general information supporting the website's core purpose.\n"
            
            # If we don't have content but it's a specific type of page, add general insights
            elif not page_content:
                url_lower = page_url.lower() if page_url else ""
                if "pricing" in url_lower:
                    report += "- **Page Purpose:** This page appears to provide pricing information for services or products.\n"
                    report += "- **Target Audience:** Potential customers seeking cost information.\n"
                    report += "- **Business Goal:** Likely conversion-focused, helping users make purchase decisions.\n"
                elif "blog" in url_lower or "news" in url_lower:
                    report += "- **Page Purpose:** This appears to be a blog or news page with articles or updates.\n"
                    report += "- **Content Type:** Articles, posts, or news updates.\n"
                    report += "- **Business Goal:** Likely focused on audience engagement and establishing authority.\n"
                elif "about" in url_lower:
                    report += "- **Page Purpose:** This appears to be an about page with company information.\n"
                    report += "- **Content Type:** Company history, mission, team information.\n"
                    report += "- **Business Goal:** Building brand trust and credibility with potential customers.\n"
                else:
                    report += "- **Page Purpose:** This page likely contains information relevant to the site's main topic.\n"
                    report += "- **Content Access:** The content may require JavaScript rendering or authentication to access.\n"
                    report += "- **Business Impact:** Unable to assess business impact due to limited content access.\n"
            
            report += "\n"
            
        if len(pages) > max_pages_to_analyze:
            report += f"*Note: {len(pages) - max_pages_to_analyze} additional pages were crawled but not included in the detailed analysis.*\n\n"
        
        # Strategic Recommendations - Enhanced with better business focus
        report += "## Strategic Recommendations\n\n"
        
        report += f"Based on this comprehensive analysis of {url}, we offer the following business-focused recommendations:\n\n"
        
        # Add tailored insights based on the URL type with numbered recommendations
        report += "1. **Content Strategy Enhancement**  \n"
        
        if total_word_count < 2000:
            report += "   Consider expanding the content to provide more comprehensive information to visitors, which can improve search rankings and user engagement.\n\n"
        else:
            report += "   The existing content provides a good foundation, but could be further optimized by adding more targeted keywords and structured data.\n\n"
        
        report += "2. **User Experience Opportunities**  \n"
        if not has_images or total_images < 5:
            report += "   Enhance user engagement by adding more visual elements including images, infographics, or videos to illustrate key concepts.\n\n"
        else:
            report += "   The current visual elements provide good engagement. Consider testing variations to identify which visuals drive the most user interaction.\n\n"
        
        # Additional custom recommendations based on site type
        if is_ecommerce:
            report += "3. **Conversion Path Optimization**  \n"
            report += "   Review the customer journey from landing page to purchase, ensuring clear calls-to-action and minimizing friction points in the conversion process.\n\n"
            
            report += "4. **Product Information Enhancement**  \n"
            report += "   Ensure product descriptions are comprehensive, address common customer questions, and highlight unique selling points to differentiate from competitors.\n\n"
        elif is_blog:
            report += "3. **Content Distribution Strategy**  \n"
            report += "   Develop a systematic approach to content promotion across relevant channels to maximize reach and engagement with target audiences.\n\n"
            
            report += "4. **Content Series Development**  \n"
            report += "   Consider creating interconnected content series on key topics to improve user retention and establish deeper authority in your niche.\n\n"
        elif is_corporate:
            report += "3. **Trust Signal Enhancement**  \n"
            report += "   Incorporate more social proof elements such as testimonials, case studies, and client logos to build credibility with potential customers.\n\n"
            
            report += "4. **Value Proposition Clarity**  \n"
            report += "   Ensure your unique value proposition is consistently and clearly communicated across all key pages of the website.\n\n"
        elif is_api_documentation:
            report += "3. **Technical Documentation Usability**  \n"
            report += "   Consider adding more code examples, interactive demos, and quick-start guides to help developers implement your solutions more efficiently.\n\n"
            
            report += "4. **Developer Community Building**  \n"
            report += "   Create opportunities for developer engagement through forums, comment sections, or integration with community platforms like GitHub or Stack Overflow.\n\n"
        
        # Universal recommendations for any site type
        report += "5. **SEO and Discoverability**  \n"
        report += "   Optimize metadata, heading structure, and internal linking to improve search engine visibility and organic traffic acquisition.\n\n"
            
        report += "6. **Analytics Implementation Review**  \n"
        report += "   Ensure proper tracking is in place to measure key performance indicators aligned with business goals, enabling data-driven optimization.\n\n"
        
        # References Section with improved formatting
        report += "## References\n\n"
        report += f"- **Main URL:** [{url}]({url})\n"
        
        # Format references as a numbered list for better readability
        for i, ref_url in enumerate(sitemap[:10]):
            try:
                ref_name = ref_url.split('//')[1].split('/')[0] if '//' in ref_url else ref_url
                path = '/'.join(ref_url.split('//')[1].split('/')[1:]) if '//' in ref_url else '/'.join(ref_url.split('/')[1:])
                if path:
                    ref_label = f"{ref_name}/{path}"
                else:
                    ref_label = ref_name
                    
                report += f"{i+1}. [{ref_label}]({ref_url})\n"
            except Exception:
                # Fallback in case URL parsing fails
                report += f"{i+1}. {ref_url}\n"
        
        if len(sitemap) > 10:
            report += f"\n*And {len(sitemap) - 10} additional referenced pages*\n"
        
        # Add research metadata
        report += "\n---\n\n"
        report += "*This report was automatically generated using RegenAI's advanced web crawling and analysis technology.*\n"
        report += f"*Research Date: {datetime.now().strftime('%Y-%m-%d')}*\n"
        
        return report

    def generate_pdf_from_markdown(self, filename: str, markdown_content: str, output_path: str = None, title: str = "Website Research Report") -> str:
        """Generate a PDF file from markdown content."""
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"website_report_{timestamp}.pdf"
                output_path = os.path.join(self.config["output_dir"], filename)
            
            converter = MarkdownPDFConverter()
            pdf_path = converter.convert(
                markdown_content=markdown_content,
                output_path=output_path,
                title=title,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                add_logos=True  # Enable the logos in the PDF header
            )
            
            logger.info(f"Successfully generated PDF: {pdf_path}")
            
            # Return the full PDF path for consistency
            # return pdf_path
            return filename
            
        except Exception as e:
            logger.error(f"Error generating PDF from markdown: {str(e)}", exc_info=True)
            raise

class URLSearchPDFAgent:
    """Helper class for integrating the URLSearchPDFTool with a phi Agent."""
    
    @staticmethod
    def configure_agent(
        agent,
        model,
        max_pages: int = 8,
        save_to_pdf: bool = True,
        output_dir: str = GENERATED_FILES_DIR,
        content_preview_length: int = 500,
        max_urls_to_display: int = 15,
        max_pages_to_analyze: int = 15,
        model_name: str = "gpt-4o-mini",
        fallback_model_name: str = "gpt-3.5-turbo",
        debug_mode: bool = False
    ):
        """
        Configure a URL Search PDF Agent with the proper tools and instructions.
        
        Args:
            agent: The phi Agent to configure
            model: The LLM model to use
            max_pages: Maximum number of pages to crawl
            save_to_pdf: Whether to save the report as a PDF
            output_dir: Directory to save output files
            content_preview_length: Length of content preview in characters
            max_urls_to_display: Maximum number of URLs to display in report
            max_pages_to_analyze: Maximum number of pages to analyze in report
            model_name: Name of the GPT model to use for analysis
            fallback_model_name: Fallback model if primary model fails
            debug_mode: Whether to enable debug mode
            
        Returns:
            The configured agent
        """
        
        # Make sure output_dir is absolute
        if not os.path.isabs(output_dir):
            output_dir = GENERATED_FILES_DIR
            
        # Create the URL Search PDF Tool with all configurable parameters
        url_search_tool = URLSearchPDFTool(
            max_pages=max_pages,
            save_to_pdf=save_to_pdf,
            output_dir=output_dir,
            content_preview_length=content_preview_length,
            max_urls_to_display=max_urls_to_display,
            max_pages_to_analyze=max_pages_to_analyze,
            model_name=model_name,
            fallback_model_name=fallback_model_name
        )
        
        # Configure post-processing callback to generate PDF from the markdown response
        def post_process_response(response, session_id=None):
            try:
                # Check if response contains PDF path marker
                pdf_marker = re.search(r'\^([^\s]+)', response)
                if pdf_marker:
                    pdf_path = pdf_marker.group(1)
                    return f"Analysis complete! Generated PDF report: {pdf_path}"
                
                # If no PDF marker found, return the original response
                return response
                
            except Exception as e:
                logger.error(f"Error in post-processing: {str(e)}", exc_info=True)
                return response
        
        # Configure the agent with improved instructions
        _url_search_agent = {
            "model": model,
            "name": "URL Search Agent",
            "role": "Generate an enterprise-grade research report from a given website URL",
            "description": "You are a Senior Business Analyst tasked with creating comprehensive website analyses with actionable business insights.",
            "instructions": [
                "When given a website URL, use the `research_website` tool to analyze the website and generate a comprehensive report.",
                "The tool will automatically crawl up to 8 pages of the site and analyze the content using advanced AI.",
                "The report will include business-focused insights on content quality, user experience, competitive positioning, and strategic recommendations.",
                "The report will be saved as both a markdown file and a PDF document for easy sharing.",
                "When you receive a response with a PDF path marker (^path/to/file.pdf), inform the user that their enterprise-grade analysis is ready."
            ],
            "tools": [url_search_tool],
            "markdown": True,
            "show_tool_calls": debug_mode,
            "add_datetime_to_instructions": True,
            "post_process_response": post_process_response,
            "save_response_to_file": None,  # We don't need to save the agent's response since the tool handles file generation
            "debug_mode": debug_mode,
        }
        
        return _url_search_agent

from typing import Union, Optional, Dict, Any, List
from textwrap import dedent
from datetime import datetime
import os
import logging
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

logger = logging.getLogger(__name__)

def create_url_search_agent(
    model: Union[str, OpenAIChat, Claude],
    session_id: Optional[str] = None,
    max_pages: int = 8,
    save_to_pdf: bool = True,
    output_dir: str = GENERATED_FILES_DIR,
    content_preview_length: int = 2500,
    max_urls_to_display: int = 15,
    max_pages_to_analyze: int = 15,
    model_name: str = "gpt-4o-mini",
    fallback_model_name: str = "gpt-3.5-turbo",
    debug_mode: bool = False
) -> Agent:
    """
    Create a URL Search Agent with proper error handling and validation.
    
    Args:
        model: The LLM model to use (OpenAI or Claude)
        session_id: Optional session identifier
        max_pages: Maximum number of pages to crawl
        save_to_pdf: Whether to save the report as a PDF
        output_dir: Directory to save generated files
        content_preview_length: Length of content preview in characters
        max_urls_to_display: Maximum number of URLs to display in report
        max_pages_to_analyze: Maximum number of pages to analyze in report
        model_name: Name of the GPT model to use for analysis
        fallback_model_name: Fallback model if primary fails
        debug_mode: Enable debug logging
        
    Returns:
        Configured Agent instance
    """
    # Validate output directory
    if not os.path.isabs(output_dir):
        output_dir = GENERATED_FILES_DIR
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the URL Search PDF Tool with all configurable parameters
    url_search_tool = URLSearchPDFTool(
        max_pages=max_pages,
        save_to_pdf=save_to_pdf,
        output_dir=output_dir,
        content_preview_length=content_preview_length,
        max_urls_to_display=max_urls_to_display,
        max_pages_to_analyze=max_pages_to_analyze,
        model_name=model_name,
        fallback_model_name=fallback_model_name
    )
    
    # Configure post-processing function
    def post_process_response(response):
        try:
            # Check if response contains PDF path marker
            pdf_marker = re.search(r'\^([^\s]+)', response)
            if pdf_marker:
                pdf_path = pdf_marker.group(1)
                return f"Analysis complete! Generated PDF report: {pdf_path}"
            
            # If no PDF marker found, return the original response
            return response
            
        except Exception as e:
            logger.error(f"Error in post-processing: {str(e)}", exc_info=True)
            return response
    
    # Create agent configuration
    agent_config = {
        "model": model,
        "name": "URL Search Agent",
        "role": "Research websites and generate comprehensive PDF reports",
        "description": dedent("""
            You are a professional research assistant specializing in website analysis.
            When provided with a URL, you produce detailed and insightful reports about the website's
            content, structure, purpose, and business value.
        """),
        "instructions": [
            "When given a website URL, use the research_website tool to analyze it.",
            "The tool will crawl the site and generate both a markdown and PDF report with business-focused insights.",
            "The report will include content analysis, user experience evaluation, competitive positioning, and strategic recommendations.",
            "Your role is to take the URL from the user and pass it to the tool, then deliver the completed report.",
            "When you receive a response with a PDF path marker (^/path/to/file.pdf), extract the path and inform the user that the report is ready."
        ],
        "tools": [url_search_tool],
        "markdown": True,
        "show_tool_calls": debug_mode,
        "add_datetime_to_instructions": True,
        "post_process_response": post_process_response,
        "save_response_to_file": f"{output_dir}/{session_id}_agent_response.md" if session_id else None,
        "debug_mode": debug_mode,
    }
    
    # Create and return the agent
    return Agent(**agent_config)

def test_url_search_tool(url: str, output_dir: str = GENERATED_FILES_DIR):
    """
    Test function to verify the enhanced URL Search PDF Tool.
    
    Args:
        url: The website URL to analyze
        output_dir: Directory to save the output files
    
    Returns:
        Path to the generated PDF file
    """
    try:
        logger.info(f"Testing enhanced URL Search PDF Tool with URL: {url}")
        
        # Create the tool with default settings
        tool = URLSearchPDFTool(
            max_pages=5,  # Use fewer pages for testing
            save_to_pdf=True,
            output_dir=output_dir,
            content_preview_length=1000,
            max_urls_to_display=10,
            max_pages_to_analyze=5,
            model_name="gpt-4o-mini",
            fallback_model_name="gpt-3.5-turbo"
        )
        
        # Generate a unique session ID for this test
        session_id = f"test_{uuid.uuid4()}"
        
        # Run the analysis
        result = tool.research_website(
            url=url,
            session_id=session_id,
            max_pages=5
        )
        
        logger.info(f"Test complete with result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Example usage of the test function
    import sys
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"Testing URL Search PDF Tool with URL: {test_url}")
        result = test_url_search_tool(test_url)
        print(f"Result: {result}")
    else:
        print("Please provide a URL as a command line argument")