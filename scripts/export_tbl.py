import json
import os
import struct

from helper import DIR_EXPORT_ROOT, DIR_ORIGINAL_ROOT


def export_tbl(input_root: str, message_root: str):
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      if not file_name.endswith(".tbl"):
        continue

      sheet_name = os.path.relpath(f"{root}/{file_name}", input_root).replace("\\", "/")
      with open(f"{root}/{file_name}", "rb") as reader:
        binary = reader.read()

      (entry_count,) = struct.unpack_from("<H", binary)
      start_offset = 2 + entry_count * 2

      texts = []
      for i in range(entry_count):
        text_start, text_end = struct.unpack_from("<2H", binary, i * 2)
        if i == 0:
          text_start = 0

        text_bytes = binary[start_offset + text_start : start_offset + text_end].rstrip(b"\0")
        texts.append(
          {
            "id": f"text_{i:03d}",
            "speaker": "",
            "lines": [text_bytes.decode("cp932")],
            "index": i,
          }
        )

      new_path = f"{message_root}/{sheet_name}.json"
      os.makedirs(os.path.dirname(new_path), exist_ok=True)
      with open(new_path, "w", -1, "utf8") as writer:
        json.dump(
          {
            "speakers": [],
            "texts": texts,
          },
          writer,
          ensure_ascii=False,
          indent=2,
        )


if __name__ == "__main__":
  export_tbl(DIR_ORIGINAL_ROOT, DIR_EXPORT_ROOT)
