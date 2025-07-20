import os
import sys
from pathlib import Path
from datetime import datetime

def rename_files(prefix, folder_path):
    folder = Path(folder_path)
    if not folder.is_dir():
        print(f"{folder_path} is not a valid directory.")
        return
    files = [f for f in folder.iterdir() if f.is_file()]
    # Sort files by last modified time and name for stability
    files.sort(key=lambda f: (f.stat().st_mtime, f.name))
    temp_names = []
    # First pass: rename to temp names to avoid collisions
    for idx, file in enumerate(files, 1):
        ext = file.suffix
        temp_name = f"__temp__{idx:04d}{ext}"
        temp_path = folder / temp_name
        file.rename(temp_path)
        temp_names.append(temp_path)
    # Second pass: rename temp names to final names
    for idx, temp_path in enumerate(temp_names, 1):
        ext = temp_path.suffix
        new_name = f"{prefix}_{idx:04d}{ext}"
        new_path = folder / new_name
        print(f"Renaming {temp_path.name} -> {new_name}")
        temp_path.rename(new_path)
    print(f"Renamed {len(files)} files.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python rename_by_date.py <filename_prefix> <folder_path>")
    else:
        rename_files(sys.argv[1], sys.argv[2])
