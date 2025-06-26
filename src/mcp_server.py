#!/usr/bin/env python3
"""MCP Server for Things 3."""

from typing import List, Optional, Dict, Any

from fastmcp import FastMCP
from pydantic import Field

from .things3_api import Things3API

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


if __name__ == "__main__":
    mcp.run()
