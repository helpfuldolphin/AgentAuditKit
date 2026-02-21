"""
Domain-separated SHA256 hashing for Agent Audit Kit.

This is the SINGLE SOURCE OF TRUTH for hashing.
The same code is embedded into exported verify.py bundles.
"""

from __future__ import annotations

import hashlib
from typing import Any

from aak.canon.rfc8785 import canonicalize_bytes

# Domain separation prefixes (version-tagged)
DOMAINS: dict[str, bytes] = {
    "llm_request": b"aak:v0:llm_req:",
    "llm_response": b"aak:v0:llm_res:",
    "tool_call": b"aak:v0:tool_call:",
    "tool_result": b"aak:v0:tool_res:",
    "rag_query": b"aak:v0:rag_query:",
    "rag_chunk": b"aak:v0:rag_chunk:",
    "event": b"aak:v0:event:",
    "chain": b"aak:v0:chain:",
    "manifest": b"aak:v0:manifest:",
}

# Genesis hash (prev_hash for first event)
GENESIS_HASH: str = hashlib.sha256(b"aak:v0:genesis").hexdigest()


def domain_hash(domain: str, data: Any) -> str:
    """
    Compute domain-separated SHA256 hash.

    Args:
        domain: One of the defined domain keys (e.g., "llm_request").
        data: Dict to canonicalize, or str/bytes for raw content.

    Returns:
        Lowercase hex SHA256 hash (64 characters).

    Raises:
        ValueError: If domain is not recognized.

    Example:
        >>> domain_hash("llm_request", {"model": "gpt-4", "messages": []})
        'a1b2c3...'
    """
    if domain not in DOMAINS:
        raise ValueError(f"Unknown domain: {domain}. Valid: {list(DOMAINS.keys())}")

    prefix = DOMAINS[domain]

    if isinstance(data, bytes):
        payload = data
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, dict):
        payload = canonicalize_bytes(data)
    else:
        # Fallback: canonicalize as JSON
        payload = canonicalize_bytes(data)

    return hashlib.sha256(prefix + payload).hexdigest()


def chain_hash(prev_hash: str, event_hash: str) -> str:
    """
    Compute hash chain link.

    Args:
        prev_hash: Hash of previous event (or genesis marker).
        event_hash: Hash of current event.

    Returns:
        Chain link hash.
    """
    # Both hashes as lowercase hex, concatenated with colon
    payload = f"{prev_hash}:{event_hash}".encode("utf-8")
    return hashlib.sha256(DOMAINS["chain"] + payload).hexdigest()


# === EMBEDDABLE CODE MARKER ===
# Everything here is used to generate verify.py
# fmt: off
EMBEDDED_HASHER = '''
import hashlib

DOMAINS = {
    "event": b"aak:v0:event:",
    "chain": b"aak:v0:chain:",
    "manifest": b"aak:v0:manifest:",
}

GENESIS_HASH = hashlib.sha256(b"aak:v0:genesis").hexdigest()


def domain_hash(domain, data):
    """Domain-separated SHA256 hash."""
    if domain not in DOMAINS:
        raise ValueError(f"Unknown domain: {domain}")
    prefix = DOMAINS[domain]
    if isinstance(data, bytes):
        payload = data
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, dict):
        payload = canonicalize(data).encode("utf-8")
    else:
        payload = canonicalize(data).encode("utf-8")
    return hashlib.sha256(prefix + payload).hexdigest()


def chain_hash(prev_hash, event_hash):
    """Compute hash chain link."""
    payload = f"{prev_hash}:{event_hash}".encode("utf-8")
    return hashlib.sha256(DOMAINS["chain"] + payload).hexdigest()
'''
# fmt: on
