# //ai/tools/string_reader.py
from typing import List

from agno.document.base import Document
from agno.document.reader.base import Reader
from agno.utils.log import logger



class StringReader(Reader):
    """Reader for text content from a string"""

    def read(self, content: str, name: str) -> List[Document]:
        if not content:
            raise ValueError("No content provided")

        try:
            logger.info(f"Reading content: {name}")
            documents = [
                Document(
                    name=name,
                    id=name,
                    content=content,
                )
            ]
            if hasattr(self, 'chunk') and self.chunk:
                chunked_documents = []
                for document in documents:
                    chunked_documents.extend(self.chunk_document(document))
                return chunked_documents
            return documents
        except Exception as e:
            logger.error(f"Error reading content: {name}: {e}")
            return []