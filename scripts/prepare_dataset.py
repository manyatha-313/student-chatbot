"""Prepare the college PDFs for the Campus Regulations Assistant (problem statement 2A).

Follows plans/datasetplan.md: check each PDF, clean the text page by page, split it into
chunks (by clause for the handbook, by course and unit for the syllabus) and save the chunks.

Usage:
    python scripts/prepare_dataset.py

Reads  dataset/documents.json, the PDFs in dataset/pdfs/ and, when present, the text read
       from images by scripts/ocr_images.py (dataset/ocr/ocr_text.json)
Writes dataset/processed/chunks.jsonl  (one chunk per line)
       dataset/processed/report.md     (checks and statistics)
Needs  pypdf (pip install pypdf)
"""

import json
import random
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
PDF_DIR = DATASET / "pdfs"
OCR_FILE = DATASET / "ocr" / "ocr_text.json"
OUT_DIR = DATASET / "processed"
IMAGE_MARKER = "[Text read from an image"    # starts OCR text: "[Text read from an image: <what it is>]"

MAX_WORDS = 130       # longest chunk body; leaves room for the prefix inside MiniLM's 256 tokens
MIN_WORDS = 30        # shorter blocks are joined with the next block on the same page
WINDOW = 120          # fallback split: words per chunk
OVERLAP = 30          # fallback split: words shared by neighbouring chunks
LOW_TEXT_WORDS = 20   # a page with fewer words is treated as an image-only page
HEADER_SHARE = 0.30   # a line repeated at the top/bottom of this share of pages is a header/footer

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}

# ---------------------------------------------------------------- headings
CLAUSE = re.compile(r"^(SRE|PG|MCA|MBA)\s*(\d+(?:\.\d+)+)\s*:?\s*(.*)$")
DEFINITION = re.compile(r"^(\d{1,2})\s*\.\s*([A-Z][^:.]{2,60}):")
STAFF_GROUP = re.compile(r"^([A-Za-z&().,/ -]{2,40}):\s*(Teaching|Non-Teaching)\s*$", re.I)
SUBJECT = re.compile(r"^(?:Subject|Course)(?:\s+(?:Title|Name))?\s*:\s*(.+)$", re.I)
SUBJECT_CODE = re.compile(r"(?:Subject|Course|Sub\.?)\s*Code\s*:\s*([0-9]{2}\s?[A-Z]{2,}[0-9A-Z]*|[A-Z]{2,}[0-9][0-9A-Z]*)", re.I)
UNITS = re.compile(r"^(?:Unit|Module)\s+(?:No\.?\s+)?(?:Description|Contents?)\b", re.I)
UNIT_ROW = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|v)(?:\s+|$)(.*)$")
SYLLABUS_HEADINGS = [
    (re.compile(r"^(?:Sl\.?\s*No\.?\s*)?Course\s+Objectives", re.I), "Course Objectives"),
    (re.compile(r"^Course\s+Outcomes?\b(?!\s*:?\s*$)|^Course\s+outcome\s+Descriptions?|^Course\s+Outcomes?\s*:?\s*$", re.I), "Course Outcomes"),
    (re.compile(r"^Text\s*Books?\b", re.I), "Text Books"),
    (re.compile(r"^Reference\s+Books?\b", re.I), "Reference Books"),
    (re.compile(r"^(?:E-?\s*resources|Web\s+links|MOOC|Online\s+resources)", re.I), "Online Resources"),
    (re.compile(r"^(?:List\s+of\s+(?:Experiments|Programs)|(?:Sl\.?\s*No\.?\s*)?(?:Experiments|Programs)\s*$)", re.I), "Lab Experiments"),
    (re.compile(r"^Scheme\s+of\s+Teaching", re.I), "Scheme of Teaching and Examination"),
]
SEMESTER_PATTERNS = [
    re.compile(r"Semester\s*:\s*([IVX]+|\d)\b", re.I),
    re.compile(r"\b(\d)\s*(?:st|nd|rd|th)\s+Sem(?:ester)?\b", re.I),
    re.compile(r"\bSemester\s+([IVX]+)\b"),
    re.compile(r"\bSEM\s*(\d)\b"),
]
ACADEMIC_YEAR = re.compile(r"academic\s+year\s*:?\s*(2\s*0\s*\d\s*\d)\s*[-–]\s*(?:20)?(\d{2})\b", re.I)

# ---------------------------------------------------------------- noise lines
NOISE = [
    re.compile(r"^Signature\s+of", re.I),
    re.compile(r"^\(?(?:HoD|Dean|Principal|Course\s+coordinator)\)?\s*$", re.I),
    re.compile(r"^(?:Academic\s+Affairs\)|coordinator)\s*$", re.I),
    re.compile(r"^(?:PO|PSO)\s*\d*\s*$|^(?:PO/PSO|CO|PO|PSO)\s*$", re.I),            # CO-PO matrix labels
    re.compile(r"^CO\s*\d+(?:\s+[0-3-])+\s*$", re.I),                                # CO-PO matrix rows
    re.compile(r"^[0-3-](?:\s+[0-3-])+\s*$"),                                        # bare matrix rows
    re.compile(r"^Course\s+Articulation\s+Matrix\s*$", re.I),
]
SYLLABUS_NOISE = [
    re.compile(r"^Department\s*:.{0,80}$", re.I),               # "Department: CSE Semester: V" (kept as metadata)
    re.compile(r"^Department\s+of\s+[A-Za-z&.() ]{5,60}$", re.I),
]
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", " ": " ", "‟": '"', "‘": "'", "’": "'",
             "“": '"', "”": '"', "–": "-", "—": "-", "•": "-", "": "-"}


def normalise(line):
    for bad, good in LIGATURES.items():
        line = line.replace(bad, good)
    return re.sub(r"\s+", " ", line).strip()


def header_key(line):
    return re.sub(r"\d+", "#", line.lower())


def is_heading_like(line):
    """Headings are never removed as page headers - except the scheme title, which some syllabus PDFs print on every page."""
    return bool(CLAUSE.match(line) or SUBJECT.match(line) or UNITS.match(line)
                or any(p.match(line) for p, name in SYLLABUS_HEADINGS
                       if name != "Scheme of Teaching and Examination"))


def is_caps_heading(line):
    letters = [c for c in line if c.isalpha()]
    words = line.split()
    return (2 <= len(words) <= 10 and len(letters) >= 6 and sum(c.isdigit() for c in line) <= 2
            and sum(c.isupper() for c in letters) / len(letters) > 0.8)


def clause_title(rest):
    """'Attendance Requirements: ...' -> 'Attendance Requirements'; a clause that opens with a sentence has no title."""
    title = rest.split(":")[0].strip() if ":" in rest else rest.strip()
    if ":" not in rest and (title.endswith(".") or len(title.split()) > 8):
        return ""
    return title if len(title.split()) <= 10 else ""


# ---------------------------------------------------------------- step 1: read and check
def read_pages(path):
    return [page.extract_text() or "" for page in PdfReader(path).pages]


def find_semester(text):
    for pattern in SEMESTER_PATTERNS:
        m = pattern.search(text)
        if m:
            value = m.group(1).upper()
            number = ROMAN.get(value) or (int(value) if value.isdigit() else None)
            if number and 1 <= number <= 8:
                return number
    return None


def find_academic_year(pages):
    years = Counter()
    for text in pages:
        for m in ACADEMIC_YEAR.finditer(text):
            start = re.sub(r"\s", "", m.group(1))
            years[f"{start}-{m.group(2)}"] += 1
    return years.most_common(1)[0][0] if years else None


# ---------------------------------------------------------------- step 2: clean
def clean_pages(raw_pages, doc_type):
    """Returns one list of cleaned lines per page. Page numbering is unchanged."""
    noise = NOISE + (SYLLABUS_NOISE if doc_type == "syllabus" else [])
    pages = [[normalise(l) for l in text.splitlines()] for text in raw_pages]
    pages = [[l for l in lines if l] for lines in pages]

    # lines repeated at the top or bottom of many pages are headers/footers
    edge_counts = Counter()
    for lines in pages:
        edge = {header_key(l) for l in lines[:8] + lines[-3:] if not is_heading_like(l)}
        edge_counts.update(edge)
    limit = max(3, HEADER_SHARE * len(pages))
    repeated = {k for k, n in edge_counts.items() if n >= limit}

    cleaned = []
    for lines in pages:
        kept = []
        for i, line in enumerate(lines):
            at_edge = i < 8 or i >= len(lines) - 3
            if at_edge and header_key(line) in repeated:
                continue
            if at_edge and re.fullmatch(r"(?:Page\s*\|?\s*)?\d{1,3}", line, re.I):
                continue                                              # page numbers
            if any(p.match(line) for p in noise):
                continue
            if kept and re.search(r"[a-z]-$", kept[-1]) and line[:1].islower():
                kept[-1] = kept[-1][:-1] + line                       # exami- / nation
                continue
            kept.append(line)
        cleaned.append(kept)
    return cleaned


# ---------------------------------------------------------------- step 3: split into blocks
def detect_heading(line, doc, state):
    """Returns (kind, label) when the line starts a new block, otherwise None. Updates state."""
    if line.startswith(IMAGE_MARKER):
        state["ocr"] = True
        return "sub", line.strip("[]")
    if state.get("ocr"):
        return None                       # text read from an image stays one block under its image label
    if doc["type"] != "syllabus":                                  # handbook
        for part in doc.get("parts", []):
            if line.startswith(part["starts_with"]):
                state.update(part=part["title"], contact=part["contact"], parent=None)
                return "part", part["title"]
        m = CLAUSE.match(line)
        if m:
            code, number, rest = m.groups()
            label = f"{code} {number} {clause_title(rest)}".strip()
            if number.endswith(".0"):
                state["parent"] = label
            return "clause", label
        m = DEFINITION.match(line)
        if m:
            return "item", f"{m.group(1)}. {m.group(2).strip()}"
        m = STAFF_GROUP.match(line)
        if m:
            return "sub", f"{m.group(1).strip()} - {m.group(2).title()} staff"
        if line.endswith(":") and 1 <= len(line.split()) <= 8 and line[0].isupper():
            return "sub", line.rstrip(":").strip()
        if is_caps_heading(line):
            return "sub", line
        return None

    # syllabus
    m = SUBJECT.match(line)
    if m:
        title = re.sub(r"\s*\(Common to.*$", "", m.group(1), flags=re.I).strip()
        state.update(course=title, code=None, in_units=False)
        return "course", title
    if UNITS.match(line):
        state["in_units"] = True
        return "units", "Units"
    for pattern, name in SYLLABUS_HEADINGS:
        if pattern.match(line):
            state["in_units"] = False
            if name == "Scheme of Teaching and Examination":
                state.update(course=None, code=None)
            return "sub", name
    if state.get("in_units"):
        m = UNIT_ROW.match(line)
        if m:
            roman = m.group(1).upper()
            return "unit", f"Unit {roman} (Unit {ROMAN[roman]})"     # students ask "unit 2" as often as "unit II"
    if is_caps_heading(line) and not state.get("course"):
        return "sub", line
    return None


def section_of(doc, state):
    if doc["type"] != "syllabus":
        return state.get("part") or doc.get("default_section", "Front matter")
    if state.get("course"):
        code = f"{state['code']} " if state.get("code") else ""
        return f"{code}{state['course']}"
    return "Programme overview and scheme"


def split_into_blocks(doc, pages, raw_pages, ocr_pages):
    """Groups each page's lines under the heading that precedes them. Blocks never cross pages.
    ocr_pages: page numbers whose whole text was read from an image."""
    state = {"part": None, "parent": None, "course": None, "code": None, "last": None,
             "semester": None, "in_units": False, "contact": doc.get("contact")}
    blocks = []
    for page_number, (lines, raw) in enumerate(zip(pages, raw_pages), start=1):
        state["ocr"] = False
        if page_number in ocr_pages:                        # a scanned notice or table stands on its own
            state.update(course=None, code=None, in_units=False, last=None)
        if doc.get("pages_stand_alone"):                    # e.g. a brochure: each page is its own topic
            state["last"] = None
        if doc["type"] == "syllabus":
            state["semester"] = find_semester(raw) or state["semester"]
        current = None
        for line in lines:
            if doc["type"] == "syllabus" and not state["ocr"]:
                m = SUBJECT_CODE.search(line)
                if m:
                    code = m.group(1).upper().replace(" ", "")
                    if (not state.get("course") or state.get("code")) and current and current["lines"]:
                        # no "Subject:" line: the course title is the line just above "Sub. Code:"
                        title = current["lines"].pop()
                        state.update(course=title, code=code, in_units=False, last=title)
                        current = {"page": page_number, "labels": [title], "parent": None,
                                   "section": section_of(doc, state), "semester": state.get("semester"),
                                   "contact": doc.get("contact"), "ocr": state["ocr"], "lines": [title]}
                        blocks.append(current)
                    else:
                        state["code"] = code
                        if current:
                            current["section"] = section_of(doc, state)
            found = detect_heading(line, doc, state)
            if found or current is None:
                if found:
                    label = found[1]
                    if not label.startswith(IMAGE_MARKER.strip("[")):
                        state["last"] = label
                else:                                                 # a page that continues the last heading
                    label = f"{state['last']} (continued)" if state.get("last") else None
                if found and found[0] == "part":
                    state["last"] = None
                current = {"page": page_number, "labels": [label] if label else [],
                           "parent": state.get("parent") if doc["type"] != "syllabus" else None,
                           "section": section_of(doc, state), "semester": state.get("semester"),
                           "contact": state.get("contact") or doc.get("contact"),
                           "ocr": state["ocr"], "lines": []}
                blocks.append(current)
            current["lines"].append(line)
    return [b for b in blocks if b["lines"]]


# ---------------------------------------------------------------- step 4: size the chunks
def words_of(block):
    return sum(len(l.split()) for l in block["lines"])


def merge_small(blocks):
    """Joins a short block with the next one on the same page, within the same section and clause."""
    merged = []
    for block in blocks:
        prev = merged[-1] if merged else None
        if (prev and prev["page"] == block["page"] and prev["section"] == block["section"]
                and prev["parent"] == block["parent"] and prev["ocr"] == block["ocr"] and words_of(prev) < MIN_WORDS
                and (words_of(prev) + words_of(block) <= MAX_WORDS + 20 or is_heading_only(prev))):
            prev["lines"] += block["lines"]
            prev["labels"] += [h for h in block["labels"] if h not in prev["labels"]]
            continue
        merged.append(block)
    # a heading left alone at the foot of a page: the next page's chunks already carry it as "(continued)"
    return [b for b in merged if not is_heading_only(b)]


def is_heading_only(block):
    return len(block["lines"]) == 1 and block["labels"] and words_of(block) < 12


def heading_of(block):
    parent = block["parent"]
    others = [h for h in block["labels"] if h != parent]
    if parent and others:
        return f"{parent} > {', '.join(others)}"
    return parent or "; ".join(others)


def split_large(block):
    if words_of(block) <= MAX_WORDS + 20:
        return [block]
    # split on line boundaries into windows of about WINDOW words, overlapping by about OVERLAP words
    lines, parts, start = block["lines"], [], 0
    while start < len(lines):
        count, end = 0, start
        while end < len(lines) and (count < WINDOW or end == start):
            count += len(lines[end].split())
            end += 1
        if end < len(lines) and sum(len(l.split()) for l in lines[end:]) < MIN_WORDS:
            end = len(lines)                                         # do not leave a tiny tail
        parts.append({**block, "lines": lines[start:end]})
        if end >= len(lines):
            break
        back, back_words = end, 0
        while back > start + 1 and back_words < OVERLAP:
            back -= 1
            back_words += len(lines[back].split())
        start = back if back > start else end
    # a single very long line (rare) is split by words
    result = []
    for part in parts:
        words = " ".join(part["lines"]).split()
        if len(words) <= MAX_WORDS + OVERLAP:
            result.append(part)
            continue
        for s in range(0, len(words), WINDOW - OVERLAP):
            result.append({**part, "lines": [" ".join(words[s:s + WINDOW])]})
            if s + WINDOW >= len(words):
                break
    return result


# ---------------------------------------------------------------- step 5: build chunk records
def describe(doc, branches):
    if doc["type"] != "syllabus":
        return doc["title"]
    return f"{doc['program']} {doc['branch']} ({branches[doc['branch']]}) Year {doc['year']} Syllabus"


def make_chunks(doc, blocks, branches):
    chunks = []
    name = Path(doc["file"]).name
    for block in blocks:
        for piece in split_large(block):
            text = "\n".join(piece["lines"]).strip()
            if len(text.split()) <= 5:
                continue
            heading = heading_of(piece)
            prefix = [describe(doc, branches)]
            if doc["type"] == "syllabus" and piece["semester"]:
                prefix[0] += f", Semester {piece['semester']}"
            prefix.append(piece["section"])
            if heading and heading != piece["section"]:
                prefix.append(heading)
            chunk = {
                "id": f"{Path(name).stem}-p{piece['page']}-{len(chunks) + 1}",
                "doc": name,
                "title": describe(doc, branches),
                "type": doc["type"],
                "program": doc.get("program"),
                "branch": doc.get("branch"),
                "branch_full": branches.get(doc.get("branch")),
                "year": doc.get("year"),
                "semester": piece["semester"],
                "academic_year": doc.get("academic_year"),
                "department": doc.get("department"),
                "publisher": doc.get("publisher", "SSIT / SSAHE"),
                "page": piece["page"],
                "section": piece["section"],
                "heading": heading,
                "contact": piece["contact"] or (f"Head of the Department, {doc['department']}, SSIT"
                                                if doc.get("department") else None),
                "text": text,
                "embed_text": " | ".join(prefix) + " | " + " ".join(text.split()),
                "words": len(text.split()),
                "extraction": "ocr" if piece["ocr"] else "text",
            }
            chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------- run
def main():
    manifest = json.loads((DATASET / "documents.json").read_text(encoding="utf-8"))
    branches = manifest["branches"]
    ocr_text = json.loads(OCR_FILE.read_text(encoding="utf-8")) if OCR_FILE.exists() else {}
    images = json.loads((DATASET / "images.json").read_text(encoding="utf-8"))
    image_what = {f"{i['file']}#{i['page']}": i["what"] for i in images["keep"]}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_chunks, report = [], []

    for doc in manifest["documents"]:
        path = PDF_DIR / doc["file"]
        raw_pages = read_pages(path)
        page_words = [len(t.split()) for t in raw_pages]
        low_pages = [i for i, w in enumerate(page_words, start=1) if w < LOW_TEXT_WORDS]

        # text read from kept images: replaces an image-only page, or is added below a page's own text
        ocr_pages, image_pages = set(), set()
        for page_number in range(1, len(raw_pages) + 1):
            key = f"{doc['file']}#{page_number}"
            if not ocr_text.get(key):
                continue
            marked = f"{IMAGE_MARKER}: {image_what.get(key, 'image')}]\n{ocr_text[key]}"
            if page_number in low_pages:
                raw_pages[page_number - 1] = marked
                ocr_pages.add(page_number)
            else:
                raw_pages[page_number - 1] += "\n" + marked
                image_pages.add(page_number)

        usable = len(raw_pages) - len(set(low_pages) - ocr_pages)
        status = "OK" if usable >= 0.5 * len(raw_pages) else "FLAGGED: mostly image-only, needs a text-based copy"
        doc.setdefault("academic_year", find_academic_year(raw_pages))

        if status == "OK":
            pages = clean_pages(raw_pages, doc["type"])
            blocks = merge_small(split_into_blocks(doc, pages, raw_pages, ocr_pages))
            chunks = make_chunks(doc, blocks, branches)
        else:
            chunks = []
        all_chunks += chunks
        sizes = [c["words"] for c in chunks] or [0]
        report.append({"doc": Path(doc["file"]).name, "original": doc.get("original_name"), "pages": len(raw_pages),
                       "words": sum(page_words), "status": status,
                       "low_pages": [p for p in low_pages if p not in ocr_pages],
                       "ocr_pages": sorted(ocr_pages | image_pages),
                       "academic_year": doc.get("academic_year"), "chunks": len(chunks),
                       "min": min(sizes), "avg": round(sum(sizes) / len(sizes)), "max": max(sizes),
                       "semesters": sorted({c["semester"] for c in chunks if c["semester"]})})
        print(f"{report[-1]['doc']:<36} {len(raw_pages):>3} pages {len(chunks):>4} chunks  {status}")

    with open(OUT_DIR / "chunks.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    write_report(report, all_chunks)
    print(f"\n{len(all_chunks)} chunks written to {OUT_DIR / 'chunks.jsonl'}")


def write_report(report, chunks):
    long_embeds = [c for c in chunks if len(c["embed_text"].split()) > 190]
    tiny = [c for c in chunks if c["words"] < 10]
    lines = [
        "# Dataset Preparation Report",
        "",
        "Generated by `scripts/prepare_dataset.py`. Do not edit by hand; rerun the script instead.",
        "",
        f"**Totals:** {len(report)} documents, {sum(r['pages'] for r in report)} pages, {len(chunks)} chunks "
        f"({sum(c['extraction'] == 'ocr' for c in chunks)} of them read from images).",
        "",
        "## Documents",
        "",
        "| File | Original name | Pages | Words | Academic year | Semesters | Chunks | Words per chunk (min/avg/max) | Pages read from images (OCR) | Image-only pages skipped | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in report:
        low = ", ".join(map(str, r["low_pages"])) or "none"
        ocr = ", ".join(map(str, r["ocr_pages"])) or "none"
        sems = ", ".join(map(str, r["semesters"])) or "-"
        lines.append(f"| {r['doc']} | {r['original']} | {r['pages']} | {r['words']} | {r['academic_year'] or '-'} | "
                     f"{sems} | {r['chunks']} | {r['min']}/{r['avg']}/{r['max']} | {ocr} | {low} | {r['status']} |")
    lines += [
        "",
        "Pages read from images: their text comes from `scripts/ocr_images.py` (the images listed under \"keep\" in "
        "`dataset/images.json`); those chunks have `\"extraction\": \"ocr\"`. Image-only pages skipped: covers, photos, "
        "logos, posters and blank pages (see \"skip\" in `dataset/images.json`). Page numbers are never changed.",
        "",
        "## Length checks",
        "",
        f"- Chunks whose embedded text is over 190 words (may pass MiniLM's 256-token limit): **{len(long_embeds)}**",
        f"- Chunks under 10 words: **{len(tiny)}**",
        "",
        "## Spot check: 10 random chunks",
        "",
        "Compare each one with its PDF page: the page, section and text should match.",
        "",
    ]
    random.seed(7)
    for c in random.sample(chunks, min(10, len(chunks))):
        preview = " ".join(c["text"].split())[:300]
        lines += [f"**{c['doc']}, p. {c['page']}** - {c['section']}"
                  + (f" - {c['heading']}" if c["heading"] else ""), "", f"> {preview}", ""]
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
