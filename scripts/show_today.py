#!/usr/bin/env python3
"""
Show today's todos in a pretty format using Rich.

This script fetches all todos from the "Today" list in Things 3
and displays them in a beautiful, formatted table.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the src directory to the path so we can import our modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from things3.things3_api import Things3API


def format_due_date(due_date):
    """Format due date for display."""
    if not due_date:
        return "[dim]No due date[/dim]"
    
    today = datetime.now().date()
    if due_date == today:
        return "[bold red]Today[/bold red]"
    elif due_date < today:
        return f"[bold red]Overdue ({due_date})[/bold red]"
    else:
        return f"[yellow]{due_date}[/yellow]"


def format_tags(tags):
    """Format tags for display."""
    if not tags:
        return ""
    return " ".join([f"[blue]#{tag}[/blue]" for tag in tags])


def extract_id_from_reference(reference):
    """Extract ID from Things 3 reference string."""
    if not reference:
        return None
    
    # References are in format "project id ABC123" or "area id XYZ789"
    if " id " in reference:
        return reference.split(" id ")[1]
    return None


def get_project_name(api, project_ref, project_cache):
    """Get project name from reference, with caching."""
    if not project_ref:
        return "[dim]No project[/dim]"
    
    project_id = extract_id_from_reference(project_ref)
    if not project_id:
        return f"[green]{project_ref}[/green]"
    
    # Check cache first
    if project_id in project_cache:
        return project_cache[project_id]
    
    # Fetch from API
    try:
        project = api.get_project(project_id)
        if project:
            result = f"[green]{project.name}[/green]"
        else:
            result = f"[green]{project_id}[/green]"
    except Exception:
        result = f"[green]{project_id}[/green]"
    
    project_cache[project_id] = result
    return result


def get_area_name(api, area_ref, area_cache):
    """Get area name from reference, with caching."""
    if not area_ref:
        return "[dim]No area[/dim]"
    
    area_id = extract_id_from_reference(area_ref)
    if not area_id:
        return f"[magenta]{area_ref}[/magenta]"
    
    # Check cache first
    if area_id in area_cache:
        return area_cache[area_id]
    
    # Fetch from API
    try:
        area = api.get_area(area_id)
        if area:
            result = f"[magenta]{area.name}[/magenta]"
        else:
            result = f"[magenta]{area_id}[/magenta]"
    except Exception:
        result = f"[magenta]{area_id}[/magenta]"
    
    area_cache[area_id] = result
    return result


def main():
    """Main function to display today's todos."""
    console = Console()
    
    api = Things3API()
        
    console.print("[bold]Fetching today's todos...[/bold]")
    todos = api.get_todos_by_list("Today")
    
    if not todos:
        console.print(Panel(
            "[yellow]No todos in Today list![/yellow]",
            title="Today's Todos",
            border_style="yellow"
        ))
        return
    
    # Create caches for projects and areas to avoid repeated API calls
    project_cache = {}
    area_cache = {}
    
    # Create a table for the todos
    table = Table(
        title=f"Today's Todos ({len(todos)} items)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Todo", style="white", width=35)
    table.add_column("Due Date", style="cyan", width=12)
    table.add_column("Project", style="green", width=18)
    table.add_column("Area", style="magenta", width=18)
    table.add_column("Tags", style="blue", width=15)
    table.add_column("Status", style="yellow", width=10)
    
    # Add todos to the table
    for todo in todos:
        # Format the todo name with notes if available
        todo_name = todo.name
        if todo.notes:
            todo_name += f"\n[dim]{todo.notes[:50]}{'...' if len(todo.notes) > 50 else ''}[/dim]"
        
        # Format status with emoji
        status_display = {
            "open": "📝 Open",
            "completed": "✅ Done",
            "canceled": "❌ Canceled"
        }.get(todo.status.value if todo.status else "open", "📝 Open")
        
        table.add_row(
            todo_name,
            format_due_date(todo.due_date),
            get_project_name(api, todo.project, project_cache),
            get_area_name(api, todo.area, area_cache),
            format_tags(todo.tags),
            status_display
        )
    
    # Display the table
    console.print(table)
    
    # Show summary statistics
    completed_count = sum(1 for todo in todos if todo.status and todo.status.value == "completed")
    open_count = len(todos) - completed_count
    
    summary_text = f"[green]Open: {open_count}[/green] | [blue]Completed: {completed_count}[/blue]"
    console.print(Panel(
        summary_text,
        title="Summary",
        border_style="cyan"
    ))
        

if __name__ == "__main__":
    main()