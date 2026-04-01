from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Set
import string
import re

from model.data.metadata import Metadata

@dataclass
class DocumentSchema:
    """
    A class to represent and validate a document processing schema.
    """
    schema_name: str 
    filename_template: str = ''
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

    def generate_metadata(self, user_inputs: Dict[str, Any]) -> Metadata:
        """
        Generates the final document metadata by applying the provided 
        user_inputs to the schema's default templates.
        """
        clean_inputs = self._normalize_inputs(user_inputs)

        missing_inputs = set(self.fields.keys()) - set(clean_inputs.keys())
        if missing_inputs:
             print(f"Warning: Generating metadata with missing inputs: {missing_inputs}")

        generated_metadata_dict = {}

        for default_key, default_template in self.defaults.items():
            try:
                generated_value = default_template.format(**clean_inputs)
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

    def generate_metadata_from_name(self, filename: str) -> Metadata:
        if not self.filename_template:
            raise ValueError("No template defined.")
        regex_pattern = "^"
        formatter = string.Formatter()
        
        for literal, field_name, _, _ in formatter.parse(self.filename_template):
            if literal:
                # 1. Split the literal wherever there is a space, dash, or underscore
                parts = re.split(r'[\s\-_]+', literal)
                
                # 2. Safely escape the remaining text
                escaped_parts = [re.escape(p) for p in parts]
                
                # 3. Glue it back together using  flexible character class
                forgiving_literal = r'[\s\-_]+'.join(escaped_parts)
                
                regex_pattern += forgiving_literal
                
            if field_name:
                regex_pattern += f"(?P<{field_name}>.+?)"
                
        regex_pattern += "$" 

        match = re.match(regex_pattern, filename, re.IGNORECASE)
        if not match:
             raise ValueError(f"Could not parse '{filename}' using template '{self.filename_template}'.")

        extracted_inputs = match.groupdict()
        
        # Strip any accidental trailing whitespace the non-greedy capture might have grabbed
        clean_inputs = {k: v.strip(' -_') for k, v in extracted_inputs.items()}
        
        return self.generate_metadata(clean_inputs)

    def _normalize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Cleans and standardizes raw inputs before they are applied to templates."""
        
        MONTH_MAP = {
            'jan': '01', 'january': '01',
            'feb': '02', 'february': '02',
            'mar': '03', 'march': '03',
            'apr': '04', 'april': '04',
            'may': '05',
            'jun': '06', 'june': '06',
            'jul': '07', 'july': '07',
            'aug': '08', 'august': '08',
            'sep': '09', 'september': '09',
            'oct': '10', 'october': '10',
            'nov': '11', 'november': '11',
            'dec': '12', 'december': '12'
        }

        normalized = {}
        for key, value in inputs.items():
            # Target any field the user named 'month' (case-insensitive)
            if 'month' in key.lower() and isinstance(value, str):
                clean_val = value.lower().strip()
                
                if clean_val in MONTH_MAP:
                    # Convert text to the 2-digit number
                    normalized[key] = MONTH_MAP[clean_val]
                elif clean_val.isdigit():
                    # ensure number padding
                    normalized[key] = clean_val.zfill(2)
                else:
                    # Fallback if  unrecognizable
                    normalized[key] = value
            else:
                # Pass all other fields
                normalized[key] = value

        return normalized


    @classmethod
    def from_dict(cls, data: Dict[str,Any]):
        required_keys = ['schema_name']
        if not all(key in data for key in required_keys):
             raise TypeError("Cannot load schema from dictionary. Missing required key: 'schema_name'.")
        try:
            return cls(
                schema_name=data['schema_name'],
                filename_template=data.get('filename_template', ''),
                fields=data.get('fields', {}),
                defaults=data.get('defaults', {})
            )
        except ValueError as e:
            raise ValueError(f"Failed to load and validate schema from dictionary: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)