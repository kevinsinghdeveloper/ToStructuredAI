"""Pipeline type service — provides pipeline type configurations and utilities."""
from typing import Dict, List, Optional
from services.pipeline_types.pipeline_type_definitions import PIPELINE_TYPES, FIELD_TYPES


class PipelineTypeService:

    def __init__(self):
        self.pipeline_types = PIPELINE_TYPES
        self.field_types = FIELD_TYPES

    def get_all_pipeline_types(self) -> List[Dict]:
        return [
            {
                "id": t["id"], "name": t["name"], "description": t["description"],
                "icon": t["icon"], "category": t["category"],
                "supports_chat": t.get("supports_chat", False),
                "supports_extraction": t.get("supports_extraction", False),
            }
            for t in self.pipeline_types.values()
        ]

    def get_pipeline_type(self, type_id: str) -> Optional[Dict]:
        return self.pipeline_types.get(type_id)

    def get_field_types(self) -> Dict:
        return self.field_types

    def build_output_schema(self, type_id: str) -> Optional[Dict]:
        pt = self.get_pipeline_type(type_id)
        return pt.get("output_schema") if pt else None

    def build_prompt_template(self, type_id: str) -> str:
        pt = self.get_pipeline_type(type_id)
        return pt.get("prompt_template", "") if pt else ""

    def validate_pipeline_type(self, type_id: str) -> bool:
        return type_id in self.pipeline_types
