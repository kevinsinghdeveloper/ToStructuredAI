"""File parsing service for CSV/XLSX user imports."""
import io
from typing import Optional
from abstractions.IServiceManagerBase import IServiceManagerBase


class FileParsingService(IServiceManagerBase):
    """Parses CSV and XLSX files for bulk user import."""

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)

    def initialize(self):
        pass

    def parse_user_file(self, file_content: bytes, filename: str) -> dict:
        """Parse a CSV or XLSX file and extract user records.

        Args:
            file_content: Raw file bytes.
            filename: Original filename (used to determine format).

        Returns:
            dict with keys: records (list of dicts), errors (list of str), total_rows (int)
        """
        import pandas as pd

        errors = []
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        try:
            if ext == "csv":
                df = pd.read_csv(io.BytesIO(file_content))
            elif ext in ("xlsx", "xls"):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                return {"records": [], "errors": [f"Unsupported file type: .{ext}"], "total_rows": 0}
        except Exception as e:
            return {"records": [], "errors": [f"Failed to parse file: {str(e)}"], "total_rows": 0}

        # Normalize column names to lowercase
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        if "email" not in df.columns:
            return {"records": [], "errors": ["File must contain an 'email' column"], "total_rows": 0}

        total_rows = len(df)
        records = []

        for idx, row in df.iterrows():
            row_num = idx + 2  # 1-indexed + header row
            email = str(row.get("email", "")).strip().lower()

            if not email or email == "nan":
                errors.append(f"Row {row_num}: Missing email")
                continue

            if "@" not in email:
                errors.append(f"Row {row_num}: Invalid email '{email}'")
                continue

            record = {"email": email}

            # Optional fields
            for field in ["first_name", "firstname", "first"]:
                if field in df.columns:
                    val = str(row.get(field, "")).strip()
                    if val and val != "nan":
                        record["first_name"] = val
                    break

            for field in ["last_name", "lastname", "last"]:
                if field in df.columns:
                    val = str(row.get(field, "")).strip()
                    if val and val != "nan":
                        record["last_name"] = val
                    break

            for field in ["company_name", "company", "business_name", "business"]:
                if field in df.columns:
                    val = str(row.get(field, "")).strip()
                    if val and val != "nan":
                        record["company_name"] = val
                    break

            for field in ["phone", "phone_number"]:
                if field in df.columns:
                    val = str(row.get(field, "")).strip()
                    if val and val != "nan":
                        record["phone"] = val
                    break

            # Check send_email column
            for field in ["send_email", "sendemail", "send_invite"]:
                if field in df.columns:
                    val = str(row.get(field, "")).strip().lower()
                    record["send_email"] = val in ("true", "1", "yes", "y")
                    break

            records.append(record)

        return {"records": records, "errors": errors, "total_rows": total_rows}
