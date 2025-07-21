"""
Unit tests for AppleScript core engine.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

from applescript.core import AppleScriptEngine
from applescript.errors import (
    AppleScriptExecutionError,
    AppleScriptTimeoutError,
)


class TestAppleScriptEngine:
    """Test cases for the AppleScript Engine."""

    @pytest.fixture
    def engine(self) -> AppleScriptEngine:
        """Create an engine instance for testing."""
        return AppleScriptEngine()

    def test_init_default_timeout(self) -> None:
        """Test engine initialization with default timeout."""
        engine = AppleScriptEngine()
        assert engine.timeout == AppleScriptEngine.DEFAULT_TIMEOUT

    def test_init_custom_timeout(self) -> None:
        """Test engine initialization with custom timeout."""
        custom_timeout = 60.0
        engine = AppleScriptEngine(timeout=custom_timeout)
        assert engine.timeout == custom_timeout

    @patch("subprocess.run")
    def test_execute_success(
        self, mock_run: MagicMock, engine: AppleScriptEngine
    ) -> None:
        """Test successful script execution."""
        mock_run.return_value = MagicMock(
            stdout="test output\n", stderr="", returncode=0
        )

        result = engine.execute('display dialog "test"')

        assert result == "test output"
        mock_run.assert_called_once()

        # Verify command structure
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "osascript"
        assert "-e" in call_args
        assert 'display dialog "test"' in call_args

    @patch("subprocess.run")
    def test_execute_with_flags(
        self, mock_run: MagicMock, engine: AppleScriptEngine
    ) -> None:
        """Test script execution with custom flags."""
        mock_run.return_value = MagicMock(
            stdout="structured output\n", stderr="", returncode=0
        )

        result = engine.execute("get properties", flags=["-s", "s"])

        assert result == "structured output"

        # Verify flags are included
        call_args = mock_run.call_args[0][0]
        assert "-s" in call_args
        assert "s" in call_args

    @patch("subprocess.run")
    def test_execute_structured(
        self, mock_run: MagicMock, engine: AppleScriptEngine
    ) -> None:
        """Test structured output execution."""
        mock_run.return_value = MagicMock(
            stdout="{key:value}\n", stderr="", returncode=0
        )

        result = engine.execute_structured("get properties")

        assert result == "{key:value}"

        # Verify structured flags are used
        call_args = mock_run.call_args[0][0]
        assert "-s" in call_args
        assert "s" in call_args

    @patch("subprocess.run")
    def test_execute_error(
        self, mock_run: MagicMock, engine: AppleScriptEngine
    ) -> None:
        """Test script execution error handling."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["osascript"], stderr="Script error"
        )

        with pytest.raises(AppleScriptExecutionError) as exc_info:
            engine.execute("invalid script")

        assert "Script error" in str(exc_info.value)
        assert exc_info.value.returncode == 1
        assert exc_info.value.stderr == "Script error"

    @patch("subprocess.run")
    def test_execute_timeout(
        self, mock_run: MagicMock, engine: AppleScriptEngine
    ) -> None:
        """Test script execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(["osascript"], timeout=30.0)

        with pytest.raises(AppleScriptTimeoutError) as exc_info:
            engine.execute("slow script")

        assert exc_info.value.timeout_seconds == 30.0

    @patch("subprocess.run")
    def test_execute_file_success(
        self, mock_run: MagicMock, engine: AppleScriptEngine, tmp_path: Path
    ) -> None:
        """Test successful file execution."""
        # Create a temporary script file
        script_file = tmp_path / "test.scpt"
        script_file.write_text('display dialog "test"')

        mock_run.return_value = MagicMock(
            stdout="file output\n", stderr="", returncode=0
        )

        result = engine.execute_file(script_file)

        assert result == "file output"

        # Verify file path is used
        call_args = mock_run.call_args[0][0]
        assert str(script_file) in call_args

    def test_execute_file_not_found(self, engine: AppleScriptEngine) -> None:
        """Test file execution with non-existent file."""
        non_existent = Path("does_not_exist.scpt")

        with pytest.raises(FileNotFoundError):
            engine.execute_file(non_existent)

    @patch("subprocess.run")
    def test_execute_custom_timeout(
        self, mock_run: MagicMock, engine: AppleScriptEngine
    ) -> None:
        """Test execution with custom timeout."""
        mock_run.return_value = MagicMock(stdout="output\n", stderr="", returncode=0)

        custom_timeout = 120.0
        engine.execute("test script", timeout=custom_timeout)

        # Verify timeout was passed to subprocess.run
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == custom_timeout
