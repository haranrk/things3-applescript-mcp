"""
AppleScript execution and parsing infrastructure.

This package provides a modular system for executing AppleScript commands
and parsing their output, with support for different parsing strategies
and type conversion.
"""

from .core import AppleScriptEngine
from .errors import AppleScriptError, AppleScriptExecutionError, AppleScriptParsingError
from .parsers import ParserStrategy, ParserChain
from .converters import (
    PythonToAppleScriptConverter,
    AppleScriptReferenceConverter,
    PropertyConverter,
)
from .builders import AppleScriptCommand, CommandBuilder

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
