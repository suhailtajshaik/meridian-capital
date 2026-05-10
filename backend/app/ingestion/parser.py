"""Document parser — converts uploaded files into a normalized pandas DataFrame.

Supported formats:
    .csv   — pandas read_csv
    .xlsx  — pandas read_excel (via openpyxl)
    .pdf   — pdfplumber table extraction

All column names are normalized to snake_case.
Date columns are auto-detected and parsed.
"""
from __future__ import annotations

import io
import logging
import re
from typing import IO

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Column normalization
# ---------------------------------------------------------------------------


def _to_snake_case(name: str) -> str:
    """Convert a column header to snake_case."""
    name = str(name).strip()
    name = re.sub(r"[\s\-/]+", "_", name)
    name = re.sub(r"[^\w]", "", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename all columns to snake_case."""
    df.columns = [_to_snake_case(c) for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# Date detection
# ---------------------------------------------------------------------------

_DATE_PATTERNS = [
    r"\d{4}-\d{2}-\d{2}",       # ISO 8601
    r"\d{2}/\d{2}/\d{4}",       # US format
    r"\d{2}-\d{2}-\d{4}",       # EU format
    r"\d{4}/\d{2}/\d{2}",       # alt ISO
]

_DATE_COLUMN_HINTS = {"date", "statement_date", "payment_date", "due_date", "next_due"}


def _try_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Auto-detect date columns and parse them."""
    for col in df.columns:
        if col in _DATE_COLUMN_HINTS or "date" in col:
            try:
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            except Exception:
                pass
        elif df[col].dtype == object and len(df) > 0:
            sample = str(df[col].dropna().iloc[0]) if len(df[col].dropna()) > 0 else ""
            if any(re.match(p, sample) for p in _DATE_PATTERNS):
                try:
                    df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
                except Exception:
                    pass
    return df


# ---------------------------------------------------------------------------
# Format-specific parsers
# ---------------------------------------------------------------------------


def _parse_csv(content: bytes) -> pd.DataFrame:
    """Parse CSV bytes into a DataFrame."""
    try:
        df = pd.read_csv(io.BytesIO(content))
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(content), encoding="latin-1")
    return df


def _parse_xlsx(content: bytes) -> pd.DataFrame:
    """Parse XLSX bytes into a DataFrame."""
    return pd.read_excel(io.BytesIO(content), engine="openpyxl")


def _parse_pdf(content: bytes) -> pd.DataFrame:
    """Extract the first table from a PDF and return it as a DataFrame.

    Falls back to a single-column 'text' DataFrame containing all page text
    if no tables are found.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF parsing. Run: pip install pdfplumber")

    rows: list[list] = []
    headers: list[str] = []
    all_text: list[str] = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            all_text.append(page.extract_text() or "")
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                if not headers and table[0]:
                    headers = [str(h) for h in table[0]]
                    data_rows = table[1:]
                else:
                    data_rows = table
                for row in data_rows:
                    if any(cell is not None and str(cell).strip() for cell in row):
                        rows.append(row)

    if rows and headers:
        df = pd.DataFrame(rows, columns=headers)
        df = df.dropna(how="all")
        return df

    # Fallback: return extracted text
    logger.warning("No tables found in PDF — returning raw text.")
    text = "\n".join(all_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return pd.DataFrame({"text": lines})


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def parse_document(file_content: bytes, filename: str) -> pd.DataFrame:
    """Parse an uploaded file and return a normalized DataFrame.

    Args:
        file_content: Raw bytes of the uploaded file.
        filename: Original filename (used to determine format).

    Returns:
        Normalized pandas DataFrame with snake_case columns and parsed dates.

    Raises:
        ValueError: If the file format is not supported.
    """
    fname = filename.lower()

    if fname.endswith(".csv"):
        df = _parse_csv(file_content)
    elif fname.endswith((".xlsx", ".xls")):
        df = _parse_xlsx(file_content)
    elif fname.endswith(".pdf"):
        df = _parse_pdf(file_content)
    else:
        raise ValueError(
            f"Unsupported file format: {filename}. "
            f"Supported formats: .csv, .xlsx, .xls, .pdf"
        )

    # Normalize
    df = _normalize_columns(df)
    df = _try_parse_dates(df)

    logger.info(
        "Parsed %s: %d rows x %d columns. Columns: %s",
        filename,
        len(df),
        len(df.columns),
        list(df.columns),
    )

    return df
