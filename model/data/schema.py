from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Set
import string

from model.data.metadata import Metadata

@dataclass
class DocumentSchema:
    """
    A class to represent and validate a document processing schema.
    """
    schema_name: str 
    fields: Dict[str, str] = field(default_factory=dict)
    defaults: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _extract_template_fields(template_string: str) -> Set[str]:
        formatter = string.Formatter()
        placeholders = {
            field_name
            for _, field_name, _, _ in formatter.parse(template_string)
            if field_name is not None
        }
        return placeholders

    def _validate_template(self, default_key: str, default_template: str):
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
        REQUIRED_DEFAULTS = {
            'identifier': '',
            'title': '',
            'date': '',
            'mediatype': 'text' 
        }
        
        merged_defaults = REQUIRED_DEFAULTS.copy()
        merged_defaults.update(self.defaults)
        self.defaults = merged_defaults

        print(f"Validating schema '{self.schema_name}'...")
        
        for default_key, default_template in self.defaults.items():
            self._validate_template(default_key, default_template)
            
        print(f"Schema '{self.schema_name}' validation successful.")

    def add_field(self, name: str, field_type: str = "Text"):
        """Adds a new field definition to the schema blueprint."""
        if name in self.fields:
            raise ValueError(f"Field '{name}' already exists.")
        self.fields[name] = field_type
        print(f"Field '{name}' of type '{field_type}' added successfully.")

    def edit_field_type(self, name: str, new_field_type: str):
        """Changes the expected data type of an existing field."""
        if name not in self.fields:
            raise ValueError(f"Field '{name}' does not exist")
        self.fields[name] = new_field_type
        print(f"Field '{name}' type set to {new_field_type}.")

    def add_template(self, key: str, template: str):
        if key != '' and key in self.defaults.keys():
            raise ValueError(f"Default for '{key}' already exists.")
        self.defaults[key] = template
        print(f"Default '{key}' added successfully.")

    # --- THE MAJOR CHANGE IS HERE ---
    def generate_metadata(self, user_inputs: Dict[str, Any]) -> Metadata:
        """
        Generates the final document metadata by applying the provided 
        user_inputs to the schema's default templates.
        """
        # Optional: Validate that the user provided all the fields we expect
        missing_inputs = set(self.fields.keys()) - set(user_inputs.keys())
        if missing_inputs:
             print(f"Warning: Generating metadata with missing inputs: {missing_inputs}")

        generated_metadata_dict = {}

        for default_key, default_template in self.defaults.items():
            try:
                # Interpolate using the passed-in user_inputs!
                generated_value = default_template.format(**user_inputs)
                generated_metadata_dict[default_key] = generated_value
            except KeyError as e:
                print(f"Runtime Format Error: Field {e} required for default '{default_key}' was not supplied.")
                continue
                
        REQUIRED_META_KEYS = ["identifier", "title", "date", "mediatype"]
        
        try:
            required_args = {k: generated_metadata_dict.pop(k) for k in REQUIRED_META_KEYS}
        except KeyError as e:
            raise ValueError(f"Schema generation failed: Missing required metadata field '{e}' in defaults.")

        return Metadata(
            identifier=required_args['identifier'],
            title=required_args['title'],
            date=required_args['date'],
            mediatype=required_args['mediatype'],
            optional_fields=generated_metadata_dict
        )

    @classmethod
    def from_dict(cls, data: Dict[str,Any]):
        required_keys = ['schema_name']
        if not all(key in data for key in required_keys):
             raise TypeError("Cannot load schema from dictionary. Missing required key: 'schema_name'.")
        try:
            return cls(
                schema_name=data['schema_name'],
                fields=data.get('fields', {}),
                defaults=data.get('defaults', {})
            )
        except ValueError as e:
            raise ValueError(f"Failed to load and validate schema from dictionary: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)