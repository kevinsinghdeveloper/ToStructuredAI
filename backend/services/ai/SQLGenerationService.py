"""SQL Generation Service — LLM-powered natural language to SQL."""
import json
import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SQL_GENERATION_SYSTEM_PROMPT = """You are a SQL query generator. Given table schemas and a natural language question, generate a valid PostgreSQL query.

RULES:
- Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
- Always use double quotes around table and column names that contain special characters
- Include a LIMIT clause if the query could return many rows (default LIMIT 100)
- Use appropriate aggregations (COUNT, SUM, AVG, etc.) when the question implies them
- For date comparisons, use PostgreSQL date functions
- Return results that directly answer the question

Available tables and their schemas:
{table_schemas}

Respond ONLY with a valid JSON object:
{{
    "sql": "SELECT ...",
    "explanation": "Brief explanation of what this query does"
}}"""

SQL_ANSWER_PROMPT = """Based on the following SQL query results, provide a clear, concise answer to the user's question.
If the results contain numerical data that could be visualized, suggest an appropriate chart type.

Question: {question}
SQL Query: {sql}
Results ({row_count} rows):
{results}

Provide a natural language answer. If appropriate, include a chart visualization using this format:
```chart
{{
    "type": "bar|line|pie|scatter",
    "title": "Chart Title",
    "data": {{
        "labels": [...],
        "datasets": [{{
            "label": "Series Name",
            "data": [...]
        }}]
    }}
}}
```"""


class SQLGenerationService:
    """Generates SQL queries from natural language questions using LLM."""

    def __init__(self, ai_service=None):
        self._ai_service = ai_service

    def generate_sql(
        self,
        question: str,
        table_schemas: List[Dict[str, Any]],
        model_id: str = None,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate a SQL query from a natural language question.

        Returns:
            {"sql": "SELECT ...", "explanation": "..."}

        Raises:
            ValueError: If generated SQL is invalid or unsafe.
        """
        if not self._ai_service:
            raise RuntimeError("AI service not configured for SQL generation")

        schemas_text = self._format_schemas(table_schemas)
        system_prompt = SQL_GENERATION_SYSTEM_PROMPT.format(table_schemas=schemas_text)

        # Build the prompt with conversation context
        prompt_parts = []
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("")

        prompt_parts.append(question)
        full_message = "\n".join(prompt_parts)

        try:
            result = self._ai_service.chat(
                message=full_message,
                session_id="sql_generation",
                user_id="system",
                model_id=model_id,
            )
            response_text = result.get("content", "")

            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            parsed = json.loads(response_text.strip())
            sql = parsed.get("sql", "")

            self._validate_sql(sql)

            logger.info("Generated SQL: %s", sql)
            return parsed

        except json.JSONDecodeError as e:
            logger.error("Failed to parse SQL generation response: %s", str(e))
            raise ValueError(f"Failed to generate valid SQL: {str(e)}")

    def generate_answer_from_results(
        self,
        question: str,
        sql: str,
        results: List[Dict[str, Any]],
        model_id: str = None,
    ) -> str:
        """Generate a natural language answer from SQL query results."""
        if not self._ai_service:
            raise RuntimeError("AI service not configured")

        results_text = self._format_results(results)

        prompt = SQL_ANSWER_PROMPT.format(
            question=question,
            sql=sql,
            row_count=len(results),
            results=results_text,
        )

        result = self._ai_service.chat(
            message=prompt,
            session_id="sql_answer",
            user_id="system",
            model_id=model_id,
        )
        return result.get("content", "")

    def _format_schemas(self, table_schemas: List[Dict[str, Any]]) -> str:
        lines = []
        for schema in table_schemas:
            table_name = schema.get("table_name", "unknown")
            columns = schema.get("columns", [])
            row_count = schema.get("row_count", "unknown")

            lines.append(f"\nTable: {table_name} (~{row_count} rows)")
            lines.append("Columns:")
            for col in columns:
                name = col.get("name", "")
                col_type = col.get("type", "unknown")
                desc = col.get("description", "")
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                pk = " [PK]" if col.get("primary_key") else ""
                line = f"  - {name} ({col_type}, {nullable}){pk}"
                if desc:
                    line += f" -- {desc}"
                lines.append(line)

        return "\n".join(lines)

    def _format_results(self, results: List[Dict[str, Any]], max_rows: int = 50) -> str:
        if not results:
            return "(no results)"

        display_results = results[:max_rows]
        lines = []

        headers = list(display_results[0].keys())
        lines.append(" | ".join(headers))
        lines.append(" | ".join(["---"] * len(headers)))

        for row in display_results:
            values = [str(row.get(h, "NULL")) for h in headers]
            lines.append(" | ".join(values))

        if len(results) > max_rows:
            lines.append(f"... and {len(results) - max_rows} more rows")

        return "\n".join(lines)

    def _validate_sql(self, sql: str) -> None:
        """Validate that the SQL is a safe SELECT query."""
        if not sql or not sql.strip():
            raise ValueError("Empty SQL query")

        upper = sql.strip().upper()

        if not upper.startswith("SELECT") and not upper.startswith("WITH"):
            raise ValueError("Only SELECT queries are allowed")

        dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
        sql_without_strings = re.sub(r"'[^']*'", "", sql)
        for keyword in dangerous:
            pattern = rf'\b{keyword}\b'
            if re.search(pattern, sql_without_strings, re.IGNORECASE):
                raise ValueError(f"Unsafe SQL: contains '{keyword}' keyword")
