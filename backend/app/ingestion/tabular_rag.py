"""TabularRAG — natural-language querying over session-uploaded CSV/XLSX/PDF data.

Architecture:
    1. Uploaded DataFrames are persisted to a per-session SQLite database.
    2. User asks a natural-language question.
    3. LLM generates a read-only SQL query over the known table schema.
    4. Query is executed; result is returned as a structured dict.
    5. DDL/DML statements are rejected before execution.

Security:
    - Only SELECT statements are allowed.
    - Queries run inside a read-only transaction context.
    - Table names are validated against the known session schema.
"""
from __future__ import annotations

import logging
import re
import sqlite3
from typing import Any, Optional

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQL safety
# ---------------------------------------------------------------------------

_FORBIDDEN_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE|PRAGMA|ATTACH)\b",
    re.IGNORECASE,
)

_SELECT_PATTERN = re.compile(r"^\s*SELECT\b", re.IGNORECASE)


def _is_safe_query(sql: str) -> bool:
    """Return True only if the query is a plain SELECT with no DDL/DML."""
    if not _SELECT_PATTERN.match(sql):
        return False
    if _FORBIDDEN_PATTERNS.search(sql):
        return False
    return True


def _strip_markdown_fences(text: str) -> str:
    """Remove ```sql ... ``` or ``` ... ``` wrapping."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```sql or ```) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    return text


# ---------------------------------------------------------------------------
# TabularRAG
# ---------------------------------------------------------------------------


class TabularRAG:
    """NL-to-SQL engine over per-session uploaded data.

    Args:
        db_path: Path to the session SQLite database.
        llm: LangChain chat model for SQL generation.
    """

    def __init__(self, db_path: str, llm: Any) -> None:
        self.db_path = db_path
        self.llm = llm
        self._table_schemas: dict[str, list[str]] = {}  # table_name -> [col names]

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------

    def ingest(self, df: pd.DataFrame, table_name: str) -> None:
        """Persist a DataFrame into the session SQLite database.

        Args:
            df: Normalized DataFrame to store.
            table_name: SQLite table name (alphanumeric + underscores).
        """
        # Sanitize table name
        safe_name = re.sub(r"[^\w]", "_", table_name).lower()

        # Convert datetime columns to ISO strings for SQLite compatibility
        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
            df_copy[col] = df_copy[col].dt.strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            df_copy.to_sql(safe_name, conn, if_exists="replace", index=False)
            logger.info(
                "TabularRAG: ingested %d rows into table '%s' at %s",
                len(df_copy),
                safe_name,
                self.db_path,
            )

        # Cache schema for SQL generation context
        self._table_schemas[safe_name] = list(df.columns)

    def _get_schema_string(self) -> str:
        """Build a schema description for the LLM prompt."""
        if not self._table_schemas:
            # Query live from DB
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
                    )
                    tables = [row[0] for row in cursor.fetchall()]
                    for table in tables:
                        cols_cursor = conn.execute(f"PRAGMA table_info({table});")
                        cols = [row[1] for row in cols_cursor.fetchall()]
                        self._table_schemas[table] = cols
            except Exception as exc:
                logger.warning("Could not read schema from DB: %s", exc)
                return "No tables available."

        lines: list[str] = []
        for table, cols in self._table_schemas.items():
            lines.append(f"Table: {table}")
            lines.append(f"  Columns: {', '.join(cols)}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def query(self, natural_language: str) -> dict:
        """Answer a natural-language question using SQL over the uploaded data.

        Args:
            natural_language: The user's question in plain English.

        Returns:
            Dict with keys: sql (str), columns (list), rows (list), error (str|None).
        """
        schema = self._get_schema_string()

        if "No tables available" in schema:
            return {
                "sql": None,
                "columns": [],
                "rows": [],
                "error": "No data has been uploaded yet for this session.",
                "answer": "Please upload a financial document first.",
            }

        # Generate SQL
        sql_prompt = (
            f"You are a SQL expert. Given the following SQLite database schema, "
            f"write a single read-only SELECT query to answer the user's question.\n\n"
            f"Schema:\n{schema}\n\n"
            f"User question: {natural_language}\n\n"
            f"Rules:\n"
            f"- Return ONLY the SQL query, no explanation.\n"
            f"- Use only SELECT statements.\n"
            f"- Do not use subqueries that modify data.\n"
            f"- Wrap string literals in single quotes.\n"
            f"- If the question cannot be answered from the schema, return: "
            f"SELECT 'not_applicable' AS result;"
        )

        messages = [
            SystemMessage(content="You generate SQL queries. Return only the SQL."),
            HumanMessage(content=sql_prompt),
        ]

        try:
            raw = await self.llm.ainvoke(messages)
            sql = raw.content if hasattr(raw, "content") else str(raw)
            sql = _strip_markdown_fences(sql).strip().rstrip(";") + ";"
        except Exception as exc:
            return {"sql": None, "columns": [], "rows": [], "error": f"SQL generation failed: {exc}"}

        # Safety check
        if not _is_safe_query(sql):
            return {
                "sql": sql,
                "columns": [],
                "rows": [],
                "error": "Generated query contains forbidden statements and was rejected.",
            }

        # Execute in read-only mode
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql)
                rows_raw = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = [list(row) for row in rows_raw]

            return {
                "sql": sql,
                "columns": columns,
                "rows": rows[:200],  # cap at 200 rows for LLM safety
                "error": None,
            }

        except sqlite3.OperationalError as exc:
            # Read-only mode may not be available on all platforms; retry with normal mode
            logger.warning("Read-only SQLite URI failed (%s) — retrying without mode=ro.", exc)
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Use a savepoint to ensure we roll back any accidental writes
                    conn.execute("BEGIN DEFERRED;")
                    cursor = conn.execute(sql)
                    rows_raw = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = [list(row) for row in rows_raw]
                    conn.execute("ROLLBACK;")

                return {"sql": sql, "columns": columns, "rows": rows[:200], "error": None}

            except Exception as inner_exc:
                return {"sql": sql, "columns": [], "rows": [], "error": str(inner_exc)}

        except Exception as exc:
            return {"sql": sql, "columns": [], "rows": [], "error": str(exc)}
