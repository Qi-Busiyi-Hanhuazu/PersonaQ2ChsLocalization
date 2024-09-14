import json
import os

from helper import (
  DIR_EXPORT_ROOT,
  DIR_IMPORT_ROOT,
  DIR_JSON_ROOT,
  convert_back_special_controls,
  convert_zh_hans_to_shift_jis,
)

LANGUAGE = os.getenv("XZ_LANGUAGE") or "zh_Hans"


def convert_json_to_messages(json_root: str, msg_root: str, msg_new_root: str):
  for root, dirs, files in os.walk(json_root):
    for file_name in files:
      if not file_name.endswith(".json"):
        continue

      sheet_name = os.path.relpath(f"{root}/{file_name}", json_root).replace("\\", "/").removesuffix(".json")
      print(f"Converting: {sheet_name}.json")

      with open(f"{root}/{file_name}", "r", -1, "utf8") as reader:
        json_input: dict[str, dict] = json.load(reader)

      with open(f"{msg_root}/{sheet_name}.json", "r", -1, "utf8") as reader:
        messages = json.load(reader)

      line_keys = set()
      for message in messages["texts"]:
        line_id = message["id"]
        if line_id in line_keys:
          dupe_i = 2
          while f"{line_id}_{dupe_i}" in line_keys:
            dupe_i += 1
          line_id = f"{line_id}_{dupe_i}"
        line_keys.add(line_id)
        for line_i, line in enumerate(message["lines"]):
          if f"{line_id}_{line_i}" not in json_input:
            pass
          v = json_input[f"{line_id}_{line_i}"]
          if v.get("trash", False):
            continue

          content = v["content"]
          flags = v.get("flags", [])
          if "[F2 03 01 FF]" in flags:
            new_contents = []
            f_0_3_65024_i = 0
            while f_0_3_65024_i < len(content):
              char = content[f_0_3_65024_i]
              if char == "[":
                while char != "]":
                  new_contents.append(content[f_0_3_65024_i])
                  f_0_3_65024_i += 1
                  char = content[f_0_3_65024_i]

              new_contents.append(char)
              new_contents.append("[F2 03 01 FF]")
              f_0_3_65024_i += 1
            content = "".join(new_contents)

          message["lines"][line_i] = convert_back_special_controls(
            "".join(
              (
                v["prefix"],
                convert_zh_hans_to_shift_jis(content),
                v["suffix"],
              )
            )
          )

      for speaker_i, speaker in enumerate(messages["speakers"]):
        if f"speaker_{speaker}" in json_input:
          messages["speakers"][speaker_i] = convert_zh_hans_to_shift_jis(json_input[f"speaker_{speaker}"]["content"])

      output_path = f"{msg_new_root}/{sheet_name}.json"
      os.makedirs(os.path.dirname(output_path), exist_ok=True)
      with open(output_path, "w", -1, "utf8") as writer:
        json.dump(messages, writer, ensure_ascii=False, indent=2)


if __name__ == "__main__":
  convert_json_to_messages(f"{DIR_JSON_ROOT}/{LANGUAGE}", DIR_EXPORT_ROOT, DIR_IMPORT_ROOT)
