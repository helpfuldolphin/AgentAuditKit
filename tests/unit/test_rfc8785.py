"""Unit tests for RFC 8785 canonical JSON."""

from aak.canon.rfc8785 import canonicalize


class TestRFC8785Canonicalization:
    """Test suite for RFC 8785 compliance."""

    def test_object_key_sorting(self):
        """Keys must be sorted by Unicode code point."""
        data = {"z": 1, "a": 2, "m": 3}
        assert canonicalize(data) == '{"a":2,"m":3,"z":1}'

    def test_nested_object_sorting(self):
        """Nested objects also sorted."""
        data = {"b": {"z": 1, "a": 2}, "a": 3}
        assert canonicalize(data) == '{"a":3,"b":{"a":2,"z":1}}'

    def test_no_whitespace(self):
        """No spaces or newlines."""
        data = {"key": [1, 2, 3]}
        result = canonicalize(data)
        assert " " not in result
        assert "\n" not in result
        assert result == '{"key":[1,2,3]}'

    def test_unicode_key_sorting(self):
        """Unicode keys sorted by code point."""
        # 'a' is 0x61=97, 'α' is 0x3B1=945, 'β' is 0x3B2=946
        data = {"β": 2, "α": 1, "a": 0}
        assert canonicalize(data) == '{"a":0,"α":1,"β":2}'

    def test_string_escaping_minimal(self):
        """Minimal escape sequences."""
        data = {"s": "line1\nline2\ttab"}
        assert canonicalize(data) == '{"s":"line1\\nline2\\ttab"}'

    def test_integer_no_leading_zeros(self):
        """Integers without leading zeros."""
        assert canonicalize({"n": 42}) == '{"n":42}'
        assert canonicalize({"n": 0}) == '{"n":0}'
        assert canonicalize({"n": -5}) == '{"n":-5}'

    def test_float_normalization(self):
        """Floats normalized per RFC 8785."""
        assert canonicalize({"f": 0.0}) == '{"f":0}'

    def test_null_boolean(self):
        """Null and boolean literals."""
        data = {"a": None, "b": True, "c": False}
        assert canonicalize(data) == '{"a":null,"b":true,"c":false}'

    def test_empty_structures(self):
        """Empty array and object."""
        assert canonicalize({}) == "{}"
        assert canonicalize([]) == "[]"
        assert canonicalize({"a": [], "b": {}}) == '{"a":[],"b":{}}'

    def test_array_order_preserved(self):
        """Array element order preserved."""
        data = [3, 1, 2]
        assert canonicalize(data) == "[3,1,2]"

    def test_deterministic_output(self):
        """Same input always produces same output."""
        data = {"z": 1, "a": {"y": 2, "x": 3}}
        results = [canonicalize(data) for _ in range(100)]
        assert len(set(results)) == 1

    def test_quote_escaping(self):
        """Quotes in strings are escaped."""
        data = {"s": 'say "hello"'}
        assert canonicalize(data) == '{"s":"say \\"hello\\""}'

    def test_backslash_escaping(self):
        """Backslashes in strings are escaped."""
        data = {"s": "path\\to\\file"}
        assert canonicalize(data) == '{"s":"path\\\\to\\\\file"}'

    def test_control_characters(self):
        """Control characters are properly escaped."""
        data = {"s": "\b\f\r"}
        assert canonicalize(data) == '{"s":"\\b\\f\\r"}'
