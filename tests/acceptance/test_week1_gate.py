"""Week 1 acceptance gate tests."""

from aak.canon.hasher import GENESIS_HASH, chain_hash, domain_hash
from aak.canon.rfc8785 import canonicalize


class TestWeek1AcceptanceCriteria:
    """
    Week 1 Gate:
    - RFC 8785 canonicalization works for all JSON types
    - Domain-separated hashing produces consistent results
    - Chain hashing links events correctly
    - Genesis hash is stable
    """

    def test_rfc8785_key_sorting(self):
        """AC-W1-01: Object keys sorted by Unicode code point."""
        assert canonicalize({"c": 3, "a": 1, "b": 2}) == '{"a":1,"b":2,"c":3}'

    def test_rfc8785_no_whitespace(self):
        """AC-W1-02: No whitespace in canonical output."""
        result = canonicalize({"key": [1, 2, {"nested": True}]})
        assert " " not in result and "\n" not in result

    def test_rfc8785_deterministic(self):
        """AC-W1-03: Same input always produces same output."""
        data = {"x": [1, 2], "y": {"z": 3}}
        assert canonicalize(data) == canonicalize(data)

    def test_domain_hash_separation(self):
        """AC-W1-04: Different domains produce different hashes."""
        data = {"test": 123}
        hashes = [domain_hash(d, data) for d in ["llm_request", "llm_response", "event"]]
        assert len(set(hashes)) == 3  # All different

    def test_domain_hash_consistency(self):
        """AC-W1-05: Same domain+data = same hash."""
        data = {"model": "gpt-4", "temp": 0.7}
        assert domain_hash("llm_request", data) == domain_hash("llm_request", data)

    def test_chain_hash_ordering_matters(self):
        """AC-W1-06: chain_hash(a,b) != chain_hash(b,a)."""
        h1, h2 = "a" * 64, "b" * 64
        assert chain_hash(h1, h2) != chain_hash(h2, h1)

    def test_genesis_hash_stable(self):
        """AC-W1-07: Genesis hash is a 64-char hex constant."""
        assert len(GENESIS_HASH) == 64
        assert all(c in "0123456789abcdef" for c in GENESIS_HASH)

    def test_canonicalize_complex_nested(self):
        """AC-W1-08: Complex nested structures canonicalize correctly."""
        data = {
            "z": [{"b": 2, "a": 1}, {"d": 4, "c": 3}],
            "a": {"nested": {"deep": True}},
        }
        result = canonicalize(data)
        # a should come before z in output
        assert result.index('"a"') < result.index('"z"')
        # Within arrays, objects should have sorted keys
        assert '{"a":1,"b":2}' in result

    def test_canonicalize_special_chars(self):
        """AC-W1-09: Special characters handled correctly."""
        data = {"msg": "Hello\nWorld\t!"}
        result = canonicalize(data)
        assert "\\n" in result
        assert "\\t" in result

    def test_domain_hash_with_string(self):
        """AC-W1-10: String data hashed correctly."""
        h1 = domain_hash("rag_chunk", "test string")
        h2 = domain_hash("rag_chunk", "test string")
        assert h1 == h2
        assert len(h1) == 64
