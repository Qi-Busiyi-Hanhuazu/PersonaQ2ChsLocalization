import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys

SOURCE_PATH = "pinyin_ime/pinyin_candidates.S"
BUILD_DIR = "temp/pinyin_ime"
PREBUILT_DIR = "pinyin_ime/prebuilt"
PREBUILT_BINARY_PATH = f"{PREBUILT_DIR}/pinyin_candidates.bin"
PREBUILT_INFO_PATH = f"{PREBUILT_DIR}/pinyin_candidates.json"

CODE_BASE = 0x00100000
PAYLOAD_VA = 0x0052D5A0
PAYLOAD_LIMIT_VA = 0x0052E000

HOOKS = (
  (0x001F2B54, bytes.fromhex("E0 10 9F E5"), "pinyin_count_hook"),
  (0x001F2B14, bytes.fromhex("30 20 9F E5"), "pinyin_candidate_hook"),
  (0x0025F274, bytes.fromhex("1F 2E 8F E2"), "pinyin_dictionary_path_hook"),
)

DATA_FILE_PATCHES = (
  (
    0x002F2018,
    b"32/njpsq2Memo.a\0",
    b"32/njubase2.a\0\0\0",
  ),
)


def find_tool(name: str) -> str | None:
  if shutil.which(f"arm-none-eabi-{name}"):
    return f"arm-none-eabi-{name}"
  candidates = [
    f"{os.getenv('DEVKITARM')}/bin/arm-none-eabi-{name}",
    f"{os.getenv('DEVKITARM')}/bin/arm-none-eabi-{name}.exe",
    f"C:/devkitPro/devkitARM/bin/arm-none-eabi-{name}",
  ]
  for candidate in candidates:
    if shutil.which(candidate):
      return candidate
  return None


def create_arm_branch(source_va: int, target_va: int) -> bytes:
  delta = target_va - (source_va + 8)
  if delta % 4:
    raise ValueError("ARM branch target must be word aligned")
  displacement = delta // 4
  if not -(1 << 23) <= displacement < (1 << 23):
    raise ValueError("ARM branch target is out of range")
  return struct.pack("<I", 0xEA000000 | (displacement & 0x00FFFFFF))


def get_source_hash() -> str:
  with open(SOURCE_PATH, "rb") as reader:
    return hashlib.sha256(reader.read()).hexdigest()


def compile_payload() -> tuple[bytes, dict[str, int]] | None:
  gcc = find_tool("gcc")
  objcopy = find_tool("objcopy")
  nm = find_tool("nm")
  if not gcc or not objcopy or not nm:
    return None

  os.makedirs(BUILD_DIR, exist_ok=True)
  elf_path = f"{BUILD_DIR}/pinyin_candidates.elf"
  binary_path = f"{BUILD_DIR}/pinyin_candidates.bin"
  map_path = f"{BUILD_DIR}/pinyin_candidates.map"

  subprocess.run(
    [
      gcc,
      "-x",
      "assembler-with-cpp",
      "-nostdlib",
      "-march=armv6k",
      "-marm",
      f"-Wl,-Ttext=0x{PAYLOAD_VA:X}",
      "-Wl,-e,pinyin_count_hook",
      "-Wl,--gc-sections",
      f"-Wl,-Map={map_path}",
      "-o",
      elf_path,
      SOURCE_PATH,
    ],
    check=True,
  )
  subprocess.run(
    [objcopy, "-O", "binary", "-j", ".text", elf_path, binary_path],
    check=True,
  )
  nm_output = subprocess.run(
    [nm, "-n", elf_path],
    check=True,
    capture_output=True,
    text=True,
  ).stdout
  symbols = {
    fields[2]: int(fields[0], 16)
    for line in nm_output.splitlines()
    if len(fields := line.split()) == 3
  }

  with open(binary_path, "rb") as reader:
    payload = reader.read()
  if not payload or PAYLOAD_VA + len(payload) > PAYLOAD_LIMIT_VA:
    raise ValueError("pinyin payload is empty or exceeds the verified code cave")
  return payload, symbols


def load_prebuilt_payload() -> tuple[bytes, dict[str, int]]:
  with open(PREBUILT_BINARY_PATH, "rb") as reader:
    payload = reader.read()
  with open(PREBUILT_INFO_PATH, "r", -1, "utf8") as reader:
    info = json.load(reader)

  if info["source_sha256"] != get_source_hash():
    raise ValueError(
      "prebuilt pinyin payload is stale; run build_pinyin_ime.py --precompile with devkitARM"
    )
  if info["payload_sha256"] != hashlib.sha256(payload).hexdigest():
    raise ValueError("prebuilt pinyin payload hash mismatch")
  if info["payload_va"] != PAYLOAD_VA:
    raise ValueError("prebuilt pinyin payload address mismatch")
  if not payload or PAYLOAD_VA + len(payload) > PAYLOAD_LIMIT_VA:
    raise ValueError(
      "prebuilt pinyin payload is empty or exceeds the verified code cave"
    )
  return payload, {k: int(v) for k, v in info["symbols"].items()}


def build_payload() -> tuple[bytes, dict[str, int]]:
  if not os.getenv("PINYIN_IME_USE_PREBUILT"):
    compiled = compile_payload()
    if compiled:
      print("building pinyin payload with devkitARM")
      return compiled
  print("devkitARM not found; using prebuilt pinyin payload")
  return load_prebuilt_payload()


def save_prebuilt_payload():
  compiled = compile_payload()
  if not compiled:
    raise FileNotFoundError(
      "devkitARM not found; cannot refresh prebuilt pinyin payload"
    )
  payload, symbols = compiled
  os.makedirs(PREBUILT_DIR, exist_ok=True)
  with open(PREBUILT_BINARY_PATH, "wb") as writer:
    writer.write(payload)
  with open(PREBUILT_INFO_PATH, "w", -1, "utf8", None, "\n") as writer:
    json.dump(
      {
        "source_sha256": get_source_hash(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_va": PAYLOAD_VA,
        "symbols": {symbol: symbols[symbol] for _, _, symbol in HOOKS},
      },
      writer,
      indent=2,
    )
    writer.write("\n")

  print(f"wrote {PREBUILT_BINARY_PATH} and {PREBUILT_INFO_PATH}")


def install_pinyin_ime(data: bytearray):
  payload, symbols = build_payload()
  payload_offset = PAYLOAD_VA - CODE_BASE
  cave = data[payload_offset : payload_offset + len(payload)]
  if any(cave):
    raise ValueError(f"code cave at 0x{payload_offset:X} is not empty")

  for hook_va, expected, symbol in HOOKS:
    hook_offset = hook_va - CODE_BASE
    actual = bytes(data[hook_offset : hook_offset + len(expected)])
    if actual != expected:
      raise ValueError(
        f"unexpected code at hook 0x{hook_offset:X}: expected {expected.hex()}, got {actual.hex()}"
      )
    if symbol not in symbols:
      raise ValueError(f"missing payload symbol: {symbol}")

  for patch_va, expected, replacement in DATA_FILE_PATCHES:
    if len(expected) != len(replacement):
      raise ValueError("data-file path replacement must preserve its original size")
    patch_offset = patch_va - CODE_BASE
    actual = bytes(data[patch_offset : patch_offset + len(expected)])
    if actual != expected:
      raise ValueError(
        f"unexpected path at 0x{patch_offset:X}: expected {expected!r}, got {actual!r}"
      )

  data[payload_offset : payload_offset + len(payload)] = payload
  for hook_va, expected, symbol in HOOKS:
    hook_offset = hook_va - CODE_BASE
    data[hook_offset : hook_offset + len(expected)] = create_arm_branch(
      hook_va, symbols[symbol]
    )
  for patch_va, expected, replacement in DATA_FILE_PATCHES:
    patch_offset = patch_va - CODE_BASE
    data[patch_offset : patch_offset + len(expected)] = replacement


if __name__ == "__main__":
  if len(sys.argv) == 2 and sys.argv[1] == "--precompile":
    save_prebuilt_payload()
    sys.exit(0)
  if len(sys.argv) == 2 and sys.argv[1] == "--check-prebuilt":
    load_prebuilt_payload()
    print("prebuilt pinyin payload is up to date")
    sys.exit(0)
  if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <input code.bin> <output code.bin>")
    sys.exit(1)

  with open(sys.argv[1], "rb") as reader:
    code = bytearray(reader.read())
  install_pinyin_ime(code)
  os.makedirs(os.path.dirname(sys.argv[2]), exist_ok=True)
  with open(sys.argv[2], "wb") as writer:
    writer.write(code)
