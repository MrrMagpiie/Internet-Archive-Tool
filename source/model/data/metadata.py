from dataclasses import dataclass, field
import json
from config import RESOURCES_PATH
from typing import Any, Dict, List, Optional, Type


with open(RESOURCES_PATH / 'IAMetadataKeys.json','r') as f:
    METADATA_SCHEMA = json.load(f)

# Mapping from schema type strings to actual Python types for validation
TYPE_MAPPING: Dict[str, Type] = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "list": list,
    "dict": dict
}

@dataclass
class Metadata:
    """
    A dataclass to hold and validate document metadata based on a predefined schema.
    """
    # Required Fields
    identifier: str
    title: str
    date: str
    mediatype: str

    # Optional Fields
    optional_fields: Dict[str, Any] = field(default_factory=dict) 

    def _validate_field(self, key: str, value: Any):
        """
        validates a single field against the schema constraints.
        Raises ValueError or TypeError on failure.
        """
        # Check if the field name is defined in the schema
        if key not in METADATA_SCHEMA:
            raise ValueError(
                f"Validation Error: Field '{key}' is not a valid metadata field "
                f"according to the schema."
            )
        
        schema_def = METADATA_SCHEMA[key]
        expected_type_str = schema_def.get("type")
        expected_type_py = TYPE_MAPPING.get(expected_type_str)

        if not expected_type_py:
            raise TypeError(f"Internal Schema Error: Unknown type '{expected_type_str}' for field '{key}'.")

        if expected_type_py in (list, dict) and not isinstance(value, expected_type_py):
             raise TypeError(
                f"Validation Error: Field '{key}' requires type '{expected_type_str}' "
                f"but received type '{type(value).__name__}' with value: {value}"
            )
        elif expected_type_py not in (list, dict) and not isinstance(value, expected_type_py):
             raise TypeError(
                f"Validation Error: Field '{key}' requires type '{expected_type_str}' "
                f"but received type '{type(value).__name__}' with value: {value}"
            )


        if "enum" in schema_def:
            allowed_values = schema_def["enum"]
            if value not in allowed_values:
                raise ValueError(
                    f"Validation Error: Field '{key}' must be one of {allowed_values}, "
                    f"but received '{value}'."
                )

    def __post_init__(self):
        """
        Performs comprehensive validation of all optional_fields provided at instantiation.
        """

        for key, value in self.optional_fields.items():
            self._validate_field(key, value)

    def add_optional_field(self, key: str, value: Any):
        """
        Adds or updates an optional field after initialization, with immediate validation.
        
        Args:
            key (str): The name of the optional field.
            value (Any): The value for the field.
        
        Raises:
            ValueError: If the field name is not valid or the value fails enum checks.
            TypeError: If the value type does not match the schema's expectation.
        """
        # Validate the field first
        self._validate_field(key, value)
        
        # If validation passes, add/update the field
        self.optional_fields[key] = value
        print(f"Successfully added/updated field '{key}' with value '{value}'.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the class instance back into a single dictionary.
        """
        data = {
            "identifier": self.identifier,
            "title": self.title,
            "date": self.date,
            "mediatype": self.mediatype,
        }
        data.update(self.optional_fields)
        return data

    def to_json(self) -> str:
        data = self.to_dict()
        return json.dumps(data)


    @classmethod
    def from_dict(cls, data: dict) -> 'Metadata':
        """
        Creates a Metadata object from a dictionary.
        """
        if 'optional_fields' not in data:
            metadata_dict = {
            'identifier': data.pop('identifier', None),
            'title': data.pop('title', None),
            'date': data.pop('date', None),
            'mediatype': data.pop('mediatype', None),
            'optional_fields': data
            }
        else:
            metadata_dict = data

        return cls(
            identifier=metadata_dict.get("identifier"),
            title=metadata_dict.get("title"),
            date=metadata_dict.get("date"),
            mediatype=metadata_dict.get("mediatype"),
            optional_fields=metadata_dict.get("optional_fields", {})
        )


    @classmethod
    def from_json(cls, json_str: str) -> 'Metadata':
        """
        Creates a Metadata object from a JSON string.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)