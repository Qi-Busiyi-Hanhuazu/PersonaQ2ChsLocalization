import json
import os
from logging import warning
from typing import Any

from helper import (
  CODE_BIN_REPLACED_PATH,
  CONTROL_PATTERN,
  DIR_IMPORT_ROOT,
  DIR_ORIGINAL_ROOT,
  DIR_PACK_ROOT,
  DIR_PATCH_ROOT,
  ITEM_TBL_PATH,
)


def import_code_bin(code_bin_path: str, sheet_name: str, message_root: str, output_path: str):
  with open(code_bin_path, "rb") as reader:
    binary = bytearray(reader.read())

  with open(f"{message_root}/{sheet_name}.json", "r", -1, "utf8") as reader:
    texts: list[dict[str, Any]] = json.load(reader)["texts"]

  for item in texts:
    offset: int = item["offset"]
    length: int = item["length"]
    text: str = item["lines"][0].replace("{", "[").replace("}", "]")
    text_bytes = bytearray()
    splited = CONTROL_PATTERN.split(text)
    for i, part in enumerate(splited):
      if i % 2 == 0:
        if sheet_name == "code.bin":
          part = part.replace("Ａ．Ｉ．Ｇ．Ｉ．Ｓ", "A.I.G.I.S")
        text_bytes += part.encode("cp932")
      elif part == "\n":
        text_bytes += b"\n"
      else:
        assert part.startswith("[") and part.endswith("]")
        text_bytes += bytes.fromhex(part[1:-1])
    if len(text_bytes) > length:
      warning(f"Text is too long: {text}")
      continue
    elif len(text_bytes) < length:
      text_bytes += b"\0" * (length - len(text_bytes))

    binary[offset : offset + length] = text_bytes

  os.makedirs(os.path.dirname(output_path), exist_ok=True)
  with open(output_path, "wb") as writer:
    writer.write(binary)


if __name__ == "__main__":
  import_code_bin(
    CODE_BIN_REPLACED_PATH,
    "code.bin",
    DIR_IMPORT_ROOT,
    f"{DIR_PATCH_ROOT}/exefs/code.bin",
  )
  import_code_bin(
    ITEM_TBL_PATH,
    os.path.relpath(ITEM_TBL_PATH, DIR_ORIGINAL_ROOT),
    DIR_IMPORT_ROOT,
    f"{DIR_PACK_ROOT}/{os.path.relpath(ITEM_TBL_PATH, DIR_ORIGINAL_ROOT)}",
  )
