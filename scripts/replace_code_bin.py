from helper import CODE_BIN_PATH, CODE_BIN_REPLACED_PATH

ARM9_REPLACEMENT = {
  # 0x002D88: "0A 18 A0 E3",
  # 跳过 patch101.cpk
  0x002DC0: "00 00 A0 E1 00 00 A0 E1 00 00 A0 E1 02 10 A0 E3",
  # 章节名 ひかり → ？？？
  0x1AEE78: "02 20 A0 E3",
  0x1AEEB0: "02 10 88 E2",
  0x1AEED4: "02 20 A0 E3",
  0x1AEF08: "02 10 88 E2",
  # ？？？の映画内の探索ができます
  0x2A635C: "04 00 54 E3 00 00 55 03 02 00 80 02 03 00 00 EA",
  0x2A6370: "03 00 54 E3 00 00 55 03 02 00 80 02 73 6C 00 EB 02 00 00 EA",
  # 敵 → 敵方
  0x33ECB4: "8E 2F 8F E2",
  0x33EE9C: "28 20 9F E5",
  0x33EECC: "65 05 00 00",
  0x33EEF4: "93 47 95 FB 00 00 55 00",
  # 月 → 月亮
  0x45377C: "8C 8E 97 BA 00 00 00 00",
  0x485CEC: "7C 37 55 00",
}


def replace_code_bin(input_path: str, output_path: str):
  with open(input_path, "rb") as reader:
    data = bytearray(reader.read())

  for offset, replacement in ARM9_REPLACEMENT.items():
    raw = bytes.fromhex(replacement)
    data[offset : offset + len(raw)] = raw

  with open(output_path, "wb") as writer:
    writer.write(data)


if __name__ == "__main__":
  replace_code_bin(CODE_BIN_PATH, CODE_BIN_REPLACED_PATH)
