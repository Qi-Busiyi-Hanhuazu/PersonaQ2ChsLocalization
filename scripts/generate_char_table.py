import json
import os
import struct

from helper import (
  CHAR_TABLE_PATH,
  CHINESE_TO_JAPANESE,
  CONTROL_PATTERN,
  DIR_JSON_ROOT,
  KANA_PATTERN,
  SPECLAL_CONTROL_PATTERN,
  ZH_HANS_2_KANJI_PATH,
)

LANGUAGE = os.getenv("XZ_LANGUAGE") or "zh_Hans"


def generate_cp932(used_kanjis: set[str]):
  for high in range(0x88, 0xA0):
    for low in range(0x40, 0xFD):
      if low == 0x7F:
        continue
      code = (high << 8) | low
      try:
        char = struct.pack(">H", code).decode("cp932")
        if char in used_kanjis:
          continue
      except UnicodeDecodeError:
        continue
      yield char


def generate_char_table(json_root: str) -> dict[str, str]:
  char_table: dict[str, str] = {}
  shift_jis_characters = set()
  with open(ZH_HANS_2_KANJI_PATH, "r", -1, "utf8") as reader:
    _: dict[str, str] = json.load(reader)
  zh_Hans_2_kanji = {k: v for k, v in _.items() if v.encode("cp932")[0] < 0xA0}

  characters = set(
    "".join(
      (
        "结城理",
        "有里凑",
        "汐见朔也",
        "鬼太郎",
        "汐见琴音",
        "哈姆子",
        "鸣上悠",
        "濑多总司",
        "浅川隼人",
        "番长",
        "雨宫莲",
        "来栖晓",
        "波特",
        "周可",
        "".join(zh_Hans_2_kanji.keys()),
      )
    )
  )
  for root, dirs, files in os.walk(json_root):
    for file_name in files:
      if not file_name.endswith(".json"):
        continue

      with open(f"{root}/{file_name}", "r", -1, "utf8") as reader:
        json_input: dict[str, dict] = json.load(reader)

      for k, v in json_input.items():
        if v.get("trash", False):
          continue

        content = SPECLAL_CONTROL_PATTERN.sub("", CONTROL_PATTERN.sub("", v["content"].replace("\n", "")))
        if KANA_PATTERN.search(content):
          continue

        for k, v in CHINESE_TO_JAPANESE.items():
          content = content.replace(k, v)
        for char in content:
          characters.add(char)

  generator = generate_cp932(set(zh_Hans_2_kanji.values()))

  def insert_char(char: str):
    shift_jis_char = next(generator)
    while shift_jis_char in shift_jis_characters:
      shift_jis_char = next(generator)
    char_table[shift_jis_char] = char
    shift_jis_characters.add(shift_jis_char)

  for char in sorted(characters):
    if not 0x4E00 <= ord(char) <= 0x9FFF:
      try:
        char.encode("cp932")
        char_table[char] = char
        continue
      except UnicodeEncodeError:
        pass

    try:
      if char.encode("cp932")[0] < 0xA0:
        if char in shift_jis_characters:
          insert_char(char_table[char])
        char_table[char] = char
        shift_jis_characters.add(char)
        continue
    except UnicodeEncodeError:
      pass

    if char in zh_Hans_2_kanji and zh_Hans_2_kanji[char] not in shift_jis_characters:
      char_table[zh_Hans_2_kanji[char]] = char
      shift_jis_characters.add(zh_Hans_2_kanji[char])
      continue

    insert_char(char)

  char_table = {k: v for k, v in sorted(char_table.items(), key=lambda x: x[0].encode("cp932").rjust(2, b"\0"))}
  return char_table


if __name__ == "__main__":
  char_table = generate_char_table(f"{DIR_JSON_ROOT}/{LANGUAGE}")
  os.makedirs(os.path.dirname(CHAR_TABLE_PATH), exist_ok=True)
  with open(CHAR_TABLE_PATH, "w", -1, "utf8") as writer:
    json.dump(char_table, writer, ensure_ascii=False, indent=2)
