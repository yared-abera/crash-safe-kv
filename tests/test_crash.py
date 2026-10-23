#!/usr/bin/env python3
"""Hidden verifier for crash-safe-kv."""

from __future__ import annotations

import os
import shutil
import struct
import tempfile
import traceback
import zlib

from kvstore.store import KVStore

MAGIC = b"KVW1"


def _ok(name: str) -> None:
    print(f"PASS: {name}")


def _fail(name: str, detail: str) -> None:
    raise AssertionError(f"{name}: {detail}")


def test_basic_persist(tmp: str) -> None:
    path = os.path.join(tmp, "basic")
    s = KVStore(path)
    s.put("x", b"abc")
    s.put("y", b"\x00\x01" * 100)
    s.flush()
    s.close()
    s2 = KVStore(path)
    if s2.get("x") != b"abc" or s2.get("y") != b"\x00\x01" * 100:
        _fail("basic_persist", "values missing after reopen")
    s2.delete("x")
    s2.flush()
    s2.close()
    s3 = KVStore(path)
    if s3.get("x") is not None or s3.get("y") != b"\x00\x01" * 100:
        _fail("basic_persist", "delete not durable")
    s3.close()
    _ok("basic_persist")


def test_flush_then_kill(tmp: str) -> None:
    path = os.path.join(tmp, "flushkill")
    s = KVStore(path)
    for i in range(50):
        s.put(f"k{i}", f"v{i}".encode())
    s.flush()
    # Simulate abrupt close without calling close() cleanly: just drop reference after flush.
    del s
    s2 = KVStore(path)
    for i in range(50):
        if s2.get(f"k{i}") != f"v{i}".encode():
            _fail("flush_then_kill", f"missing k{i}")
    s2.close()
    _ok("flush_then_kill")


def test_torn_tail(tmp: str) -> None:
    path = os.path.join(tmp, "torn")
    s = KVStore(path)
    s.put("good", b"solid")
    s.flush()
    s.close()

    log = os.path.join(path, "wal.log")
    if not os.path.exists(log):
        # Accept any durable layout: append junk to any file in the store dir, or create torn wal.
        # If implementation uses a different filename, inject a torn trailer via a second put
        # by writing garbage into the largest file.
        files = [
            os.path.join(path, f)
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f))
        ]
        if not files:
            _fail("torn_tail", "store directory has no files after flush")
        log = max(files, key=os.path.getsize)

    with open(log, "ab") as fp:
        fp.write(b"\xff\xffTORN_PARTIAL_RECORD")

    s2 = KVStore(path)
    if s2.get("good") != b"solid":
        _fail("torn_tail", "lost flushed value after torn append")
    s2.put("after", b"ok")
    s2.flush()
    s2.close()
    s3 = KVStore(path)
    if s3.get("good") != b"solid" or s3.get("after") != b"ok":
        _fail("torn_tail", "store unusable after torn recovery")
    s3.close()
    _ok("torn_tail")


def test_overwrite_and_large(tmp: str) -> None:
    path = os.path.join(tmp, "ov")
    s = KVStore(path)
    s.put("k", b"one")
    s.flush()
    s.put("k", b"two")
    s.flush()
    blob = os.urandom(200_000)
    s.put("big", blob)
    s.flush()
    s.close()
    s2 = KVStore(path)
    if s2.get("k") != b"two":
        _fail("overwrite", "overwrite not durable")
    if s2.get("big") != blob:
        _fail("overwrite", "large value mismatch")
    s2.close()
    _ok("overwrite_and_large")


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="kv-verify-")
    try:
        test_basic_persist(tmp)
        test_flush_then_kill(tmp)
        test_torn_tail(tmp)
        test_overwrite_and_large(tmp)
        print("ALL_PASS")
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
