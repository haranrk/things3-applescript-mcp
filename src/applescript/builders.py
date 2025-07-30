"""
Command builder pattern for constructing AppleScript commands.

This module provides a fluent interface for building AppleScript
commands in a type-safe and maintainable way.
"""

from typing import Any, Dict, List, Optional, Union

from applescript.converters import PythonToAppleScriptConverter


class AppleScriptCommand:
    """
    Represents an AppleScript command with a fluent interface for building.

    This class allows constructing complex AppleScript commands step by step
    using method chaining.
    """

    def __init__(self) -> None:
        """Initialize an empty AppleScript command."""
        self._tell_app: Optional[str] = None
        self._commands: List[str] = []
        self._converter = PythonToAppleScriptConverter()
        self._raw_script: Optional[str] = None

    def tell(self, application: str) -> "AppleScriptCommand":
        """
        Set the application to tell.

        Args:
            application: Name of the macOS application

        Returns:
            Self for method chaining
        """
        self._tell_app = application
        return self

    def add_command(self, command: str) -> "AppleScriptCommand":
        """
        Add a command to execute.

        Args:
            command: AppleScript command string

        Returns:
            Self for method chaining
        """
        self._commands.append(command)
        return self

    def set(self, property_name: str, of: str, to: Any) -> "AppleScriptCommand":
        """
        Add a property set command.

        Args:
            property_name: Name of the property to set
            of: Object reference (e.g., "newTodo", 'to do id "123"')
            to: Value to set the property to

        Returns:
            Self for method chaining
        """
        # Handle special case where 'to' value is already an AppleScript expression
        if isinstance(to, str) and hasattr(self._converter, '_is_applescript_expression') and self._converter._is_applescript_expression(to):
            value_str = to
        else:
            value_str = self._converter.convert(to)
        self._commands.append(f"set {property_name} of {of} to {value_str}")
        return self

    def get(self, property_name: str, of: Optional[str] = None) -> "AppleScriptCommand":
        """
        Add a property get command.

        Args:
            property_name: Name of the property to get
            of: Optional object reference

        Returns:
            Self for method chaining
        """
        if of:
            self._commands.append(f"get {property_name} of {of}")
        else:
            self._commands.append(f"get {property_name}")
        return self

    def make_new(
        self,
        class_name: str,
        with_properties: Optional[Dict[str, Any]] = None,
        at: Optional[str] = None,
    ) -> "AppleScriptCommand":
        """
        Add a make new object command.

        Args:
            class_name: Type of object to create (e.g., "to do", "project")
            with_properties: Properties for the new object
            at: Optional location (e.g., "beginning of list 'Today'")

        Returns:
            Self for method chaining
        """
        cmd = f"make new {class_name}"

        if with_properties:
            props_str = self._build_properties_record(with_properties)
            cmd += f" with properties {props_str}"

        if at:
            cmd += f" at {at}"

        self._commands.append(cmd)
        return self

    def delete(self, object_ref: str) -> "AppleScriptCommand":
        """
        Add a delete command.

        Args:
            object_ref: Reference to object to delete

        Returns:
            Self for method chaining
        """
        self._commands.append(f"delete {object_ref}")
        return self

    def move(self, object_ref: str, to: str) -> "AppleScriptCommand":
        """
        Add a move command.

        Args:
            object_ref: Reference to object to move
            to: Destination (e.g., 'list "Today"', 'project "Work"')

        Returns:
            Self for method chaining
        """
        self._commands.append(f"move {object_ref} to {to}")
        return self

    def return_value(self, expression: str) -> "AppleScriptCommand":
        """
        Add a return statement.

        Args:
            expression: Expression to return

        Returns:
            Self for method chaining
        """
        self._commands.append(f"return {expression}")
        return self

    def raw(self, script: str) -> "AppleScriptCommand":
        """
        Set raw AppleScript (bypasses command building).

        Args:
            script: Complete raw AppleScript

        Returns:
            Self for method chaining
        """
        self._raw_script = script
        return self

    def with_properties(self, properties: Dict[str, Any]) -> "AppleScriptCommand":
        """
        Convenience method to set multiple properties at once.

        Args:
            properties: Dictionary of property names and values

        Returns:
            Self for method chaining
        """
        props_str = self._build_properties_record(properties)
        self._commands.append(f"with properties {props_str}")
        return self

    def _build_properties_record(self, properties: Dict[str, Any]) -> str:
        """Build an AppleScript record from a dictionary."""
        if not properties:
            return "{}"

        items = []
        for key, value in properties.items():
            value_str = self._converter.convert(value)
            items.append(f"{key}:{value_str}")

        return "{" + ", ".join(items) + "}"

    def build(self) -> str:
        """
        Build the final AppleScript command.

        Returns:
            Complete AppleScript as a string

        Raises:
            ValueError: If the command is invalid
        """
        # If raw script is provided, return it directly
        if self._raw_script is not None:
            return self._raw_script

        # If no commands, raise error
        if not self._commands:
            raise ValueError("No commands added to build")

        # If tell application is set, wrap commands
        if self._tell_app:
            # Join commands with newlines and proper indentation
            commands_str = "\n    ".join(self._commands)
            return f'tell application "{self._tell_app}"\n    {commands_str}\nend tell'
        else:
            # Return commands without tell block
            return "\n".join(self._commands)


class CommandBuilder:
    """Base class for specialized command builders."""

    def build_command(self, **kwargs: Any) -> AppleScriptCommand:
        """
        Build a specialized AppleScript command.

        Args:
            **kwargs: Arguments specific to the command type

        Returns:
            Configured AppleScriptCommand instance
        """
        # Default implementation - subclasses should override
        raise NotImplementedError(
            "Subclasses should implement build_command or use specific methods"
        )


class TellBlockBuilder:
    """
    Helper class for building tell blocks with multiple commands.

    This is useful when you need to execute multiple commands
    within the same tell application block.
    """

    def __init__(self, application: str):
        """
        Initialize the tell block builder.

        Args:
            application: Name of the application
        """
        self.application = application
        self.commands: List[str] = []

    def add(self, command: Union[str, AppleScriptCommand]) -> "TellBlockBuilder":
        """
        Add a command to the tell block.

        Args:
            command: Either a string command or an AppleScriptCommand

        Returns:
            Self for method chaining
        """
        if isinstance(command, AppleScriptCommand):
            # Extract commands from the AppleScriptCommand
            # This assumes the command was built without a tell block
            script = command.build()
            # If it has a tell block, extract the inner commands
            if script.startswith("tell application"):
                # Extract commands between tell and end tell
                lines = script.split("\n")
                for line in lines[1:-1]:  # Skip first and last lines
                    self.commands.append(line.strip())
            else:
                self.commands.append(script)
        else:
            self.commands.append(command)

        return self

    def build(self) -> str:
        """
        Build the complete tell block.

        Returns:
            Complete AppleScript tell block
        """
        if not self.commands:
            return f'tell application "{self.application}"\nend tell'

        commands_str = "\n    ".join(self.commands)
        return f'tell application "{self.application}"\n    {commands_str}\nend tell'


class ConditionalBuilder:
    """Helper for building if-then-else statements."""

    def __init__(self, condition: str):
        """
        Initialize conditional builder.

        Args:
            condition: The condition to test
        """
        self.condition = condition
        self.then_commands: List[str] = []
        self.else_commands: List[str] = []

    def then(self, command: str) -> "ConditionalBuilder":
        """Add a then command."""
        self.then_commands.append(command)
        return self

    def else_(self, command: str) -> "ConditionalBuilder":
        """Add an else command."""
        self.else_commands.append(command)
        return self

    def build(self) -> str:
        """Build the if-then-else statement."""
        result = f"if {self.condition} then\n"

        if self.then_commands:
            for cmd in self.then_commands:
                result += f"    {cmd}\n"

        if self.else_commands:
            result += "else\n"
            for cmd in self.else_commands:
                result += f"    {cmd}\n"

        result += "end if"
        return result


class RepeatLoopBuilder:
    """Helper for building repeat loops."""

    def __init__(
        self,
        times: Optional[int] = None,
        with_var: Optional[str] = None,
        in_list: Optional[str] = None,
    ):
        """
        Initialize repeat loop builder.

        Args:
            times: Number of times to repeat
            with_var: Variable name for repeat with
            in_list: List to iterate over
        """
        self.times = times
        self.with_var = with_var
        self.in_list = in_list
        self.commands: List[str] = []

    def add_command(self, command: str) -> "RepeatLoopBuilder":
        """Add a command to the loop body."""
        self.commands.append(command)
        return self

    def build(self) -> str:
        """Build the repeat loop."""
        if self.times is not None:
            result = f"repeat {self.times} times\n"
        elif self.with_var and self.in_list:
            result = f"repeat with {self.with_var} in {self.in_list}\n"
        else:
            result = "repeat\n"

        for cmd in self.commands:
            result += f"    {cmd}\n"

        result += "end repeat"
        return result
