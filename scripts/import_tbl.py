import json
import os
import struct
from typing import Any

from helper import DIR_IMPORT_ROOT, DIR_ORIGINAL_ROOT, DIR_PACK_ROOT


def import_tbl(input_root: str, message_root: str, output_root: str):
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      if not file_name.endswith(".tbl"):
        continue

      sheet_name = os.path.relpath(f"{root}/{file_name}", input_root).replace("\\", "/")
      json_path = f"{message_root}/{sheet_name}.json"
      if not os.path.exists(json_path):
        continue

      with open(json_path, "r", -1, "utf8") as reader:
        texts: list[dict[str, Any]] = json.load(reader)["texts"]

      binary = bytearray()
      binary += struct.pack("<H", len(texts))

      text_binary = bytearray()
      for i, text in enumerate(texts):
        text_binary += text["lines"][0].encode("cp932") + b"\0"
        binary += struct.pack("<H", len(text_binary))

      binary += text_binary

      new_path = f"{output_root}/{sheet_name}"
      os.makedirs(os.path.dirname(new_path), exist_ok=True)
      with open(new_path, "wb") as writer:
        writer.write(binary)


if __name__ == "__main__":
  import_tbl(DIR_ORIGINAL_ROOT, DIR_IMPORT_ROOT, DIR_PACK_ROOT)
