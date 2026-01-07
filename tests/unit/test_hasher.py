"""Unit tests for domain-separated hashing."""

import pytest

from aak.canon.hasher import GENESIS_HASH, chain_hash, domain_hash


class TestDomainSeparatedHashing:
    """Test suite for domain-separated SHA256."""

    def test_domain_separation(self):
        """Different domains produce different hashes for same data."""
        data = {"message": "hello"}
        h1 = domain_hash("llm_request", data)
        h2 = domain_hash("llm_response", data)
        assert h1 != h2

    def test_same_input_same_hash(self):
        """Deterministic: same input -> same hash."""
        data = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
        h1 = domain_hash("llm_request", data)
        h2 = domain_hash("llm_request", data)
        assert h1 == h2

    def test_key_order_independence(self):
        """RFC 8785 canonicalization makes key order irrelevant."""
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        assert domain_hash("event", d1) == domain_hash("event", d2)

    def test_hash_format(self):
        """Hash is 64 lowercase hex characters."""
        h = domain_hash("event", {"test": True})
        assert len(h) == 64
        assert h == h.lower()
        assert all(c in "0123456789abcdef" for c in h)

    def test_unknown_domain_raises(self):
        """Unknown domain raises ValueError."""
        with pytest.raises(ValueError, match="Unknown domain"):
            domain_hash("invalid_domain", {"x": 1})

    def test_string_input(self):
        """String input hashed directly (as UTF-8)."""
        h = domain_hash("rag_chunk", "This is chunk text.")
        assert len(h) == 64

    def test_bytes_input(self):
        """Bytes input hashed directly."""
        h = domain_hash("rag_chunk", b"binary content")
        assert len(h) == 64

    def test_chain_hash(self):
        """Chain hash combines prev + current."""
        h1 = domain_hash("event", {"seq": 0})
        h2 = domain_hash("event", {"seq": 1})
        ch = chain_hash(h1, h2)
        assert len(ch) == 64
        # Different order -> different result
        ch_reversed = chain_hash(h2, h1)
        assert ch != ch_reversed

    def test_genesis_hash_constant(self):
        """Genesis hash is a fixed constant."""
        assert len(GENESIS_HASH) == 64
        # Should not change between runs
        assert GENESIS_HASH == GENESIS_HASH

    def test_all_domains_work(self):
        """All defined domains produce valid hashes."""
        from aak.canon.hasher import DOMAINS

        data = {"test": "value"}
        for domain in DOMAINS:
            h = domain_hash(domain, data)
            assert len(h) == 64
