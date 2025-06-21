#!/usr/bin/env python3
"""
Generic AppleScript Orchestrator

This module handles the execution of AppleScript commands for any macOS application.
It provides a clean API for executing AppleScript commands and parsing their results.
"""

import subprocess
import json
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class AppleScriptError(Exception):
    """Exception raised when an AppleScript execution fails."""

    pass


class AppleScriptOrchestrator:
    """
    Generic orchestrator for executing AppleScript commands.

    This class provides methods for constructing and executing AppleScript
    commands to interact with any macOS application.
    """

    def __init__(self, app_name: str):
        """
        Initialize the AppleScript orchestrator.

        Args:
            app_name: The name of the macOS application to interact with.
        """
        self.app_name = app_name

    def _execute_script(self, script: str) -> str:
        """
        Execute an AppleScript and return its output.

        Args:
            script: The AppleScript code to execute.

        Returns:
            The output of the AppleScript execution.

        Raises:
            AppleScriptError: If the AppleScript execution fails.
        """
        try:
            logger.debug(f"Executing AppleScript: {script}")
            result = subprocess.run(
                ["osascript", "-s", "s", "-e", script],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"AppleScript execution failed: {e.stderr}")
            raise AppleScriptError(f"AppleScript execution failed: {e.stderr}")

    def _build_tell_block(self, commands: str) -> str:
        """
        Build a tell application block for the AppleScript.

        Args:
            commands: The AppleScript commands to execute within the tell block.

        Returns:
            The complete AppleScript with tell application block.
        """
        return f'tell application "{self.app_name}"\n{commands}\nend tell'

    def _to_applescript_value(self, value: Any) -> str:
        """
        Convert a Python value to its AppleScript representation.

        Args:
            value: The Python value to convert.

        Returns:
            The AppleScript representation of the value.
        """
        if value is None:
            return "missing value"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, list):
            items = ", ".join(self._to_applescript_value(item) for item in value)
            return f"{{{items}}}"
        elif isinstance(value, dict):
            items = ", ".join(
                f"{k}:{self._to_applescript_value(v)}" for k, v in value.items()
            )
            return f"{{{items}}}"
        else:
            return f'"{str(value)}"'

    def _parse_result(self, result: str) -> Any:
        """
        Parse the result of an AppleScript execution.

        Args:
            result: The raw output from the AppleScript execution.

        Returns:
            The parsed result, converted to appropriate Python types.
        """
        if not result:
            return None

        # Try parsing as JSON first
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass

        # Handle structured AppleScript records (from -s s flag)
        if result.startswith("{{") and result.endswith("}}"):
            return self._parse_structured_records(result)
        elif result.startswith("{") and ":" in result:
            return self._parse_single_structured_record(result)

        # Handle boolean values
        if result.lower() == "true":
            return True
        elif result.lower() == "false":
            return False

        # Handle numeric values
        try:
            if "." in result:
                return float(result)
            else:
                return int(result)
        except ValueError:
            pass

        # Return as string
        return result

    def _parse_structured_records(self, result: str) -> List[Dict[str, Any]]:
        """
        Parse structured AppleScript records (array format) into Python dictionaries.

        Args:
            result: Raw structured AppleScript output from -s s flag.

        Returns:
            List of dictionaries representing the records.
        """
        # Remove outer braces
        content = result[2:-2]  # Remove {{ and }}

        # Simple approach: split on "}, {" pattern
        record_strings = content.split("}, {")

        records = []
        for i, record_str in enumerate(record_strings):
            # Add back the braces that were removed by split
            if i == 0:
                # First record: add closing brace
                full_record = "{" + record_str + "}"
            elif i == len(record_strings) - 1:
                # Last record: add opening brace
                full_record = "{" + record_str + "}"
            else:
                # Middle records: add both braces
                full_record = "{" + record_str + "}"

            record = self._parse_single_structured_record(full_record)
            if record:
                records.append(record)

        return records

    def _parse_single_structured_record(self, record_str: str) -> Dict[str, Any]:
        """
        Parse a single structured AppleScript record into a Python dictionary.

        Args:
            record_str: String representation of a single structured record.

        Returns:
            Dictionary representation of the record.
        """
        record = {}

        # Remove outer braces
        content = record_str.strip()[1:-1]  # Remove { and }

        # Parse key-value pairs
        pairs = self._split_record_pairs(content)

        for pair in pairs:
            if ":" not in pair:
                continue

            # Find the first colon that's not inside quotes
            colon_pos = self._find_key_value_separator(pair)
            if colon_pos == -1:
                continue

            key = pair[:colon_pos].strip()
            value = pair[colon_pos + 1 :].strip()

            # Parse the value
            parsed_value = self._parse_structured_value(value)
            record[key] = parsed_value

        return record

    def _split_record_pairs(self, content: str) -> List[str]:
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

    def _find_key_value_separator(self, pair: str) -> int:
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

    def _parse_structured_value(self, value_str: str) -> Any:
        """Parse a structured AppleScript value."""
        value_str = value_str.strip()

        # Handle missing value
        if value_str == "missing value":
            return None

        # Handle boolean values
        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False

        # Handle quoted strings
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]  # Remove quotes

        # Handle date values
        if value_str.startswith('date "') and value_str.endswith('"'):
            return value_str[6:-1]  # Remove 'date "' and '"'

        # Handle object references (project id, area id, etc.)
        if " id " in value_str and " of application " in value_str:
            # Extract just the ID part
            if value_str.startswith('project id "'):
                end_quote = value_str.find('"', 12)
                if end_quote != -1:
                    return f"project id {value_str[12:end_quote]}"
            elif value_str.startswith('area id "'):
                end_quote = value_str.find('"', 9)
                if end_quote != -1:
                    return f"area id {value_str[9:end_quote]}"
            return value_str.split(" of application ")[
                0
            ]  # Remove application reference

        # Handle numeric values
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Handle class values
        if value_str.startswith("selected to do"):
            return "selected to do"

        # Return as string
        return value_str

    def execute_command(self, command: str, return_raw: bool = False) -> Any:
        """
        Execute an AppleScript command within the application tell block.

        Args:
            command: The AppleScript command to execute.
            return_raw: Whether to return the raw output or parse it.

        Returns:
            The result of the command execution.

        Raises:
            AppleScriptError: If the AppleScript execution fails.
        """
        script = self._build_tell_block(command)
        result = self._execute_script(script)
        return result if return_raw else self._parse_result(result)

    def execute_raw_script(self, script: str, return_raw: bool = False) -> Any:
        """
        Execute a raw AppleScript without wrapping in a tell block.

        Args:
            script: The complete AppleScript to execute.
            return_raw: Whether to return the raw output or parse it.

        Returns:
            The result of the script execution.

        Raises:
            AppleScriptError: If the AppleScript execution fails.
        """
        result = self._execute_script(script)
        return result if return_raw else self._parse_result(result)
