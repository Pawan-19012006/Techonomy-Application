"""Ingestion & Reset CLI script for Company Evidence and Instruction Knowledge Datasets."""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.knowledge.ingestion.ingest import (
    ingest_company_pdf,
    ingest_instruction_pdf,
    reset_company_knowledge,
    reset_instruction_knowledge,
)
from app.utils.logging import logger


def main():
    parser = argparse.ArgumentParser(description="Ingest or Reset Techonomy Datasets (Company vs Instruction)")
    parser.add_argument(
        "--type",
        choices=["company", "instruction", "reset-company", "reset-instruction", "all"],
        required=True,
        help="Target action or dataset category to ingest/reset.",
    )
    args = parser.parse_args()

    base_dir = settings.BASE_DIR / "data" / "documents"
    company_dir = base_dir / "company"
    instruction_dir = base_dir / "instructions"

    company_dir.mkdir(parents=True, exist_ok=True)
    instruction_dir.mkdir(parents=True, exist_ok=True)

    if args.type == "reset-company":
        logger.info("=== Resetting Company Knowledge Collection ===")
        reset_company_knowledge()
        logger.info("✅ company_knowledge collection reset successfully.")
        return

    if args.type == "reset-instruction":
        logger.info("=== Resetting Instruction Knowledge Collection ===")
        reset_instruction_knowledge()
        logger.info("✅ instruction_knowledge collection reset successfully.")
        return

    if args.type in ["company", "all"]:
        logger.info(f"=== Ingesting Company Documents from '{company_dir}' ===")
        company_pdfs = list(company_dir.glob("*.pdf"))
        if not company_pdfs:
            logger.warning(f"No PDF files found in '{company_dir}'. Place company PDFs inside this directory.")
        else:
            for pdf in company_pdfs:
                logger.info(f"Ingesting company PDF: {pdf.name}")
                ingest_company_pdf(pdf)
            logger.info("✅ Company documents ingestion complete.")

    if args.type in ["instruction", "all"]:
        logger.info(f"=== Ingesting Instruction Documents from '{instruction_dir}' ===")
        instruction_pdfs = list(instruction_dir.glob("*.pdf"))
        if not instruction_pdfs:
            logger.warning(f"No PDF files found in '{instruction_dir}'. Place analytical instruction PDFs inside this directory.")
        else:
            for pdf in instruction_pdfs:
                logger.info(f"Ingesting instruction PDF: {pdf.name}")
                ingest_instruction_pdf(pdf)
            logger.info("✅ Analytical instruction documents ingestion complete.")


if __name__ == "__main__":
    main()
