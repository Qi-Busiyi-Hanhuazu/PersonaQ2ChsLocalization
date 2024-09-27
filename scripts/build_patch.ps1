$3dstool = "bin\3dstool\3dstool.exe"
$makerom = "bin\Project_CTR\makerom.exe"
$cpkmakec = "bin\CRI_File_System_Tools_v2.40.13.0\cpkmakec.exe"
$pq2helper = "bin\PersonaQ2ChsLocalizationHelper\PersonaQ2ChsLocalizationHelper\bin\Release\net8.0-windows\publish\PersonaQ2ChsLocalizationHelper.exe"

# Clean output folder
if (Test-Path -Path "out\" -PathType "Container") {
  Remove-Item -Recurse -Force "out\"
}
if (Test-Path -Path "temp\" -PathType "Container") {
  Remove-Item -Recurse -Force "temp\"
}

# Unpack/extract original files
if (-Not (Test-Path -Path "unpacked\exefs\code.bin" -PathType "Leaf")) {
  if (Test-Path -Path "unpacked\" -PathType "Container") {
    Remove-Item -Recurse -Force "unpacked\"
  }
  New-Item -ItemType Directory -Path "unpacked" -Force
  & $3dstool -xvtf cxi "original_files\00000002.app" --header "unpacked\ncch0_header.bin" --exh "unpacked\exheader.bin" --exefs "unpacked\exefs.bin" --romfs "unpacked\romfs.bin" --logo "unpacked\logo.bin" --plain "unpacked\plain.bin"
  & $3dstool -xvtfu exefs "unpacked\exefs.bin" --header "unpacked\exefs_header.bin" --exefs-dir "unpacked\exefs"
  & $3dstool -xvtf romfs "unpacked\romfs.bin" --romfs-dir "unpacked\romfs"
  & $cpkmakec "unpacked\romfs\patch101.cpk" -extract="unpacked\patch102"
  & $cpkmakec "unpacked\romfs\patch102.cpk" -extract="unpacked\patch102"
  & $cpkmakec "original_files\addition_files.cpk" -extract="unpacked\addition_files"
}
Copy-Item -Path "unpacked\patch102" -Destination "temp\patch102" -Recurse

# Prepare for tools
dotnet publish -c Release --framework "net8.0-windows" "bin\PersonaQ2ChsLocalizationHelper\PersonaQ2ChsLocalizationHelper\PersonaQ2ChsLocalizationHelper.csproj"

# Unpack/extract original files
& $pq2helper export -i "unpacked\addition_files" -o "temp\export"
python scripts\copy_replaced_files.py
python scripts\replace_code_bin.py
python scripts\export_code_bin.py
python scripts\export_ctd.py
python scripts\export_tbl.py

# Convert texts and create a character table
python scripts\remove_duplicate_files.py
# python scripts\import_official_names.py
python scripts\convert_messages_to_json.py
python scripts\import_csv_to_json.py
python scripts\generate_char_table.py
python scripts\convert_json_to_messages.py
python scripts\copy_duplicate_files.py
python scripts\copy_images.py

# Import texts
python scripts\import_tbl.py
python scripts\import_ctd.py
python scripts\import_code_bin.py
& $pq2helper import -i "unpacked\addition_files" -j "temp\import" -o "temp\patch102"

# Create new font
New-Item -ItemType Directory -Path "temp\font" -Force
Push-Location "temp\font"
python ..\..\bin\3dstools\bcfnt.py -a -x -y -f ..\..\unpacked\addition_files\font\seurapro_12_12.bcfnt
python ..\..\bin\3dstools\bcfnt.py -a -x -y -f ..\..\unpacked\addition_files\font\seurapro_13_13.bcfnt
Pop-Location
python scripts\create_new_font.py
New-Item -ItemType Directory -Path "temp\patch102\font" -Force
Push-Location "temp\new_font"
python ..\..\bin\3dstools\bcfnt.py -c -y -f ..\patch102\font\seurapro_12_12.bcfnt
python ..\..\bin\3dstools\bcfnt.py -c -y -f ..\patch102\font\seurapro_13_13.bcfnt
Pop-Location

# Repack cpk
New-Item -Type "Directory" -Path "temp\patch101"
Write-Output "" > "temp\patch101\.gitkeep"
& $cpkmakec "temp\patch101" "out\00040000001CBE00\romfs\patch101.cpk" -mode=FILENAME -forcecompress
& $cpkmakec "temp\patch102" "out\00040000001CBE00\romfs\patch102.cpk" -mode=FILENAME -forcecompress

# Build cia
New-Item -Type "Directory" -Path "temp\repack" -Force
Copy-Item -Path "unpacked\exefs\icon.icn" -Destination "out\00040000001CBE00\exefs\icon.icn" -Force
& $3dstool -cvtfz exefs "temp\repack\exefs.bin" --header "unpacked\exefs_header.bin" --exefs-dir "out\00040000001CBE00\exefs"
& $3dstool -cvtf romfs "temp\repack\romfs.bin" --romfs-dir "out\00040000001CBE00\romfs"
& $3dstool -cvtf cxi "temp\repack\00000002.app" --header "unpacked\ncch0_header.bin" --exh "unpacked\exheader.bin" --exefs "temp\repack\exefs.bin" --romfs "temp\repack\romfs.bin" --logo "unpacked\logo.bin" --plain "unpacked\plain.bin"
& $makerom -target p -ignoresign -f cia -content "temp\repack\00000002.app:0:0x00" -content "original_files\00000001.app:1:0x01" -o "out\00040000001CBE00.cia" -major 2 -minor 3 -micro 0
