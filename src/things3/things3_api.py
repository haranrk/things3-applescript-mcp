#!/usr/bin/env python3
"""
Things 3 API Layer - Read-only implementation

This module provides a high-level Python API for reading data from Things 3
via the AppleScript orchestrator.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dateutil import parser as date_parser

from things3.orchestrator import Things3Orchestrator
from applescript.errors import AppleScriptError
from things3.models import (
    Todo,
    Project,
    Area,
    Tag,
    ClassType,
    TodoCreate,
    TodoUpdate,
    ProjectCreate,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)


class Things3API:
    """
    Read-only API for interacting with Things 3.

    This class provides methods for reading Things 3 entities
    like todos, projects, areas, and tags.
    """

    def __init__(self) -> None:
        """Initialize the Things 3 API."""
        self.orchestrator = Things3Orchestrator()

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse an AppleScript date string to Python datetime.

        Args:
            date_str: AppleScript date string (e.g. "Friday, June 20, 2025 at 20:24:26")

        Returns:
            Parsed datetime object or None if parsing fails.
        """
        if not date_str:
            return None

        try:
            return date_parser.parse(date_str)
        except Exception:
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    def _parse_tags(self, tag_names: str) -> List[str]:
        """
        Parse comma-separated tag names into a list.

        Args:
            tag_names: Comma-separated string of tag names

        Returns:
            List of tag names
        """
        if not tag_names:
            return []
        return [tag.strip() for tag in tag_names.split(",") if tag.strip()]

    def _parse_class(self, class_value: str) -> Optional[ClassType]:
        """
        Parse class string to ClassType enum.

        Args:
            class_value: The class value from AppleScript

        Returns:
            ClassType enum value or None
        """
        mapping = {
            "to do": ClassType.TODO,
            "selected to do": ClassType.SELECTED_TODO,
            "project": ClassType.PROJECT,
            "area": ClassType.AREA,
            "tag": ClassType.TAG,
        }
        return mapping.get(class_value)

    def _parse_todo(self, props: Dict[str, Any]) -> Todo:
        """
        Parse AppleScript properties into a Todo object.

        Args:
            props: Dictionary of properties from AppleScript

        Returns:
            Todo object
        """
        # Parse dates - some should be date only, others datetime
        due_date = self._parse_date(props.get("due date"))
        deadline = self._parse_date(props.get("deadline"))
        start_date = self._parse_date(props.get("start date"))

        # Parse required dates (creation_date is required)
        creation_date = self._parse_date(props["creation date"])
        if not creation_date:
            raise ValueError("creation date is required for Todo")
        
        modification_date = (
            self._parse_date(props.get("modification date")) or creation_date
        )
        
        return Todo(
            id=props["id"],
            name=props["name"],
            notes=props.get("notes", ""),
            status=props.get("status"),
            due_date=due_date.date() if due_date else None,
            deadline=deadline.date() if deadline else None,
            start_date=start_date.date() if start_date else None,
            creation_date=creation_date,
            modification_date=modification_date,
            completion_date=self._parse_date(props.get("completion date")),
            cancellation_date=self._parse_date(props.get("cancellation date")),
            activation_date=self._parse_date(props.get("activation date")),
            tags=self._parse_tags(props.get("tag names", "")),
            project=props.get("project"),
            area=props.get("area"),
            contact=props.get("contact"),
            class_=self._parse_class(props.get("class", "")),
        )

    def _parse_project(self, props: Dict[str, Any]) -> Project:
        """
        Parse AppleScript properties into a Project object.

        Args:
            props: Dictionary of properties from AppleScript

        Returns:
            Project object
        """
        # Parse deadline as date only (Projects use "due date" property)
        deadline = self._parse_date(props.get("due date"))

        # Parse required dates
        creation_date = self._parse_date(props["creation date"])
        if not creation_date:
            raise ValueError("creation date is required for Project")
        
        modification_date = (
            self._parse_date(props.get("modification date")) or creation_date
        )
        
        return Project(
            id=props["id"],
            name=props["name"],
            notes=props.get("notes", ""),
            status=props.get("status"),
            creation_date=creation_date,
            modification_date=modification_date,
            completion_date=self._parse_date(props.get("completion date")),
            cancellation_date=self._parse_date(props.get("cancellation date")),
            activation_date=self._parse_date(props.get("activation date")),
            tags=self._parse_tags(props.get("tag names", "")),
            area=props.get("area"),
            deadline=deadline.date() if deadline else None,
            contact=props.get("contact"),
            class_=self._parse_class(props.get("class", "")),
        )

    def _parse_area(self, props: Dict[str, Any]) -> Area:
        """
        Parse AppleScript properties into an Area object.

        Args:
            props: Dictionary of properties from AppleScript

        Returns:
            Area object
        """
        return Area(
            id=props["id"],
            name=props["name"],
            tags=self._parse_tags(props.get("tag names", "")),
            collapsed=props.get("collapsed", False),
            class_=self._parse_class(props.get("class", "")),
        )

    def _parse_tag(self, props: Dict[str, Any]) -> Tag:
        """
        Parse AppleScript properties into a Tag object.

        Args:
            props: Dictionary of properties from AppleScript

        Returns:
            Tag object
        """
        return Tag(
            id=props["id"],
            name=props["name"],
            parent_tag=props.get("parent tag"),
            keyboard_shortcut=props.get("keyboard shortcut"),
            class_=self._parse_class(props.get("class", "")),
        )

    # Todo read operations

    def get_todo(self, todo_id: str) -> Optional[Todo]:
        """
        Get a single todo by ID.

        Args:
            todo_id: The ID of the todo

        Returns:
            Todo object or None if not found

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        try:
            command = f'get properties of to do id "{todo_id}"'
            props = self.orchestrator.execute_command(command)
            if not props:
                return None
            return self._parse_todo(props)
        except AppleScriptError as e:
            if "Can't get to do id" in str(e):
                return None
            raise

    def get_all_todos(self) -> List[Todo]:
        """
        Get all todos.

        Returns:
            List of all todos

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        command = "get properties of to dos"
        props_list = self.orchestrator.execute_command(command)

        if not isinstance(props_list, list):
            props_list = [props_list] if props_list else []

        return [self._parse_todo(props) for props in props_list]

    def get_todos_by_list(self, list_name: str) -> List[Todo]:
        """
        Get todos from a specific list.

        Args:
            list_name: Name of the list ("Inbox", "Today", "Upcoming", "Anytime", "Someday", "Logbook")

        Returns:
            List of todos in the specified list

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        command = f'get properties of to dos of list "{list_name}"'
        props_list = self.orchestrator.list_todos(list_name)

        if not isinstance(props_list, list):
            props_list = [props_list] if props_list else []

        return [self._parse_todo(props) for props in props_list]

    def get_todos_by_project(self, project_id: str) -> List[Todo]:
        """
        Get todos belonging to a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            List of todos in the project

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        command = f'get properties of to dos of project id "{project_id}"'
        props_list = self.orchestrator.execute_command(command)

        if not isinstance(props_list, list):
            props_list = [props_list] if props_list else []

        return [self._parse_todo(props) for props in props_list]

    def get_todos_by_area(self, area_id: str) -> List[Todo]:
        """
        Get todos belonging to a specific area.

        Args:
            area_id: The ID of the area

        Returns:
            List of todos in the area

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        command = f'get properties of to dos of area id "{area_id}"'
        props_list = self.orchestrator.execute_command(command)

        if not isinstance(props_list, list):
            props_list = [props_list] if props_list else []

        return [self._parse_todo(props) for props in props_list]

    def get_todos_by_tag(self, tag_name: str) -> List[Todo]:
        """
        Get todos with a specific tag.

        Args:
            tag_name: Name of the tag

        Returns:
            List of todos with the tag

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        # Things 3 doesn't have direct tag filtering in AppleScript, so we get all todos and filter
        all_todos = self.get_all_todos()
        return [todo for todo in all_todos if todo.tags and tag_name in todo.tags]

    # Project read operations

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a single project by ID.

        Args:
            project_id: The ID of the project

        Returns:
            Project object or None if not found

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        try:
            command = f'get properties of project id "{project_id}"'
            props = self.orchestrator.execute_command(command)
            if not props:
                return None
            return self._parse_project(props)
        except AppleScriptError as e:
            if "Can't get project id" in str(e):
                return None
            raise

    def get_all_projects(self) -> List[Project]:
        """
        Get all projects.

        Returns:
            List of all projects

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        command = "get properties of projects"
        props_list = self.orchestrator.execute_command(command)

        if not isinstance(props_list, list):
            props_list = [props_list] if props_list else []

        return [self._parse_project(props) for props in props_list]

    def get_projects_by_area(self, area_id: str) -> List[Project]:
        """
        Get projects belonging to a specific area.

        Args:
            area_id: The ID of the area

        Returns:
            List of projects in the area

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        # Things 3 doesn't support direct area filtering in AppleScript, so we get all projects and filter
        all_projects = self.get_all_projects()
        # Area references look like "area id ABC123"
        area_ref = f"area id {area_id}"
        return [project for project in all_projects if project.area == area_ref]

    # Area read operations

    def get_area(self, area_id: str) -> Optional[Area]:
        """
        Get a single area by ID.

        Args:
            area_id: The ID of the area

        Returns:
            Area object or None if not found

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        try:
            command = f'get properties of area id "{area_id}"'
            props = self.orchestrator.execute_command(command)
            if not props:
                return None
            return self._parse_area(props)
        except AppleScriptError as e:
            if "Can't get area id" in str(e):
                return None
            raise

    def get_all_areas(self) -> List[Area]:
        """
        Get all areas.

        Returns:
            List of all areas

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        command = "get properties of areas"
        props_list = self.orchestrator.execute_command(command)

        if not isinstance(props_list, list):
            props_list = [props_list] if props_list else []

        return [self._parse_area(props) for props in props_list]

    # Tag read operations

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """
        Get a single tag by ID.

        Args:
            tag_id: The ID of the tag

        Returns:
            Tag object or None if not found

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        try:
            command = f'get properties of tag id "{tag_id}"'
            props = self.orchestrator.execute_command(command)
            if not props:
                return None
            return self._parse_tag(props)
        except AppleScriptError as e:
            if "Can't get tag id" in str(e):
                return None
            raise

    def get_all_tags(self) -> List[Tag]:
        """
        Get all tags.

        Returns:
            List of all tags

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        command = "get properties of tags"
        props_list = self.orchestrator.execute_command(command)

        if not isinstance(props_list, list):
            props_list = [props_list] if props_list else []

        return [self._parse_tag(props) for props in props_list]

    def create_todo(self, todo_data: TodoCreate) -> Todo:
        """
        Create a new todo in Things 3.

        Args:
            todo_data: TodoCreate object with todo properties

        Returns:
            The created Todo object

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        # Extract data from the TodoCreate object
        if hasattr(todo_data, "model_dump"):
            data = todo_data.model_dump(exclude_none=True)
        else:
            data = dict(todo_data)

        # Create the todo using the orchestrator
        todo_id = self.orchestrator.create_todo(data)

        if not todo_id:
            raise AppleScriptError("Failed to create todo - no ID returned")

        # Fetch and return the created todo
        created_todo = self.get_todo(todo_id)
        if not created_todo:
            raise AppleScriptError(
                f"Failed to retrieve created todo with ID: {todo_id}"
            )

        return created_todo

    def update_todo(self, todo_id: str, update_data: TodoUpdate) -> Todo:
        """
        Update an existing todo in Things 3.

        Args:
            todo_id: The ID of the todo to update
            update_data: TodoUpdate object with update properties

        Returns:
            The updated Todo object

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        # Extract data from the TodoUpdate object
        if hasattr(update_data, "model_dump"):
            # For updates, preserve None values that were explicitly set
            all_data = update_data.model_dump(exclude_none=False)
            # Only include fields that were explicitly set
            data = {
                k: v
                for k, v in all_data.items()
                if getattr(update_data, k) is not None
                or k in update_data.model_fields_set
            }
        else:
            data = dict(update_data)

        # Update the todo using the orchestrator
        result_id = self.orchestrator.update_todo(todo_id, data)

        if not result_id or result_id != todo_id:
            raise AppleScriptError(
                f"Failed to update todo - unexpected result: {result_id}"
            )

        # Fetch and return the updated todo
        updated_todo = self.get_todo(todo_id)
        if not updated_todo:
            raise AppleScriptError(
                f"Failed to retrieve updated todo with ID: {todo_id}"
            )

        return updated_todo

    def create_project(self, project_data: ProjectCreate) -> Project:
        """
        Create a new project in Things 3.

        Args:
            project_data: ProjectCreate object with project properties

        Returns:
            The created Project object

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        # Extract data from the ProjectCreate object
        if hasattr(project_data, "model_dump"):
            data = project_data.model_dump(exclude_none=True)
        else:
            data = dict(project_data)

        # Create the project using the orchestrator
        project_id = self.orchestrator.create_project(data)

        if not project_id:
            raise AppleScriptError("Failed to create project - no ID returned")

        # Fetch and return the created project
        created_project = self.get_project(project_id)
        if not created_project:
            raise AppleScriptError(
                f"Failed to retrieve created project with ID: {project_id}"
            )

        return created_project

    def update_project(self, project_id: str, update_data: ProjectUpdate) -> Project:
        """
        Update an existing project in Things 3.

        Args:
            project_id: The ID of the project to update
            update_data: ProjectUpdate object with update properties

        Returns:
            The updated Project object

        Raises:
            AppleScriptError: If the AppleScript execution fails
        """
        # Extract data from the ProjectUpdate object
        if hasattr(update_data, "model_dump"):
            # For updates, preserve None values that were explicitly set
            all_data = update_data.model_dump(exclude_none=False)
            # Only include fields that were explicitly set
            data = {
                k: v
                for k, v in all_data.items()
                if getattr(update_data, k) is not None
                or k in update_data.model_fields_set
            }
        else:
            data = dict(update_data)

        # Update the project using the orchestrator
        result_id = self.orchestrator.update_project(project_id, data)

        if not result_id or result_id != project_id:
            raise AppleScriptError(
                f"Failed to update project - unexpected result: {result_id}"
            )

        # Fetch and return the updated project
        updated_project = self.get_project(project_id)
        if not updated_project:
            raise AppleScriptError(
                f"Failed to retrieve updated project with ID: {project_id}"
            )

        return updated_project
