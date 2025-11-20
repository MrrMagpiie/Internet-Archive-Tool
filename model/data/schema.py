from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Set
import string
import json

from model.metadata import Metadata



@dataclass
class DocumentSchema:
    """
    A class to represent and validate a document processing schema.

    This class ensures that all placeholders used in the 'defaults' template strings
    are present as keys in the 'fields' dictionary, both at initialization and 
    when adding new defaults.
    """
    schema_name: str 
    fields: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _extract_template_fields(template_string: str) -> Set[str]:
        """
        Extracts all unique placeholder field names from a template string.
        E.g., "{year}_{month}_{day}_Comet" -> {'year', 'month', 'day'}
        """
        formatter = string.Formatter()
        
        placeholders = {
            field_name
            for _, field_name, _, _ in formatter.parse(template_string)
            if field_name is not None
        }
        return placeholders

    def _validate_template(self, default_key: str, default_template: str):
        """
        Validates a single template against the current defined fields.
        Raises ValueError if any placeholder is missing from self.fields.
        """
        defined_fields = set(self.fields.keys())
        required_template_fields = self._extract_template_fields(default_template)
        
        missing_fields = required_template_fields - defined_fields
        
        if missing_fields:
            raise ValueError(
                f"Schema Validation Error for '{self.schema_name}': "
                f"The default value for metadata field '{default_key}' uses undefined fields. "
                f"Missing fields: {sorted(list(missing_fields))}"
            )

    def __post_init__(self):
        """
        Validates the schema by checking all initial default templates against defined fields.
        """

        REQUIRED_TEMPLATES = {
            'identifier': '',
            'title': '',
            'date': '',
            'mediatype': 'text' 
        }
        # Make sure instace has required defaults
        merged_defaults = REQUIRED_DEFAULTS.copy()
        merged_defaults.update(self.defaults)
        self.defaults = merged_defaults

        print(f"Validating schema '{self.schema_name}'...")
        
        # Validate all initial defaults
        for default_key, default_template in self.defaults.items():
            self._validate_template(default_key, default_template)
                
        print(f"Schema '{self.schema_name}' validation successful. All default templates are resolvable.")

    def add_field(self, name: str, value: Any = ""):
        """
        Adds a new input field to the schema.
        
        Args:
            name (str): The name of the new field (e.g., 'city').
            value (Any): An optional initial value or type hint for the field.
        """
        if name in self.fields:
            raise ValueError(
                f"Field '{name}' already exists."
                )
        
        self.fields[name] = value
        print(f"Field '{name}' added successfully.")

    def edit_field(self,name:str, value: Any):
        if name not in self.fields:
            raise ValueError(
                f"Field '{name}' does not exist"
            )
        self.fields[name] = value
        print(f"Field '{name}' set to {value}.")

    def add_template(self, key: str, template: str):
        """
        Adds a new default template, performing immediate validation against current fields.
        
        Args:
            key (str): The name of the metadata field to generate (e.g., 'collection').
            template (str): The template string using existing field names (e.g., 'Collection {year}').
        
        Raises:
            ValueError: If the Default key already exists in the schema.
        """
        if key in self.defaults.keys():
            raise ValueError(
                f"Default for '{key}' already exists."
                )
                
        self.defaults[key] = template
        print(f"Default '{key}' added successfully, validated against current fields.")

    def generate_metadata(self) -> DocumentMetadata:
        """
        Generates the final document metadata by applying current field values to the defaults templates.

        Returns:
            DocumentMetadata: The fully generated and validated metadata object.
        """

        generated_metadata_dict = {}

        for default_key, default_template in self.defaults.items():
            try:
                # Use str.format(**user_inputs) to perform the interpolation
                generated_value = default_template.format(**self.fields)
                generated_metadata_dict[default_key] = generated_value
            except KeyError as e:
                print(f"Runtime Format Error: Field {e} required for default '{default_key}' was not supplied.")
                continue
                
        # Define the four required keys for the DocumentMetadata constructor
        REQUIRED_META_KEYS = ["identifier", "title", "date", "mediatype"]
        
        # Extract required fields for the DocumentMetadata constructor using .pop()
        try:
            required_args = {k: generated_metadata_dict.pop(k) for k in REQUIRED_META_KEYS}
        except KeyError as e:
            raise ValueError(f"Schema generation failed: Missing required metadata field '{e}' in defaults.")

        # The remaining items in the dict are the optional fields
        optional_args = generated_metadata_dict

        # Instantiate and return the fully validated DocumentMetadata object
        return DocumentMetadata(
            identifier=required_args['identifier'],
            title=required_args['title'],
            date=required_args['date'],
            mediatype=required_args['mediatype'],
            optional_fields=optional_args
        )

    @classmethod
    def from_dict(cls, data: Dict[str,Any]):
        required_keys = ['schema_name']
        if not all(key in data for key in required_keys):
             raise TypeError(
                f"Cannot load schema from dictionary. Missing required key: 'schema_name'."
            )
        try:
            return cls(
                schema_name=data['schema_name'],
                # Use .get with empty dict defaults to avoid key errors if fields/defaults are optional in the source data
                fields=data.get('fields', {}),
                defaults=data.get('defaults', {})
            )
        except ValueError as e:
            # Re-raise validation errors encountered during __post_init__
            raise ValueError(f"Failed to load and validate schema from dictionary: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)