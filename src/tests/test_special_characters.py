#!/usr/bin/env python3
"""
Test cases for special characters in todo names to prevent regression.
"""

import sys
from pathlib import Path
import unittest

# Add the src directory to the path so we can import our modules
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from applescript.parsers import StructuredRecordParser


class TestSpecialCharacters(unittest.TestCase):
    """Test parsing of todos with special characters."""

    def setUp(self):
        """Set up test parser."""
        self.parser = StructuredRecordParser()

    def test_colon_in_todo_name(self):
        """Test todo names containing colons."""
        # Simulate AppleScript output with colon in name
        raw_output = '{{status:open, name:"Claude Code now supports hooks : r/ClaudeAI", id:"test1"}, {status:open, name:"Regular todo", id:"test2"}}'
        
        result = self.parser.parse(raw_output)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Claude Code now supports hooks : r/ClaudeAI")
        self.assertEqual(result[1]["name"], "Regular todo")

    def test_unicode_characters(self):
        """Test todo names with unicode characters."""
        raw_output = '{{status:open, name:"• Bullet point todo", id:"test1"}, {status:open, name:"Weekly Review ®=", id:"test2"}}'
        
        result = self.parser.parse(raw_output)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "• Bullet point todo")
        self.assertEqual(result[1]["name"], "Weekly Review ®=")

    def test_special_symbols(self):
        """Test todo names with various special symbols."""
        raw_output = '{{status:open, name:"Test @ symbol & more", id:"test1"}, {status:open, name:"Price $100.50", id:"test2"}, {status:open, name:"Email user@domain.com", id:"test3"}}'
        
        result = self.parser.parse(raw_output)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "Test @ symbol & more")
        self.assertEqual(result[1]["name"], "Price $100.50") 
        self.assertEqual(result[2]["name"], "Email user@domain.com")

    def test_quotes_and_escapes(self):
        """Test todo names with quotes and escape sequences."""
        raw_output = '{{status:open, name:"Todo with \\"quoted\\" text", id:"test1"}, {status:open, name:"Path\\\\to\\\\file", id:"test2"}}'
        
        result = self.parser.parse(raw_output)
        
        self.assertEqual(len(result), 2)
        # Parser preserves escaped quotes as-is (this is correct behavior)
        self.assertEqual(result[0]["name"], "Todo with \\\"quoted\\\" text")
        self.assertEqual(result[1]["name"], "Path\\\\to\\\\file")

    def test_complex_mixed_characters(self):
        """Test todo names with complex mix of special characters."""
        raw_output = '{{status:open, name:"• Project: Review & Update ® symbols", id:"test1"}, {status:open, name:"URL: https://example.com/path?param=value", id:"test2"}}'
        
        result = self.parser.parse(raw_output)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "• Project: Review & Update ® symbols")
        self.assertEqual(result[1]["name"], "URL: https://example.com/path?param=value")

    def test_empty_and_whitespace_names(self):
        """Test edge cases with empty or whitespace-only names."""
        raw_output = '{{status:open, name:"", id:"test1"}, {status:open, name:"   ", id:"test2"}, {status:open, name:"Normal todo", id:"test3"}}'
        
        result = self.parser.parse(raw_output)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "")
        self.assertEqual(result[1]["name"], "   ")
        self.assertEqual(result[2]["name"], "Normal todo")

    def test_single_record_with_special_chars(self):
        """Test single record parsing with special characters."""
        raw_output = '{status:open, name:"• Claude Code now supports hooks : r/ClaudeAI", id:"test1"}'
        
        result = self.parser.parse(raw_output)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "• Claude Code now supports hooks : r/ClaudeAI")


if __name__ == "__main__":
    unittest.main()