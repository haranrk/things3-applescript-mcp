#!/usr/bin/env python3
"""
Unit tests for AppleScript Orchestrator.

These tests focus on verifying the accuracy of parsing raw AppleScript output
without actually executing AppleScript commands.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.applescript_orchestrator import AppleScriptOrchestrator, AppleScriptError


class TestAppleScriptOrchestrator:
    """Test cases for the AppleScript Orchestrator."""
    
    @pytest.fixture
    def orchestrator(self) -> AppleScriptOrchestrator:
        """Create an orchestrator instance for testing."""
        return AppleScriptOrchestrator("Things3")
    
    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"
    
    def load_fixture(self, fixtures_dir: Path, filename: str) -> str:
        """Load a fixture file content."""
        with open(fixtures_dir / filename, 'r') as f:
            return f.read()
    
    # Test initialization
    def test_init(self) -> None:
        """Test orchestrator initialization."""
        orch = AppleScriptOrchestrator("TestApp")
        assert orch.app_name == "TestApp"
    
    # Test value conversion (_to_applescript_value)
    def test_to_applescript_value_none(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test None conversion."""
        assert orchestrator._to_applescript_value(None) == "missing value"
    
    def test_to_applescript_value_bool(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test boolean conversion."""
        assert orchestrator._to_applescript_value(True) == "true"
        assert orchestrator._to_applescript_value(False) == "false"
    
    def test_to_applescript_value_numbers(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test numeric conversion."""
        assert orchestrator._to_applescript_value(42) == "42"
        assert orchestrator._to_applescript_value(3.14) == "3.14"
    
    def test_to_applescript_value_string(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test string conversion."""
        assert orchestrator._to_applescript_value("hello") == '"hello"'
        assert orchestrator._to_applescript_value("") == '""'
    
    def test_to_applescript_value_list(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test list conversion."""
        assert orchestrator._to_applescript_value([1, 2, 3]) == "{1, 2, 3}"
        assert orchestrator._to_applescript_value(["a", "b"]) == '{"a", "b"}'
        assert orchestrator._to_applescript_value([]) == "{}"
    
    def test_to_applescript_value_dict(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test dictionary conversion."""
        assert orchestrator._to_applescript_value({"key": "value"}) == '{key:"value"}'
        assert orchestrator._to_applescript_value({"a": 1, "b": 2}) == '{a:1, b:2}'
    
    # Test result parsing (_parse_result)
    def test_parse_result_empty(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing empty result."""
        assert orchestrator._parse_result("") is None
        # Whitespace-only strings are returned as-is
        assert orchestrator._parse_result("   ") == "   "
    
    def test_parse_result_boolean(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing boolean values."""
        assert orchestrator._parse_result("true") is True
        assert orchestrator._parse_result("false") is False
        assert orchestrator._parse_result("TRUE") is True
        assert orchestrator._parse_result("FALSE") is False
    
    def test_parse_result_numeric(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing numeric values."""
        assert orchestrator._parse_result("42") == 42
        assert orchestrator._parse_result("3.14") == 3.14
        assert orchestrator._parse_result("-10") == -10
    
    def test_parse_result_string(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing string values."""
        assert orchestrator._parse_result("hello world") == "hello world"
    
    def test_parse_result_structured_single(self, orchestrator: AppleScriptOrchestrator, fixtures_dir: Path) -> None:
        """Test parsing single structured record."""
        raw_data = self.load_fixture(fixtures_dir, "single_todo_raw.txt")
        result = orchestrator._parse_result(raw_data)
        
        assert isinstance(result, dict)
        assert result["id"] == "7x1hyC1h5a1vyonNyqPqs2"
        assert result["name"] == "reply to joan "
        assert result["status"] == "open"
        assert result["notes"] == ""
        assert result["project"] is None  # missing value
        assert result["area"] is None  # missing value
    
    def test_parse_result_structured_multiple(self, orchestrator: AppleScriptOrchestrator, fixtures_dir: Path) -> None:
        """Test parsing multiple structured records."""
        raw_data = self.load_fixture(fixtures_dir, "list_todos_raw.txt")
        result = orchestrator._parse_result(raw_data)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check first todo
        first_todo = result[0]
        assert isinstance(first_todo, dict)
        assert "id" in first_todo
        assert "name" in first_todo
        assert "status" in first_todo
    
    # Test structured value parsing (_parse_structured_value)
    def test_parse_structured_value_missing(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing missing value."""
        assert orchestrator._parse_structured_value("missing value") is None
    
    def test_parse_structured_value_boolean(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing boolean in structured value."""
        assert orchestrator._parse_structured_value("true") is True
        assert orchestrator._parse_structured_value("false") is False
    
    def test_parse_structured_value_quoted_string(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing quoted strings."""
        assert orchestrator._parse_structured_value('"hello world"') == "hello world"
        assert orchestrator._parse_structured_value('""') == ""
    
    def test_parse_structured_value_date(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing date values."""
        date_str = 'date "Friday, June 20, 2025 at 20:24:30"'
        assert orchestrator._parse_structured_value(date_str) == "Friday, June 20, 2025 at 20:24:30"
    
    def test_parse_structured_value_object_reference(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing object references."""
        project_ref = 'project id "ABC123" of application "Things3"'
        assert orchestrator._parse_structured_value(project_ref) == "project id ABC123"
        
        area_ref = 'area id "XYZ789" of application "Things3"'
        assert orchestrator._parse_structured_value(area_ref) == "area id XYZ789"
    
    def test_parse_structured_value_class(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test parsing class values."""
        assert orchestrator._parse_structured_value("selected to do") == "selected to do"
    
    # Test key-value pair splitting (_split_record_pairs)
    def test_split_record_pairs_simple(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test splitting simple key-value pairs."""
        content = 'key1:value1, key2:value2, key3:value3'
        pairs = orchestrator._split_record_pairs(content)
        assert pairs == ['key1:value1', 'key2:value2', 'key3:value3']
    
    def test_split_record_pairs_with_quotes(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test splitting pairs with quoted values."""
        content = 'name:"John, Doe", age:30, city:"New York"'
        pairs = orchestrator._split_record_pairs(content)
        assert pairs == ['name:"John, Doe"', 'age:30', 'city:"New York"']
    
    def test_split_record_pairs_nested(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test splitting pairs with nested structures."""
        content = 'simple:value, nested:{a:1, b:2}, another:test'
        pairs = orchestrator._split_record_pairs(content)
        assert pairs == ['simple:value', 'nested:{a:1, b:2}', 'another:test']
    
    # Test key-value separator finding (_find_key_value_separator)
    def test_find_key_value_separator(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test finding colon separator."""
        assert orchestrator._find_key_value_separator('key:value') == 3
        assert orchestrator._find_key_value_separator('key:"value:with:colons"') == 3
        assert orchestrator._find_key_value_separator('no separator') == -1
    
    # Test command execution with mocked subprocess
    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run: MagicMock, orchestrator: AppleScriptOrchestrator) -> None:
        """Test successful command execution."""
        mock_run.return_value = MagicMock(
            stdout="true",
            stderr="",
            returncode=0
        )
        
        result = orchestrator.execute_command("test command")
        assert result is True
        
        # Verify the command was wrapped in tell block
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "osascript" in args
        assert "-s" in args
        assert "s" in args
    
    @patch('subprocess.run')
    def test_execute_command_raw_output(self, mock_run: MagicMock, orchestrator: AppleScriptOrchestrator) -> None:
        """Test command execution with raw output."""
        raw_output = "{test:value}"
        mock_run.return_value = MagicMock(
            stdout=raw_output,
            stderr="",
            returncode=0
        )
        
        result = orchestrator.execute_command("test command", return_raw=True)
        assert result == raw_output
    
    @patch('subprocess.run')
    def test_execute_command_error(self, mock_run: MagicMock, orchestrator: AppleScriptOrchestrator) -> None:
        """Test command execution error handling."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["osascript"], stderr="Script error"
        )
        
        with pytest.raises(AppleScriptError) as exc_info:
            orchestrator.execute_command("failing command")
        
        assert "Script error" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_execute_raw_script(self, mock_run: MagicMock, orchestrator: AppleScriptOrchestrator) -> None:
        """Test raw script execution."""
        mock_run.return_value = MagicMock(
            stdout="42",
            stderr="",
            returncode=0
        )
        
        result = orchestrator.execute_raw_script('display dialog "test"')
        assert result == 42
    
    # Test tell block building
    def test_build_tell_block(self, orchestrator: AppleScriptOrchestrator) -> None:
        """Test building tell application block."""
        commands = "get properties of windows"
        result = orchestrator._build_tell_block(commands)
        
        expected = 'tell application "Things3"\nget properties of windows\nend tell'
        assert result == expected
    
    # Integration tests with real fixture data
    def test_parse_list_projects(self, orchestrator: AppleScriptOrchestrator, fixtures_dir: Path) -> None:
        """Test parsing list of projects from fixture."""
        raw_data = self.load_fixture(fixtures_dir, "list_projects_raw.txt")
        result = orchestrator._parse_result(raw_data)
        
        assert isinstance(result, list)
        if len(result) > 0:
            project = result[0]
            assert "id" in project
            assert "name" in project
            assert "status" in project
    
    def test_parse_list_areas(self, orchestrator, fixtures_dir):
        """Test parsing list of areas from fixture."""
        raw_data = self.load_fixture(fixtures_dir, "list_areas_raw.txt")
        result = orchestrator._parse_result(raw_data)
        
        assert isinstance(result, list)
        if len(result) > 0:
            area = result[0]
            assert "id" in area
            assert "name" in area
    
    def test_parse_single_project(self, orchestrator, fixtures_dir):
        """Test parsing single project from fixture."""
        raw_data = self.load_fixture(fixtures_dir, "single_project_raw.txt")
        result = orchestrator._parse_result(raw_data)
        
        assert isinstance(result, dict)
        assert "id" in result
        assert "name" in result
        assert "status" in result
    
    def test_parse_single_area(self, orchestrator, fixtures_dir):
        """Test parsing single area from fixture."""
        raw_data = self.load_fixture(fixtures_dir, "single_area_raw.txt")
        result = orchestrator._parse_result(raw_data)
        
        assert isinstance(result, dict)
        assert "id" in result
        assert "name" in result


# Additional test for subprocess import
def test_subprocess_import():
    """Ensure subprocess is imported for mocking."""
    import subprocess
    assert subprocess is not None