#!/usr/bin/env python3
"""
Unit tests for Things 3 API.

These tests mock the AppleScript orchestrator to test the API logic
without requiring actual Things 3 application access.
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch

from src.things3_api import Things3API
from src.applescript_orchestrator import AppleScriptError
from src.models import Todo, Project, Area, Tag, Status, ClassType


class TestThings3APIInit:
    """Test API initialization."""

    @patch("src.things3_api.AppleScriptOrchestrator")
    def test_init_creates_orchestrator(self, mock_orchestrator_class):
        """Test that initialization creates orchestrator with correct app name."""
        api = Things3API()
        mock_orchestrator_class.assert_called_once_with(app_name="Things3")
        assert api.orchestrator == mock_orchestrator_class.return_value


class TestThings3APIHelperMethods:
    """Test helper methods for parsing and conversion."""

    @pytest.fixture
    def api(self):
        """Create API instance for testing."""
        return Things3API()

    def test_parse_date_valid(self, api):
        """Test parsing valid AppleScript date strings."""
        date_str = "Friday, June 20, 2025 at 20:24:26"
        result = api._parse_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 20
        assert result.hour == 20
        assert result.minute == 24
        assert result.second == 26

    def test_parse_date_none(self, api):
        """Test parsing None date."""
        assert api._parse_date(None) is None
        assert api._parse_date("") is None

    def test_parse_date_invalid(self, api):
        """Test parsing invalid date string."""
        with patch("src.things3_api.logger") as mock_logger:
            result = api._parse_date("not a date")
            assert result is None
            mock_logger.warning.assert_called()

    def test_parse_tags_empty(self, api):
        """Test parsing empty tag string."""
        assert api._parse_tags("") == []
        assert api._parse_tags(None) == []

    def test_parse_tags_single(self, api):
        """Test parsing single tag."""
        assert api._parse_tags("work") == ["work"]
        assert api._parse_tags("  work  ") == ["work"]

    def test_parse_tags_multiple(self, api):
        """Test parsing multiple comma-separated tags."""
        assert api._parse_tags("work, home, urgent") == ["work", "home", "urgent"]
        assert api._parse_tags("work,home,urgent") == ["work", "home", "urgent"]
        assert api._parse_tags("  work , home , urgent  ") == ["work", "home", "urgent"]

    def test_parse_class_valid(self, api):
        """Test parsing valid class values."""
        assert api._parse_class("to do") == ClassType.TODO
        assert api._parse_class("selected to do") == ClassType.SELECTED_TODO
        assert api._parse_class("project") == ClassType.PROJECT
        assert api._parse_class("area") == ClassType.AREA
        assert api._parse_class("tag") == ClassType.TAG

    def test_parse_class_invalid(self, api):
        """Test parsing invalid class values."""
        assert api._parse_class("unknown") is None
        assert api._parse_class("") is None
        assert api._parse_class(None) is None


class TestThings3APITodoOperations:
    """Test todo-related operations."""

    @pytest.fixture
    def api_with_mock(self):
        """Create API with mocked orchestrator."""
        with patch("src.things3_api.AppleScriptOrchestrator"):
            api = Things3API()
            api.orchestrator = Mock()
            return api

    @pytest.fixture
    def sample_todo_props(self):
        """Sample todo properties from AppleScript."""
        return {
            "id": "test-todo-123",
            "name": "Test Todo",
            "notes": "Some notes",
            "status": "open",
            "due date": "Friday, June 20, 2025 at 20:24:26",
            "deadline": None,
            "creation date": "Thursday, June 19, 2025 at 10:00:00",
            "modification date": "Friday, June 20, 2025 at 20:24:26",
            "completion date": None,
            "cancellation date": None,
            "activation date": "Friday, June 20, 2025 at 00:00:00",
            "tag names": "work, urgent",
            "project": "project id ABC123",
            "area": "area id XYZ789",
            "contact": None,
            "class": "selected to do",
        }

    def test_get_todo_success(self, api_with_mock, sample_todo_props):
        """Test successful todo retrieval."""
        api_with_mock.orchestrator.execute_command.return_value = sample_todo_props

        result = api_with_mock.get_todo("test-todo-123")

        assert isinstance(result, Todo)
        assert result.id == "test-todo-123"
        assert result.name == "Test Todo"
        assert result.notes == "Some notes"
        assert result.status == Status.OPEN
        assert result.class_ == ClassType.SELECTED_TODO
        assert result.tags == ["work", "urgent"]

        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            'get properties of to do id "test-todo-123"'
        )

    def test_get_todo_not_found(self, api_with_mock):
        """Test when todo doesn't exist."""
        api_with_mock.orchestrator.execute_command.side_effect = AppleScriptError(
            "Can't get to do id"
        )

        result = api_with_mock.get_todo("nonexistent")
        assert result is None

    def test_get_todo_other_error(self, api_with_mock):
        """Test when other error occurs."""
        api_with_mock.orchestrator.execute_command.side_effect = AppleScriptError(
            "Some other error"
        )

        with pytest.raises(AppleScriptError):
            api_with_mock.get_todo("test-id")

    def test_get_all_todos_empty(self, api_with_mock):
        """Test getting all todos when none exist."""
        api_with_mock.orchestrator.execute_command.return_value = []

        result = api_with_mock.get_all_todos()
        assert result == []
        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            "get properties of to dos"
        )

    def test_get_all_todos_single(self, api_with_mock, sample_todo_props):
        """Test getting all todos with single result."""
        # AppleScript might return single dict instead of list
        api_with_mock.orchestrator.execute_command.return_value = sample_todo_props

        result = api_with_mock.get_all_todos()
        assert len(result) == 1
        assert result[0].id == "test-todo-123"

    def test_get_all_todos_multiple(self, api_with_mock, sample_todo_props):
        """Test getting all todos with multiple results."""
        todo2 = sample_todo_props.copy()
        todo2["id"] = "test-todo-456"
        todo2["name"] = "Another Todo"

        api_with_mock.orchestrator.execute_command.return_value = [
            sample_todo_props,
            todo2,
        ]

        result = api_with_mock.get_all_todos()
        assert len(result) == 2
        assert result[0].id == "test-todo-123"
        assert result[1].id == "test-todo-456"

    @pytest.mark.parametrize(
        "list_name", ["Inbox", "Today", "Upcoming", "Anytime", "Someday", "Logbook"]
    )
    def test_get_todos_by_list(self, api_with_mock, sample_todo_props, list_name):
        """Test getting todos by list name."""
        api_with_mock.orchestrator.execute_command.return_value = [sample_todo_props]

        result = api_with_mock.get_todos_by_list(list_name)
        assert len(result) == 1
        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            f'get properties of to dos of list "{list_name}"'
        )

    def test_get_todos_by_project(self, api_with_mock, sample_todo_props):
        """Test getting todos by project."""
        api_with_mock.orchestrator.execute_command.return_value = [sample_todo_props]

        result = api_with_mock.get_todos_by_project("project-123")
        assert len(result) == 1
        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            'get properties of to dos of project id "project-123"'
        )

    def test_get_todos_by_area(self, api_with_mock, sample_todo_props):
        """Test getting todos by area."""
        api_with_mock.orchestrator.execute_command.return_value = [sample_todo_props]

        result = api_with_mock.get_todos_by_area("area-123")
        assert len(result) == 1
        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            'get properties of to dos of area id "area-123"'
        )

    def test_get_todos_by_tag(self, api_with_mock, sample_todo_props):
        """Test getting todos by tag."""
        # This method gets all todos and filters
        todo1 = sample_todo_props.copy()
        todo2 = sample_todo_props.copy()
        todo2["id"] = "test-todo-456"
        todo2["tag names"] = "home, personal"

        api_with_mock.orchestrator.execute_command.return_value = [todo1, todo2]

        result = api_with_mock.get_todos_by_tag("work")
        assert len(result) == 1
        assert result[0].id == "test-todo-123"

        result = api_with_mock.get_todos_by_tag("home")
        assert len(result) == 1
        assert result[0].id == "test-todo-456"

        result = api_with_mock.get_todos_by_tag("nonexistent")
        assert len(result) == 0


class TestThings3APIProjectOperations:
    """Test project-related operations."""

    @pytest.fixture
    def api_with_mock(self):
        """Create API with mocked orchestrator."""
        with patch("src.things3_api.AppleScriptOrchestrator"):
            api = Things3API()
            api.orchestrator = Mock()
            return api

    @pytest.fixture
    def sample_project_props(self):
        """Sample project properties from AppleScript."""
        return {
            "id": "project-123",
            "name": "Test Project",
            "notes": "Project notes",
            "status": "open",
            "creation date": "Thursday, June 19, 2025 at 10:00:00",
            "modification date": "Friday, June 20, 2025 at 20:24:26",
            "completion date": None,
            "cancellation date": None,
            "activation date": None,
            "tag names": "important",
            "area": "area id ABC123",
            "deadline": None,
            "contact": None,
            "class": "project",
        }

    def test_get_project_success(self, api_with_mock, sample_project_props):
        """Test successful project retrieval."""
        api_with_mock.orchestrator.execute_command.return_value = sample_project_props

        result = api_with_mock.get_project("project-123")

        assert isinstance(result, Project)
        assert result.id == "project-123"
        assert result.name == "Test Project"
        assert result.class_ == ClassType.PROJECT

        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            'get properties of project id "project-123"'
        )

    def test_get_project_not_found(self, api_with_mock):
        """Test when project doesn't exist."""
        api_with_mock.orchestrator.execute_command.side_effect = AppleScriptError(
            "Can't get project id"
        )

        result = api_with_mock.get_project("nonexistent")
        assert result is None

    def test_get_all_projects(self, api_with_mock, sample_project_props):
        """Test getting all projects."""
        api_with_mock.orchestrator.execute_command.return_value = [sample_project_props]

        result = api_with_mock.get_all_projects()
        assert len(result) == 1
        assert result[0].id == "project-123"
        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            "get properties of projects"
        )

    def test_get_projects_by_area(self, api_with_mock, sample_project_props):
        """Test getting projects by area."""
        project1 = sample_project_props.copy()
        project2 = sample_project_props.copy()
        project2["id"] = "project-456"
        project2["area"] = "area id XYZ789"

        # Method gets all projects and filters
        api_with_mock.orchestrator.execute_command.return_value = [project1, project2]

        # Patch get_all_projects to return our test data
        with patch.object(api_with_mock, "get_all_projects") as mock_get_all:
            mock_get_all.return_value = [
                api_with_mock._parse_project(project1),
                api_with_mock._parse_project(project2),
            ]

            result = api_with_mock.get_projects_by_area("ABC123")
            assert len(result) == 1
            assert result[0].id == "project-123"


class TestThings3APIAreaOperations:
    """Test area-related operations."""

    @pytest.fixture
    def api_with_mock(self):
        """Create API with mocked orchestrator."""
        with patch("src.things3_api.AppleScriptOrchestrator"):
            api = Things3API()
            api.orchestrator = Mock()
            return api

    @pytest.fixture
    def sample_area_props(self):
        """Sample area properties from AppleScript."""
        return {
            "id": "area-123",
            "name": "Test Area",
            "tag names": "work",
            "collapsed": False,
            "class": "area",
        }

    def test_get_area_success(self, api_with_mock, sample_area_props):
        """Test successful area retrieval."""
        api_with_mock.orchestrator.execute_command.return_value = sample_area_props

        result = api_with_mock.get_area("area-123")

        assert isinstance(result, Area)
        assert result.id == "area-123"
        assert result.name == "Test Area"
        assert result.collapsed is False
        assert result.class_ == ClassType.AREA

        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            'get properties of area id "area-123"'
        )

    def test_get_area_not_found(self, api_with_mock):
        """Test when area doesn't exist."""
        api_with_mock.orchestrator.execute_command.side_effect = AppleScriptError(
            "Can't get area id"
        )

        result = api_with_mock.get_area("nonexistent")
        assert result is None

    def test_get_all_areas(self, api_with_mock, sample_area_props):
        """Test getting all areas."""
        api_with_mock.orchestrator.execute_command.return_value = [sample_area_props]

        result = api_with_mock.get_all_areas()
        assert len(result) == 1
        assert result[0].id == "area-123"
        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            "get properties of areas"
        )


class TestThings3APITagOperations:
    """Test tag-related operations."""

    @pytest.fixture
    def api_with_mock(self):
        """Create API with mocked orchestrator."""
        with patch("src.things3_api.AppleScriptOrchestrator"):
            api = Things3API()
            api.orchestrator = Mock()
            return api

    @pytest.fixture
    def sample_tag_props(self):
        """Sample tag properties from AppleScript."""
        return {
            "id": "tag-123",
            "name": "Test Tag",
            "parent tag": None,
            "keyboard shortcut": "t",
            "class": "tag",
        }

    def test_get_tag_success(self, api_with_mock, sample_tag_props):
        """Test successful tag retrieval."""
        api_with_mock.orchestrator.execute_command.return_value = sample_tag_props

        result = api_with_mock.get_tag("tag-123")

        assert isinstance(result, Tag)
        assert result.id == "tag-123"
        assert result.name == "Test Tag"
        assert result.keyboard_shortcut == "t"
        assert result.class_ == ClassType.TAG

        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            'get properties of tag id "tag-123"'
        )

    def test_get_tag_not_found(self, api_with_mock):
        """Test when tag doesn't exist."""
        api_with_mock.orchestrator.execute_command.side_effect = AppleScriptError(
            "Can't get tag id"
        )

        result = api_with_mock.get_tag("nonexistent")
        assert result is None

    def test_get_all_tags(self, api_with_mock, sample_tag_props):
        """Test getting all tags."""
        api_with_mock.orchestrator.execute_command.return_value = [sample_tag_props]

        result = api_with_mock.get_all_tags()
        assert len(result) == 1
        assert result[0].id == "tag-123"
        api_with_mock.orchestrator.execute_command.assert_called_once_with(
            "get properties of tags"
        )


class TestThings3APIParsingMethods:
    """Test parsing methods for different entity types."""

    @pytest.fixture
    def api(self):
        """Create API instance for testing."""
        return Things3API()

    def test_parse_todo_complete(self, api):
        """Test parsing todo with all fields."""
        props = {
            "id": "todo-123",
            "name": "Complete Todo",
            "notes": "Detailed notes\nMultiple lines",
            "status": "open",
            "due date": "Saturday, June 21, 2025 at 15:00:00",
            "deadline": "Sunday, June 22, 2025 at 23:59:59",
            "creation date": "Thursday, June 19, 2025 at 10:00:00",
            "modification date": "Friday, June 20, 2025 at 20:24:26",
            "completion date": None,
            "cancellation date": None,
            "activation date": "Friday, June 20, 2025 at 00:00:00",
            "tag names": "urgent, work, @office",
            "project": "project id PROJ123",
            "area": "area id AREA456",
            "contact": "john@example.com",
            "class": "selected to do",
        }

        result = api._parse_todo(props)

        assert result.id == "todo-123"
        assert result.name == "Complete Todo"
        assert result.notes == "Detailed notes\nMultiple lines"
        assert result.status == "open"
        assert result.tags == ["urgent", "work", "@office"]
        assert result.project == "project id PROJ123"
        assert result.area == "area id AREA456"
        assert result.contact == "john@example.com"
        assert result.class_ == ClassType.SELECTED_TODO
        assert isinstance(result.due_date, date)
        assert isinstance(result.deadline, date)

    def test_parse_todo_minimal(self, api):
        """Test parsing todo with minimal fields."""
        props = {
            "id": "todo-min",
            "name": "Minimal Todo",
            "notes": "",
            "status": "open",
            "due date": None,
            "deadline": None,
            "creation date": "Thursday, June 19, 2025 at 10:00:00",
            "modification date": None,  # Will use creation date as fallback
            "completion date": None,
            "cancellation date": None,
            "activation date": None,
            "tag names": "",
            "project": None,
            "area": None,
            "contact": None,
            "class": "to do",
        }

        result = api._parse_todo(props)

        assert result.id == "todo-min"
        assert result.name == "Minimal Todo"
        assert result.notes == ""
        assert result.tags == []
        assert result.project is None
        assert result.area is None
        assert result.due_date is None
        assert result.deadline is None
        assert result.class_ == ClassType.TODO

    def test_parse_project_complete(self, api):
        """Test parsing project with all fields."""
        props = {
            "id": "proj-123",
            "name": "Complete Project",
            "notes": "Project description",
            "status": "open",
            "creation date": "Monday, June 1, 2025 at 09:00:00",
            "modification date": "Friday, June 20, 2025 at 18:30:00",
            "completion date": None,
            "cancellation date": None,
            "activation date": "Tuesday, June 2, 2025 at 08:00:00",
            "tag names": "quarterly, high-priority",
            "area": "area id WORK123",
            "deadline": "Monday, June 30, 2025 at 17:00:00",
            "contact": "team@company.com",
            "class": "project",
        }

        result = api._parse_project(props)

        assert result.id == "proj-123"
        assert result.name == "Complete Project"
        assert result.notes == "Project description"
        assert result.tags == ["quarterly", "high-priority"]
        assert result.area == "area id WORK123"
        assert result.class_ == ClassType.PROJECT
        assert isinstance(result.deadline, date)

    def test_parse_area_complete(self, api):
        """Test parsing area with all fields."""
        props = {
            "id": "area-789",
            "name": "Work Area",
            "tag names": "professional",
            "collapsed": True,
            "class": "area",
        }

        result = api._parse_area(props)

        assert result.id == "area-789"
        assert result.name == "Work Area"
        assert result.tags == ["professional"]
        assert result.collapsed is True
        assert result.class_ == ClassType.AREA

    def test_parse_tag_complete(self, api):
        """Test parsing tag with all fields."""
        props = {
            "id": "tag-abc",
            "name": "Important",
            "parent tag": "tag-parent-123",
            "keyboard shortcut": "i",
            "class": "tag",
        }

        result = api._parse_tag(props)

        assert result.id == "tag-abc"
        assert result.name == "Important"
        assert result.parent_tag == "tag-parent-123"
        assert result.keyboard_shortcut == "i"
        assert result.class_ == ClassType.TAG

    def test_parse_tag_minimal(self, api):
        """Test parsing tag with minimal fields."""
        props = {
            "id": "tag-min",
            "name": "Simple Tag",
            "parent tag": None,
            "keyboard shortcut": None,
            "class": "tag",
        }

        result = api._parse_tag(props)

        assert result.id == "tag-min"
        assert result.name == "Simple Tag"
        assert result.parent_tag is None
        assert result.keyboard_shortcut is None
