import os
import shutil

from helper import DIR_IMAGE_ROOT, DIR_IMPORT_ROOT


def copy_images(from_root: str, to_root: str):
  for root, dirs, files in os.walk(from_root):
    for file_name in files:
      if not file_name.endswith(".png"):
        continue

      from_path = f"{root}/{file_name}"
      sheet_name = os.path.relpath(from_path, from_root).replace("\\", "/")
      to_path = f"{to_root}/{sheet_name}"
      os.makedirs(os.path.dirname(to_path), exist_ok=True)
      shutil.copyfile(from_path, to_path)


if __name__ == "__main__":
  copy_images(DIR_IMAGE_ROOT, DIR_IMPORT_ROOT)
