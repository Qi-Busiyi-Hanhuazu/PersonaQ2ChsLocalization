import json
import re
from collections import defaultdict

from helper import CHAR_TABLE_PATH, ZH_HANS_2_KANJI_PATH

PINYIN_MAPPING_PATH = "temp/pinyin_db.json"
LUNA_PATH = "pinyin_ime/sources/rime-luna-pinyin/luna_pinyin.dict.yaml"
ESSAY_PATH = "pinyin_ime/sources/rime-essay/essay.txt"
PINYIN_PATTERN = re.compile(r"^[a-z]+$")
MAX_CANDIDATES = 80


def load_luna(path: str) -> dict[str, list[tuple[str, float]]]:
  readings: dict[str, list[tuple[str, float]]] = defaultdict(list)
  in_entries = False
  with open(path, "r", -1, "utf8") as reader:
    for line in reader:
      line = line.rstrip("\r\n")
      if not in_entries:
        if line == "...":
          in_entries = True
        continue
      fields = line.split("\t")
      if (
        len(fields) < 2
        or len(fields[0]) != 1
        or not PINYIN_PATTERN.fullmatch(fields[1])
      ):
        continue
      probability = 1.0
      if len(fields) >= 3 and fields[2].endswith("%"):
        probability = float(fields[2][:-1]) / 100.0
      readings[fields[0]].append((fields[1], probability))
  return readings


def load_frequency(path: str) -> dict[str, int]:
  frequency: dict[str, int] = {}
  with open(path, "r", -1, "utf8") as reader:
    for line in reader:
      fields = line.rstrip("\r\n").rsplit("\t", 1)
      if len(fields) != 2 or len(fields[0]) != 1:
        continue
      try:
        frequency[fields[0]] = int(fields[1])
      except ValueError:
        continue
  return frequency


def generate_mapping(
  char_table: dict[str, str],
  zh_hans_to_kanji: dict[str, str],
  readings: dict[str, list[tuple[str, float]]],
  frequency: dict[str, int],
) -> dict[str, list[str]]:
  ranked: dict[str, dict[str, tuple[float, str]]] = defaultdict(dict)
  for storage_char, display_char in char_table.items():
    if len(storage_char) != 1 or len(display_char) != 1:
      continue
    try:
      storage_char.encode("cp932")
    except UnicodeEncodeError:
      continue

    mapped_storage = zh_hans_to_kanji.get(display_char)
    reading_char = storage_char if mapped_storage == storage_char else display_char
    char_readings = readings.get(reading_char) or readings.get(display_char)
    if not char_readings:
      continue
    base_score = max(frequency.get(display_char, 0), frequency.get(storage_char, 0))
    for pinyin, probability in char_readings:
      score = base_score * probability
      previous = ranked[pinyin].get(display_char)
      if previous is None or score > previous[0]:
        ranked[pinyin][display_char] = (score, storage_char)

  result: dict[str, list[str]] = {}
  for pinyin, candidates in sorted(ranked.items()):
    ordered = sorted(candidates.items(), key=lambda item: (-item[1][0], item[0]))
    result[pinyin] = [storage_char for _, (_, storage_char) in ordered[:MAX_CANDIDATES]]
  return result


def generate_pinyin_mapping():
  with open(CHAR_TABLE_PATH, "r", -1, "utf8") as reader:
    char_table: dict[str, str] = json.load(reader)
  with open(ZH_HANS_2_KANJI_PATH, "r", -1, "utf8") as reader:
    zh_hans_to_kanji: dict[str, str] = json.load(reader)

  mapping = generate_mapping(
    char_table,
    zh_hans_to_kanji,
    load_luna(LUNA_PATH),
    load_frequency(ESSAY_PATH),
  )
  with open(PINYIN_MAPPING_PATH, "w", -1, "utf8") as writer:
    json.dump(mapping, writer, ensure_ascii=False, indent=2)
  candidate_count = sum(len(candidates) for candidates in mapping.values())
  print(
    f"wrote {PINYIN_MAPPING_PATH} ({len(mapping)} readings, {candidate_count} candidates)"
  )


if __name__ == "__main__":
  generate_pinyin_mapping()
