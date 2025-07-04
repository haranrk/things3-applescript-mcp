"""
AppleScript error types for better error handling and debugging.
"""

from typing import Optional


class AppleScriptError(Exception):
    """Base exception for all AppleScript-related errors."""

    pass


class AppleScriptExecutionError(AppleScriptError):
    """Raised when osascript command fails to execute."""

    def __init__(
        self, message: str, stderr: str, returncode: int, script: Optional[str] = None
    ):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode
        self.script = script

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.stderr:
            parts.append(f"Error output: {self.stderr}")
        if self.returncode:
            parts.append(f"Return code: {self.returncode}")
        if self.script:
            parts.append(f"Script: {self.script[:100]}...")
        return " | ".join(parts)


class AppleScriptParsingError(AppleScriptError):
    """Raised when parsing AppleScript output fails."""

    def __init__(
        self,
        raw_output: str,
        parser_type: str,
        original_error: Optional[Exception] = None,
    ):
        message = f"Failed to parse AppleScript output with {parser_type}"
        if original_error:
            message += f": {original_error}"
        super().__init__(message)
        self.raw_output = raw_output
        self.parser_type = parser_type
        self.original_error = original_error

    def __str__(self) -> str:
        return f"{super().__str__()} | Output: {self.raw_output[:100]}..."


class AppleScriptTimeoutError(AppleScriptError):
    """Raised when AppleScript execution times out."""

    def __init__(self, timeout_seconds: float, script: Optional[str] = None):
        super().__init__(
            f"AppleScript execution timed out after {timeout_seconds} seconds"
        )
        self.timeout_seconds = timeout_seconds
        self.script = script
