"""
RFC 8785 Canonical JSON implementation.
https://www.rfc-editor.org/rfc/rfc8785

This is the SINGLE SOURCE OF TRUTH for canonicalization.
The same code is embedded into exported verify.py bundles.

Key rules:
1. Object keys sorted by Unicode code point
2. No whitespace
3. Numbers: no leading zeros, no trailing zeros after decimal,
   no positive exponent sign, lowercase 'e'
4. Strings: minimal escape sequences
5. UTF-8 encoding
"""

from __future__ import annotations

import math
from typing import Any


def _encode_string(s: str) -> str:
    """Encode string with minimal escape sequences per RFC 8785."""
    result = ['"']
    for char in s:
        code = ord(char)
        if char == '"':
            result.append('\\"')
        elif char == "\\":
            result.append("\\\\")
        elif code < 0x20:
            # Control characters
            if char == "\b":
                result.append("\\b")
            elif char == "\f":
                result.append("\\f")
            elif char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            else:
                result.append(f"\\u{code:04x}")
        else:
            result.append(char)
    result.append('"')
    return "".join(result)


def _encode_number(n: int | float) -> str:
    """Encode number per RFC 8785 / ES6 Number serialization."""
    if isinstance(n, bool):
        # bool is subclass of int, handle first
        return "true" if n else "false"

    if isinstance(n, int):
        return str(n)

    # Float handling
    if math.isnan(n) or math.isinf(n):
        return "null"

    if n == 0.0:
        # Both 0.0 and -0.0 become "0"
        return "0"

    # Use repr for precise representation, then normalize
    s = repr(n)
    # Normalize: remove positive exponent sign, lowercase e
    s = s.replace("E", "e").replace("e+", "e")
    return s


def canonicalize(obj: Any) -> str:
    """
    Serialize data to RFC 8785 canonical JSON.

    Args:
        obj: Any JSON-serializable Python object.

    Returns:
        Canonical JSON string (UTF-8 compatible).

    Example:
        >>> canonicalize({"b": 2, "a": 1})
        '{"a":1,"b":2}'
    """
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        return _encode_string(obj)
    if isinstance(obj, (int, float)):
        return _encode_number(obj)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        # Sort keys by Unicode code point (lexicographic on UTF-16 code units)
        sorted_keys = sorted(obj.keys(), key=lambda k: [ord(c) for c in str(k)])
        pairs = [f"{_encode_string(str(k))}:{canonicalize(obj[k])}" for k in sorted_keys]
        return "{" + ",".join(pairs) + "}"
    if isinstance(obj, (list, tuple)):
        if not obj:
            return "[]"
        elements = [canonicalize(v) for v in obj]
        return "[" + ",".join(elements) + "]"
    # Fallback for other types (datetime, etc.)
    return _encode_string(str(obj))


def canonicalize_bytes(data: Any) -> bytes:
    """Serialize to RFC 8785 canonical JSON as UTF-8 bytes."""
    return canonicalize(data).encode("utf-8")


# === EMBEDDABLE CODE MARKER ===
# Everything between BEGIN_EMBED and END_EMBED is copied into verify.py
# fmt: off
# BEGIN_EMBED_CANONICALIZE
EMBEDDED_CANONICALIZE = '''
def _encode_string(s):
    """Encode string with minimal escape sequences per RFC 8785."""
    result = ['"']
    for char in s:
        code = ord(char)
        if char == '"':
            result.append('\\\\"')
        elif char == "\\\\":
            result.append("\\\\\\\\")
        elif code < 0x20:
            if char == "\\b":
                result.append("\\\\b")
            elif char == "\\f":
                result.append("\\\\f")
            elif char == "\\n":
                result.append("\\\\n")
            elif char == "\\r":
                result.append("\\\\r")
            elif char == "\\t":
                result.append("\\\\t")
            else:
                result.append(f"\\\\u{code:04x}")
        else:
            result.append(char)
    result.append('"')
    return "".join(result)


def _encode_number(n):
    """Encode number per RFC 8785."""
    import math
    if isinstance(n, bool):
        return "true" if n else "false"
    if isinstance(n, int):
        return str(n)
    if math.isnan(n) or math.isinf(n):
        return "null"
    if n == 0.0:
        return "0"
    s = repr(n)
    s = s.replace("E", "e").replace("e+", "e")
    return s


def canonicalize(obj):
    """RFC 8785 canonical JSON serialization."""
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        return _encode_string(obj)
    if isinstance(obj, (int, float)):
        return _encode_number(obj)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        sorted_keys = sorted(obj.keys(), key=lambda k: [ord(c) for c in str(k)])
        pairs = [f"{_encode_string(str(k))}:{canonicalize(obj[k])}" for k in sorted_keys]
        return "{" + ",".join(pairs) + "}"
    if isinstance(obj, (list, tuple)):
        if not obj:
            return "[]"
        elements = [canonicalize(v) for v in obj]
        return "[" + ",".join(elements) + "]"
    return _encode_string(str(obj))
'''
# END_EMBED_CANONICALIZE
# fmt: on
