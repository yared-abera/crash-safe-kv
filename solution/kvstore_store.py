"""Reference durable KV store with length-prefixed WAL and CRC32."""

from __future__ import annotations

import os
import struct
import zlib
from typing import BinaryIO

MAGIC = b"KVW1"
REC_PUT = 1
REC_DEL = 2
HEADER = struct.Struct("<4sI")  # magic + payload_len
# payload: type(u8) key_len(u16) key value_len(u32) value  OR type key_len key
# then crc32 over payload


class KVStore:
    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(path, exist_ok=True)
        self._log_path = os.path.join(path, "wal.log")
        self._mem: dict[str, bytes] = {}
        self._replay()
        self._fp: BinaryIO = open(self._log_path, "ab", buffering=0)

    def _replay(self) -> None:
        if not os.path.exists(self._log_path):
            open(self._log_path, "ab").close()
            return
        with open(self._log_path, "rb") as fp:
            data = fp.read()
        offset = 0
        good = 0
        while offset + HEADER.size <= len(data):
            magic, plen = HEADER.unpack_from(data, offset)
            if magic != MAGIC:
                break
            rec_start = offset
            offset += HEADER.size
            if offset + plen + 4 > len(data):
                break
            payload = data[offset : offset + plen]
            offset += plen
            (crc,) = struct.unpack_from("<I", data, offset)
            offset += 4
            if zlib.crc32(payload) & 0xFFFFFFFF != crc:
                break
            self._apply(payload)
            good = offset
        if good != len(data):
            # Truncate torn/corrupt tail so future appends stay aligned.
            with open(self._log_path, "r+b") as fp:
                fp.truncate(good)

    def _apply(self, payload: bytes) -> None:
        typ = payload[0]
        key_len = struct.unpack_from("<H", payload, 1)[0]
        key = payload[3 : 3 + key_len].decode("utf-8")
        if typ == REC_DEL:
            self._mem.pop(key, None)
            return
        if typ != REC_PUT:
            raise ValueError("bad record type")
        pos = 3 + key_len
        (vlen,) = struct.unpack_from("<I", payload, pos)
        pos += 4
        value = payload[pos : pos + vlen]
        self._mem[key] = value

    def _append(self, payload: bytes) -> None:
        body = HEADER.pack(MAGIC, len(payload)) + payload + struct.pack(
            "<I", zlib.crc32(payload) & 0xFFFFFFFF
        )
        self._fp.write(body)

    def put(self, key: str, value: bytes) -> None:
        if not key or len(key) > 256:
            raise ValueError("invalid key")
        if len(value) > 1 << 20:
            raise ValueError("value too large")
        kb = key.encode("utf-8")
        payload = (
            bytes([REC_PUT])
            + struct.pack("<H", len(kb))
            + kb
            + struct.pack("<I", len(value))
            + value
        )
        self._append(payload)
        self._mem[key] = value

    def get(self, key: str) -> bytes | None:
        return self._mem.get(key)

    def delete(self, key: str) -> None:
        kb = key.encode("utf-8")
        payload = bytes([REC_DEL]) + struct.pack("<H", len(kb)) + kb
        self._append(payload)
        self._mem.pop(key, None)

    def flush(self) -> None:
        self._fp.flush()
        os.fsync(self._fp.fileno())

    def close(self) -> None:
        try:
            self.flush()
        finally:
            self._fp.close()
