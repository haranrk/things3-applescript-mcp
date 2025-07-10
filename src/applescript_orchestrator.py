#!/usr/bin/env python3
"""
AppleScript Orchestrator - Refactored to use modular architecture.

This module now serves as a facade that uses the new modular AppleScript
infrastructure while maintaining backward compatibility.
"""

import logging
from typing import Any
from datetime import date, datetime

from things3_mcp.applescript import (
    AppleScriptEngine,
    AppleScriptError,
    ParserChain,
    PythonToAppleScriptConverter,
)
from things3_mcp.things3 import Things3Orchestrator

logger = logging.getLogger(__name__)


class AppleScriptOrchestrator:
    """
    Orchestrator for executing AppleScript commands.

    This class now uses the modular architecture internally while
    maintaining the same public interface for backward compatibility.
    """

    def __init__(self, app_name: str):
        """
        Initialize the AppleScript orchestrator.

        Args:
            app_name: The name of the macOS application to interact with.
        """
        self.app_name = app_name

        # Use specialized orchestrator for Things3
        if app_name == "Things3":
            self._impl = Things3Orchestrator()
            self._engine = self._impl.engine
            self._converter = self._impl.converter
            self._parser = self._impl.parser_chain
        else:
            # Generic implementation for other apps
            self._impl = None
            self._engine = AppleScriptEngine()
            self._converter = PythonToAppleScriptConverter()
            self._parser = ParserChain()

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
            return self._engine.execute_structured(script)
        except Exception as e:
            logger.error(f"AppleScript execution failed: {e}")
            raise AppleScriptError(str(e))

    def _execute_script_without_structured_output(self, script: str) -> str:
        """
        Execute an AppleScript without structured output flag.

        Args:
            script: The AppleScript code to execute.

        Returns:
            The raw output of the AppleScript execution.

        Raises:
            AppleScriptError: If the AppleScript execution fails.
        """
        try:
            return self._engine.execute(script)
        except Exception as e:
            logger.error(f"AppleScript execution failed: {e}")
            raise AppleScriptError(str(e))

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
        return self._parser.parse(result)

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
        # Delegate to Things3Orchestrator if available
        if self._impl:
            return self._impl.execute_command(command, return_raw)

        # Otherwise use generic implementation
        if command.startswith("tell application"):
            script = command
        else:
            script = self._build_tell_block(command)

        # Determine which execution method to use
        if return_raw or "make new to do" in command or "return " in command:
            result = self._execute_script_without_structured_output(script)
        else:
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

    def _encode_todo_properties(self, todo_data) -> str:
        """
        Convert a TodoCreate object to AppleScript properties format.

        Args:
            todo_data: TodoCreate pydantic model or dict with todo properties

        Returns:
            AppleScript properties string for creating a todo
        """
        if hasattr(todo_data, "model_dump"):
            # Pydantic model
            data = todo_data.model_dump(exclude_none=True)
        else:
            # Dictionary
            data = {k: v for k, v in todo_data.items() if v is not None}

        properties = []

        # Required name field
        if "name" in data:
            properties.append(f"name:{self._to_applescript_value(data['name'])}")

        # Optional notes
        if "notes" in data:
            properties.append(f"notes:{self._to_applescript_value(data['notes'])}")

        # Skip dates in initial properties - set them after creation

        # Tags - convert list to comma-separated string
        if "tags" in data and data["tags"]:
            tag_names = ", ".join(data["tags"])
            properties.append(f"tag names:{self._to_applescript_value(tag_names)}")

        # Skip checklist items in initial properties - add them after creation

        return "{" + ", ".join(properties) + "}"

    def _extract_data(self, data_obj) -> dict:
        """Extract data dict from TodoCreate/TodoUpdate object or dict.

        For updates, we need to preserve None values to handle clearing operations.
        """
        if hasattr(data_obj, "model_dump"):
            # For updates, preserve None values that were explicitly set
            if (
                hasattr(data_obj, "__class__")
                and "Update" in data_obj.__class__.__name__
            ):
                # This is an update object - preserve None values to handle clearing
                all_data = data_obj.model_dump(exclude_none=False)
                # Only include fields that were explicitly set (not just defaults)
                explicitly_set = {
                    k: v
                    for k, v in all_data.items()
                    if getattr(data_obj, k) is not None
                    or k in data_obj.model_fields_set
                }
                return explicitly_set
            else:
                # This is a create object - exclude None values as before
                return data_obj.model_dump(exclude_none=True)
        else:
            # For dicts, include None values (they were explicitly set)
            return dict(data_obj)

    def _set_todo_dates(self, todo_ref: str, data: dict) -> list:
        """Generate AppleScript commands for setting todo dates."""
        commands = []

        # Set due date
        if "due_date" in data:
            if data["due_date"]:
                date_str = self._format_date_for_applescript(data["due_date"])
                if date_str:
                    commands.append(f"set due date of {todo_ref} to {date_str}")
            else:
                # Clear due date by deleting the property
                commands.append(f"delete due date of {todo_ref}")

        # Note: deadline is not supported for todos, only for projects
        # Skip deadline setting for todos

        # Note: start_date is not supported for todos, only for projects
        # Skip start_date setting for todos

        return commands

    def _set_todo_scheduling(self, todo_ref: str, data: dict) -> list:
        """Generate AppleScript commands for todo scheduling (when)."""
        commands = []

        if "when" in data:
            when_value = data["when"].lower()
            if when_value == "tomorrow":
                commands.append(f'move {todo_ref} to list "Today"')
                commands.append(
                    f"set due date of {todo_ref} to (current date) + (1 * days)"
                )
            elif when_value in ["today", "upcoming", "anytime", "someday"]:
                list_name = when_value.capitalize()
                commands.append(f'move {todo_ref} to list "{list_name}"')

        return commands

    def _set_todo_project(self, todo_ref: str, data: dict) -> list:
        """Generate AppleScript commands for project assignment."""
        commands = []

        if "project" in data:
            project_ref = data["project"]
            if project_ref:
                if project_ref.startswith("project id "):
                    # Reference by ID
                    project_id = project_ref.replace("project id ", "")
                    commands.append(f'move {todo_ref} to project id "{project_id}"')
                else:
                    # Reference by name
                    commands.append(f'move {todo_ref} to project "{project_ref}"')
            else:
                # Remove from project (move to inbox)
                commands.append(f'move {todo_ref} to list "Inbox"')

        return commands

    def _set_todo_area(self, todo_ref: str, data: dict) -> list:
        """Generate AppleScript commands for area assignment."""
        commands = []

        if "area" in data:
            area_ref = data["area"]
            if area_ref:
                if area_ref.startswith("area id "):
                    # Reference by ID
                    area_id = area_ref.replace("area id ", "")
                    commands.append(f'set area of {todo_ref} to area id "{area_id}"')
                else:
                    # Reference by name
                    commands.append(f'set area of {todo_ref} to area "{area_ref}"')
            else:
                commands.append(f"set area of {todo_ref} to missing value")

        return commands

    def _set_todo_tags(self, todo_ref: str, data: dict) -> list:
        """Generate AppleScript commands for tag management."""
        commands = []

        if "tags" in data:
            if data["tags"]:
                tags_str = ", ".join(data["tags"])
                tags_value = self._to_applescript_value(tags_str)
                commands.append(f"set tag names of {todo_ref} to {tags_value}")
            else:
                commands.append(f'set tag names of {todo_ref} to ""')

        return commands

    def _set_todo_status(self, todo_ref: str, data: dict) -> list:
        """Generate AppleScript commands for status changes."""
        commands = []

        if "status" in data:
            status = data["status"]
            if status == "completed":
                commands.append(f"set completion date of {todo_ref} to (current date)")
            elif status == "canceled":
                commands.append(
                    f"set cancellation date of {todo_ref} to (current date)"
                )
            elif status == "open":
                # Note: Things 3 doesn't allow directly setting completion/cancellation dates to missing value
                # Instead, we rely on Things 3's built-in behavior to handle reopening todos
                # The status change will be reflected when we fetch the updated todo
                pass

        return commands

    def _set_todo_basic_props(self, todo_ref: str, data: dict) -> list:
        """Generate AppleScript commands for basic properties (name, notes)."""
        commands = []

        if "name" in data:
            name_value = self._to_applescript_value(data["name"])
            commands.append(f"set name of {todo_ref} to {name_value}")

        if "notes" in data:
            notes_value = self._to_applescript_value(data["notes"])
            commands.append(f"set notes of {todo_ref} to {notes_value}")

        return commands

    def _add_todo_checklist(self, todo_ref: str, data: dict) -> list:
        """Generate AppleScript commands for checklist items (create only)."""
        commands = []

        if "checklist" in data and data["checklist"]:
            for item in data["checklist"]:
                if isinstance(item, dict) and "name" in item:
                    item_name = self._to_applescript_value(item["name"])
                    commands.append(
                        f"tell {todo_ref} to make new checklist item with properties {{name:{item_name}}}"
                    )
                elif isinstance(item, str):
                    item_name = self._to_applescript_value(item)
                    commands.append(
                        f"tell {todo_ref} to make new checklist item with properties {{name:{item_name}}}"
                    )

        return commands

    def _build_todo_commands(self, todo_ref: str, data: dict, operation: str) -> list:
        """
        Generate AppleScript commands for todo properties.

        Args:
            todo_ref: Reference to the todo (e.g. "newTodo" or 'to do id "ABC123"')
            data: Dictionary of properties to set
            operation: "create" or "update"

        Returns:
            List of AppleScript command strings
        """
        commands = []

        # For updates, set basic properties first
        if operation == "update":
            commands.extend(self._set_todo_basic_props(todo_ref, data))
            commands.extend(self._set_todo_status(todo_ref, data))

        # Set dates (both create and update)
        commands.extend(self._set_todo_dates(todo_ref, data))

        # Set tags (both create and update)
        commands.extend(self._set_todo_tags(todo_ref, data))

        # Handle scheduling/when (both create and update)
        commands.extend(self._set_todo_scheduling(todo_ref, data))

        # Handle project assignment (both create and update)
        commands.extend(self._set_todo_project(todo_ref, data))

        # Handle area assignment (both create and update)
        commands.extend(self._set_todo_area(todo_ref, data))

        # Add checklist items (create only)
        if operation == "create":
            commands.extend(self._add_todo_checklist(todo_ref, data))

        return commands

    def _wrap_applescript_commands(self, commands: list) -> str:
        """Wrap commands in AppleScript tell block."""
        if not commands:
            return ""

        command_block = "\n    ".join(commands)
        return f'''tell application "{self.app_name}"
    {command_block}
end tell'''

    def _format_date_for_applescript(self, date_value) -> str:
        """
        Format a Python date/datetime for AppleScript.

        Args:
            date_value: date, datetime, or date string

        Returns:
            AppleScript date expression
        """
        if isinstance(date_value, str):
            try:
                # Try to parse as ISO date
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

        # Calculate days difference from today
        today = datetime.now().date()
        target_date = parsed_date.date()
        days_diff = (target_date - today).days

        # Format as AppleScript date expression
        if days_diff == 0:
            return "current date"
        elif days_diff == 1:
            return "(current date) + (1 * days)"
        elif days_diff == -1:
            return "(current date) - (1 * days)"
        else:
            return f"(current date) + ({days_diff} * days)"

    def create_todo_command(self, todo_data) -> str:
        """
        Generate AppleScript command to create a todo.

        Args:
            todo_data: TodoCreate object or dict with todo properties

        Returns:
            AppleScript command to create the todo
        """
        # Delegate to Things3Orchestrator if available
        if self._impl:
            data = self._extract_data(todo_data)
            command = self._impl.todo_builder.create_todo(data)
            return command.build()

        # Fallback to legacy implementation
        properties = self._encode_todo_properties(todo_data)
        data = self._extract_data(todo_data)

        commands = [f"set newTodo to make new to do with properties {properties}"]
        commands.extend(self._build_todo_commands("newTodo", data, "create"))
        commands.append("return id of newTodo")

        return self._wrap_applescript_commands(commands)

    def update_todo_command(self, todo_id: str, update_data) -> str:
        """
        Generate AppleScript command to update an existing todo.

        Args:
            todo_id: The ID of the todo to update
            update_data: TodoUpdate object or dict with update properties

        Returns:
            AppleScript command to update the todo
        """
        # Delegate to Things3Orchestrator if available
        if self._impl:
            data = self._extract_data(update_data)
            command = self._impl.todo_builder.update_todo(todo_id, data)
            return command.build()

        # Fallback to legacy implementation
        from things3_mcp.models import TodoUpdate

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
