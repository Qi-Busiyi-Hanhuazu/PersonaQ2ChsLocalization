import csv
import json
import os

from helper import DIR_CSV_ROOT, DIR_OFFICIAL_TRANSLATIONS_ROOT, load_csv

LANGUAGE = os.getenv("XZ_LANGUAGE") or "zh_Hans"


def load_official_names(root: str) -> dict[str, dict[str, str]]:
  translations: dict[str, dict[str, str]] = {}
  for file_name in sorted(os.listdir(root)):
    if not file_name.endswith(".csv"):
      continue

    source = file_name.split(".", 1)[0].split("_", 1)[-1]
    with open(f"{root}/{file_name}", "r", -1, "utf-8-sig", "ignore", "") as csvfile:
      reader = csv.reader(csvfile)

      row_iter = reader
      headers = next(row_iter)
      for row in row_iter:
        item_dict = dict(zip(headers, row))
        ja, zh = item_dict["ja"], item_dict["zh_Hans"]
        if ja in translations:
          continue
        translations[ja] = {
          "translation": zh,
          "source": source,
        }

  return translations


def import_official_names(csv_root_without_language: str, language: str, official_translations_root: str):
  translations = load_official_names(official_translations_root)
  for root, dirs, files in os.walk(f"{csv_root_without_language}/{language}"):
    for file_name in files:
      if not file_name.endswith(".json"):
        continue

      sheet_name = (
        os.path.relpath(
          f"{root}/{file_name}",
          f"{csv_root_without_language}/{language}",
        )
        .replace("\\", "/")
        .removesuffix(".json")
      )

      if not os.path.exists(f"{csv_root_without_language}/ja/{sheet_name}.json"):
        os.remove(f"{root}/{file_name}")
        continue
      original = load_csv(f"{csv_root_without_language}/ja", sheet_name)
      translated = load_csv(f"{csv_root_without_language}/{language}", sheet_name)

      output_list = []
      for i, (original_line, translated_line) in enumerate(zip(original, translated)):
        line_id = original_line["key"]
        ja = original_line["translation"]
        zh = translated_line["translation"]
        stage = translated_line["stage"]
        comments = translated_line.get("context", "")

        if ja in translations:
          zh = translations[ja]["translation"]
          stage = 9
          comments = f"翻译匹配：{translations[ja]['source']}"

        output_list.append(
          {
            "key": line_id,
            "original": ja,
            "translation": zh,
            "stage": stage,
            "context": comments,
          }
        )

      with open(f"{root}/{file_name}", "w", -1, "utf-8", None, "\n") as writer:
        json.dump(output_list, writer, ensure_ascii=False, indent=2)


if __name__ == "__main__":
  import_official_names(DIR_CSV_ROOT, LANGUAGE, DIR_OFFICIAL_TRANSLATIONS_ROOT)
