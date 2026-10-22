"""Incomplete starter store — replace with a durable implementation."""

from __future__ import annotations


class KVStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._mem: dict[str, bytes] = {}

    def put(self, key: str, value: bytes) -> None:
        if not key or len(key) > 256:
            raise ValueError("invalid key")
        if len(value) > 1 << 20:
            raise ValueError("value too large")
        self._mem[key] = value

    def get(self, key: str) -> bytes | None:
        return self._mem.get(key)

    def delete(self, key: str) -> None:
        self._mem.pop(key, None)

    def flush(self) -> None:
        # Starter is memory-only; does not persist.
        return

    def close(self) -> None:
        return
