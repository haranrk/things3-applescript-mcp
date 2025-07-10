"""
Parser strategies for different AppleScript output formats.

This module implements the Strategy pattern for parsing various
AppleScript output formats into Python objects.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from things3_mcp.applescript.errors import AppleScriptParsingError

logger = logging.getLogger(__name__)


class ParserStrategy(ABC):
    """Abstract base class for AppleScript output parsers."""

    @abstractmethod
    def can_parse(self, raw_output: str) -> bool:
        """
        Check if this parser can handle the given output.

        Args:
            raw_output: Raw AppleScript output string

        Returns:
            True if this parser can handle the output
        """
        pass

    @abstractmethod
    def parse(self, raw_output: str) -> Any:
        """
        Parse the raw AppleScript output.

        Args:
            raw_output: Raw AppleScript output string

        Returns:
            Parsed Python object

        Raises:
            AppleScriptParsingError: If parsing fails
        """
        pass


class JSONParser(ParserStrategy):
    """Parser for JSON-formatted AppleScript output."""

    def can_parse(self, raw_output: str) -> bool:
        """Check if output looks like JSON."""
        if not raw_output:
            return False

        stripped = raw_output.strip()

        # JSON objects or arrays
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            # But exclude AppleScript record format (unquoted keys with colons)
            if ":" in stripped and '"' not in stripped.split(":")[0]:
                return False  # This looks like AppleScript record format
            return True

        return False

    def parse(self, raw_output: str) -> Union[Dict, List]:
        """Parse JSON output."""
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError as e:
            raise AppleScriptParsingError(raw_output, "JSONParser", e)


class PrimitiveParser(ParserStrategy):
    """Parser for primitive values (bool, int, float, string)."""

    def can_parse(self, raw_output: str) -> bool:
        """Primitive parser can handle any non-structured output."""
        return True  # This is the fallback parser

    def parse(self, raw_output: str) -> Union[bool, int, float, str]:
        """Parse primitive values."""
        if not raw_output:
            return None

        value = raw_output.strip()

        # If it's just whitespace, return the original
        if not value and raw_output:
            return raw_output

        # Boolean values
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False

        # Numeric values
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Default to string
        return value


class StructuredRecordParser(ParserStrategy):
    """Parser for AppleScript structured record format (from -s s flag)."""

    def can_parse(self, raw_output: str) -> bool:
        """Check if output is in structured record format."""
        if not raw_output:
            return False

        stripped = raw_output.strip()
        # Single record: {key:value, ...}
        # Multiple records: {{key:value, ...}, {key:value, ...}}
        return (stripped.startswith("{{") and stripped.endswith("}}")) or (
            stripped.startswith("{") and ":" in stripped and stripped.endswith("}")
        )

    def parse(self, raw_output: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse structured record format."""
        stripped = raw_output.strip()

        try:
            if stripped.startswith("{{") and stripped.endswith("}}"):
                # Multiple records
                return self._parse_multiple_records(stripped)
            else:
                # Single record
                return self._parse_single_record(stripped)
        except Exception as e:
            raise AppleScriptParsingError(raw_output, "StructuredRecordParser", e)

    def _parse_multiple_records(self, content: str) -> List[Dict[str, Any]]:
        """Parse multiple structured records."""
        # Remove outer braces {{ and }}
        inner = content[2:-2]

        # Split on "}, {" but be careful about nested structures
        records = []
        current_record = ""
        depth = 0
        in_string = False
        escape_next = False

        i = 0
        while i < len(inner):
            char = inner[i]

            if escape_next:
                escape_next = False
                current_record += char
                i += 1
                continue

            if char == "\\":
                escape_next = True
                current_record += char
                i += 1
                continue

            if char == '"':
                in_string = not in_string
                current_record += char
            elif not in_string:
                if char == "{":
                    depth += 1
                    current_record += char
                elif char == "}":
                    current_record += char
                    if depth == 0:
                        # We found the end of a record
                        records.append(current_record)
                        current_record = ""

                        # Skip comma and whitespace after record
                        i += 1
                        while i < len(inner) and inner[i] in ", \t\n":
                            i += 1
                        continue
                    else:
                        depth -= 1
                else:
                    current_record += char
            else:
                current_record += char

            i += 1

        # Handle any remaining content
        if current_record.strip():
            records.append(current_record)

        # Parse each record by wrapping in braces
        parsed_records = []
        for record in records:
            if record.strip():
                # Ensure record is properly wrapped
                wrapped = "{" + record + "}" if not record.startswith("{") else record
                parsed_records.append(self._parse_single_record(wrapped))

        return parsed_records

    def _parse_single_record(self, record_str: str) -> Dict[str, Any]:
        """Parse a single structured record."""
        result = {}

        # Remove outer braces
        content = record_str.strip()[1:-1]

        # Split into key-value pairs
        pairs = self._split_pairs(content)

        for pair in pairs:
            key, value = self._parse_pair(pair)
            if key:
                result[key] = value

        return result

    def _split_pairs(self, content: str) -> List[str]:
        """Split record content into key-value pairs."""
        pairs = []
        current_pair = ""
        depth = 0
        in_string = False
        escape_next = False

        for char in content:
            if escape_next:
                escape_next = False
                current_pair += char
                continue

            if char == "\\":
                escape_next = True
                current_pair += char
                continue

            if char == '"':
                in_string = not in_string
            elif not in_string:
                if char in "({":
                    depth += 1
                elif char in ")}":
                    depth -= 1
                elif char == "," and depth == 0:
                    pairs.append(current_pair.strip())
                    current_pair = ""
                    continue

            current_pair += char

        if current_pair.strip():
            pairs.append(current_pair.strip())

        return pairs

    def _parse_pair(self, pair: str) -> tuple[str, Any]:
        """Parse a key-value pair."""
        # Find the key-value separator
        colon_pos = self._find_separator(pair)
        if colon_pos == -1:
            return None, None

        key = pair[:colon_pos].strip()
        value_str = pair[colon_pos + 1 :].strip()

        # Parse the value
        value = self._parse_value(value_str)

        return key, value

    def _find_separator(self, pair: str) -> int:
        """Find the colon that separates key from value."""
        in_string = False
        escape_next = False

        for i, char in enumerate(pair):
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"':
                in_string = not in_string
            elif not in_string and char == ":":
                return i

        return -1

    def _parse_value(self, value_str: str) -> Any:
        """Parse a structured value string."""
        value_str = value_str.strip()

        # Missing value
        if value_str == "missing value":
            return None

        # Boolean values
        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False

        # Quoted strings
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]

        # Date values - handle various malformed date formats
        if value_str.startswith('date "'):
            if value_str.endswith('"}'):
                return value_str[6:-2]  # Remove 'date "' and '"}'
            elif value_str.endswith('"'):
                return value_str[6:-1]  # Remove 'date "' and '"'
            else:
                # Missing closing quote - just remove 'date "'
                return value_str[6:]

        # Numeric values
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Default to string
        return value_str


class DateParser(ParserStrategy):
    """Specialized parser for AppleScript date format."""

    DATE_PATTERN = re.compile(r'^date "(.+)"$')

    def can_parse(self, raw_output: str) -> bool:
        """Check if output is an AppleScript date."""
        return bool(self.DATE_PATTERN.match(raw_output.strip()))

    def parse(self, raw_output: str) -> str:
        """Extract date string from AppleScript date format."""
        match = self.DATE_PATTERN.match(raw_output.strip())
        if match:
            return match.group(1)

        raise AppleScriptParsingError(raw_output, "DateParser")


class ListParser(ParserStrategy):
    """Parser for AppleScript list format."""

    def can_parse(self, raw_output: str) -> bool:
        """Check if output is a simple AppleScript list."""
        if not raw_output:
            return False

        stripped = raw_output.strip()
        # Simple list format: {item1, item2, item3}
        return (
            stripped.startswith("{")
            and stripped.endswith("}")
            and ":" not in stripped
            and not stripped.startswith("{{")
        )

    def parse(self, raw_output: str) -> List[str]:
        """Parse simple AppleScript list."""
        # Remove outer braces
        content = raw_output.strip()[1:-1]

        if not content:
            return []

        # Split by comma (simple implementation for now)
        items = []
        current_item = ""
        in_quotes = False

        for char in content:
            if char == '"':
                in_quotes = not in_quotes
            elif char == "," and not in_quotes:
                items.append(current_item.strip())
                current_item = ""
                continue

            current_item += char

        if current_item:
            items.append(current_item.strip())

        # Clean up quoted items
        cleaned_items = []
        for item in items:
            if item.startswith('"') and item.endswith('"'):
                cleaned_items.append(item[1:-1])
            else:
                cleaned_items.append(item)

        return cleaned_items


class ParserChain:
    """
    Chain of responsibility for parsing AppleScript output.

    Tries each parser in order until one can handle the output.
    """

    def __init__(self, parsers: Optional[List[ParserStrategy]] = None):
        """
        Initialize the parser chain.

        Args:
            parsers: List of parsers to try in order
        """
        self.parsers = parsers or self._default_parsers()

    def _default_parsers(self) -> List[ParserStrategy]:
        """Get default parser chain."""
        return [
            JSONParser(),
            StructuredRecordParser(),
            DateParser(),
            ListParser(),
            PrimitiveParser(),  # Fallback parser
        ]

    def parse(self, raw_output: str) -> Any:
        """
        Parse raw output using the first applicable parser.

        Args:
            raw_output: Raw AppleScript output

        Returns:
            Parsed Python object

        Raises:
            AppleScriptParsingError: If no parser can handle the output
        """
        if not raw_output:
            return None

        for parser in self.parsers:
            if parser.can_parse(raw_output):
                logger.debug(f"Using {parser.__class__.__name__} to parse output")
                return parser.parse(raw_output)

        # This should never happen with PrimitiveParser as fallback
        raise AppleScriptParsingError(
            raw_output,
            "No suitable parser",
            ValueError("No parser could handle the output"),
        )
