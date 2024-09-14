import json
import os
import struct

from helper import DIR_EXPORT_ROOT


def export_ctd(input_root: str, message_root: str):
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      if not (file_name.endswith(".ctd") or file_name.endswith(".ftd") or file_name.endswith(".qtd")):
        continue

      sheet_name = os.path.relpath(f"{root}/{file_name}", input_root).replace("\\", "/")
      with open(f"{root}/{file_name}", "rb") as reader:
        binary = reader.read()

      size, rows = struct.unpack_from("<2I", binary)
      row_size = size // rows
      if row_size not in [0x38, 0x40] or size % rows != 0:
        continue
      if size + 0x20 <= len(binary):
        size_2, rows_2 = struct.unpack_from("<2I", binary, size + 0x10)
        if size != size_2 or rows != rows_2:
          continue

      texts = []
      try:
        for i in range(rows):
          raw_bytes = binary[0x10 + i * row_size : 0x10 + (i + 1) * row_size]
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
              right_len = 0x0C
            else:
              left_len = 0x00
              right_len = 0x00

          text_bytes = raw_bytes[left_len : row_size - right_len].rstrip(b"\0")

          texts.append(
            {
              "id": f"text_{i:03d}",
              "speaker": "",
              "lines": [text_bytes.decode("cp932")],
              "index": i,
            }
          )
      except UnicodeDecodeError:
        continue

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
  export_ctd(DIR_EXPORT_ROOT, DIR_EXPORT_ROOT)
