import pymupdf
import pdfplumber
import re
import os

PDF_PATH = "/home/pang/work/AI/AI_Demo/CXL_Spec_CCI_Test_Plan/CXL.pdf"
OUTPUT_DIR = "/home/pang/work/AI/AI_Demo/CXL_Spec_CCI_Test_Plan/spec_chapters"

HEADER_HEIGHT = 60
FOOTER_HEIGHT = 60

BAD_PATTERNS = [
    r"YPOC",
    r"NOITAULAVE",
    r"LAVE",
]


def clean_watermark_text(text):
    if not text:
        return ""
    for pattern in BAD_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def find_text_top(page_obj, text_str):
    if not text_str:
        return None
    matches = page_obj.search(text_str)
    if matches:
        return matches[0]["top"]
    first_word = text_str.strip().split(" ")[0]
    if len(first_word) > 1 and any(char.isdigit() for char in first_word):
        matches = page_obj.search(first_word)
        if matches:
            return matches[0]["top"]
    return None


def extract_chapter_content(
    pdf_path,
    start_page,
    end_page,
    start_title,
    end_title=None,
    include_end_page_full=False,
):
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        if end_page is None:
            end_page = len(pdf.pages) - 1

        for p_num in range(start_page, min(end_page + 1, len(pdf.pages))):
            page = pdf.pages[p_num]
            width = page.width
            height = page.height

            valid_top = HEADER_HEIGHT
            valid_bottom = height - FOOTER_HEIGHT

            if p_num == start_page and start_title:
                title_top = find_text_top(page, start_title)
                if title_top is not None:
                    valid_top = max(valid_top, title_top)

            if p_num == end_page and end_title and not include_end_page_full:
                next_top = find_text_top(page, end_title)
                if next_top is not None:
                    valid_bottom = min(valid_bottom, next_top - 2)

            if valid_top >= valid_bottom:
                continue

            try:
                bbox = (0, valid_top, width, valid_bottom)
                cropped_page = page.crop(bbox=bbox)
                text = cropped_page.extract_text()
                clean_text = clean_watermark_text(text)
                if clean_text:
                    results.append(clean_text)
            except Exception as e:
                print(f"   [P{p_num + 1}] Error: {e}")

    return "\n".join(results)


def sanitize_filename(name):
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w.-]", "", name)
    return name


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    doc = pymupdf.open(PDF_PATH)
    toc = doc.get_toc()
    doc.close()

    main_start_page = None
    main_end_page = None

    for i, entry in enumerate(toc):
        level, title, page_num = entry
        if isinstance(title, str) and title == "8.2.9 Component Command Interface":
            main_start_page = page_num - 1
            for j in range(i + 1, len(toc)):
                next_level, next_title, next_page = toc[j]
                if isinstance(next_title, str):
                    if next_title.startswith("8.2.9."):
                        continue
                    main_end_page = next_page - 2
                    break
            break

    if main_start_page is None:
        print("8.2.9 not found in TOC")
        return

    sub_chapters = []
    for i, entry in enumerate(toc):
        level, title, page_num = entry
        if isinstance(title, str) and title.startswith("8.2.9.") and level >= 4:
            sub_chapters.append((title, page_num - 1))

    print(f"8.2.9 section: pages {main_start_page + 1} to {main_end_page + 1}")
    print(f"Found {len(sub_chapters)} sub-chapters")

    intro_end_page = sub_chapters[0][1] - 1
    intro_content = extract_chapter_content(
        PDF_PATH,
        main_start_page,
        intro_end_page,
        start_title="8.2.9 Component Command Interface",
        end_title=sub_chapters[0][0] if sub_chapters else None,
    )
    intro_path = os.path.join(OUTPUT_DIR, "8.2.9_Introduction.txt")
    with open(intro_path, "w", encoding="utf-8") as f:
        f.write(intro_content)
    print(f"Created: 8.2.9_Introduction.txt ({len(intro_content)} chars)")

    for idx in range(len(sub_chapters)):
        title, start_page = sub_chapters[idx]
        is_last_chapter = idx + 1 == len(sub_chapters)

        if idx + 1 < len(sub_chapters):
            end_title = sub_chapters[idx + 1][0]
            end_page_raw = sub_chapters[idx + 1][1]
            include_end_page_full = False
        else:
            end_title = None
            end_page_raw = main_end_page
            include_end_page_full = True

        content = extract_chapter_content(
            PDF_PATH,
            start_page,
            end_page_raw,
            start_title=title,
            end_title=end_title,
            include_end_page_full=include_end_page_full,
        )

        filename = sanitize_filename(title) + ".txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {filename} ({len(content)} chars)")

    print(f"\nDone. Extracted {len(sub_chapters) + 1} files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
