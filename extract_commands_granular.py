import os
import re
import json
from pathlib import Path

SPEC_DIR = "/home/pang/work/AI/AI_Demo/CXL_Spec_CCI_Test_Plan/spec_chapters"
OUTPUT_DIR = "/home/pang/work/AI/AI_Demo/CXL_Spec_CCI_Test_Plan/spec_commands"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "checkpoint.json")


def sanitize_filename(name):
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w.-]", "", name)
    return name


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed": [], "last_chapter": None}


def save_checkpoint(checkpoint):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


def find_commands_in_content(content):
    """Find all command sections by parsing lines with (Opcode XXXXh)"""
    commands = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if "(" in line and "Opcode" in line:
            parts = line.split("(")
            if len(parts) == 2 and parts[0].strip().startswith("8."):
                cmd_id = parts[0].strip()
                opcode_part = parts[1].strip()
                opcode_match = re.match(r"(Opcode\s+\w+h)", opcode_part)
                if opcode_match:
                    opcode = opcode_match.group(1)
                    # Get command name (after chapter number)
                    cmd_parts = cmd_id.split(maxsplit=1)
                    if len(cmd_parts) >= 2:
                        chapter_num = cmd_parts[0]
                        cmd_name = cmd_parts[1].rsplit("(", 1)[0].strip()

                        # Find content start (this line)
                        start_pos = content.find(line)
                        # Find next command or end
                        next_cmd_start = None
                        for j in range(i + 1, len(lines)):
                            if (
                                "(" in lines[j]
                                and "Opcode" in lines[j]
                                and lines[j].strip().startswith("8.")
                            ):
                                next_cmd_start = content.find(
                                    lines[j], start_pos + len(line)
                                )
                                break
                        if next_cmd_start is None:
                            next_cmd_start = len(content)

                        cmd_content = content[start_pos:next_cmd_start]
                        commands.append((chapter_num, cmd_name, opcode, cmd_content))

    return commands


def extract_overview(content, chapter_key):
    """Extract overview text before first command"""
    lines = content.split("\n")
    overview_lines = []

    for line in lines:
        if "(" in line and "Opcode" in line and line.strip().startswith("8."):
            break
        overview_lines.append(line)

    return "\n".join(overview_lines).strip()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed", []))

    print(f"Output: {OUTPUT_DIR}")
    print(f"Checkpoint: {len(processed)} files already processed\n")

    # Load 8.2.9 Introduction
    intro_file = os.path.join(SPEC_DIR, "8.2.9_Introduction.txt")
    with open(intro_file, "r", encoding="utf-8") as f:
        intro_8_2_9 = f.read()

    # Save/update introduction file
    intro_out = os.path.join(OUTPUT_DIR, "8.2.9_Introduction.txt")
    with open(intro_out, "w", encoding="utf-8") as f:
        f.write(intro_8_2_9)
    processed.add(intro_out)
    print(f"Created: 8.2.9_Introduction.txt")

    # Load all spec chapters
    chapters = {}
    for f in sorted(Path(SPEC_DIR).glob("*.txt")):
        if f.stem != "8.2.9_Introduction":
            chapters[f.stem] = f.read_text(encoding="utf-8")

    # Process each sub-chapter in order
    sub_chapters = sorted([k for k in chapters.keys() if k.startswith("8.2.9.")])

    for chapter_key in sub_chapters:
        chapter_content = chapters[chapter_key]
        chapter_dir = os.path.join(OUTPUT_DIR, chapter_key)

        print(f"\n{'=' * 60}")
        print(f"Processing: {chapter_key}")

        # Extract overview
        overview = extract_overview(chapter_content, chapter_key)
        overview_file = os.path.join(chapter_dir, f"{chapter_key}_Overview.txt")

        if overview_file not in processed:
            os.makedirs(chapter_dir, exist_ok=True)
            with open(overview_file, "w", encoding="utf-8") as f:
                f.write(intro_8_2_9)
                f.write("\n\n")
                f.write(f"=== {chapter_key} Overview ===\n\n")
                f.write(overview)
            processed.add(overview_file)
            print(f"  Created: {chapter_key}_Overview.txt")
        else:
            print(f"  Skipped: {chapter_key}_Overview.txt")

        # Find commands
        commands = find_commands_in_content(chapter_content)
        print(f"  Found {len(commands)} commands")

        for chapter_num, cmd_name, opcode, cmd_content in commands:
            filename = f"{chapter_num}_{cmd_name}.txt"
            filename = sanitize_filename(filename)
            filepath = os.path.join(chapter_dir, filename)

            if filepath in processed:
                print(f"    Skipped: {filename}")
                continue

            os.makedirs(chapter_dir, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(intro_8_2_9)
                f.write("\n\n")
                f.write(f"=== {chapter_key} Overview ===\n\n")
                f.write(overview)
                f.write("\n\n")
                f.write(f"=== {chapter_num} {cmd_name} ({opcode}) ===\n\n")
                f.write(cmd_content)

            processed.add(filepath)
            print(f"    Created: {filename}")

        save_checkpoint({"processed": list(processed), "last_chapter": chapter_key})
        print(f"  Progress saved")

    print(f"\n{'=' * 60}")
    print(f"Extraction complete!")
    print(f"Total files: {len(processed)}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
