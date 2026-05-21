# parser_agent.py
# Responsible for extracting raw German words from three input types:
# plain text, image files, and PDF files.
# This agent does ONE thing — extract text. No translation, no enrichment.

import fitz  # PyMuPDF for PDF extraction
import pytesseract
from PIL import Image
from pathlib import Path

from pipeline.config import SUPPORTED_INPUT_TYPES, TESSERACT_PATH

# Tell pytesseract where the Tesseract executable lives on this machine
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_from_text(raw_text: str) -> list[str]:
    """
    Cleans and splits a plain text string into individual words.
    Handles comma-separated, newline-separated, or space-separated inputs.
    """
    # Replace common separators with spaces so we can split uniformly
    cleaned = raw_text.replace(",", " ").replace("\n", " ").replace(";", " ")

    # Split into individual words and strip whitespace from each
    words = [word.strip() for word in cleaned.split(" ")]

    # Remove empty strings that appear after splitting
    words = [word for word in words if word]

    return words


def extract_from_image(image_path: str) -> list[str]:
    """
    Uses OCR to extract text from an image file, then returns word list.
    Expects German text — language hint improves OCR accuracy.
    """
    image = Image.open(image_path)

    # lang="deu" tells Tesseract to expect German text
    # This improves accuracy for German characters like ä, ö, ü, ß
    raw_text = pytesseract.image_to_string(image, lang="deu")

    # Reuse our text extractor to clean and split the OCR output
    return extract_from_text(raw_text)


def extract_from_pdf(pdf_path: str) -> list[str]:
    """
    Extracts all text from every page of a PDF file, then returns word list.
    """
    all_text = ""

    # Open the PDF — fitz is PyMuPDF's main interface
    pdf_document = fitz.open(pdf_path)

    for page in pdf_document:
        # Extract plain text from each page and append
        all_text += page.get_text()

    pdf_document.close()

    return extract_from_text(all_text)


def run(input_type: str, input_data: str) -> list[str]:
    """
    Main entry point for the Parser Agent.
    Routes the input to the correct extractor based on input_type.

    Args:
        input_type: one of 'text', 'image', 'pdf'
        input_data: either raw text string or a file path

    Returns:
        List of extracted German words
    """
    if input_type not in SUPPORTED_INPUT_TYPES:
        raise ValueError(f"Unsupported input type: {input_type}. "
                         f"Must be one of {SUPPORTED_INPUT_TYPES}")

    if input_type == "text":
        return extract_from_text(input_data)

    if input_type == "image":
        # Verify the file actually exists before trying to open it
        if not Path(input_data).exists():
            raise FileNotFoundError(f"Image file not found: {input_data}")
        return extract_from_image(input_data)

    if input_type == "pdf":
        # Verify the file actually exists before trying to open it
        if not Path(input_data).exists():
            raise FileNotFoundError(f"PDF file not found: {input_data}")
        return extract_from_pdf(input_data)