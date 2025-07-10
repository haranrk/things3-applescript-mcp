"""
Unit tests for AppleScript parsers.
"""

import pytest
from things3_mcp.applescript.parsers import (
    JSONParser,
    PrimitiveParser,
    StructuredRecordParser,
    DateParser,
    ListParser,
    ParserChain,
)
from things3_mcp.applescript.errors import AppleScriptParsingError


class TestJSONParser:
    """Test cases for JSONParser."""

    @pytest.fixture
    def parser(self) -> JSONParser:
        return JSONParser()

    def test_can_parse_object(self, parser: JSONParser) -> None:
        """Test JSON object detection."""
        assert parser.can_parse('{"key": "value"}')
        assert parser.can_parse('  {"key": "value"}  ')
        assert not parser.can_parse("not json")
        assert not parser.can_parse("")

    def test_can_parse_array(self, parser: JSONParser) -> None:
        """Test JSON array detection."""
        assert parser.can_parse("[1, 2, 3]")
        assert parser.can_parse("  [1, 2, 3]  ")

    def test_parse_object(self, parser: JSONParser) -> None:
        """Test JSON object parsing."""
        result = parser.parse('{"name": "test", "value": 42}')
        assert result == {"name": "test", "value": 42}

    def test_parse_array(self, parser: JSONParser) -> None:
        """Test JSON array parsing."""
        result = parser.parse("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_parse_invalid_json(self, parser: JSONParser) -> None:
        """Test invalid JSON handling."""
        with pytest.raises(AppleScriptParsingError):
            parser.parse('{"invalid": json}')


class TestPrimitiveParser:
    """Test cases for PrimitiveParser."""

    @pytest.fixture
    def parser(self) -> PrimitiveParser:
        return PrimitiveParser()

    def test_can_parse_always(self, parser: PrimitiveParser) -> None:
        """Test that primitive parser accepts everything."""
        assert parser.can_parse("anything")
        assert parser.can_parse("")
        assert parser.can_parse("123")

    def test_parse_boolean(self, parser: PrimitiveParser) -> None:
        """Test boolean parsing."""
        assert parser.parse("true") is True
        assert parser.parse("TRUE") is True
        assert parser.parse("false") is False
        assert parser.parse("FALSE") is False

    def test_parse_integer(self, parser: PrimitiveParser) -> None:
        """Test integer parsing."""
        assert parser.parse("42") == 42
        assert parser.parse("-10") == -10
        assert parser.parse("0") == 0

    def test_parse_float(self, parser: PrimitiveParser) -> None:
        """Test float parsing."""
        assert parser.parse("3.14") == 3.14
        assert parser.parse("-2.5") == -2.5

    def test_parse_string(self, parser: PrimitiveParser) -> None:
        """Test string parsing."""
        assert parser.parse("hello world") == "hello world"
        assert parser.parse("not a number") == "not a number"

    def test_parse_empty(self, parser: PrimitiveParser) -> None:
        """Test empty value parsing."""
        assert parser.parse("") is None
        assert parser.parse("   ") == "   "


class TestStructuredRecordParser:
    """Test cases for StructuredRecordParser."""

    @pytest.fixture
    def parser(self) -> StructuredRecordParser:
        return StructuredRecordParser()

    def test_can_parse_single_record(self, parser: StructuredRecordParser) -> None:
        """Test single record detection."""
        assert parser.can_parse('{key:"value", number:42}')
        assert not parser.can_parse("not a record")
        assert not parser.can_parse("")

    def test_can_parse_multiple_records(self, parser: StructuredRecordParser) -> None:
        """Test multiple records detection."""
        assert parser.can_parse('{{key1:"value1"}, {key2:"value2"}}')

    def test_parse_single_record(self, parser: StructuredRecordParser) -> None:
        """Test single record parsing."""
        result = parser.parse('{name:"test", value:42, active:true}')

        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42
        assert result["active"] is True

    def test_parse_multiple_records(self, parser: StructuredRecordParser) -> None:
        """Test multiple records parsing."""
        result = parser.parse('{{name:"first", id:1}, {name:"second", id:2}}')

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "first"
        assert result[1]["name"] == "second"

    def test_parse_missing_value(self, parser: StructuredRecordParser) -> None:
        """Test missing value parsing."""
        result = parser.parse('{name:"test", empty:missing value}')
        assert result["empty"] is None

    def test_parse_quoted_strings(self, parser: StructuredRecordParser) -> None:
        """Test quoted string parsing."""
        result = parser.parse('{message:"hello, world!"}')
        assert result["message"] == "hello, world!"


class TestDateParser:
    """Test cases for DateParser."""

    @pytest.fixture
    def parser(self) -> DateParser:
        return DateParser()

    def test_can_parse_date(self, parser: DateParser) -> None:
        """Test date format detection."""
        assert parser.can_parse('date "Friday, June 20, 2025 at 20:24:30"')
        assert not parser.can_parse("not a date")
        assert not parser.can_parse('just "some string"')

    def test_parse_date(self, parser: DateParser) -> None:
        """Test date parsing."""
        result = parser.parse('date "Friday, June 20, 2025 at 20:24:30"')
        assert result == "Friday, June 20, 2025 at 20:24:30"

    def test_parse_invalid_date(self, parser: DateParser) -> None:
        """Test invalid date format."""
        with pytest.raises(AppleScriptParsingError):
            parser.parse("not a date format")


class TestListParser:
    """Test cases for ListParser."""

    @pytest.fixture
    def parser(self) -> ListParser:
        return ListParser()

    def test_can_parse_list(self, parser: ListParser) -> None:
        """Test list format detection."""
        assert parser.can_parse("{item1, item2, item3}")
        assert parser.can_parse('{"quoted item", "another"}')
        assert not parser.can_parse("{key:value}")  # Record, not list
        assert not parser.can_parse("not a list")

    def test_parse_simple_list(self, parser: ListParser) -> None:
        """Test simple list parsing."""
        result = parser.parse("{item1, item2, item3}")
        assert result == ["item1", "item2", "item3"]

    def test_parse_quoted_list(self, parser: ListParser) -> None:
        """Test quoted items list parsing."""
        result = parser.parse('{"hello world", "another item"}')
        assert result == ["hello world", "another item"]

    def test_parse_empty_list(self, parser: ListParser) -> None:
        """Test empty list parsing."""
        result = parser.parse("{}")
        assert result == []


class TestParserChain:
    """Test cases for ParserChain."""

    @pytest.fixture
    def chain(self) -> ParserChain:
        return ParserChain()

    def test_default_parsers(self, chain: ParserChain) -> None:
        """Test default parser chain."""
        assert len(chain.parsers) > 0
        # Last parser should be PrimitiveParser as fallback
        assert isinstance(chain.parsers[-1], PrimitiveParser)

    def test_parse_json(self, chain: ParserChain) -> None:
        """Test JSON parsing through chain."""
        result = chain.parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_structured_record(self, chain: ParserChain) -> None:
        """Test structured record parsing through chain."""
        result = chain.parse('{name:"test", value:42}')
        assert isinstance(result, dict)
        assert result["name"] == "test"

    def test_parse_primitive(self, chain: ParserChain) -> None:
        """Test primitive parsing through chain."""
        assert chain.parse("true") is True
        assert chain.parse("42") == 42
        assert chain.parse("hello") == "hello"

    def test_parse_empty(self, chain: ParserChain) -> None:
        """Test empty value parsing."""
        assert chain.parse("") is None

    def test_custom_parsers(self) -> None:
        """Test custom parser chain."""
        custom_chain = ParserChain([PrimitiveParser()])
        assert len(custom_chain.parsers) == 1
        assert isinstance(custom_chain.parsers[0], PrimitiveParser)
