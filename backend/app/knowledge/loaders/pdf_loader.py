"""PDF Document Loader using PyMuPDF (fitz)."""

from pathlib import Path
from typing import List, Union
import fitz  # PyMuPDF

from app.knowledge.exceptions import PDFLoaderError
from app.knowledge.models.page import Page
from app.utils.logging import logger


class PDFLoader:
    """PDF Document Loader utilizing PyMuPDF for raw page text extraction."""

    @staticmethod
    def load(file_path: Union[str, Path]) -> List[Page]:
        """Opens a PDF file and extracts text page-by-page into Page domain objects.

        Args:
            file_path (Union[str, Path]): Path to the PDF file on disk.

        Returns:
            List[Page]: List of extracted Page domain objects (1-indexed).

        Raises:
            PDFLoaderError: If file is not found, unreadable, or invalid PDF format.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"PDFLoader error: File not found at path '{file_path}'")
            raise PDFLoaderError(f"PDF file not found: {file_path}")

        if not path.is_file():
            logger.error(f"PDFLoader error: Path '{file_path}' is not a valid file.")
            raise PDFLoaderError(f"Path is not a valid file: {file_path}")

        logger.info(f"Opening PDF file '{path.name}' for page text extraction...")

        pages: List[Page] = []
        doc = None

        try:
            doc = fitz.open(str(path))
            total_count = len(doc)
            logger.info(f"PDF '{path.name}' opened successfully. Total pages: {total_count}")

            for idx, page in enumerate(doc):
                page_num = idx + 1
                raw_text = page.get_text("text") or ""
                
                # Page-level extraction metadata
                page_meta = {
                    "raw_char_count": len(raw_text),
                    "width": float(page.rect.width),
                    "height": float(page.rect.height),
                }

                pages.append(
                    Page(
                        page_number=page_num,
                        text=raw_text,
                        metadata=page_meta
                    )
                )
                logger.debug(f"Extracted page {page_num}/{total_count} ({len(raw_text)} chars)")

            logger.info(f"Finished PDF text extraction for '{path.name}'. Extracted {len(pages)} pages.")
            return pages

        except fitz.FileDataError as e:
            logger.error(f"Corrupt or invalid PDF file '{file_path}': {e}")
            raise PDFLoaderError(f"Invalid or corrupt PDF file '{file_path}': {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error while reading PDF '{file_path}': {e}")
            raise PDFLoaderError(f"Failed to load PDF '{file_path}': {str(e)}") from e
        finally:
            if doc is not None:
                doc.close()
