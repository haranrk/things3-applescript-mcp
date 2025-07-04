"""
Core AppleScript execution engine.

This module provides a pure AppleScript execution engine without any
parsing or application-specific logic.
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from .errors import AppleScriptExecutionError, AppleScriptTimeoutError

logger = logging.getLogger(__name__)


class AppleScriptEngine:
    """
    Pure AppleScript execution engine.

    This class only handles the execution of AppleScript commands
    and returns raw output. No parsing or type conversion is performed.
    """

    DEFAULT_TIMEOUT = 30.0  # seconds

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize the AppleScript engine.

        Args:
            timeout: Default timeout for script execution in seconds
        """
        self.timeout = timeout

    def execute(
        self,
        script: str,
        flags: Optional[List[str]] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Execute an AppleScript and return its raw output.

        Args:
            script: The AppleScript code to execute
            flags: Optional list of osascript flags (e.g., ["-s", "s"] for structured output)
            timeout: Timeout in seconds (uses default if not specified)

        Returns:
            Raw output from the AppleScript execution

        Raises:
            AppleScriptExecutionError: If the script execution fails
            AppleScriptTimeoutError: If the script execution times out
        """
        cmd = ["osascript"]

        if flags:
            cmd.extend(flags)

        cmd.extend(["-e", script])

        timeout_value = timeout or self.timeout

        logger.debug(f"Executing AppleScript with command: {cmd}")
        logger.debug(f"Script content: {script}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=timeout_value
            )

            output = result.stdout.strip()
            logger.debug(f"AppleScript output: {output}")

            return output

        except subprocess.TimeoutExpired:
            logger.error(f"AppleScript execution timed out after {timeout_value}s")
            raise AppleScriptTimeoutError(timeout_value, script)

        except subprocess.CalledProcessError as e:
            logger.error(f"AppleScript execution failed: {e.stderr}")
            raise AppleScriptExecutionError(
                "AppleScript execution failed", e.stderr, e.returncode, script
            )

    def execute_file(
        self,
        file_path: Path,
        flags: Optional[List[str]] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Execute an AppleScript file and return its raw output.

        Args:
            file_path: Path to the AppleScript file
            flags: Optional list of osascript flags
            timeout: Timeout in seconds (uses default if not specified)

        Returns:
            Raw output from the AppleScript execution

        Raises:
            AppleScriptExecutionError: If the script execution fails
            AppleScriptTimeoutError: If the script execution times out
            FileNotFoundError: If the script file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"AppleScript file not found: {file_path}")

        cmd = ["osascript"]

        if flags:
            cmd.extend(flags)

        cmd.append(str(file_path))

        timeout_value = timeout or self.timeout

        logger.debug(f"Executing AppleScript file: {file_path}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=timeout_value
            )

            output = result.stdout.strip()
            logger.debug(f"AppleScript output: {output}")

            return output

        except subprocess.TimeoutExpired:
            logger.error(f"AppleScript execution timed out after {timeout_value}s")
            raise AppleScriptTimeoutError(timeout_value, str(file_path))

        except subprocess.CalledProcessError as e:
            logger.error(f"AppleScript execution failed: {e.stderr}")
            raise AppleScriptExecutionError(
                "AppleScript file execution failed",
                e.stderr,
                e.returncode,
                str(file_path),
            )

    def execute_structured(self, script: str, timeout: Optional[float] = None) -> str:
        """
        Execute an AppleScript with structured output format.

        This is a convenience method that adds the "-s s" flags for
        structured output format.

        Args:
            script: The AppleScript code to execute
            timeout: Timeout in seconds (uses default if not specified)

        Returns:
            Raw structured output from the AppleScript execution
        """
        return self.execute(script, flags=["-s", "s"], timeout=timeout)
