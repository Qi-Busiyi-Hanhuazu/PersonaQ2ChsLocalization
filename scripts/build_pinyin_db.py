import json
import os
import struct

PINYIN_MAPPING_PATH = "temp/pinyin_db.json"
PINYIN_DATABASE_PATH = "out/00040000001CBE00/romfs/iWnn/dic/JA_small/32/njubase2.a"


def build_pydb(mapping: dict[str, list[str]]) -> bytes:
  records = bytearray()
  for key, candidates in sorted(mapping.items()):
    normalized = key.lower().encode("ascii")
    if not normalized or len(normalized) > 0xFF:
      raise ValueError(f"invalid pinyin key: {key!r}")
    if not candidates or len(candidates) > 0xFF:
      raise ValueError(f"invalid candidate count for {key!r}")

    encoded_candidates = bytearray()
    for candidate in candidates:
      raw = candidate.encode("cp932")
      if b"\0" in raw or len(raw) >= 0x30:
        raise ValueError(
          f"candidate is not a valid 0x30-byte CP932 string: {candidate!r}"
        )
      encoded_candidates.extend(raw)
      encoded_candidates.append(0)

    record_size = 4 + len(normalized) + len(encoded_candidates)
    padded_size = (record_size + 3) & ~3
    records.extend(struct.pack("<BBH", len(normalized), len(candidates), padded_size))
    records.extend(normalized)
    records.extend(encoded_candidates)
    records.extend(b"\0" * (padded_size - record_size))

  if len(mapping) > 0xFFFF:
    raise ValueError("too many pinyin entries")
  return b"PYDB" + struct.pack("<HH", 1, len(mapping)) + records


def build_njdc_container() -> bytes:
  container = bytearray(0x88)
  container[:4] = b"NJDC"
  struct.pack_into(
    ">3I", container, 0x04, 0x00020000, 0x00020002, len(container) - 0x48
  )
  struct.pack_into(
    ">14I",
    container,
    0x10,
    0x2C,
    1,
    1,
    0,
    0x60,
    1,
    1,
    0x20,
    0,
    0,
    0,
    0x48,
    0x4C,
    0,
  )
  struct.pack_into(">3H", container, 0x48, 0, 1, 0)
  container[0x60:0x67] = bytes.fromhex("11 5F 82 12 00 30 42")
  container[0x80:0x84] = bytes.fromhex("00 CE 00 00")
  container[0x84:0x88] = b"NJDC"
  return bytes(container)


def build_pinyin_db(mapping_path: str, output_path: str):
  with open(mapping_path, "r", -1, "utf8") as reader:
    mapping: dict[str, list[str]] = json.load(reader)
  output = build_njdc_container() + build_pydb(mapping)
  os.makedirs(os.path.dirname(output_path), exist_ok=True)
  with open(output_path, "wb") as writer:
    writer.write(output)
  print(f"built {output_path} ({len(output)} bytes, {len(mapping)} readings)")


if __name__ == "__main__":
  build_pinyin_db(PINYIN_MAPPING_PATH, PINYIN_DATABASE_PATH)
