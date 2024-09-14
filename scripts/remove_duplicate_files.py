import json
import os

from helper import DIR_EXPORT_ROOT, DUPLICATE_FILES_INFO_PATH


def remove_duplicate_files(root: str, info_path: str):
  with open(info_path, "r", -1, "utf8") as reader:
    duplicate_files: list[list[str]] = json.load(reader)

  for sub_list in duplicate_files:
    for file_path in sub_list[1:]:
      full_path = f"{root}/{file_path}.json"
      if os.path.exists(full_path):
        os.remove(full_path)


if __name__ == "__main__":
  remove_duplicate_files(DIR_EXPORT_ROOT, DUPLICATE_FILES_INFO_PATH)
