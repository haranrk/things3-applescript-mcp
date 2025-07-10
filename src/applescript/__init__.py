"""
AppleScript execution and parsing infrastructure.

This package provides a modular system for executing AppleScript commands
and parsing their output, with support for different parsing strategies
and type conversion.
"""

from things3_mcp.applescript.core import AppleScriptEngine
from things3_mcp.applescript.errors import (
    AppleScriptError,
    AppleScriptExecutionError,
    AppleScriptParsingError,
)
from things3_mcp.applescript.parsers import ParserStrategy, ParserChain
from things3_mcp.applescript.converters import (
    PythonToAppleScriptConverter,
    AppleScriptReferenceConverter,
    PropertyConverter,
)
from things3_mcp.applescript.builders import AppleScriptCommand, CommandBuilder

__all__ = [
    "AppleScriptEngine",
    "AppleScriptError",
    "AppleScriptExecutionError",
    "AppleScriptParsingError",
    "ParserStrategy",
    "ParserChain",
    "PythonToAppleScriptConverter",
    "AppleScriptReferenceConverter",
    "PropertyConverter",
    "AppleScriptCommand",
    "CommandBuilder",
]
