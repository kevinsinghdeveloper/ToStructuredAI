"""Tests for SQLGenerationService — SQL validation, generation, and formatting."""
import json
import pytest
from unittest.mock import MagicMock

from services.ai.SQLGenerationService import SQLGenerationService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ai_service():
    """Returns a MagicMock AI service with a chat() method."""
    return MagicMock()


@pytest.fixture
def service(mock_ai_service):
    """SQLGenerationService wired up with the mock AI service."""
    return SQLGenerationService(ai_service=mock_ai_service)


@pytest.fixture
def service_no_ai():
    """SQLGenerationService with no AI service configured."""
    return SQLGenerationService(ai_service=None)


@pytest.fixture
def sample_schemas():
    """Minimal table schema list for testing."""
    return [
        {
            "table_name": "users",
            "row_count": 150,
            "columns": [
                {"name": "id", "type": "integer", "nullable": False, "primary_key": True},
                {"name": "name", "type": "varchar", "nullable": False, "description": "User full name"},
                {"name": "email", "type": "varchar", "nullable": False},
            ],
        },
        {
            "table_name": "orders",
            "row_count": 5000,
            "columns": [
                {"name": "id", "type": "integer", "nullable": False, "primary_key": True},
                {"name": "user_id", "type": "integer", "nullable": False},
                {"name": "total", "type": "numeric", "nullable": True},
            ],
        },
    ]


# ---------------------------------------------------------------------------
# _validate_sql — allowed queries
# ---------------------------------------------------------------------------

class TestValidateSqlAllowed:
    def test_validate_sql_select_allowed(self, service):
        """A plain SELECT query should pass validation."""
        service._validate_sql("SELECT id, name FROM users WHERE id = 1")

    def test_validate_sql_with_cte_allowed(self, service):
        """A WITH ... SELECT (CTE) query should pass validation."""
        sql = "WITH active AS (SELECT * FROM users WHERE active = true) SELECT * FROM active"
        service._validate_sql(sql)

    def test_validate_sql_keyword_in_string_literal_allowed(self, service):
        """Dangerous keywords inside string literals should NOT trigger rejection."""
        sql = "SELECT * FROM users WHERE name = 'DELETE'"
        service._validate_sql(sql)


# ---------------------------------------------------------------------------
# _validate_sql — blocked queries
# ---------------------------------------------------------------------------

class TestValidateSqlBlocked:
    def test_validate_sql_empty_raises(self, service):
        """Empty or whitespace-only SQL must raise ValueError."""
        with pytest.raises(ValueError, match="Empty SQL query"):
            service._validate_sql("")

        with pytest.raises(ValueError, match="Empty SQL query"):
            service._validate_sql("   ")

    def test_validate_sql_insert_blocked(self, service):
        """INSERT statements must be rejected (caught by startswith check)."""
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            service._validate_sql("INSERT INTO users (name) VALUES ('test')")

    def test_validate_sql_delete_blocked(self, service):
        """DELETE statements must be rejected (caught by startswith check)."""
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            service._validate_sql("DELETE FROM users WHERE id = 1")

    def test_validate_sql_drop_blocked(self, service):
        """DROP statements must be rejected (caught by startswith check)."""
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            service._validate_sql("DROP TABLE users")

    @pytest.mark.parametrize("keyword", [
        "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE",
    ])
    def test_validate_sql_all_dangerous_keywords(self, service, keyword):
        """Dangerous keywords embedded in a SELECT sub-query must still be caught."""
        # Wrap in a SELECT so the startswith guard passes, then the keyword scan fires.
        sql = f"SELECT * FROM users; {keyword} users"
        with pytest.raises(ValueError, match=keyword):
            service._validate_sql(sql)


# ---------------------------------------------------------------------------
# generate_sql
# ---------------------------------------------------------------------------

class TestGenerateSql:
    def test_generate_sql_success(self, service, mock_ai_service, sample_schemas):
        """Happy path: AI returns valid JSON with a safe SELECT query."""
        ai_response = json.dumps({
            "sql": "SELECT id, name FROM users LIMIT 100",
            "explanation": "Fetches all user ids and names",
        })
        mock_ai_service.chat.return_value = {"content": ai_response}

        result = service.generate_sql("Show me all users", sample_schemas)

        assert result["sql"] == "SELECT id, name FROM users LIMIT 100"
        assert "explanation" in result
        mock_ai_service.chat.assert_called_once()

    def test_generate_sql_json_parse_error(self, service, mock_ai_service, sample_schemas):
        """AI returns non-JSON text -- should raise ValueError."""
        mock_ai_service.chat.return_value = {"content": "This is not JSON at all"}

        with pytest.raises(ValueError, match="Failed to generate valid SQL"):
            service.generate_sql("Show me all users", sample_schemas)

    def test_generate_sql_unsafe_sql(self, service, mock_ai_service, sample_schemas):
        """AI returns valid JSON but with an INSERT statement -- should raise ValueError."""
        ai_response = json.dumps({
            "sql": "INSERT INTO users (name) VALUES ('hacker')",
            "explanation": "Inserts a user",
        })
        mock_ai_service.chat.return_value = {"content": ai_response}

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            service.generate_sql("Add a user", sample_schemas)

    def test_generate_sql_no_ai_service(self, service_no_ai, sample_schemas):
        """Calling generate_sql without an AI service must raise RuntimeError."""
        with pytest.raises(RuntimeError, match="AI service not configured"):
            service_no_ai.generate_sql("Show me users", sample_schemas)


# ---------------------------------------------------------------------------
# generate_answer_from_results
# ---------------------------------------------------------------------------

class TestGenerateAnswerFromResults:
    def test_generate_answer_from_results(self, service, mock_ai_service):
        """Should forward formatted results to the AI service and return the content."""
        mock_ai_service.chat.return_value = {"content": "There are 3 users in the system."}

        answer = service.generate_answer_from_results(
            question="How many users?",
            sql="SELECT COUNT(*) AS cnt FROM users",
            results=[{"cnt": 3}],
        )

        assert answer == "There are 3 users in the system."
        mock_ai_service.chat.assert_called_once()
        call_kwargs = mock_ai_service.chat.call_args
        assert "sql_answer" in (call_kwargs.kwargs.get("session_id") or call_kwargs[1].get("session_id", ""))


# ---------------------------------------------------------------------------
# _format_schemas
# ---------------------------------------------------------------------------

class TestFormatSchemas:
    def test_format_schemas(self, service, sample_schemas):
        """Formatted output should include table names, columns, types, and descriptions."""
        output = service._format_schemas(sample_schemas)

        assert "users" in output
        assert "orders" in output
        assert "~150 rows" in output
        assert "~5000 rows" in output
        assert "id (integer, NOT NULL) [PK]" in output
        assert "name (varchar, NOT NULL)" in output
        assert "-- User full name" in output
        assert "total (numeric, NULL)" in output


# ---------------------------------------------------------------------------
# _format_results
# ---------------------------------------------------------------------------

class TestFormatResults:
    def test_format_results_empty(self, service):
        """An empty result list should return the '(no results)' sentinel."""
        assert service._format_results([]) == "(no results)"

    def test_format_results_with_data(self, service):
        """Formatted table output should contain headers, separator, and row values."""
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        output = service._format_results(rows)

        assert "id | name" in output
        assert "--- | ---" in output
        assert "1 | Alice" in output
        assert "2 | Bob" in output
