"""
PDF processing service for insurance policy documents.

Handles text extraction (including OCR fallback), chunking, and cleaning.
"""

import re
from typing import Optional


# =========================
# CONFIG (safe defaults)
# =========================
PDF_CHUNK_SIZE = 500
PDF_MAX_WORDS = 5000

OCR_FALLBACK_THRESHOLD = 50


# =========================
# MAIN FUNCTION
# =========================
def extract_text_from_pdf(file):
    """
    Extract text from PDF using pdfplumber with OCR fallback.

    Returns:
        tuple: (full_text, table_data)
    """
    import pdfplumber

    try:
        print("=== STEP 1: TRYING PDFPLUMBER ===")

        with pdfplumber.open(file) as pdf:
            text = ""
            tables = []

            print(f"PDF OPENED: {len(pdf.pages)} pages found")

            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"
                        print(f"Page {i+1}: Extracted {len(page_text)} chars")
                    else:
                        print(f"Page {i+1}: No text")

                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                        print(f"Page {i+1}: Found {len(page_tables)} tables")

                except Exception as e:
                    print(f"Page {i+1} error:", e)

            text = text.strip()

            print("TOTAL TEXT LENGTH:", len(text))
            print("TOTAL TABLES:", len(tables))

            # =========================
            # OCR FALLBACK
            # =========================
            if len(text) < OCR_FALLBACK_THRESHOLD:
                print("TEXT TOO SHORT → USING OCR")
                ocr_text = extract_text_with_ocr(file)

                if ocr_text and len(ocr_text) > len(text):
                    text = ocr_text
                    print("OCR USED, LENGTH:", len(text))
                else:
                    print("OCR NOT BETTER")

            if not text:
                print("WARNING: NO TEXT EXTRACTED")
                return "", []

            print("PDFPLUMBER SUCCESS")

            return text, tables

    except Exception as e:
        print("PDF ERROR:", e)

        # LAST RESORT OCR
        try:
            ocr_text = extract_text_with_ocr(file)
            if ocr_text:
                return ocr_text, []
        except Exception as e:
            print("OCR FAILED:", e)

        return "", []


# =========================
# OCR FUNCTION
# =========================
def extract_text_with_ocr(file):
    try:
        from pdf2image import convert_from_path
        import pytesseract

        print("OCR: Converting PDF → Images")

        images = convert_from_path(file)

        text = ""

        for i, img in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(img)

                if page_text:
                    text += page_text + "\n"
                    print(f"OCR Page {i+1}: {len(page_text)} chars")

            except Exception as e:
                print(f"OCR Page {i+1} error:", e)

        text = text.strip()
        print("OCR TOTAL LENGTH:", len(text))

        return text

    except Exception as e:
        print("OCR ERROR:", e)
        return ""


# =========================
# CLEAN TEXT
# =========================
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =========================
# CHUNK TEXT (ONLY ONE VERSION)
# =========================
def chunk_text(text: str, max_words: Optional[int] = None) -> list[str]:
    if not text:
        return []

    max_words = max_words or PDF_MAX_WORDS
    words = text.split()

    if len(words) <= max_words:
        return [text]

    chunks = []
    current = []

    for word in words:
        current.append(word)
        if len(current) >= PDF_CHUNK_SIZE:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


# =========================
# TABLE PROCESSING
# =========================
def process_tables(tables):
    processed = []

    for table in tables:
        if table:
            rows = []
            for row in table:
                clean_row = [str(cell).strip() if cell else "" for cell in row]
                rows.append(" | ".join(clean_row))
            processed.append("\n".join(rows))

    return processed


# =========================
# MAIN WRAPPER
# =========================
def get_processed_text(pdf_path: str):
    full_text, tables = extract_text_from_pdf(pdf_path)

    if not full_text:
        return "", [], []

    full_text = clean_text(full_text)
    chunks = chunk_text(full_text)
    table_data = process_tables(tables)

    return full_text, chunks, table_data