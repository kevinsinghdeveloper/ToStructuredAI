"""Pipeline type definitions — single source of truth for pipeline configurations."""

PIPELINE_TYPES = {
    "document_explore": {
        "id": "document_explore",
        "name": "Document Explore",
        "description": "Interactive Q&A chat with your documents. Ask questions and get AI-powered answers based on document content.",
        "icon": "chat",
        "category": "general",
        "default_fields": [
            {
                "id": "test_field",
                "name": "Test Text Box",
                "description": "This is a test text field - enter anything you want!",
                "field_type": "text",
                "required": False,
                "default_enabled": True,
            },
            {
                "id": "array_fields",
                "name": "Test Text Box",
                "description": "This is a test text field - enter anything you want!",
                "field_type": "code",
                "required": False,
                "default_enabled": True,
            },
        ],
        "prompt_template": """You are a helpful AI assistant. Answer the user's question based on the provided document context.

Context from documents:
{context}

Question: {question}

Please provide a clear, accurate answer based solely on the information in the context above. If the answer cannot be found in the context, say so.""",
        "output_schema": None,
        "supports_chat": True,
        "supports_extraction": False,
    },
    "data_analyzer": {
        "id": "data_analyzer",
        "name": "Data Analyzer",
        "description": "Ask natural language questions about your database tables. Generates SQL queries automatically and returns results with visualizations.",
        "icon": "analytics",
        "category": "data",
        "requires_embedding": False,
        "queryable_sources_only": True,
        "default_fields": [],
        "prompt_template": "",
        "output_schema": None,
        "supports_chat": True,
        "supports_extraction": False,
    },
}

FIELD_TYPES = {
    "text": {"name": "Text", "description": "Single line or multi-line text", "json_type": "string"},
    "code": {"name": "Code", "description": "Single line or multi-line code", "json_type": "string"},
    "number": {"name": "Number", "description": "Numeric value (integer or decimal)", "json_type": "number"},
    "date": {"name": "Date", "description": "Calendar date (YYYY-MM-DD)", "json_type": "string", "format": "date"},
    "datetime": {"name": "Date & Time", "description": "Date and time timestamp", "json_type": "string", "format": "date-time"},
    "boolean": {"name": "Boolean", "description": "True/False value", "json_type": "boolean"},
    "array": {"name": "Array/List", "description": "List of items", "json_type": "array"},
    "object": {"name": "Object", "description": "Nested object structure", "json_type": "object"},
}
