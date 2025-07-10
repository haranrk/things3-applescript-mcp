"""
Things 3 specific orchestrator implementation.

This module provides a Things 3 specific orchestrator that uses
the generic AppleScript infrastructure with Things 3 specific
parsers and converters.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from things3_mcp.applescript.core import AppleScriptEngine
from things3_mcp.applescript.parsers import (
    ParserChain,
    PrimitiveParser,
    DateParser,
    ListParser,
)
from things3_mcp.applescript.converters import (
    PythonToAppleScriptConverter,
    PropertyConverter,
)
from things3_mcp.applescript.builders import AppleScriptCommand
from things3_mcp.applescript.errors import AppleScriptError

from things3_mcp.things3.parsers import Things3RecordParser, Things3PropertyNormalizer
from things3_mcp.things3.command_builders import (
    TodoCommandBuilder,
    ProjectCommandBuilder,
    AreaCommandBuilder,
    TagCommandBuilder,
)

logger = logging.getLogger(__name__)


class Things3Orchestrator:
    """
    Orchestrator for Things 3 AppleScript operations.

    This class provides a high-level interface for interacting with
    Things 3 using the modular AppleScript infrastructure.
    """

    def __init__(self):
        """Initialize the Things 3 orchestrator."""
        self.app_name = "Things3"
        self.engine = AppleScriptEngine()
        self.converter = PythonToAppleScriptConverter()
        self.property_converter = PropertyConverter()

        # Set up parser chain with Things 3 specific parsers
        self.parser_chain = ParserChain(
            [
                Things3RecordParser(),
                DateParser(),
                ListParser(),
                PrimitiveParser(),  # Fallback
            ]
        )

        # Property normalizer for Things 3 specific values
        self.normalizer = Things3PropertyNormalizer()

        # Command builders
        self.todo_builder = TodoCommandBuilder()
        self.project_builder = ProjectCommandBuilder()
        self.area_builder = AreaCommandBuilder()
        self.tag_builder = TagCommandBuilder()

    def execute_command(
        self, command: Union[str, AppleScriptCommand], return_raw: bool = False
    ) -> Any:
        """
        Execute an AppleScript command.

        Args:
            command: Either a string command or an AppleScriptCommand instance
            return_raw: If True, return raw output without parsing

        Returns:
            Parsed result or raw output string

        Raises:
            AppleScriptError: If execution fails
        """
        # Build the script
        if isinstance(command, AppleScriptCommand):
            script = command.build()
        else:
            # Legacy string command - wrap in tell block if needed
            if not command.startswith("tell application"):
                script = f'tell application "{self.app_name}"\n    {command}\nend tell'
            else:
                script = command

        # Determine if we should use structured output
        use_structured = not return_raw and not self._is_write_command(script)

        try:
            # Execute the script
            if use_structured:
                raw_output = self.engine.execute_structured(script)
            else:
                raw_output = self.engine.execute(script)

            logger.debug(f"Raw output: {raw_output}")

            # Return raw or parse
            if return_raw:
                return raw_output
            else:
                return self.parser_chain.parse(raw_output)

        except AppleScriptError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing command: {e}")
            raise AppleScriptError(f"Failed to execute command: {e}")

    def _is_write_command(self, script: str) -> bool:
        """Check if a script is a write operation."""
        write_indicators = [
            "make new",
            "set ",
            "delete ",
            "move ",
            "create ",
            "update ",
        ]

        return any(indicator in script for indicator in write_indicators)

    # Todo operations
    def create_todo(self, data: Dict[str, Any]) -> str:
        """
        Create a new todo.

        Args:
            data: Todo properties

        Returns:
            ID of the created todo
        """
        command = self.todo_builder.create_todo(data)
        return self.execute_command(command)

    def update_todo(self, todo_id: str, data: Dict[str, Any]) -> str:
        """
        Update an existing todo.

        Args:
            todo_id: ID of the todo to update
            data: Properties to update

        Returns:
            ID of the updated todo
        """
        command = self.todo_builder.update_todo(todo_id, data)
        return self.execute_command(command)

    def delete_todo(self, todo_id: str) -> str:
        """
        Delete a todo.

        Args:
            todo_id: ID of the todo to delete

        Returns:
            Success message
        """
        command = self.todo_builder.delete_todo(todo_id)
        return self.execute_command(command)

    def get_todo(self, todo_id: str) -> Dict[str, Any]:
        """
        Get a single todo by ID.

        Args:
            todo_id: ID of the todo to retrieve

        Returns:
            Dictionary of todo properties
        """
        command = (
            AppleScriptCommand()
            .tell(self.app_name)
            .get("properties", of=f'to do id "{todo_id}"')
        )

        result = self.execute_command(command)

        # Normalize the properties
        if isinstance(result, dict):
            return self.normalizer.normalize_properties(result)

        return result

    def list_todos(self, list_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List todos, optionally filtered by list.

        Args:
            list_name: Optional list name to filter by

        Returns:
            List of todo property dictionaries
        """
        if list_name:
            command = (
                AppleScriptCommand()
                .tell(self.app_name)
                .get("properties", of=f'every to do of list "{list_name}"')
            )
        else:
            command = (
                AppleScriptCommand()
                .tell(self.app_name)
                .get("properties", of="every to do")
            )

        result = self.execute_command(command)

        # Normalize each todo
        if isinstance(result, list):
            return [
                self.normalizer.normalize_properties(todo)
                for todo in result
                if isinstance(todo, dict)
            ]

        return result if isinstance(result, list) else []

    # Project operations
    def create_project(self, data: Dict[str, Any]) -> str:
        """Create a new project."""
        command = self.project_builder.create_project(data)
        return self.execute_command(command)

    def update_project(self, project_id: str, data: Dict[str, Any]) -> str:
        """Update an existing project."""
        command = self.project_builder.update_project(project_id, data)
        return self.execute_command(command)

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a single project by ID."""
        command = (
            AppleScriptCommand()
            .tell(self.app_name)
            .get("properties", of=f'project id "{project_id}"')
        )

        result = self.execute_command(command)

        if isinstance(result, dict):
            return self.normalizer.normalize_properties(result)

        return result

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        command = (
            AppleScriptCommand()
            .tell(self.app_name)
            .get("properties", of="every project")
        )

        result = self.execute_command(command)

        if isinstance(result, list):
            return [
                self.normalizer.normalize_properties(project)
                for project in result
                if isinstance(project, dict)
            ]

        return result if isinstance(result, list) else []

    # Area operations
    def create_area(self, data: Dict[str, Any]) -> str:
        """Create a new area."""
        command = self.area_builder.create_area(data)
        return self.execute_command(command)

    def update_area(self, area_id: str, data: Dict[str, Any]) -> str:
        """Update an existing area."""
        command = self.area_builder.update_area(area_id, data)
        return self.execute_command(command)

    def get_area(self, area_id: str) -> Dict[str, Any]:
        """Get a single area by ID."""
        command = (
            AppleScriptCommand()
            .tell(self.app_name)
            .get("properties", of=f'area id "{area_id}"')
        )

        result = self.execute_command(command)

        if isinstance(result, dict):
            return self.normalizer.normalize_properties(result)

        return result

    def list_areas(self) -> List[Dict[str, Any]]:
        """List all areas."""
        command = (
            AppleScriptCommand().tell(self.app_name).get("properties", of="every area")
        )

        result = self.execute_command(command)

        if isinstance(result, list):
            return [
                self.normalizer.normalize_properties(area)
                for area in result
                if isinstance(area, dict)
            ]

        return result if isinstance(result, list) else []

    # Tag operations
    def create_tag(self, data: Dict[str, Any]) -> str:
        """Create a new tag."""
        command = self.tag_builder.create_tag(data)
        return self.execute_command(command)

    def list_tags(self) -> List[str]:
        """List all tag names."""
        command = AppleScriptCommand().tell(self.app_name).get("name", of="every tag")

        result = self.execute_command(command)

        return result if isinstance(result, list) else []

    # Legacy compatibility methods
    def execute_raw_script(self, script: str, return_raw: bool = False) -> Any:
        """
        Execute a raw AppleScript (legacy compatibility).

        Args:
            script: Complete AppleScript to execute
            return_raw: If True, return raw output

        Returns:
            Parsed result or raw output
        """
        raw_output = self.engine.execute(script)

        if return_raw:
            return raw_output
        else:
            return self.parser_chain.parse(raw_output)
