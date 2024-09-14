import json
import os
import struct
from typing import Any

from helper import DIR_EXPORT_ROOT, DIR_IMPORT_ROOT


def import_ctd(input_root: str, message_root: str, output_root: str):
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      if not (file_name.endswith(".ctd") or file_name.endswith(".ftd") or file_name.endswith(".qtd")):
        continue

      sheet_name = os.path.relpath(f"{root}/{file_name}", input_root).replace("\\", "/")
      json_path = f"{message_root}/{sheet_name}.json"
      if not os.path.exists(json_path):
        continue

      with open(json_path, "r", -1, "utf8") as reader:
        texts: list[dict[str, Any]] = json.load(reader)["texts"]

      with open(f"{root}/{file_name}", "rb") as reader:
        binary = bytearray(reader.read())

      size, rows = struct.unpack_from("<2I", binary)
      row_size = size // rows
      if row_size not in [0x38, 0x40] or size % rows != 0:
        continue
      if size + 0x20 <= len(binary):
        size_2, rows_2 = struct.unpack_from("<2I", binary, size + 0x10)
        if size != size_2 or rows != rows_2:
          continue

      for i in range(rows):
        text_bytes: bytes = texts[i]["lines"][0].encode("cp932")
        start_pos = 0x10 + i * row_size
        if row_size == 0x38:
          if "fclHelpTable_" in sheet_name:
            left_len = 0x14
            right_len = 0x04
          elif "tutorialConditions" in sheet_name:
            left_len = 0x04
            right_len = 0x04
          else:
            raise ValueError(f"Unknown sheet name: {sheet_name}")
        else:
          if "bgmSettingConditions" in sheet_name:
            left_len = 0x04
            right_len = 0x08
          else:
            left_len = 0x00
            right_len = 0x00
        raw_bytes = (
          binary[start_pos : start_pos + left_len]
          + text_bytes.ljust(row_size - left_len - right_len, b"\0")
          + binary[start_pos + row_size - right_len : start_pos + row_size]
        )

        binary[start_pos : start_pos + row_size] = raw_bytes

      new_path = f"{output_root}/{sheet_name}"
      os.makedirs(os.path.dirname(new_path), exist_ok=True)
      with open(new_path, "wb") as writer:
        writer.write(binary)


if __name__ == "__main__":
  import_ctd(DIR_EXPORT_ROOT, DIR_IMPORT_ROOT, DIR_IMPORT_ROOT)
