"""Read the text of the images listed under "keep" in dataset/images.json (OCR).

Some college information is only in images: scanned notifications and scheme tables. This
script renders each kept image, reads its text with RapidOCR, rebuilds the lines (table cells
are separated by " | "), and saves the result for scripts/prepare_dataset.py.

Usage:
    python scripts/ocr_images.py

Reads  dataset/images.json and the PDFs in dataset/pdfs/
Writes dataset/ocr/ocr_text.json   {"<file>#<page>": "text", ...}
Needs  pymupdf and rapidocr_onnxruntime (pip install pymupdf rapidocr_onnxruntime)
"""

import json
import statistics
import tempfile
from pathlib import Path

import pymupdf
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
OUT = DATASET / "ocr" / "ocr_text.json"

MIN_IMAGE_SHARE = 0.08   # embedded images smaller than this share of the page are ignored (icons, logos)
LOW_TEXT_WORDS = 20      # a page with fewer words of real text is treated as one whole image
ZOOM = 2.5               # render at 2.5 x 72 = 180 dpi
MIN_CONFIDENCE = 0.5     # OCR pieces read with less confidence are dropped


def image_regions(page):
    """The regions of a page that are images, in a fixed order (k = 0, 1, ...)."""
    if len(page.get_text().split()) < LOW_TEXT_WORDS:
        return [page.rect]
    area = page.rect.width * page.rect.height
    regions = []
    for img in page.get_images(full=True):
        for rect in page.get_image_rects(img[0]):
            if rect.width * rect.height >= MIN_IMAGE_SHARE * area:
                regions.append(rect & page.rect)
    return regions


def rebuild_lines(result):
    """Groups OCR pieces into lines by their vertical position, left to right; wide gaps become ' | '."""
    pieces = []
    for box, text, score in result or []:
        if float(score) < MIN_CONFIDENCE:
            continue
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        pieces.append({"x0": min(xs), "x1": max(xs), "y": (min(ys) + max(ys)) / 2, "h": max(ys) - min(ys), "text": text})
    if not pieces:
        return ""
    height = statistics.median(p["h"] for p in pieces)
    lines = []
    for piece in sorted(pieces, key=lambda p: p["y"]):
        if lines and abs(piece["y"] - lines[-1][0]["y"]) < 0.6 * height:
            lines[-1].append(piece)
        else:
            lines.append([piece])
    out = []
    for line in lines:
        line.sort(key=lambda p: p["x0"])
        text = line[0]["text"]
        for prev, piece in zip(line, line[1:]):
            text += (" | " if piece["x0"] - prev["x1"] > 1.5 * height else " ") + piece["text"]
        out.append(text)
    return "\n".join(out)


def main():
    images = json.loads((DATASET / "images.json").read_text(encoding="utf-8"))
    ocr = RapidOCR()
    texts = {}
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        for item in images["keep"]:
            page = pymupdf.open(DATASET / "pdfs" / item["file"])[item["page"] - 1]
            region = image_regions(page)[item["k"]]
            png = Path(tmp) / "page.png"
            page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=region).save(png)
            result, _ = ocr(str(png))
            text = rebuild_lines(result)
            key = f"{item['file']}#{item['page']}"
            texts[key] = (texts[key] + "\n" + text) if key in texts else text
            print(f"{key:<55} {len(text.split()):>4} words")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(texts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"\nOCR text for {len(texts)} pages written to {OUT}")


if __name__ == "__main__":
    main()
