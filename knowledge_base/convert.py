import os
import json
import glob
import botocore
from pathlib import Path

OUTPUT_FILE = Path("knowledge_base/botocore_services.txt")

def get_botocore_data_path():
    """
    Automatically find the botocore data folder inside your environment.
    """
    botocore_path = Path(botocore.__file__).parent
    data_path = botocore_path / "data"

    if not data_path.exists():
        raise FileNotFoundError(f"Botocore data folder not found at: {data_path}")

    return data_path


def collect_json_files(root):
    """
    Recursively collect ALL JSON files in botocore/data
    """
    pattern = str(root / "**/*.json")
    return glob.glob(pattern, recursive=True)


def convert_json_files_to_text(json_files):
    """
    Read each JSON file and convert it into formatted text.
    """
    output_blocks = []

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Format JSON pretty for RAG
            block = f"### FILE: {file_path}\n\n"
            block += json.dumps(data, indent=2)
            block += "\n\n\n"

            output_blocks.append(block)

        except Exception as e:
            print(f"Failed to process {file_path}: {e}")

    return "\n".join(output_blocks)


def save_output(text):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"\n✔ Saved botocore service definitions to:\n{OUTPUT_FILE}\n")
    print(f"Total size: {len(text) / 1_000_000:.2f} MB")


def main():
    print("🔍 Locating botocore data folder...")
    data_path = get_botocore_data_path()
    print(f"📁 Found botocore data at: {data_path}\n")

    print("📂 Collecting JSON files...")
    json_files = collect_json_files(data_path)
    print(f"➡ Found {len(json_files)} JSON files\n")

    print("📝 Converting JSON files to text...")
    text = convert_json_files_to_text(json_files)

    print("💾 Saving output...")
    save_output(text)

    print("🎉 Conversion completed!")


if __name__ == "__main__":
    main()
