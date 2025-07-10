"""
Things 3 specific command builders.

This module contains command builders for creating Things 3
specific AppleScript commands using the generic builder infrastructure.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from things3_mcp.applescript.builders import AppleScriptCommand, CommandBuilder
from things3_mcp.applescript.converters import (
    PythonToAppleScriptConverter,
    AppleScriptReferenceConverter,
)


class Things3CommandBuilder(CommandBuilder):
    """Base class for Things 3 command builders."""

    def __init__(self):
        self.converter = PythonToAppleScriptConverter()
        self.ref_converter = AppleScriptReferenceConverter()

    def _format_date(self, date_value: Union[date, datetime, str]) -> Optional[str]:
        """Format a date for Things 3."""
        if not date_value:
            return None

        if isinstance(date_value, str):
            # Handle special Things 3 date keywords
            if date_value.lower() in [
                "today",
                "tomorrow",
                "evening",
                "anytime",
                "someday",
            ]:
                return date_value.lower()

        # Use converter for date objects
        return self.converter.convert(date_value)

    def _format_reference(self, ref: str, ref_type: str) -> Optional[str]:
        """Format an object reference for Things 3."""
        if not ref:
            return None

        # Check if it's already a reference
        if self.ref_converter.is_reference(ref):
            return ref

        # Check if it's an ID reference
        if ref.startswith(f"{ref_type} id "):
            return ref

        # Otherwise, treat as name reference
        return f'{ref_type} "{ref}"'


class TodoCommandBuilder(Things3CommandBuilder):
    """Builder for Things 3 todo-related commands."""

    def create_todo(self, data: Dict[str, Any]) -> AppleScriptCommand:
        """
        Build command to create a new todo.

        Args:
            data: Todo properties (name, notes, due_date, etc.)

        Returns:
            AppleScriptCommand ready to execute
        """
        cmd = AppleScriptCommand().tell("Things3")

        # Build initial properties
        properties = {}

        # Required properties
        if "name" in data:
            properties["name"] = data["name"]

        # Optional properties
        if "notes" in data:
            properties["notes"] = data["notes"]

        # Tags need special handling
        if "tags" in data and data["tags"]:
            properties["tag names"] = ", ".join(data["tags"])

        # Create the todo
        cmd.add_command(
            "set newTodo to make new to do with properties "
            + self._build_properties_record(properties)
        )

        # Set additional properties that can't be set during creation
        self._add_todo_property_commands(cmd, "newTodo", data)

        # Return the ID
        cmd.return_value("id of newTodo")

        return cmd

    def update_todo(self, todo_id: str, data: Dict[str, Any]) -> AppleScriptCommand:
        """
        Build command to update an existing todo.

        Args:
            todo_id: ID of the todo to update
            data: Properties to update

        Returns:
            AppleScriptCommand ready to execute
        """
        cmd = AppleScriptCommand().tell("Things3")
        todo_ref = f'to do id "{todo_id}"'

        # Basic properties
        if "name" in data:
            cmd.set("name", of=todo_ref, to=data["name"])

        if "notes" in data:
            cmd.set("notes", of=todo_ref, to=data["notes"])

        # Status changes
        if "status" in data:
            self._add_status_change_command(cmd, todo_ref, data["status"])

        # Other properties
        self._add_todo_property_commands(cmd, todo_ref, data)

        # Return the ID
        cmd.return_value(f'"{todo_id}"')

        return cmd

    def delete_todo(self, todo_id: str) -> AppleScriptCommand:
        """Build command to delete a todo."""
        return (
            AppleScriptCommand()
            .tell("Things3")
            .delete(f'to do id "{todo_id}"')
            .return_value('"success"')
        )

    def _add_todo_property_commands(
        self, cmd: AppleScriptCommand, todo_ref: str, data: Dict[str, Any]
    ) -> None:
        """Add commands for setting todo properties."""
        # Due date
        if "due_date" in data:
            if data["due_date"]:
                date_expr = self._format_date(data["due_date"])
                if date_expr:
                    cmd.set("due date", of=todo_ref, to=date_expr)
            else:
                # Clear due date
                cmd.delete(f"due date of {todo_ref}")

        # Tags
        if "tags" in data:
            if data["tags"]:
                tag_names = ", ".join(data["tags"])
                cmd.set("tag names", of=todo_ref, to=tag_names)
            else:
                cmd.set("tag names", of=todo_ref, to="")

        # Project assignment
        if "project" in data:
            if data["project"]:
                project_ref = self._format_reference(data["project"], "project")
                cmd.move(todo_ref, to=project_ref)
            else:
                # Remove from project (move to inbox)
                cmd.move(todo_ref, to='list "Inbox"')

        # Area assignment
        if "area" in data:
            if data["area"]:
                area_ref = self._format_reference(data["area"], "area")
                cmd.set("area", of=todo_ref, to=area_ref)
            else:
                cmd.set("area", of=todo_ref, to="missing value")

        # When/scheduling
        if "when" in data:
            self._add_scheduling_command(cmd, todo_ref, data["when"])

        # Checklist items (only for creation)
        if "checklist" in data and "newTodo" in todo_ref:
            self._add_checklist_commands(cmd, todo_ref, data["checklist"])

    def _add_status_change_command(
        self, cmd: AppleScriptCommand, todo_ref: str, status: str
    ) -> None:
        """Add command to change todo status."""
        if status == "completed":
            cmd.set("completion date", of=todo_ref, to="(current date)")
        elif status == "canceled":
            cmd.set("cancellation date", of=todo_ref, to="(current date)")
        # Note: "open" status is handled by Things 3 automatically

    def _add_scheduling_command(
        self, cmd: AppleScriptCommand, todo_ref: str, when: str
    ) -> None:
        """Add command to schedule a todo."""
        when_lower = when.lower()

        if when_lower == "tomorrow":
            cmd.move(todo_ref, to='list "Today"')
            cmd.set("due date", of=todo_ref, to="(current date) + (1 * days)")
        elif when_lower in ["today", "upcoming", "anytime", "someday"]:
            list_name = when_lower.capitalize()
            cmd.move(todo_ref, to=f'list "{list_name}"')

    def _add_checklist_commands(
        self, cmd: AppleScriptCommand, todo_ref: str, checklist: List[Union[str, Dict]]
    ) -> None:
        """Add commands to create checklist items."""
        for item in checklist:
            if isinstance(item, dict) and "name" in item:
                item_name = item["name"]
            else:
                item_name = str(item)

            cmd.add_command(
                f"tell {todo_ref} to make new checklist item "
                f"with properties {{name:{self.converter.convert(item_name)}}}"
            )

    def _build_properties_record(self, properties: Dict[str, Any]) -> str:
        """Build an AppleScript record from properties."""
        if not properties:
            return "{}"

        items = []
        for key, value in properties.items():
            value_str = self.converter.convert(value)
            items.append(f"{key}:{value_str}")

        return "{" + ", ".join(items) + "}"


class ProjectCommandBuilder(Things3CommandBuilder):
    """Builder for Things 3 project-related commands."""

    def create_project(self, data: Dict[str, Any]) -> AppleScriptCommand:
        """Build command to create a new project."""
        cmd = AppleScriptCommand().tell("Things3")

        # Build initial properties
        properties = {}

        if "name" in data:
            properties["name"] = data["name"]

        if "notes" in data:
            properties["notes"] = data["notes"]

        if "tags" in data and data["tags"]:
            properties["tag names"] = ", ".join(data["tags"])

        # Create the project
        cmd.add_command(
            "set newProject to make new project with properties "
            + self._build_properties_record(properties)
        )

        # Set additional properties
        self._add_project_property_commands(cmd, "newProject", data)

        # Return the ID
        cmd.return_value("id of newProject")

        return cmd

    def update_project(
        self, project_id: str, data: Dict[str, Any]
    ) -> AppleScriptCommand:
        """Build command to update an existing project."""
        cmd = AppleScriptCommand().tell("Things3")
        project_ref = f'project id "{project_id}"'

        # Basic properties
        if "name" in data:
            cmd.set("name", of=project_ref, to=data["name"])

        if "notes" in data:
            cmd.set("notes", of=project_ref, to=data["notes"])

        # Status changes
        if "status" in data:
            self._add_project_status_command(cmd, project_ref, data["status"])

        # Other properties
        self._add_project_property_commands(cmd, project_ref, data)

        # Return the ID
        cmd.return_value(f'"{project_id}"')

        return cmd

    def _add_project_property_commands(
        self, cmd: AppleScriptCommand, project_ref: str, data: Dict[str, Any]
    ) -> None:
        """Add commands for setting project properties."""
        # Deadline
        if "deadline" in data:
            if data["deadline"]:
                date_expr = self._format_date(data["deadline"])
                if date_expr:
                    cmd.set("deadline", of=project_ref, to=date_expr)
            else:
                cmd.delete(f"deadline of {project_ref}")

        # Tags
        if "tags" in data:
            if data["tags"]:
                tag_names = ", ".join(data["tags"])
                cmd.set("tag names", of=project_ref, to=tag_names)
            else:
                cmd.set("tag names", of=project_ref, to="")

        # Area assignment
        if "area" in data:
            if data["area"]:
                area_ref = self._format_reference(data["area"], "area")
                cmd.set("area", of=project_ref, to=area_ref)
            else:
                cmd.set("area", of=project_ref, to="missing value")

        # When/scheduling
        if "when" in data:
            self._add_project_scheduling_command(cmd, project_ref, data["when"])

    def _add_project_status_command(
        self, cmd: AppleScriptCommand, project_ref: str, status: str
    ) -> None:
        """Add command to change project status."""
        if status == "completed":
            cmd.set("completion date", of=project_ref, to="(current date)")
        elif status == "canceled":
            cmd.set("cancellation date", of=project_ref, to="(current date)")

    def _add_project_scheduling_command(
        self, cmd: AppleScriptCommand, project_ref: str, when: str
    ) -> None:
        """Add command to schedule a project."""
        # Projects can be scheduled similar to todos
        when_lower = when.lower()

        if when_lower in ["anytime", "someday"]:
            # Move to appropriate list
            list_name = when_lower.capitalize()
            cmd.move(project_ref, to=f'list "{list_name}"')


class AreaCommandBuilder(Things3CommandBuilder):
    """Builder for Things 3 area-related commands."""

    def create_area(self, data: Dict[str, Any]) -> AppleScriptCommand:
        """Build command to create a new area."""
        cmd = AppleScriptCommand().tell("Things3")

        # Areas have minimal properties
        properties = {}

        if "name" in data:
            properties["name"] = data["name"]

        # Create the area
        cmd.add_command(
            "set newArea to make new area with properties "
            + self._build_properties_record(properties)
        )

        # Return the ID
        cmd.return_value("id of newArea")

        return cmd

    def update_area(self, area_id: str, data: Dict[str, Any]) -> AppleScriptCommand:
        """Build command to update an existing area."""
        cmd = AppleScriptCommand().tell("Things3")
        area_ref = f'area id "{area_id}"'

        if "name" in data:
            cmd.set("name", of=area_ref, to=data["name"])

        # Return the ID
        cmd.return_value(f'"{area_id}"')

        return cmd


class TagCommandBuilder(Things3CommandBuilder):
    """Builder for Things 3 tag-related commands."""

    def create_tag(self, data: Dict[str, Any]) -> AppleScriptCommand:
        """Build command to create a new tag."""
        cmd = AppleScriptCommand().tell("Things3")

        properties = {}

        if "name" in data:
            properties["name"] = data["name"]

        if "parent" in data:
            # Tags can have parent tags
            parent_ref = self._format_reference(data["parent"], "tag")
            properties["parent tag"] = parent_ref

        # Create the tag
        cmd.add_command(
            "set newTag to make new tag with properties "
            + self._build_properties_record(properties)
        )

        # Return the tag name (tags don't have IDs in Things 3)
        cmd.return_value("name of newTag")

        return cmd
