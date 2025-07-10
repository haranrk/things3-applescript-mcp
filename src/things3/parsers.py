"""
Things 3 specific parsers for AppleScript output.

This module contains parsers that understand Things 3 specific
data formats and object references.
"""

import re
from typing import Any, Dict, Optional

from things3_mcp.applescript.parsers import StructuredRecordParser


class Things3RecordParser(StructuredRecordParser):
    """
    Enhanced structured record parser for Things 3 specific formats.

    This parser extends the base StructuredRecordParser to handle
    Things 3 specific object references and data types.
    """

    def _parse_value(self, value_str: str) -> Any:
        """
        Parse a structured value string with Things 3 specific handling.

        This method extends the base parser to handle Things 3 object
        references like 'project id "ABC123" of application "Things3"'.
        """
        value_str = value_str.strip()

        # Handle Things 3 object references
        if self._is_things3_reference(value_str):
            return self._parse_things3_reference(value_str)

        # Fall back to base parser
        return super()._parse_value(value_str)

    def _is_things3_reference(self, value_str: str) -> bool:
        """Check if a value is a Things 3 object reference."""
        reference_patterns = [
            r'^project id ".*" of application "Things3"$',
            r'^area id ".*" of application "Things3"$',
            r'^to do id ".*" of application "Things3"$',
            r'^tag ".*" of application "Things3"$',
            r'^list ".*" of application "Things3"$',
        ]

        for pattern in reference_patterns:
            if re.match(pattern, value_str):
                return True

        return False

    def _parse_things3_reference(self, value_str: str) -> str:
        """
        Parse Things 3 object reference to a simplified format.

        Converts:
        - 'project id "ABC123" of application "Things3"' -> 'project id ABC123'
        - 'area id "XYZ789" of application "Things3"' -> 'area id XYZ789'
        - 'tag "Work" of application "Things3"' -> 'tag Work'
        """
        # Remove the 'of application "Things3"' part
        simplified = value_str.split(" of application ")[0]

        # Extract the ID or name from quotes
        match = re.match(r'^(\w+)(?:\s+id)?\s+"([^"]+)"$', simplified)
        if match:
            obj_type = match.group(1)
            identifier = match.group(2)

            # Check if it's an ID reference
            if " id " in value_str:
                return f"{obj_type} id {identifier}"
            else:
                return f"{obj_type} {identifier}"

        return simplified


class Things3DateParser:
    """
    Parser for Things 3 specific date formats and expressions.

    Things 3 uses various date representations that need special handling.
    """

    def parse_date_expression(self, expr: str) -> Optional[str]:
        """
        Parse Things 3 date expressions.

        Handles:
        - Relative dates: "today", "tomorrow", "evening"
        - Date strings: "Friday, June 20, 2025 at 20:24:30"
        - Missing dates: "missing value"
        """
        if not expr or expr == "missing value":
            return None

        # Relative date keywords
        relative_dates = {
            "today": "today",
            "tomorrow": "tomorrow",
            "evening": "evening",
            "anytime": "anytime",
            "someday": "someday",
        }

        if expr.lower() in relative_dates:
            return relative_dates[expr.lower()]

        # Standard date format
        if re.match(r"^\w+, \w+ \d+, \d+ at \d+:\d+:\d+$", expr):
            return expr

        return expr


class Things3StatusParser:
    """Parser for Things 3 status values."""

    STATUS_MAP = {
        "open": "open",
        "completed": "completed",
        "canceled": "canceled",
        "cancelled": "canceled",  # Handle alternate spelling
    }

    def parse_status(self, status_str: str) -> Optional[str]:
        """Parse Things 3 status string to normalized value."""
        if not status_str:
            return None

        return self.STATUS_MAP.get(status_str.lower())


class Things3ClassParser:
    """Parser for Things 3 class/type values."""

    CLASS_MAP = {
        "to do": "todo",
        "selected to do": "selected_todo",
        "project": "project",
        "area": "area",
        "tag": "tag",
        "checklist item": "checklist_item",
    }

    def parse_class(self, class_str: str) -> Optional[str]:
        """Parse Things 3 class string to normalized value."""
        if not class_str:
            return None

        return self.CLASS_MAP.get(class_str.lower())


class Things3PropertyNormalizer:
    """
    Normalizes Things 3 property values to consistent Python types.

    This handles the conversion of Things 3 specific values to
    standardized Python representations.
    """

    def __init__(self):
        self.date_parser = Things3DateParser()
        self.status_parser = Things3StatusParser()
        self.class_parser = Things3ClassParser()

    def normalize_properties(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a dictionary of Things 3 properties.

        Args:
            props: Raw properties from AppleScript

        Returns:
            Normalized properties dictionary
        """
        normalized = {}

        for key, value in props.items():
            # Handle specific property types
            if key.endswith("date") or key in ["deadline", "when"]:
                normalized[key] = self.date_parser.parse_date_expression(value)
            elif key == "status":
                normalized[key] = self.status_parser.parse_status(value)
            elif key == "class":
                normalized[key] = self.class_parser.parse_class(value)
            elif key == "tag names" and isinstance(value, str):
                # Convert comma-separated tags to list
                normalized[key] = [
                    tag.strip() for tag in value.split(",") if tag.strip()
                ]
            else:
                normalized[key] = value

        return normalized
