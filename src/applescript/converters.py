"""
Type conversion system for Python to AppleScript and vice versa.

This module provides converters for translating between Python types
and their AppleScript representations.
"""

import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


class TypeConverter(ABC):
    """Abstract base class for type converters."""

    @abstractmethod
    def to_applescript(self, value: Any) -> str:
        """Convert Python value to AppleScript representation."""
        pass

    @abstractmethod
    def from_applescript(self, value: str) -> Any:
        """Convert AppleScript value to Python representation."""
        pass


class PythonToAppleScriptConverter:
    """
    Converts Python types to their AppleScript string representation.

    This converter handles basic Python types and converts them to
    strings that can be used in AppleScript commands.
    """

    def convert(self, value: Any) -> str:
        """
        Convert a Python value to its AppleScript representation.

        Args:
            value: Python value to convert

        Returns:
            AppleScript string representation
        """
        if value is None:
            return "missing value"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Check for special AppleScript expressions that should not be quoted
            if self._is_applescript_expression(value):
                return value
            return self._quote_string(value)
        elif isinstance(value, (date, datetime)):
            return self._format_date(value)
        elif isinstance(value, list):
            return self._convert_list(value)
        elif isinstance(value, dict):
            return self._convert_dict(value)
        else:
            # Fallback: convert to string and quote
            return self._quote_string(str(value))

    def _is_applescript_expression(self, s: str) -> bool:
        """
        Check if a string is an AppleScript expression that should not be quoted.
        
        This includes:
        - Date expressions: (current date), (current date) + (N * days)
        - Object references: area id "ABC", project id "XYZ"
        - Special values: missing value, current date
        """
        s = s.strip()
        
        # Date expressions
        if s == "current date" or s == "(current date)":
            return True
        if s.startswith("(current date)") and ("+" in s or "-" in s) and "days" in s:
            return True
            
        # Object references
        reference_prefixes = [
            "area id ", "project id ", "tag id ", "to do id ",
            "area ", "project ", "tag ", "list "
        ]
        for prefix in reference_prefixes:
            if s.startswith(prefix):
                return True
                
        # Special AppleScript values
        if s in ["missing value", "true", "false"]:
            return True
            
        return False

    def _quote_string(self, s: str) -> str:
        """Quote a string for AppleScript."""
        # Escape internal quotes
        escaped = s.replace('"', '\\"')
        return f'"{escaped}"'

    def _format_date(self, d: Union[date, datetime]) -> str:
        """
        Format a date for AppleScript.

        Returns a date expression like 'current date' or
        '(current date) + (N * days)' for relative dates.
        """
        if isinstance(d, date) and not isinstance(d, datetime):
            d = datetime.combine(d, datetime.min.time())

        # Calculate days difference from today
        today = datetime.now().date()
        target_date = d.date()
        days_diff = (target_date - today).days

        # Generate AppleScript date expression
        if days_diff == 0:
            return "current date"
        elif days_diff == 1:
            return "(current date) + (1 * days)"
        elif days_diff == -1:
            return "(current date) - (1 * days)"
        elif days_diff > 0:
            return f"(current date) + ({days_diff} * days)"
        else:
            return f"(current date) - ({abs(days_diff)} * days)"

    def _convert_list(self, lst: List[Any]) -> str:
        """Convert a Python list to AppleScript list format."""
        if not lst:
            return "{}"

        items = [self.convert(item) for item in lst]
        return "{" + ", ".join(items) + "}"

    def _convert_dict(self, d: Dict[str, Any]) -> str:
        """Convert a Python dict to AppleScript record format."""
        if not d:
            return "{}"

        items = []
        for key, value in d.items():
            # Keys in AppleScript records are not quoted
            items.append(f"{key}:{self.convert(value)}")

        return "{" + ", ".join(items) + "}"


class AppleScriptReferenceConverter:
    """
    Handles special AppleScript object references.

    This converter recognizes and properly formats references to
    AppleScript objects like 'project id "ABC123"' or 'area "Work"'.
    """

    REFERENCE_PATTERNS = {
        "project": r"project (?:id )?",
        "area": r"area (?:id )?",
        "tag": r"tag ",
        "todo": r"to do (?:id )?",
        "list": r"list ",
    }

    def is_reference(self, value: str) -> bool:
        """Check if a value is an AppleScript object reference."""
        if not isinstance(value, str):
            return False

        for pattern in self.REFERENCE_PATTERNS.values():
            if value.startswith(pattern.replace("(?:id )?", "id ")) or value.startswith(
                pattern.replace("(?:id )?", "")
            ):
                return True

        return False

    def format_reference(
        self, ref_type: str, identifier: str, by_id: bool = True
    ) -> str:
        """
        Format an AppleScript object reference.

        Args:
            ref_type: Type of reference (project, area, tag, etc.)
            identifier: The identifier (ID or name)
            by_id: Whether to reference by ID (True) or name (False)

        Returns:
            Formatted reference string
        """
        if by_id:
            return f'{ref_type} id "{identifier}"'
        else:
            return f'{ref_type} "{identifier}"'

    def parse_reference(self, reference: str) -> tuple[str, str, bool]:
        """
        Parse an AppleScript object reference.

        Args:
            reference: Reference string like 'project id "ABC123"'

        Returns:
            Tuple of (type, identifier, is_by_id)
        """
        for ref_type, pattern in self.REFERENCE_PATTERNS.items():
            if reference.startswith(f"{ref_type} id "):
                # Extract ID from quotes
                id_part = reference[len(f"{ref_type} id ") :]
                if id_part.startswith('"') and id_part.endswith('"'):
                    return ref_type, id_part[1:-1], True
            elif reference.startswith(f"{ref_type} "):
                # Extract name from quotes
                name_part = reference[len(f"{ref_type} ") :]
                if name_part.startswith('"') and name_part.endswith('"'):
                    return ref_type, name_part[1:-1], False

        return None, None, None


class PropertyConverter:
    """
    Converts between Python property names and AppleScript property names.

    Handles the mapping between Pythonic names (snake_case) and
    AppleScript names (usually space-separated).
    """

    # Common property mappings
    PROPERTY_MAP = {
        # Python -> AppleScript
        "due_date": "due date",
        "creation_date": "creation date",
        "modification_date": "modification date",
        "completion_date": "completion date",
        "cancellation_date": "cancellation date",
        "activation_date": "activation date",
        "start_date": "start date",
        "tag_names": "tag names",
        "class_": "class",
        # Reverse mappings (AppleScript -> Python)
        "due date": "due_date",
        "creation date": "creation_date",
        "modification date": "modification_date",
        "completion date": "completion_date",
        "cancellation date": "cancellation_date",
        "activation date": "activation_date",
        "start date": "start_date",
        "tag names": "tag_names",
        "class": "class_",
    }

    def to_applescript_name(self, python_name: str) -> str:
        """Convert Python property name to AppleScript name."""
        return self.PROPERTY_MAP.get(python_name, python_name)

    def to_python_name(self, applescript_name: str) -> str:
        """Convert AppleScript property name to Python name."""
        return self.PROPERTY_MAP.get(applescript_name, applescript_name)

    def convert_dict_keys(
        self, data: Dict[str, Any], to_applescript: bool = True
    ) -> Dict[str, Any]:
        """
        Convert all keys in a dictionary between Python and AppleScript naming.

        Args:
            data: Dictionary with property names as keys
            to_applescript: If True, convert Python->AppleScript; if False, convert AppleScript->Python

        Returns:
            Dictionary with converted keys
        """
        result = {}
        for key, value in data.items():
            if to_applescript:
                new_key = self.to_applescript_name(key)
            else:
                new_key = self.to_python_name(key)
            result[new_key] = value

        return result
