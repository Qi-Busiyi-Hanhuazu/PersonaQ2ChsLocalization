import json
import os

from helper import (
  CODE_BIN_REPLACED_PATH,
  DIR_EXPORT_ROOT,
  DIR_ORIGINAL_ROOT,
  HARDCODED_TEXTS_CODE_BIN,
  HARDCODED_TEXTS_ITEM_TBL,
  ITEM_TBL_PATH,
  get_text_bases,
)


def export_code_bin(input_path: str, sheet_name: str, message_root: str, hardcoded_texts: list[tuple[str, str]]):
  def find_strings(binary: bytes, texts: list, start: str | bytes, end: str | bytes, start_index: int = 0):
    if type(start) is str:
      start_bytes = start.encode("cp932") + b"\0"
    else:
      start_bytes = start + b"\0"

    if type(end) is str:
      end_bytes = end.encode("cp932")
    else:
      end_bytes = end

    start_index = binary.find(start_bytes, start_index)
    if start_index == -1:
      return start_index
    index = start_index
    while index < len(binary):
      zero_index = binary.find(b"\0", index)
      if zero_index == -1:
        break
      sub_bytes = binary[index:zero_index]
      if index != zero_index:
        if index > start_index:
          texts[-1]["length"] = index - texts[-1]["offset"] - 1
        texts.append(
          {
            "id": f"offset_{index:08x}",
            "speaker": "",
            "lines": ["".join([str(i) for i in get_text_bases(sub_bytes)])],
            "offset": index,
            "length": zero_index - index,
          }
        )
      index = zero_index + 1
      if sub_bytes == end_bytes:
        break

    return index

  with open(input_path, "rb") as reader:
    binary = reader.read()

  texts = []
  index = 0
  for start, end in hardcoded_texts:
    index = find_strings(binary, texts, start, end, index)
    if index == -1:
      break

  with open(f"{message_root}/{sheet_name}.json", "w", -1, "utf8") as writer:
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
  export_code_bin(
    CODE_BIN_REPLACED_PATH,
    "code.bin",
    DIR_EXPORT_ROOT,
    HARDCODED_TEXTS_CODE_BIN,
  )
  export_code_bin(
    ITEM_TBL_PATH,
    os.path.relpath(ITEM_TBL_PATH, DIR_ORIGINAL_ROOT),
    DIR_EXPORT_ROOT,
    HARDCODED_TEXTS_ITEM_TBL,
  )
