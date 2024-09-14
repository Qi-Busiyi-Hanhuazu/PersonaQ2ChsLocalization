import os
import shutil

from helper import DIR_EXPORT_ROOT, DIR_REPLACE_ROOT


def copy_replaced_files(input_root: str, output_root: str):
  for root, _, files in os.walk(input_root):
    for file in files:
      input_path = os.path.join(root, file)
      output_path = os.path.join(output_root, os.path.relpath(input_path, input_root))
      os.makedirs(os.path.dirname(output_path), exist_ok=True)
      shutil.copy(input_path, output_path)


if __name__ == "__main__":
  copy_replaced_files(DIR_REPLACE_ROOT, DIR_EXPORT_ROOT)
