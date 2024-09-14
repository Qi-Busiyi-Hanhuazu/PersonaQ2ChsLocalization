import json
import os

from helper import (
  DIR_EXPORT_ROOT,
  DIR_JSON_ROOT,
  TRASH_PATTERN,
  convert_special_controls,
  remove_controls,
)


def convert_messages_to_json(msg_root: str, json_root: str):
  for root, dirs, files in os.walk(msg_root):
    for file_name in files:
      if not file_name.endswith(".json"):
        continue

      sheet_name = os.path.relpath(f"{root}/{file_name}", msg_root).replace("\\", "/").removesuffix(".json")
      print(f"Converting: {sheet_name}.json")

      output = {}
      with open(f"{root}/{file_name}", "r", -1, "utf8") as reader:
        messages = json.load(reader)

      line_keys = set()
      for message in messages["texts"]:
        speaker = message.get("speaker", "")
        line_id = message["id"]
        if line_id in line_keys:
          dupe_i = 2
          while f"{line_id}_{dupe_i}" in line_keys:
            dupe_i += 1
          line_id = f"{line_id}_{dupe_i}"
        line_keys.add(line_id)

        for line_i, line in enumerate(message["lines"]):
          line: str = convert_special_controls(line)
          prefix, content, suffix = remove_controls(line)

          item = {
            "speaker": speaker,
            "prefix": prefix,
            "content": content,
            "suffix": suffix,
          }

          if "[F2 03 01 FF]" in content and all(
            map(
              lambda x: len(x) == 1 or (x.startswith("[") and x.endswith("]")),
              content.split("[F2 03 01 FF]"),
            )
          ):
            content = content.replace("[F2 03 01 FF]", "")
            item.update(
              {
                "content": content,
                "flags": item.get("flags", []) + ["[F2 03 01 FF]"],
              }
            )

          item["trash"] = bool(TRASH_PATTERN.search(item["content"])) or "だいだら" in speaker
          output[f"{line_id}_{line_i}"] = item

      all_trash = all(map(lambda x: x["trash"], output.values()))

      for speaker in messages["speakers"]:
        output[f"speaker_{speaker}"] = {
          "speaker": "",
          "content": speaker,
        }

      new_path = f"{json_root}/{sheet_name}.json"
      if len(output) == 0 or all_trash:
        if os.path.exists(new_path):
          os.remove(new_path)
        continue
      os.makedirs(os.path.dirname(new_path), exist_ok=True)
      with open(new_path, "w", -1, "utf8") as writer:
        writer.write(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
  convert_messages_to_json(DIR_EXPORT_ROOT, f"{DIR_JSON_ROOT}/ja")
