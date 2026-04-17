"""Unit tests for ExportService."""
import pytest
from services.export.ExportService import ExportService


SAMPLE_ENTRIES = [
    {
        "date": "2024-01-15",
        "user_name": "John Doe",
        "client_name": "Acme Corp",
        "project_name": "Website Redesign",
        "task_name": "Design",
        "description": "Homepage mockup",
        "duration_minutes": 120,
        "hours": 2.0,
        "is_billable": True,
        "hourly_rate": 150.0,
        "amount": 300.0,
    },
    {
        "date": "2024-01-16",
        "user_name": "Jane Smith",
        "client_name": "Acme Corp",
        "project_name": "Website Redesign",
        "task_name": "Development",
        "description": "Frontend implementation",
        "duration_minutes": 180,
        "hours": 3.0,
        "is_billable": True,
        "hourly_rate": 125.0,
        "amount": 375.0,
    },
    {
        "date": "2024-01-16",
        "user_name": "John Doe",
        "client_name": "Internal",
        "project_name": "Team Meeting",
        "task_name": "Standup",
        "description": "Daily standup",
        "duration_minutes": 30,
        "hours": 0.5,
        "is_billable": False,
        "hourly_rate": 0,
        "amount": 0,
    },
]

META = {
    "org_name": "Test Corp",
    "report_title": "Time Entry Report",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
}

INVOICE_DATA = {
    "invoiceNumber": "INV-202401150930",
    "date": "2024-01-31",
    "from": {"name": "Test Corp"},
    "to": {
        "name": "Acme Inc",
        "contactName": "Jane Manager",
        "contactEmail": "jane@acme.com",
        "address": "123 Business Ave",
    },
    "project": "Website Redesign",
    "period": {"start": "2024-01-01", "end": "2024-01-31"},
    "lineItems": [
        {
            "date": "2024-01-15",
            "user": "John Doe",
            "task": "Design",
            "description": "Homepage mockup",
            "hours": 2.0,
            "rate": 150.0,
            "amount": 300.0,
        },
        {
            "date": "2024-01-16",
            "user": "Jane Smith",
            "task": "Development",
            "description": "Frontend implementation",
            "hours": 3.0,
            "rate": 125.0,
            "amount": 375.0,
        },
    ],
    "totalHours": 5.0,
    "totalAmount": 675.0,
    "currency": "USD",
    "taxRate": 0,
}


class TestCSVExport:
    def test_csv_returns_bytes(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "csv", metadata=META)
        assert isinstance(result, bytes)

    def test_csv_contains_headers(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "csv", metadata=META)
        text = result.decode("utf-8")
        assert "Date" in text
        assert "User" in text
        assert "Hours" in text

    def test_csv_contains_data(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "csv", metadata=META)
        text = result.decode("utf-8")
        assert "John Doe" in text
        assert "Jane Smith" in text
        assert "Homepage mockup" in text

    def test_csv_contains_metadata(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "csv", metadata=META)
        text = result.decode("utf-8")
        assert "Test Corp" in text
        assert "Time Entry Report" in text
        assert "2024-01-01" in text

    def test_csv_contains_totals(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "csv", metadata=META)
        text = result.decode("utf-8")
        assert "TOTAL" in text

    def test_csv_without_metadata(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "csv")
        text = result.decode("utf-8")
        assert "Date" in text
        assert "John Doe" in text

    def test_csv_empty_entries(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries([], "csv", metadata=META)
        assert isinstance(result, bytes)
        text = result.decode("utf-8")
        assert "TOTAL" in text


class TestXLSXExport:
    def test_xlsx_returns_bytes(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "xlsx", metadata=META)
        assert isinstance(result, bytes)
        assert len(result) > 100  # Valid XLSX is non-trivial size

    def test_xlsx_is_valid_zip(self):
        """XLSX files are ZIP archives."""
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "xlsx", metadata=META)
        assert result[:2] == b"PK"  # ZIP magic bytes

    def test_xlsx_empty_entries(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries([], "xlsx", metadata=META)
        assert isinstance(result, bytes)
        assert len(result) > 100


class TestPDFExport:
    def test_pdf_returns_bytes(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "pdf", metadata=META)
        assert isinstance(result, bytes)

    def test_pdf_has_valid_header(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "pdf", metadata=META)
        assert result[:4] == b"%PDF"

    def test_pdf_without_metadata(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "pdf")
        assert result[:4] == b"%PDF"

    def test_pdf_empty_entries(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries([], "pdf", metadata=META)
        assert result[:4] == b"%PDF"


class TestInvoicePDF:
    def test_invoice_pdf_returns_valid_pdf(self):
        svc = ExportService()
        svc.initialize()
        result = svc.generate_invoice_pdf(INVOICE_DATA)
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"

    def test_invoice_pdf_with_tax(self):
        svc = ExportService()
        svc.initialize()
        data = {**INVOICE_DATA, "taxRate": 10}
        result = svc.generate_invoice_pdf(data)
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"

    def test_invoice_pdf_no_line_items(self):
        svc = ExportService()
        svc.initialize()
        data = {**INVOICE_DATA, "lineItems": []}
        result = svc.generate_invoice_pdf(data)
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"

    def test_invoice_pdf_minimal_data(self):
        svc = ExportService()
        svc.initialize()
        data = {
            "invoiceNumber": "INV-TEST",
            "date": "2024-01-31",
            "from": {},
            "to": {},
            "project": "",
            "period": {},
            "lineItems": [],
            "totalHours": 0,
            "totalAmount": 0,
        }
        result = svc.generate_invoice_pdf(data)
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"


class TestUnknownFormat:
    def test_unknown_format_falls_back_to_csv(self):
        svc = ExportService()
        svc.initialize()
        result = svc.export_entries(SAMPLE_ENTRIES, "unknown")
        text = result.decode("utf-8")
        assert "Date" in text
        assert "John Doe" in text
