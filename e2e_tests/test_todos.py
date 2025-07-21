"""
End-to-end tests for Things3 API that run actual AppleScript commands.

This test suite performs real operations against the Things 3 application
to verify that the API works correctly with actual AppleScript execution.
"""

import pytest
from datetime import date, timedelta
from typing import List, Optional

from things3.things3_api import Things3API
from things3.models import Todo, Project, Area, TodoCreate, TodoUpdate, ProjectCreate, ProjectUpdate


def test_get_all_todos(api: Things3API):
    """Test get_all_todos returns results without errors."""
    todos = api.get_all_todos()
    assert isinstance(todos, list)
    print(f"Found {len(todos)} todos")


def test_get_all_projects(api: Things3API):
    """Test get_all_projects returns results without errors."""
    projects = api.get_all_projects()
    assert isinstance(projects, list)
    print(f"Found {len(projects)} projects")


def test_get_all_areas(api: Things3API):
    """Test get_all_areas returns results without errors."""
    areas = api.get_all_areas()
    assert isinstance(areas, list)
    print(f"Found {len(areas)} areas")


def test_todo_create_and_read(api: Things3API):
    """Test creating a todo and reading it back."""
    # Create a todo
    tomorrow = date.today() + timedelta(days=1)
    
    create_data = TodoCreate(
        name="E2E Test Todo - Basic",
        notes="This is a test todo created by the e2e test suite.",
        due_date=tomorrow,
        tags=["e2e-test", "automated"],
        when="today"
    )
    
    created_todo = api.create_todo(create_data)
    
    # Verify creation
    assert created_todo.name == create_data.name
    assert created_todo.notes == create_data.notes
    assert created_todo.due_date == tomorrow
    assert created_todo.id is not None
    
    print(f"Created todo with ID: {created_todo.id}")
    
    # Read the created todo back
    read_todo = api.get_todo(created_todo.id)
    assert read_todo is not None
    assert read_todo.name == create_data.name
    assert read_todo.notes == create_data.notes
    
    print(f"Successfully read back todo: {read_todo.name}")


def test_todo_update_and_read(api: Things3API):
    """Test updating a todo and reading it back."""
    # First create a todo
    create_data = TodoCreate(
        name="E2E Test Todo - For Update",
        notes="This todo will be updated.",
        tags=["e2e-test"],
        when="anytime"
    )
    
    created_todo = api.create_todo(create_data)
    print(f"Created todo for update test: {created_todo.id}")
    
    # Update the todo
    next_week = date.today() + timedelta(days=7)
    
    update_data = TodoUpdate(
        name="E2E Test Todo - Updated",
        notes="Updated notes: This todo has been modified by the e2e test suite.",
        due_date=next_week,
        tags=["e2e-test", "automated", "updated"],
        when="anytime"
    )
    
    updated_todo = api.update_todo(created_todo.id, update_data)
    
    # Verify update
    assert updated_todo.name == update_data.name
    assert updated_todo.notes == update_data.notes
    assert updated_todo.due_date == next_week
    
    print(f"Successfully updated todo: {updated_todo.name}")
    
    # Read the updated todo back
    final_todo = api.get_todo(created_todo.id)
    assert final_todo is not None
    assert final_todo.name == update_data.name
    assert final_todo.notes == update_data.notes
    
    print(f"Successfully read back updated todo: {final_todo.name}")
    
    # Print final details for verification
    print(f"Final todo details:")
    print(f"  ID: {final_todo.id}")
    print(f"  Name: {final_todo.name}")
    print(f"  Notes: {final_todo.notes}")
    print(f"  Due Date: {final_todo.due_date}")
    print(f"  Deadline: {final_todo.deadline}")
    print(f"  Start Date: {final_todo.start_date}")
    print(f"  Tags: {final_todo.tags}")
    print(f"  Status: {final_todo.status}")


def test_project_create_and_read(api: Things3API):
    """Test creating a project and reading it back."""
    # Create a project
    next_week = date.today() + timedelta(days=7)
    
    create_data = ProjectCreate(
        name="E2E Test Project - Basic",
        notes="This is a test project created by the e2e test suite.",
        deadline=next_week,
        tags=["e2e-test", "automated"],
        when="today"
    )
    
    created_project = api.create_project(create_data)
    
    # Verify creation
    assert created_project.name == create_data.name
    assert created_project.notes == create_data.notes
    assert created_project.deadline == next_week
    assert created_project.id is not None
    
    print(f"Created project with ID: {created_project.id}")
    
    # Read the created project back
    read_project = api.get_project(created_project.id)
    assert read_project is not None
    assert read_project.name == create_data.name
    assert read_project.notes == create_data.notes
    
    print(f"Successfully read back project: {read_project.name}")


def test_project_update_and_read(api: Things3API):
    """Test updating a project and reading it back."""
    # First create a project
    create_data = ProjectCreate(
        name="E2E Test Project - For Update",
        notes="This project will be updated.",
        tags=["e2e-test"],
        when="anytime"
    )
    
    created_project = api.create_project(create_data)
    print(f"Created project for update test: {created_project.id}")
    
    # Update the project
    two_weeks = date.today() + timedelta(days=14)
    
    update_data = ProjectUpdate(
        name="E2E Test Project - Updated",
        notes="Updated notes: This project has been modified by the e2e test suite.",
        deadline=two_weeks,
        tags=["e2e-test", "automated", "updated"],
        when="today"
    )
    
    updated_project = api.update_project(created_project.id, update_data)
    
    # Verify update
    assert updated_project.name == update_data.name
    assert updated_project.notes == update_data.notes
    assert updated_project.deadline == two_weeks
    
    print(f"Successfully updated project: {updated_project.name}")
    
    # Read the updated project back
    final_project = api.get_project(created_project.id)
    assert final_project is not None
    assert final_project.name == update_data.name
    assert final_project.notes == update_data.notes
    
    print(f"Successfully read back updated project: {final_project.name}")
    
    # Print final details for verification
    print(f"Final project details:")
    print(f"  ID: {final_project.id}")
    print(f"  Name: {final_project.name}")
    print(f"  Notes: {final_project.notes}")
    print(f"  Deadline: {final_project.deadline}")
    print(f"  Area: {final_project.area}")
    print(f"  Tags: {final_project.tags}")
    print(f"  Status: {final_project.status}")