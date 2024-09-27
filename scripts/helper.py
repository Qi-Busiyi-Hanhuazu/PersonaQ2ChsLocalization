import json
import re
from logging import warning
from typing import Any, Generator

DIR_ORIGINAL_ROOT = "unpacked/addition_files"
DIR_OFFICIAL_TRANSLATIONS_ROOT = "files/official_translations"
DIR_IMAGE_ROOT = "files/images"
DIR_REPLACE_ROOT = "files/replace"
DIR_EXPORT_ROOT = "temp/export"
DIR_IMPORT_ROOT = "temp/import"
DIR_JSON_ROOT = "temp/json"
DIR_PACK_ROOT = "temp/patch102"
DIR_CSV_ROOT = "texts"
DIR_XLSX_ROOT = "out/xlsx"
DIR_PATCH_ROOT = "out/00040000001CBE00"

CODE_BIN_PATH = "unpacked/exefs/code.bin"
ITEM_TBL_PATH = "unpacked/addition_files/init/itemtbl.bin"
ZH_HANS_2_KANJI_PATH = "files/zh_Hans_2_kanji.json"
DUPLICATE_FILES_INFO_PATH = "files/duplicate_files.json"
CHAR_TABLE_PATH = "out/char_table.json"
CODE_BIN_REPLACED_PATH = "temp/code.bin"

FONT_PATHS = [
  "files/fonts/FZFWQingYinTiJWB.ttf",
  "files/fonts/FOT-HummingStd-B.otf",
  "files/fonts/MiSans-Semibold.otf",
  "files/fonts/SourceHanSansSC-Medium.otf",
]

CONTROL_PATTERN = re.compile(r"(\[[0-9A-F]{2}(?: [0-9A-F]{2})*\]|\n)")
TRASH_PATTERN = re.compile(
  r"^(?:|.*(?:0x|0ｘ|_|＿|※|（仮）|ダミー|ダミ－|ＲＥＳＥＲＶＥ|RESERVE|ｂｌａｎｋ|ＢＬＡＮＫ|リザーブ|ダ\[(?:n|e|f(?: \d+)+)\]ミ\[(?:n|e|f(?: \d+)+)\]ー|★未使用|・未使用|未使用・|MSG|これが出るとバグです|バッファ|仮テキスト|テスト小目標|テスト[0-9０-９]|テストミッション[0-9０-９]|イベント[0-9０-９]|テスト用|PSQ2|“ブランク”|カット予定|だみー|テストメッセージ|デバック|＜声のみ＞|だいだら).*|ブランク|未使用\d*|%s|？+|NULL|仮・.+|仮msg|カット　予定)$",
  re.DOTALL,
)
KANA_PATTERN = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]+")
SPECLAL_CONTROL_PATTERN = re.compile(r"^\[(?:P[345]P?[姓名全]|(?:占位[A-B]|颜色) [0-9A-F]{2}|道具 [0-9A-F]{4})\]$")
CHINESE_TO_JAPANESE = {
  "·": "・",
  "•": "・",
  "—": "―",
  "-": "－",
  ".": "．",
  "%": "％",
}
CHINESE_PUNCTUATIONS_LEFT = "，。、；：？！…》）"
CHINESE_PUNCTUATIONS_RIGHT = "《（"
CHINESE_PUNCTUATIONS_CENTER = "…·・—―"

TO_SPECIAL_CONTROLS = {
  r"\[F5 C1 0D 01 01 01 01 01 01 01\]": "[P4姓]",
  r"\[F5 C1 0E 01 01 01 01 01 01 01\]": "[P4名]",
  r"\[F5 C1 0F 01 01 01 01 01 01 01\]": "[P4全]",
  r"\[F5 C1 10 01 01 01 01 01 01 01\]": "[P3姓]",
  r"\[F5 C1 11 01 01 01 01 01 01 01\]": "[P3名]",
  r"\[F5 C1 12 01 01 01 01 01 01 01\]": "[P3全]",
  r"\[F5 C1 1B 01 01 01 01 01 01 01\]": "[P3P姓]",
  r"\[F5 C1 1C 01 01 01 01 01 01 01\]": "[P3P名]",
  r"\[F5 C1 1D 01 01 01 01 01 01 01\]": "[P3P全]",
  r"\[F5 C1 1E 01 01 01 01 01 01 01\]": "[P5姓]",
  r"\[F5 C1 1F 01 01 01 01 01 01 01\]": "[P5名]",
  r"\[F5 C1 20 01 01 01 01 01 01 01\]": "[P5全]",
  r"\[F2 44 ([0-9A-F]{2}) 01\]": r"[占位A \1]",
  r"\[F4 45 04 01 00 00 ([0-9A-F]{2}) 01\]": r"[占位B \1]",
  r"\[F2 01 ([0-9A-F]{2}) 01\]": r"[颜色 \1]",
  r"\[F4 84 04 01 01 01 ([0-9A-F]{2}) ([0-9A-F]{2})\]": r"[道具 \2\1]",
}
TO_NORMAL_CONTROLS = {
  r"\[P4姓\]": "[F5 C1 0D 01 01 01 01 01 01 01]",
  r"\[P4名\]": "[F5 C1 0E 01 01 01 01 01 01 01]",
  r"\[P4全\]": "[F5 C1 0F 01 01 01 01 01 01 01]",
  r"\[P3姓\]": "[F5 C1 10 01 01 01 01 01 01 01]",
  r"\[P3名\]": "[F5 C1 11 01 01 01 01 01 01 01]",
  r"\[P3全\]": "[F5 C1 12 01 01 01 01 01 01 01]",
  r"\[P3P姓\]": "[F5 C1 1B 01 01 01 01 01 01 01]",
  r"\[P3P名\]": "[F5 C1 1C 01 01 01 01 01 01 01]",
  r"\[P3P全\]": "[F5 C1 1D 01 01 01 01 01 01 01]",
  r"\[P5姓\]": "[F5 C1 1E 01 01 01 01 01 01 01]",
  r"\[P5名\]": "[F5 C1 1F 01 01 01 01 01 01 01]",
  r"\[P5全\]": "[F5 C1 20 01 01 01 01 01 01 01]",
  r"\[占位A ([0-9A-F]{2})\]": r"[F2 44 \1 01]",
  r"\[占位B ([0-9A-F]{2})\]": r"[F4 45 04 01 00 00 \1 01]",
  r"\[颜色 ([0-9A-F]{2})\]": r"[F2 01 \1 01]",
  r"\[道具 ([0-9A-F]{2})([0-9A-F]{2})\]": r"[F4 84 04 01 01 01 \2 \1]",
}

HARDCODED_TEXTS_CODE_BIN = [
  ("？？？", "ひかり"),
  ("プロローグ", "？？？"),
  ("研究所 第%dフロア", "研究所 第%dフロア"),
  ("複数ターゲット", "みんな"),
  ("パーティ編成", "戻る"),
  ("ひかり", "？？？"),
  ("ｂｌａｎｋ", "L or R で10個ずつ飛ばせますー"),
  ("よろしくおねがいします", "よろしくおねがいします"),
  ("味方", "味方"),
  ("敵方", "敵方"),
  ("ブランクカード", "ブランクカード"),
  ("戦闘ナビを%sにまかせる。", "戦闘ナビを%sにまかせる。"),
  ("探索ナビを%sにまかせる。", "探索ナビを%sにまかせる。"),
  ("システムエラー。", "指定されたバージョンではデータを格納できません。"),
  ("データを入力してください。", "分割方法が不正です。"),
  ("月亮", "月亮"),
  ("剛毅", "塔"),
  ("恋愛", "女帝"),
  ("Aチーム", "Ｐ３女主人公"),
  ("扉", "扉"),
  ("扉", "扉"),
  ("扉", "扉"),
  ("電気柵", "電気柵"),
  ("謎解き", "採取"),
  ("第%dエリア", "大衆の映画館街"),
  ("ジュネシック・ランド", "ジュネシック・ランド"),
  ("中央集積所", "カモシダ記念広場"),
  ("エリザベス＆テオドア", "アリアドネ"),
  ("マーガレット＆菜々子", "入手金上昇アクセサリ"),
  (" 第１エリア", "上り階段"),
  ("メモ", "矢印"),
  ("ダミー 50", "カモシダーマン 記念広場"),
  (
    bytes.fromhex(
      "F2 05 FF FF F1 41 83 4E 83 8A 83 41 83 66 81 5B 83 5E 82 F0 95 DB 91 B6 82 B5 82 DC 82 B7 82 A9 81 48 0A"
    ),
    bytes.fromhex("F2 05 FF FF F1 41 8F E3 8F 91 82 AB 82 B7 82 E9 0A 82 E2 82 DF 82 E9 0A"),
  ),
]
HARDCODED_TEXTS_ITEM_TBL = [
  ("NULL", "鑑定・0xDFF"),
]

char_table_reversed: dict[str, str] = {}
zh_hans_no_code = set()


def convert_special_controls(line: str) -> str:
  line = line.replace("{", "[").replace("}", "]")
  for k, v in TO_SPECIAL_CONTROLS.items():
    line = re.sub(k, v, line)
  return line


def convert_back_special_controls(line: str) -> str:
  for k, v in TO_NORMAL_CONTROLS.items():
    line = re.sub(k, v, line)
  line = line.replace("[", "{").replace("]", "}")
  return line


def remove_controls(line: str) -> tuple[str, str, str]:
  splited: list[str] = CONTROL_PATTERN.split(line)

  start = 0
  while start < len(splited):
    part = splited[start].strip()
    if part and start % 2 == 0 and not SPECLAL_CONTROL_PATTERN.search(part):
      break
    start += 1
  end = len(splited) - 1
  while end >= start:
    part = splited[end].strip()
    if part and end % 2 == 0 and not SPECLAL_CONTROL_PATTERN.search(part):
      break
    end -= 1

  return (
    "".join(splited[:start]),
    "".join(splited[start : end + 1]),
    "".join(splited[end + 1 :]),
  )


def convert_zh_hans_to_shift_jis(zh_hans: str) -> str:
  global char_table_reversed
  if len(char_table_reversed) == 0:
    with open(CHAR_TABLE_PATH, "r", -1, "utf8") as reader:
      char_table: dict[str, str] = json.load(reader)
      for k, v in char_table.items():
        char_table_reversed[v] = k

  output = []
  control = False
  for char in zh_hans:
    if char == "[":
      control = True
    if control:
      output.append(char)
      if char == "]":
        control = False
      continue

    char = CHINESE_TO_JAPANESE.get(char, char)
    if char in "0123456789":
      char = chr(ord(char) - ord("0") + ord("０"))
    elif char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
      char = chr(ord(char) - ord("A") + ord("Ａ"))
    elif char in "abcdefghijklmnopqrstuvwxyz":
      char = chr(ord(char) - ord("a") + ord("ａ"))

    if char in char_table_reversed:
      output.append(char_table_reversed[char])
    else:
      try:
        char.encode("cp932")
        output.append(char)
      except UnicodeEncodeError:
        if char not in zh_hans_no_code:
          warning(f"Missing char: {char}")
          zh_hans_no_code.add(char)
        output.append("?")

  return "".join(output).replace("％ｓ", "%s").replace("％ｄ", "%d")


def load_translations(root: str, sheet_name: str) -> dict[str, str]:
  with open(f"{root}/{sheet_name}.json", "r", -1, "utf8") as reader:
    translation_list: list[dict] = json.load(reader)

  translations = {}
  for item_dict in translation_list:
    translations[item_dict["key"]] = item_dict["translation"]

  return translations


def load_csv(root: str, sheet_name: str) -> list[dict[str, str]]:
  with open(f"{root}/{sheet_name}.json", "r", -1, "utf8") as reader:
    translation_list: list[dict] = json.load(reader)

  return translation_list


# https://github.com/Meloman19/PersonaEditor/blob/master/PersonaEditorLib/Text/Extension.cs
# License: MIT
#
# MIT License
#
# Copyright (c) 2023 Meloman19
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


class TextBaseElement:
  def __init__(self, is_text: bool, data: bytearray):
    self.is_text: bool = is_text
    self.data: bytearray = data

  def __str__(self) -> str:
    if self.is_text:
      return self.data.decode("cp932", "ignore")
    else:
      return "{" + " ".join(f"{byte:02X}" for byte in self.data) + "}"

  def __repr__(self):
    return f"TextBaseElement(is_text={self.is_text}, data={self.data})"


def get_text_bases(array: bytearray | bytes) -> Generator[TextBaseElement, Any, None]:
  temp = bytearray()

  i = 0
  while i < len(array):
    if 0x20 <= array[i] < 0x80:
      temp.append(array[i])
    elif 0x80 <= array[i] < 0xF0:
      temp.append(array[i])
      i += 1
      temp.append(array[i])
    else:
      if 0x00 <= array[i] < 0x20:
        if temp:
          yield TextBaseElement(True, temp)
          temp = bytearray()
        temp.append(array[i])
        yield TextBaseElement(array[i] == 0x0A, temp)
        temp = bytearray()
      else:
        if temp:
          yield TextBaseElement(True, temp)
          temp = bytearray()
        temp.append(array[i])
        count = (array[i] - 0xF0) * 2 - 1
        for _ in range(count):
          i += 1
          temp.append(array[i])
        yield TextBaseElement(False, temp)
        temp = bytearray()
    i += 1

  if temp:
    yield TextBaseElement(True, temp)
