"""
Markdown to PDF Converter with Enhanced Formatting Support

This utility module provides robust markdown to PDF conversion with proper formatting
preservation including headers, bold text, italics, tables, code blocks, and more.

It uses a combination of markdown, HTML/CSS styling, and WeasyPrint to create
professional-looking PDF documents from markdown content.
"""

import os
import logging
import tempfile
from typing import Optional, List, Dict, Any
import base64

# PDF generation imports
import markdown
from weasyprint import HTML, CSS
from agno.utils.log import logger

# Define the path to logos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGOS_DIR = os.path.join(CURRENT_DIR, "logos")

class MarkdownPDFConverter:
    """
    Enterprise-grade Markdown to PDF converter with enhanced formatting support.
    
    This class provides methods to convert markdown content to properly formatted
    PDF documents while preserving all formatting styles, including:
    - Headers (h1-h6)
    - Bold/italic text
    - Lists (ordered and unordered)
    - Tables
    - Code blocks with syntax highlighting
    - Links
    - Images
    - Blockquotes
    """
    
    def __init__(self, 
                 css_stylesheet: Optional[str] = None,
                 page_size: str = "A4",
                 margin: str = "2cm"):
        """
        Initialize the converter with optional styling parameters.
        
        Args:
            css_stylesheet: Optional custom CSS stylesheet
            page_size: Page size (default: A4)
            margin: Page margins (default: 2cm)
        """
        self.page_size = page_size
        self.margin = margin
        self.css_stylesheet = css_stylesheet or self._get_default_stylesheet()
        
    def _get_default_stylesheet(self) -> str:
        """
        Get the default CSS stylesheet for PDF generation.
        
        Returns:
            str: CSS stylesheet string
        """
        return """
            @page {{
                size: {page_size};
                margin: {margin};
                @bottom-center {{
                    content: element(footer);
                    width: 100%;
                }}
            }}
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                counter-reset: page 1;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #333;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            h1 {{ font-size: 24pt; }}
            h2 {{ font-size: 18pt; }}
            h3 {{ font-size: 16pt; }}
            h4 {{ font-size: 14pt; }}
            h5 {{ font-size: 12pt; font-weight: bold; }}
            h6 {{ font-size: 12pt; font-style: italic; }}
            p {{ margin-bottom: 1em; }}
            strong {{ font-weight: bold; }}
            em {{ font-style: italic; }}
            ul, ol {{ margin-left: 2em; margin-bottom: 1em; }}
            li {{ margin-bottom: 0.5em; }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 1em;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
            }}
            th {{ background-color: #f2f2f2; }}
            code {{
                font-family: monospace;
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 3px;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 12px;
                border-radius: 3px;
                overflow-x: auto;
            }}
            a {{ color: #0066cc; }}
            blockquote {{
                margin-left: 1em;
                padding-left: 1em;
                border-left: 3px solid #ccc;
                color: #555;
            }}
            img {{ max-width: 100%; }}
            .header {{ text-align: center; margin-bottom: 2em; }}
            .footer {{ 
                text-align: center; 
                font-size: 9pt; 
                color: #777; 
                margin-top: 2em;
                position: running(footer);
                padding-bottom: 10px;
            }}
            .logo-container {{ 
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 20px;
                width: 100%;
                padding: 20px 0px 0 0px;
            }}
            .client-logo {{ 
                height: 80px;
                width: auto;
                object-fit: contain;
            }}
            .letterhead {{
                position: relative;
                width: 100%;
                height: 100px;
                margin-bottom: 30px;
            }}
            #main-content {{
                min-height: 800px;
            }}
        """.format(page_size=self.page_size, margin=self.margin)
        
    def convert(self, 
                markdown_content: str, 
                output_path: str,
                title: Optional[str] = None,
                author: Optional[str] = None,
                date: Optional[str] = None,
                add_header_footer: bool = True,
                add_logos: bool = True) -> str:
        """
        Convert markdown content to a PDF file.
        
        Args:
            markdown_content: The markdown content to convert
            output_path: Path where to save the PDF file
            title: Optional title for the document
            author: Optional author name
            date: Optional date string
            add_header_footer: Whether to add header and footer to the document
            add_logos: Whether to add logos to the header
            
        Returns:
            str: Path to the generated PDF file
        """
        try:
            # Convert markdown to HTML with extensions for enhanced formatting
            html_content = markdown.markdown(
                markdown_content,
                extensions=[
                    'markdown.extensions.tables',
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.toc',
                    'markdown.extensions.sane_lists',
                    'markdown.extensions.nl2br'
                ]
            )
            
            # Initialize HTML components
            header_html = ""
            
            if add_header_footer and add_logos:
                # Define the client logo path
                client_logo_path = os.path.join(LOGOS_DIR, "sgu_logo.png")
                
                # Add client logo in center if available
                if os.path.exists(client_logo_path):
                    with open(client_logo_path, "rb") as f:
                        client_logo_data = base64.b64encode(f.read()).decode("utf-8")
                    
                    header_html += f"""
                    <div class="letterhead">
                        <div class="logo-container">
                            <img src="data:image/png;base64,{client_logo_data}" class="client-logo" alt="Client Logo">
                        </div>
                    </div>
                    """
            
            # Add document title section
            if add_header_footer:
                header_html += "<div class='header'>"
                if title:
                    header_html += f"<h1>{title}</h1>"
                if author:
                    header_html += f"<p><em>Author: {author}</em></p>"
                if date:
                    header_html += f"<p><em>Date: {date}</em></p>"
                header_html += "</div>"
            
            # Add simple footer without logo
            footer_html = """
            <div class='footer'>
                <p>Generated by RegenAI</p>
            </div>
            """ if add_header_footer else ""
            
            # Combine everything into a properly structured HTML document
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    {self.css_stylesheet}
                </style>
            </head>
            <body>
                {header_html}
                <div id="main-content">
                    {html_content}
                </div>
                {footer_html}
            </body>
            </html>
            """
            
            # Create a temporary HTML file
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_html:
                tmp_html_path = tmp_html.name
                tmp_html.write(full_html.encode('utf-8'))
            
            # Convert HTML to PDF using WeasyPrint
            HTML(tmp_html_path).write_pdf(output_path)
            
            # Clean up temporary file
            os.unlink(tmp_html_path)
            
            logger.info(f"Successfully converted markdown to PDF: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting markdown to PDF: {str(e)}")
            raise
    
    @staticmethod
    def save_markdown_and_convert_to_pdf(markdown_content: str, 
                                         base_path: str,
                                         filename_base: str,
                                         title: Optional[str] = None,
                                         author: Optional[str] = None,
                                         date: Optional[str] = None) -> Dict[str, str]:
        """
        Save markdown content to a file and convert it to PDF.
        
        Args:
            markdown_content: The markdown content
            base_path: Base path for saving files
            filename_base: Base filename (without extension)
            title: Optional title for the document
            author: Optional author name
            date: Optional date string
            
        Returns:
            Dict with paths to the generated files
        """
        # Ensure directory exists
        os.makedirs(base_path, exist_ok=True)
        
        # Create file paths
        md_path = os.path.join(base_path, f"{filename_base}.md")
        pdf_path = os.path.join(base_path, f"{filename_base}.pdf")
        
        # Save markdown content
        with open(md_path, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_content)
            
        # Convert to PDF
        converter = MarkdownPDFConverter()
        converter.convert(
            markdown_content=markdown_content,
            output_path=pdf_path,
            title=title,
            author=author,
            date=date,
            add_logos=True  # Enable logos
        )
        logger.info(f"Saved markdown to: {md_path}")
        logger.info(f"Saved PDF to: {pdf_path}")
        
        return {
            "markdown_path": md_path,
            "pdf_path": pdf_path
        }