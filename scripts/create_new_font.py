import json
import math
import os
from copy import deepcopy
from math import ceil

from fontTools.ttLib import TTFont
from helper import (
  CHAR_TABLE_PATH,
  CHINESE_PUNCTUATIONS_CENTER,
  CHINESE_PUNCTUATIONS_LEFT,
  CHINESE_PUNCTUATIONS_RIGHT,
  FONT_PATHS,
)
from PIL import Image, ImageDraw, ImageFont


def has_glyph(font: TTFont, glyph: str):
  for table in font["cmap"].tables:
    if ord(glyph) in table.cmap.keys():
      return True
  return False


def create_new_font(file_name: str, input_dir: str, output_dir: str, char_table: dict[str, str], font_paths: list[str]):
  SCALE = 8

  with open(f"{input_dir}/{file_name}_manifest.json", "r", -1, "utf8") as reader:
    manifest = json.load(reader)

  os.makedirs(output_dir, exist_ok=True)

  new_manifest = deepcopy(manifest)
  new_characters: list[str] = []
  old_character_width = {}

  for char, char_id in manifest["glyphMap"].items():
    real_char = char.encode("utf-16-be").decode("cp932").strip("\0")

    if real_char == "㍽" or 0x4E00 <= ord(real_char) <= 0x9FFF:
      continue
    new_characters.append(real_char)
    old_character_width[real_char] = {
      "index": char_id,
      "info": manifest["glyphWidths"][str(char_id)],
    }

  for char in char_table:
    if char not in new_characters:
      new_characters.append(char)

  new_characters.sort(key=lambda x: x.encode("cp932").rjust(2, b"\0"))
  new_widths = {}

  sheet_index, x, y = 0, 0, 0
  sheet_width = manifest["textureInfo"]["sheetInfo"]["width"]
  sheet_height = manifest["textureInfo"]["sheetInfo"]["height"]
  glyph_width = manifest["textureInfo"]["glyph"]["width"] + 1
  glyph_height = manifest["textureInfo"]["glyph"]["height"] + 1
  cols = manifest["textureInfo"]["sheetInfo"]["cols"]
  rows = manifest["textureInfo"]["sheetInfo"]["rows"]
  assert cols == sheet_width // glyph_width
  assert rows == sheet_height // glyph_height
  glyphs_per_sheet = cols * rows
  sheet = Image.new("RGBA", (sheet_width, sheet_height))
  font_size = manifest["fontInfo"]["width"] - 1
  ascent = manifest["fontInfo"]["ascent"] + 0.5
  fonts = [ImageFont.truetype(font_path, font_size * SCALE) for font_path in font_paths if os.path.exists(font_path)]
  ttfonts = [TTFont(font_path, fontNumber=0) for font_path in font_paths if os.path.exists(font_path)]

  check_image_cols = math.ceil(math.sqrt(len(new_characters)))
  check_image_rows = math.ceil(len(new_characters) / check_image_cols)
  check_image = Image.new("RGBA", (check_image_cols * glyph_width, check_image_rows * glyph_height), (0, 0, 0, 255))

  old_sheet_cache = {}
  for i, char in enumerate(new_characters):
    if char in old_character_width:
      old_char_id: int = old_character_width[char]["index"]
      char_info: dict[str, int] = old_character_width[char]["info"]
      old_sheet_index = old_char_id // glyphs_per_sheet
      old_char_in_sheet = old_char_id % glyphs_per_sheet
      if old_sheet_index not in old_sheet_cache:
        old_sheet_cache[old_sheet_index] = Image.open(f"{input_dir}/{file_name}_sheet{old_sheet_index}.png")
      glyph = old_sheet_cache[old_sheet_index].crop(
        (
          (old_char_in_sheet % cols) * glyph_width + 1,
          (old_char_in_sheet // cols) * glyph_height + 2,
          (old_char_in_sheet % cols + 1) * glyph_width + 1,
          (old_char_in_sheet // cols + 1) * glyph_height + 2,
        )
      )
    else:
      glyph = Image.new("RGBA", (glyph_width * SCALE, glyph_height * SCALE))
      draw = ImageDraw.Draw(glyph)
      for font, ttfont in zip(fonts, ttfonts):
        if not has_glyph(ttfont, char_table[char]):
          continue
        draw.text(
          (0 * SCALE, ascent * SCALE),
          char_table[char],
          (255, 255, 255, 255),
          font,
          "ls",
        )
        break
      glyph = glyph.resize((glyph_width, glyph_height), Image.LANCZOS)
      char_info = {
        "char": font_size,
        "glyph": font_size,
        "left": 0,
      }
      if char == "㍽":
        char_info["char"] = round(font_size * 0.75)

    if char in CHINESE_PUNCTUATIONS_LEFT:
      char_info["char"] = font_size
      char_info["glyph"] = char_info["char"]
    elif char in CHINESE_PUNCTUATIONS_RIGHT:
      char_info["left"] = font_size - char_info["char"]
      char_info["glyph"] = char_info["char"]
    elif char in CHINESE_PUNCTUATIONS_CENTER:
      char_info["left"] = (font_size - char_info["char"]) // 2
      char_info["char"] = font_size - char_info["left"]
      char_info["glyph"] = char_info["char"]

    sheet.paste(glyph, (x * glyph_width + 1, y * glyph_height + 2))
    check_image.paste(glyph, (i % check_image_cols * glyph_width, i // check_image_cols * glyph_height), glyph)
    if 0x4E00 <= ord(char) <= 0x9FFF:
      if str(i) in new_widths:
        del new_widths[str(i)]
    else:
      new_widths[str(i)] = char_info

    x += 1
    if x == cols:
      x = 0
      y += 1
      if y == rows:
        sheet.save(f"{output_dir}/{file_name}_sheet{sheet_index}.png")
        sheet_index += 1
        sheet = Image.new("RGBA", (sheet_width, sheet_height))
        x, y = 0, 0

  if x + y > 0:
    sheet.save(f"{output_dir}/{file_name}_sheet{sheet_index}.png")
  new_manifest["glyphMap"] = {
    char.encode("cp932").rjust(2, b"\0").decode("utf-16-be"): i for i, char in enumerate(new_characters)
  }
  new_manifest["glyphWidths"] = new_widths
  new_manifest["textureInfo"]["sheetCount"] = ceil(len(new_characters) / glyphs_per_sheet)

  with open(f"{output_dir}/{file_name}_manifest.json", "w", -1, "utf8") as writer:
    json.dump(new_manifest, writer, ensure_ascii=False, indent=2)
  check_image.save(f"{output_dir}/{file_name}.png")


if __name__ == "__main__":
  with open(CHAR_TABLE_PATH, "r", -1, "utf8") as reader:
    char_table = json.load(reader)

  create_new_font("seurapro_12_12", "temp/font", "temp/new_font", char_table, FONT_PATHS)
  create_new_font("seurapro_13_13", "temp/font", "temp/new_font", char_table, FONT_PATHS)
