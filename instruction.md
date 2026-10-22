# Crash-Safe Key-Value Store

Build a durable, crash-recoverable key-value store under `/app`.

Your workspace already contains a Python package skeleton in `/app/kvstore/` and a small public smoke harness in `/app/smoke_test.py`. Replace the incomplete implementation so that a process crash cannot leave the on-disk state unreadable or silently corrupted.

## API

Implement `kvstore.store.KVStore` with this interface:

- `KVStore(path: str)` — open or create a store directory at `path`
- `put(key: str, value: bytes) -> None`
- `get(key: str) -> bytes | None`
- `delete(key: str) -> None`
- `flush() -> None` — force durability of all committed operations to disk
- `close() -> None`

Keys are non-empty UTF-8 strings of length at most 256. Values are arbitrary byte strings up to 1 MiB.

## Durability rules

1. After a successful `flush()`, every prior `put` / `delete` must survive an abrupt process kill and still be visible after reopening the same path.
2. If the process dies mid-write (torn record, truncated log), reopening must recover to a consistent snapshot of some prefix of committed operations. It must never raise on open solely because of a torn trailing record, and it must never return garbage values for keys that were fully flushed earlier.
3. Unflushed operations may be lost; that is acceptable.
4. Do not rely on an external database. Implement your own log or table format under the store directory. You may use only the Python standard library.

## How to work

```bash
cd /app
python smoke_test.py
```

Iterate until the smoke test passes, then harden crash recovery. Keep the public module path `kvstore.store.KVStore` stable — grading imports that symbol.

Work autonomously. Offline environment: no internet access.
