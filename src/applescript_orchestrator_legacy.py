"""
Legacy AppleScript Orchestrator - Backward compatibility wrapper.

This module provides a backward-compatible interface that wraps the new
modular AppleScript infrastructure. It maintains the same API as the
original AppleScriptOrchestrator for seamless migration.
"""

import logging
from typing import Any, Dict, List
from datetime import date, datetime

from applescript import AppleScriptEngine
from applescript.parsers import ParserChain
from applescript.converters import PythonToAppleScriptConverter
from things3 import Things3Orchestrator

logger = logging.getLogger(__name__)


class AppleScriptOrchestrator:
    """
    Legacy orchestrator that maintains backward compatibility.

    This class wraps the new modular architecture to provide the same
    interface as the original AppleScriptOrchestrator.
    """

    def __init__(self, app_name: str):
        """
        Initialize the AppleScript orchestrator.

        Args:
            app_name: The name of the macOS application to interact with.
        """
        self.app_name = app_name

        # Use Things3Orchestrator for Things3, generic for others
        if app_name == "Things3":
            self._orchestrator = Things3Orchestrator()
            self._engine = self._orchestrator.engine
            self._converter = self._orchestrator.converter
            self._parser_chain = self._orchestrator.parser_chain
        else:
            # Generic orchestrator for other apps
            self._engine = AppleScriptEngine()
            self._converter = PythonToAppleScriptConverter()
            self._parser_chain = ParserChain()
            self._orchestrator = None

    def _execute_script(self, script: str) -> str:
        """Legacy method for executing with structured output."""
        return self._engine.execute_structured(script)

    def _execute_script_without_structured_output(self, script: str) -> str:
        """Legacy method for executing without structured output."""
        return self._engine.execute(script)

    def _build_tell_block(self, commands: str) -> str:
        """Legacy method for building tell blocks."""
        return f'tell application "{self.app_name}"\n{commands}\nend tell'

    def _to_applescript_value(self, value: Any) -> str:
        """Legacy method for converting Python values to AppleScript."""
        return self._converter.convert(value)

    def _parse_result(self, result: str) -> Any:
        """Legacy method for parsing AppleScript results."""
        return self._parser_chain.parse(result)

    def execute_command(self, command: str, return_raw: bool = False) -> Any:
        """
        Legacy method for executing commands.

        If Things3Orchestrator is available, delegates to it.
        Otherwise uses the generic infrastructure.
        """
        if self._orchestrator:
            return self._orchestrator.execute_command(command, return_raw)

        # Generic execution
        if command.startswith("tell application"):
            script = command
        else:
            script = self._build_tell_block(command)

        # Determine execution method
        if return_raw or "make new to do" in command or "return " in command:
            result = self._execute_script_without_structured_output(script)
        else:
            result = self._execute_script(script)

        return result if return_raw else self._parse_result(result)

    def execute_raw_script(self, script: str, return_raw: bool = False) -> Any:
        """Legacy method for executing raw scripts."""
        if self._orchestrator:
            return self._orchestrator.execute_raw_script(script, return_raw)

        result = self._execute_script(script)
        return result if return_raw else self._parse_result(result)

    # Legacy parsing methods (delegated to parser chain)
    def _parse_structured_records(self, result: str) -> List[Dict[str, Any]]:
        """Legacy parsing method."""
        parsed = self._parser_chain.parse(result)
        return parsed if isinstance(parsed, list) else [parsed]

    def _parse_single_structured_record(self, record_str: str) -> Dict[str, Any]:
        """Legacy parsing method."""
        parsed = self._parser_chain.parse(record_str)
        return parsed if isinstance(parsed, dict) else {}

    def _split_record_pairs(self, content: str) -> List[str]:
        """Legacy parsing helper - maintained for compatibility."""
        # This is now handled internally by parsers
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
        """Legacy parsing helper - maintained for compatibility."""
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
        """Legacy parsing helper - delegated to parser chain."""
        return self._parser_chain.parse(value_str)

    # Things 3 specific methods (delegated when available)
    def _encode_todo_properties(self, todo_data) -> str:
        """Legacy Things 3 method."""
        if hasattr(todo_data, "model_dump"):
            data = todo_data.model_dump(exclude_none=True)
        else:
            data = {k: v for k, v in todo_data.items() if v is not None}

        properties = []

        if "name" in data:
            properties.append(f"name:{self._to_applescript_value(data['name'])}")

        if "notes" in data:
            properties.append(f"notes:{self._to_applescript_value(data['notes'])}")

        if "tags" in data and data["tags"]:
            tag_names = ", ".join(data["tags"])
            properties.append(f"tag names:{self._to_applescript_value(tag_names)}")

        return "{" + ", ".join(properties) + "}"

    def _extract_data(self, data_obj) -> dict:
        """Legacy Things 3 method."""
        if hasattr(data_obj, "model_dump"):
            if (
                hasattr(data_obj, "__class__")
                and "Update" in data_obj.__class__.__name__
            ):
                all_data = data_obj.model_dump(exclude_none=False)
                explicitly_set = {
                    k: v
                    for k, v in all_data.items()
                    if getattr(data_obj, k) is not None
                    or k in data_obj.model_fields_set
                }
                return explicitly_set
            else:
                return data_obj.model_dump(exclude_none=True)
        else:
            return dict(data_obj)

    def create_todo_command(self, todo_data) -> str:
        """Legacy Things 3 method - delegates to orchestrator."""
        if self._orchestrator:
            data = self._extract_data(todo_data)
            return self._orchestrator.todo_builder.create_todo(data).build()

        # Fallback to legacy implementation
        properties = self._encode_todo_properties(todo_data)
        data = self._extract_data(todo_data)

        commands = [f"set newTodo to make new to do with properties {properties}"]
        commands.extend(self._build_todo_commands("newTodo", data, "create"))
        commands.append("return id of newTodo")

        return self._wrap_applescript_commands(commands)

    def update_todo_command(self, todo_id: str, update_data) -> str:
        """Legacy Things 3 method - delegates to orchestrator."""
        if self._orchestrator:
            data = self._extract_data(update_data)
            return self._orchestrator.todo_builder.update_todo(todo_id, data).build()

        # Fallback to legacy implementation
        from .models import TodoUpdate

        if isinstance(update_data, dict):
            update_data = TodoUpdate(**update_data)

        data = self._extract_data(update_data)
        todo_ref = f'to do id "{todo_id}"'

        commands = self._build_todo_commands(todo_ref, data, "update")
        if not commands:
            return (
                f'tell application "{self.app_name}"\n    return "{todo_id}"\nend tell'
            )

        commands.append(f'return "{todo_id}"')
        return self._wrap_applescript_commands(commands)

    # Legacy helper methods maintained for compatibility
    def _format_date_for_applescript(self, date_value) -> str:
        """Legacy date formatting method."""
        if isinstance(date_value, str):
            try:
                if "T" in date_value or " " in date_value:
                    parsed_date = datetime.fromisoformat(
                        date_value.replace("Z", "+00:00")
                    )
                else:
                    parsed_date = datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                return None
        elif isinstance(date_value, datetime):
            parsed_date = date_value
        elif isinstance(date_value, date):
            parsed_date = datetime.combine(date_value, datetime.min.time())
        else:
            return None

        today = datetime.now().date()
        target_date = parsed_date.date()
        days_diff = (target_date - today).days

        if days_diff == 0:
            return "current date"
        elif days_diff == 1:
            return "(current date) + (1 * days)"
        elif days_diff == -1:
            return "(current date) - (1 * days)"
        else:
            return f"(current date) + ({days_diff} * days)"

    def _build_todo_commands(self, todo_ref: str, data: dict, operation: str) -> list:
        """Legacy Things 3 command building - stub for compatibility."""
        # This would contain the full legacy implementation
        # For now, returning empty list as this should be handled by new architecture
        return []

    def _wrap_applescript_commands(self, commands: list) -> str:
        """Legacy command wrapping method."""
        if not commands:
            return ""

        command_block = "\n    ".join(commands)
        return f'''tell application "{self.app_name}"
    {command_block}
end tell'''

    # Stub methods for other legacy helpers
    def _set_todo_dates(self, todo_ref: str, data: dict) -> list:
        return []

    def _set_todo_scheduling(self, todo_ref: str, data: dict) -> list:
        return []

    def _set_todo_project(self, todo_ref: str, data: dict) -> list:
        return []

    def _set_todo_area(self, todo_ref: str, data: dict) -> list:
        return []

    def _set_todo_tags(self, todo_ref: str, data: dict) -> list:
        return []

    def _set_todo_status(self, todo_ref: str, data: dict) -> list:
        return []

    def _set_todo_basic_props(self, todo_ref: str, data: dict) -> list:
        return []

    def _add_todo_checklist(self, todo_ref: str, data: dict) -> list:
        return []
