"""Document Parser orchestrator for converting files to Document objects."""

from pathlib import Path
from typing import Optional, Union

from app.knowledge.exceptions import DocumentParserError, PDFLoaderError
from app.knowledge.loaders.pdf_loader import PDFLoader
from app.knowledge.models.document import Document
from app.utils.logging import logger


class DocumentParser:
    """Orchestrates document loading and parses files into structured Document domain objects."""

    @staticmethod
    def parse(file_path: Union[str, Path], document_id: Optional[str] = None) -> Document:
        """Parses a document file on disk into a Document domain object.

        Args:
            file_path (Union[str, Path]): Path to target file.
            document_id (Optional[str]): Optional custom document UUID identifier.

        Returns:
            Document: Constructed Document object containing page objects.

        Raises:
            DocumentParserError: If extension is unsupported or parsing fails.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"DocumentParser error: File does not exist at '{file_path}'")
            raise DocumentParserError(f"File not found: {file_path}")

        file_ext = path.suffix.lower().lstrip(".")
        if not file_ext:
            file_ext = "pdf"

        logger.info(f"Parsing document '{path.name}' (type: {file_ext})...")

        try:
            if file_ext == "pdf":
                pages = PDFLoader.load(path)
            else:
                logger.error(f"Unsupported file format '.{file_ext}' for file '{path.name}'")
                raise DocumentParserError(f"Unsupported file format: .{file_ext}")

            # Construct Document object
            file_size = path.stat().st_size if path.exists() else 0
            doc_kwargs = {
                "filename": path.name,
                "title": path.stem.replace("_", " ").replace("-", " ").title(),
                "file_type": file_ext,
                "total_pages": len(pages),
                "pages": pages,
                "metadata": {
                    "source_path": str(path.resolve()),
                    "file_size_bytes": file_size,
                },
            }
            if document_id:
                doc_kwargs["id"] = document_id

            document = Document(**doc_kwargs)
            logger.info(
                f"Successfully parsed '{document.filename}' into Document (ID: {document.id}) "
                f"with {document.total_pages} pages ({document.total_characters} total characters)."
            )
            return document

        except PDFLoaderError as e:
            logger.error(f"Loader failed while parsing '{path.name}': {e}")
            raise DocumentParserError(f"Failed to parse document '{path.name}': {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error while parsing '{path.name}': {e}")
            raise DocumentParserError(f"Error parsing document '{path.name}': {str(e)}") from e
