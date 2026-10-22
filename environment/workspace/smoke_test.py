#!/usr/bin/env python3
"""Public smoke test the agent can run locally."""

from __future__ import annotations

import os
import shutil
import tempfile

from kvstore.store import KVStore


def main() -> None:
    root = tempfile.mkdtemp(prefix="kv-smoke-")
    try:
        store_path = os.path.join(root, "db")
        s = KVStore(store_path)
        s.put("a", b"1")
        s.put("b", b"hello")
        s.flush()
        s.close()

        s2 = KVStore(store_path)
        assert s2.get("a") == b"1"
        assert s2.get("b") == b"hello"
        s2.delete("a")
        s2.flush()
        s2.close()

        s3 = KVStore(store_path)
        assert s3.get("a") is None
        assert s3.get("b") == b"hello"
        s3.close()
        print("smoke_test: OK")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
