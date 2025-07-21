#!/usr/bin/env python3
"""MCP Server for Things 3."""

import signal
import sys
from typing import List, Optional, Dict, Any

from fastmcp import FastMCP
from pydantic import Field

from things3.things3_api import Things3API
from things3.models import TodoCreate, TodoUpdate, ProjectCreate, ProjectUpdate

# Create the MCP server
mcp = FastMCP(name="things3-mcp")

# Create Things3 API instance
api = Things3API()


# Todo operations
@mcp.tool
async def get_todo(
    todo_id: str = Field(description="The ID of the todo to retrieve"),
) -> Optional[Dict[str, Any]]:
    """Get a single todo by ID.

    Returns the todo if found, or None if the todo doesn't exist.
    """
    todo = api.get_todo(todo_id)
    return todo.model_dump() if todo else None


@mcp.tool
async def get_all_todos() -> List[Dict[str, Any]]:
    """Get all todos from Things 3.

    Returns a list of all todos in the system.
    """
    todos = api.get_all_todos()
    return [todo.model_dump() for todo in todos]


@mcp.tool
async def get_todos_by_list(
    list_name: str = Field(
        description="Name of the list: Inbox, Today, Upcoming, Anytime, Someday, or Logbook"
    ),
) -> List[Dict[str, Any]]:
    """Get todos from a specific list.

    Valid list names are: Inbox, Today, Upcoming, Anytime, Someday, Logbook
    """
    todos = api.get_todos_by_list(list_name)
    return [todo.model_dump() for todo in todos]


@mcp.tool
async def get_todos_by_project(
    project_id: str = Field(description="The ID of the project"),
) -> List[Dict[str, Any]]:
    """Get todos belonging to a specific project."""
    todos = api.get_todos_by_project(project_id)
    return [todo.model_dump() for todo in todos]


@mcp.tool
async def get_todos_by_area(
    area_id: str = Field(description="The ID of the area"),
) -> List[Dict[str, Any]]:
    """Get todos belonging to a specific area."""
    todos = api.get_todos_by_area(area_id)
    return [todo.model_dump() for todo in todos]


@mcp.tool
async def get_todos_by_tag(
    tag_name: str = Field(description="Name of the tag"),
) -> List[Dict[str, Any]]:
    """Get todos with a specific tag."""
    todos = api.get_todos_by_tag(tag_name)
    return [todo.model_dump() for todo in todos]


@mcp.tool
async def create_todo(
    name: str = Field(description="The title/name of the todo"),
    notes: Optional[str] = Field(
        default=None, description="Notes or description for the todo"
    ),
    due_date: Optional[str] = Field(
        default=None, description="Due date in YYYY-MM-DD format"
    ),
    deadline: Optional[str] = Field(
        default=None, description="Deadline in YYYY-MM-DD format"
    ),
    start_date: Optional[str] = Field(
        default=None, description="Start date in YYYY-MM-DD format"
    ),
    tags: Optional[List[str]] = Field(
        default=None, description="List of tag names to apply to the todo"
    ),
    project_id: Optional[str] = Field(
        default=None, description="ID of the project to assign the todo to"
    ),
    area_id: Optional[str] = Field(
        default=None, description="ID of the area to assign the todo to"
    ),
    when: Optional[str] = Field(
        default=None,
        description="When to schedule: 'today', 'tomorrow', 'anytime', 'someday', etc.",
    ),
) -> Dict[str, Any]:
    """Create a new todo in Things 3.

    Creates a new todo with the specified properties and returns the created todo.
    """
    # Convert date strings to date objects if provided
    from datetime import datetime

    parsed_due_date = None
    parsed_deadline = None
    parsed_start_date = None

    if due_date:
        parsed_due_date = datetime.fromisoformat(due_date).date()
    if deadline:
        parsed_deadline = datetime.fromisoformat(deadline).date()
    if start_date:
        parsed_start_date = datetime.fromisoformat(start_date).date()

    # Build project/area references if provided
    project_ref = f"project id {project_id}" if project_id else None
    area_ref = f"area id {area_id}" if area_id else None

    # Create TodoCreate object
    todo_data = TodoCreate(
        name=name,
        notes=notes,
        due_date=parsed_due_date,
        deadline=parsed_deadline,
        start_date=parsed_start_date,
        tags=tags,
        project=project_ref,
        area=area_ref,
        when=when,
    )

    # Create the todo
    created_todo = api.create_todo(todo_data)
    return created_todo.model_dump()


@mcp.tool
async def update_todo(
    todo_id: str = Field(description="The ID of the todo to update"),
    name: Optional[str] = Field(
        default=None, description="New title/name for the todo"
    ),
    notes: Optional[str] = Field(
        default=None, description="New notes or description for the todo"
    ),
    due_date: Optional[str] = Field(
        default=None, description="New due date in YYYY-MM-DD format"
    ),
    tags: Optional[List[str]] = Field(
        default=None, description="New list of tag names to apply to the todo"
    ),
    project_id: Optional[str] = Field(
        default=None, description="ID of the project to assign the todo to"
    ),
    area_id: Optional[str] = Field(
        default=None, description="ID of the area to assign the todo to"
    ),
    when: Optional[str] = Field(
        default=None,
        description="When to schedule: 'today', 'tomorrow', 'anytime', 'someday', etc.",
    ),
    status: Optional[str] = Field(
        default=None, description="Status: 'open', 'completed', or 'canceled'"
    ),
) -> Dict[str, Any]:
    """Update an existing todo in Things 3.

    Updates the specified todo with the provided properties and returns the updated todo.
    Only provided fields will be updated; others remain unchanged.
    """
    # Convert date strings to date objects if provided
    from datetime import datetime

    parsed_due_date = None

    if due_date is not None:
        if due_date:  # Non-empty string
            parsed_due_date = datetime.fromisoformat(due_date).date()
        # Empty string or None will clear the date

    # Build project/area references if provided
    project_ref = None
    if project_id is not None:
        project_ref = f"project id {project_id}" if project_id else None

    area_ref = None
    if area_id is not None:
        area_ref = f"area id {area_id}" if area_id else None

    # Create TodoUpdate object with only provided fields
    update_fields = {}
    if name is not None:
        update_fields["name"] = name
    if notes is not None:
        update_fields["notes"] = notes
    if due_date is not None:
        update_fields["due_date"] = parsed_due_date
    if tags is not None:
        update_fields["tags"] = tags
    if project_ref is not None:
        update_fields["project"] = project_ref
    if area_ref is not None:
        update_fields["area"] = area_ref
    if when is not None:
        update_fields["when"] = when
    if status is not None:
        update_fields["status"] = status

    update_data = TodoUpdate(**update_fields)

    # Update the todo
    updated_todo = api.update_todo(todo_id, update_data)
    return updated_todo.model_dump()


# Project operations
@mcp.tool
async def get_project(
    project_id: str = Field(description="The ID of the project to retrieve"),
) -> Optional[Dict[str, Any]]:
    """Get a single project by ID.

    Returns the project if found, or None if the project doesn't exist.
    """
    project = api.get_project(project_id)
    return project.model_dump() if project else None


@mcp.tool
async def get_all_projects() -> List[Dict[str, Any]]:
    """Get all projects from Things 3.

    Returns a list of all projects in the system.
    """
    projects = api.get_all_projects()
    return [project.model_dump() for project in projects]


@mcp.tool
async def get_projects_by_area(
    area_id: str = Field(description="The ID of the area"),
) -> List[Dict[str, Any]]:
    """Get projects belonging to a specific area."""
    projects = api.get_projects_by_area(area_id)
    return [project.model_dump() for project in projects]


@mcp.tool
async def create_project(
    name: str = Field(description="The title/name of the project"),
    notes: Optional[str] = Field(
        default=None, description="Notes or description for the project"
    ),
    deadline: Optional[str] = Field(
        default=None, description="Deadline in YYYY-MM-DD format"
    ),
    tags: Optional[List[str]] = Field(
        default=None, description="List of tag names to apply to the project"
    ),
    area_id: Optional[str] = Field(
        default=None, description="ID of the area to assign the project to"
    ),
    when: Optional[str] = Field(
        default=None,
        description="When to schedule: 'anytime', 'someday', etc.",
    ),
) -> Dict[str, Any]:
    """Create a new project in Things 3.

    Creates a new project with the specified properties and returns the created project.
    """
    # Convert date strings to date objects if provided
    from datetime import datetime

    parsed_deadline = None

    if deadline:
        parsed_deadline = datetime.fromisoformat(deadline).date()

    # Build area reference if provided
    area_ref = f"area id {area_id}" if area_id else None

    # Create ProjectCreate object
    project_data = ProjectCreate(
        name=name,
        notes=notes,
        deadline=parsed_deadline,
        tags=tags,
        area=area_ref,
        when=when,
    )

    # Create the project
    created_project = api.create_project(project_data)
    return created_project.model_dump()


@mcp.tool
async def update_project(
    project_id: str = Field(description="The ID of the project to update"),
    name: Optional[str] = Field(
        default=None, description="New title/name for the project"
    ),
    notes: Optional[str] = Field(
        default=None, description="New notes or description for the project"
    ),
    deadline: Optional[str] = Field(
        default=None, description="New deadline in YYYY-MM-DD format"
    ),
    tags: Optional[List[str]] = Field(
        default=None, description="New list of tag names to apply to the project"
    ),
    area_id: Optional[str] = Field(
        default=None, description="ID of the area to assign the project to"
    ),
    when: Optional[str] = Field(
        default=None,
        description="When to schedule: 'anytime', 'someday', etc.",
    ),
    status: Optional[str] = Field(
        default=None, description="Status: 'open', 'completed', or 'canceled'"
    ),
) -> Dict[str, Any]:
    """Update an existing project in Things 3.

    Updates the specified project with the provided properties and returns the updated project.
    Only provided fields will be updated; others remain unchanged.
    """
    # Convert date strings to date objects if provided
    from datetime import datetime

    parsed_deadline = None

    if deadline is not None:
        if deadline:  # Non-empty string
            parsed_deadline = datetime.fromisoformat(deadline).date()
        # Empty string or None will clear the date

    # Build area reference if provided
    area_ref = None
    if area_id is not None:
        area_ref = f"area id {area_id}" if area_id else None

    # Create ProjectUpdate object with only provided fields
    update_fields = {}
    if name is not None:
        update_fields["name"] = name
    if notes is not None:
        update_fields["notes"] = notes
    if deadline is not None:
        update_fields["deadline"] = parsed_deadline
    if tags is not None:
        update_fields["tags"] = tags
    if area_ref is not None:
        update_fields["area"] = area_ref
    if when is not None:
        update_fields["when"] = when
    if status is not None:
        update_fields["status"] = status

    update_data = ProjectUpdate(**update_fields)

    # Update the project
    updated_project = api.update_project(project_id, update_data)
    return updated_project.model_dump()


# Area operations
@mcp.tool
async def get_area(
    area_id: str = Field(description="The ID of the area to retrieve"),
) -> Optional[Dict[str, Any]]:
    """Get a single area by ID.

    Returns the area if found, or None if the area doesn't exist.
    """
    area = api.get_area(area_id)
    return area.model_dump() if area else None


@mcp.tool
async def get_all_areas() -> List[Dict[str, Any]]:
    """Get all areas from Things 3.

    Returns a list of all areas in the system.
    """
    areas = api.get_all_areas()
    return [area.model_dump() for area in areas]


# Tag operations
@mcp.tool
async def get_tag(
    tag_id: str = Field(description="The ID of the tag to retrieve"),
) -> Optional[Dict[str, Any]]:
    """Get a single tag by ID.

    Returns the tag if found, or None if the tag doesn't exist.
    """
    tag = api.get_tag(tag_id)
    return tag.model_dump() if tag else None


@mcp.tool
async def get_all_tags() -> List[Dict[str, Any]]:
    """Get all tags from Things 3.

    Returns a list of all tags in the system.
    """
    tags = api.get_all_tags()
    return [tag.model_dump() for tag in tags]


def signal_handler(signum, frame):
    """Handle SIGINT gracefully."""
    print("\nShutting down server gracefully...", file=sys.stderr)
    sys.exit(0)


def main():
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    try:
        mcp.run(transport="streamable-http", port=8000)
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
