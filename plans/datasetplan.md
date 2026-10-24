# Dataset Plan: Preparing the College PDFs

**Problem statement:** 2A, Campus Regulations Assistant (Theme 2: RAG Application with Gemma)

This plan covers only the documents: which PDFs we use, how we check them, how we clean them, how we split them into chunks, and what each chunk stores. The model, prompt and app are planned separately.

**Status:** implemented in [`scripts/prepare_dataset.py`](../scripts/prepare_dataset.py). The documents are listed in [`dataset/README.md`](../dataset/README.md), and the latest run's numbers are in [`dataset/processed/report.md`](../dataset/processed/report.md).

---

## 1. Rules the data must follow (from the hack day brief)

| Rule | What it means for us |
|---|---|
| Official, publicly available regulations from our own college | Use only official SSIT / SSAHE documents: the handbook and the department syllabus. No notes or summaries written by us. |
| At least two documents | We have 22 SSIT documents (1 handbook + 21 syllabus PDFs) plus 1 upGrad brochure, and every citation names its document. |
| Text-based PDFs only | The starter kit cannot read scanned pages. We read the useful images ourselves with OCR, before the notebook runs (section 4.1); the notebook still only sees text. |
| Only our college's documents | The dental college calendar was left out. The upGrad brochure was added on request, but every one of its chunks is marked as not an SSIT document (section 4.2). |
| Each answer cites the document and page | Each chunk keeps its document name and page number, and a chunk never crosses a page boundary. |
| Runs in Google Colab on CPU | Chunking runs once (about 30 seconds) and the chunks are saved, so the notebook only has to embed them. |
| Embedding model `all-MiniLM-L6-v2` | It reads at most 256 tokens (about 180-200 words) per chunk and ignores the rest, so chunk bodies stay at or under about 150 words. |

---

## 2. The two kinds of documents

| Kind | Files | How it is organised | How we split it |
|---|---|---|---|
| **Handbook** (the main source of rules) | `SSIT_Handbook_2025-26.pdf` (was `RULE-BOOK.pdf`) | Parts (B.E. regulations, M.Tech., MCA, MBA, NEP, anti-ragging, scholarships, holidays, faculty list), each made of numbered clauses: `SRE 7.0 Attendance Requirements`, `SRE 7.1`, `PG 2.1`, `MCA 8.0`, `MBA 5.1` | **One clause per chunk** (section 5) |
| **Syllabus** (one per branch and year) | 21 files under `syllabus/BE/` and `syllabus/MTech/` | A scheme table for each semester, then one or two pages per course: title, code, units/modules, objectives, outcomes, textbooks | **One unit or one course part per chunk** (section 6) |

The short branch names in the original file names are expanded in `dataset/documents.json` and stored in every chunk:

| Short form | Full name |
|---|---|
| CSE | Computer Science and Engineering |
| ECE (EC) | Electronics and Communication Engineering |
| ME | Mechanical Engineering |
| IT | Computer Science group, common first year (CSE, ISE, AI&ML, CS(AI&ML), Data Science, Cyber Security) |
| VLSI-ES | M.Tech. VLSI and Embedded Systems (ECE department) |
| DE | M.Tech. Digital Electronics (ECE department) |
| PDM | M.Tech. Product Design and Manufacturing (ME department) |
| TPE | M.Tech. Thermal Power Engineering (ME department) |
| CV | Civil Engineering |
| CSE-CY | Computer Science and Engineering (Cyber Security) |
| CSE-DS | Computer Science and Engineering (Data Science) |
| CADS | M.Tech. Computer Aided Design of Structures (Civil department) |

---

## 3. Folder layout and naming

```
dataset/
  documents.json                      <- one entry per PDF: type, program, branch, year, department, contact
  pdfs/handbook/SSIT_Handbook_2025-26.pdf
  pdfs/syllabus/BE/BE_<BRANCH>_Year<N>_Syllabus.pdf
  pdfs/syllabus/MTech/MTech_<BRANCH>_Year<N>_Syllabus.pdf
  processed/chunks.jsonl              <- generated
  processed/report.md                 <- generated
scripts/prepare_dataset.py
```

Each PDF is renamed to a short, clear name before it is added, because the file name appears in citations, e.g. `EC YR2.pdf` becomes `BE_ECE_Year2_Syllabus.pdf`. The original name is kept in `documents.json`.

---

## 4. Step 1: check each PDF

1. Extract the text of every page with `pypdf`.
2. Count the words per page. A page with **fewer than 20 words** is an image-only page (cover, photo, scanned calendar): it is skipped, but the numbering of the other pages is not changed.
3. If **more than half** of a document's pages are image-only, the whole document is flagged in the report and left out. It needs a text-based copy; OCR is not part of the starter kit.
4. The academic year is read from the text (e.g. "Academic year 2024-2025") and stored with the document.

Result of the current run: all 22 documents are **OK**.

### 4.1 Images that carry information (OCR)

Some college information exists only as an image: scanned notifications, and scheme tables pasted in as pictures. We handle images in three steps:

1. **Find:** every image-only page, and every embedded image covering at least 8% of a page (smaller ones are icons and logos). The current documents have 39 such images.
2. **Decide:** each image is looked at by a person and listed in `dataset/images.json` as **keep** (it carries college information) or **skip** (photos of people or buildings, logos, covers, posters, blank pages), with the reason.
3. **Read:** `scripts/ocr_images.py` renders each kept image at 180 dpi and reads it with **RapidOCR** (open-source, runs offline on the CPU). It rebuilds the lines from the positions of the words, so a table keeps one row per line, with ` | ` between cells.

`prepare_dataset.py` then puts that text in place of the image-only page, or below the page's own text, and chunks it like any other text. A chunk read from an image is marked `"extraction": "ocr"` and its heading starts with "Text read from an image: ...".

| | Images | What |
|---|---|---|
| **Kept** | 14 (27 chunks) | SSAHE curriculum notifications (page 2 of 9 syllabus PDFs), the ME 3rd and 4th semester scheme tables, the SSAHE internship guidelines notice (CSE-CY Year 4, p. 75), the brochure's startup and research journey timelines (pp. 14-15) |
| **Skipped** | 40 | Preamble to the Constitution poster (9), founders' portraits, photos, company and university logos, background images whose text is already in the PDF, covers, a blank page, the handbook's plain 2025/2026 month calendars (no events; the holidays are in the text on pp. 64-65), and the 10 pages of the dental college calendar |

OCR can misread words. The internship notice is a low-resolution scan, so some words run together, but its facts are readable (mandatory, zero credits, CIE only, 6 to 8 weeks).

### 4.2 Documents that are not from SSIT

**Left out:** `Calendar-of-events-25-26.pdf` is the calendar of **Sri Siddhartha Dental College & Hospital** (BDS/MDS), not SSIT. It would give engineering students wrong dates.

**Added with a label:** `Principle_Brochure.pdf` (saved as `other/upGrad_SoT_Brochure.pdf`) is a marketing brochure of **upGrad School of Technology** and does not mention SSIT. It was added on request as type `brochure`. Each of its 51 chunks has `"publisher": "upGrad School of Technology"` (all others: `"SSIT / SSAHE"`), the title "upGrad School of Technology Brochure (not an SSIT document)" at the front of its `embed_text`, and upGrad's admissions contact. Each brochure page is treated as its own topic, so headings never carry over from one page to the next.

---

## 5. Step 2: clean the text

Done page by page, so page numbers stay correct.

| Problem | Fix |
|---|---|
| The same header or footer on many pages ("SRI SIDDHARTHA INSTITUTE OF TECHNOLOGY- TUMAKURU", "Academic year 2024-2025", page numbers) | A line at the top or bottom of at least 30% of the pages is removed. Headings such as "Unit Description" are never removed this way. |
| The "Department: ... Semester: V" line at the top of each syllabus page | Removed from the text, but the semester is read from it first and stored in the chunk. |
| Course Articulation Matrix (CO-PO tables of 1s, 2s and 3s) and signature lines | Removed: they are numbers with no meaning for students. |
| Words split by hyphens across lines ("exami-" / "nation") | Joined back together. |
| Ligatures and odd characters (ﬁ, curly quotes, bullets) | Replaced with plain characters. |
| Tables (fee tables, holiday lists, faculty lists, schemes) | Kept row by row, one row per line. |

We do not rewrite or summarise the rules. The words stay exactly as in the official document. (`pypdf` sometimes inserts a space inside a word, e.g. "Vice -Chancellor". We leave this as it is, because the embedding model copes with it.)

---

## 6. Step 3: split into chunks

### 6.1 Handbook: one clause per chunk

1. **Parts.** The handbook is divided into the parts listed in `documents.json` (e.g. "B.E. Regulations (SRE)", "Anti-ragging Committee", "University Holidays 2026"). Each part has its own office to contact.
2. **Clauses.** Every line starting with a clause number (`SRE 7.1`, `PG 2.1`, `MCA 8.0`, `MBA 5.1`) starts a new chunk. A clause ending in `.0` is the parent (e.g. `SRE 7.0 Attendance Requirements`), and its name is carried into every sub-clause's heading: `SRE 7.0 Attendance Requirements > SRE 7.1`.
3. **Other headings.** Numbered definitions ("17. Letter Grade:"), short headings ending in ":", headings in capitals, and staff groups ("CSE: Teaching") also start a new chunk.
4. A clause is **never merged with a clause from a different parent**. For example, the end of `SRE 6.7` (results) and the start of `SRE 7.1` (attendance) stay in separate chunks.

### 6.2 Syllabus: one unit or course part per chunk

1. **Course.** A new course starts at "Subject:" or "Course:", or at a title line followed by "Sub. Code:" (the M.Tech. PDM format). The course code and title (e.g. `22CS501 Database Management System`) are stored with every chunk of that course, including on its second page.
2. **Parts of a course.** Each of these starts a new chunk: each **unit / module** (I, II, III …), **Course Objectives**, **Course Outcomes**, **Text Books**, **Reference Books**, **Lab Experiments**, **Online Resources**.
3. **Scheme pages** (the semester's table of courses, credits and marks) are split by size, under the heading "Scheme of Teaching and Examination".
4. **Semester.** It is read from each page ("Semester: V", "5th Semester B.E.") and stored in the chunk.

### 6.3 Size rules (both kinds)

| Setting | Value | Reason |
|---|---|---|
| Longest chunk body | about 150 words (130 + 20 margin) | Leaves room for the title prefix within MiniLM's 256 tokens. |
| Shorter than | 30 words: joined with the next chunk on the same page, in the same section and clause | Avoids tiny chunks with no context. |
| A heading alone at the foot of a page | dropped as a chunk | The next page's chunks already carry it as "(continued)". |
| Longer sections | split into windows of 120 words with a 30-word overlap, on line boundaries | Same as the starter kit, so a sentence cut at the edge appears whole in the neighbour. |
| Every chunk | never crosses a page and never mixes two documents | Page citations are always correct. |

---

## 7. Step 4: what each chunk stores

Each line of `dataset/processed/chunks.jsonl` is one chunk:

```json
{
  "id": "SSIT_Handbook_2025-26-p21-85",
  "doc": "SSIT_Handbook_2025-26.pdf",
  "title": "SSIT Hand Book cum Work Planner 2025-2026",
  "type": "handbook",
  "program": null, "branch": null, "branch_full": null, "year": null, "semester": null,
  "academic_year": "2025-26",
  "department": null,
  "page": 21,
  "section": "B.E. Regulations (SSAHE Regulations Engineering, SRE)",
  "heading": "SRE 7.0 Attendance Requirements > SRE 7.1",
  "contact": "Office of the Dean (Academics), SSIT",
  "text": "SRE 7.0: Attendance Requirements:\nSRE 7.1:\nEach semester shall be considered a unit for calculating attendance. A candidate must have a\nminimum of 85% attendance in each course. ...",
  "embed_text": "SSIT Hand Book cum Work Planner 2025-2026 | B.E. Regulations (SSAHE Regulations Engineering, SRE) | SRE 7.0 Attendance Requirements > SRE 7.1 | SRE 7.0: Attendance Requirements: ...",
  "words": 101
}
```

A syllabus chunk fills the other fields, e.g. `"program": "B.E.", "branch": "CSE", "branch_full": "Computer Science and Engineering", "year": 3, "semester": 5, "section": "22CS501 Database Management System", "heading": "Unit II", "contact": "Head of the Department, Computer Science and Engineering, SSIT"`.

| Field | Used for |
|---|---|
| `embed_text` | **What gets embedded.** The document, section and heading are put in front of the text, so a short question such as "minimum attendance?" or "DBMS unit 2" matches the right chunk. |
| `text` | What Gemma reads and what the app shows as the retrieved passage. |
| `doc` + `page` | The citation, e.g. `(SSIT_Handbook_2025-26.pdf, p. 21)`. |
| `contact` | Whom to suggest when the assistant cannot answer. |
| `program`, `branch`, `year`, `semester` | Filtering, e.g. a student picks "B.E. CSE, Year 3" and only those syllabus chunks plus the handbook are searched. |

How the notebook formats a chunk for Gemma:

```
[SSIT_Handbook_2025-26.pdf, Page 21, SRE 7.0 Attendance Requirements > SRE 7.1] Each semester shall be ...
```

---

## 8. Step 5: check the chunks

The script writes `dataset/processed/report.md` on every run with:

1. **Totals:** for each document, pages, words, academic year, semesters found, number of chunks, words per chunk (min/avg/max), image-only pages and status.
2. **Length:** the number of chunks whose embedded text is over 190 words, and the number under 10 words.
3. **Spot check:** 10 random chunks to read next to the original PDF pages.

Current run: **23 documents, 1,153 pages, 3,651 chunks** (310 from the handbook, 3,290 from the syllabus PDFs, 51 from the upGrad brochure; 27 read from images). 1 chunk is over the 190-word limit and 15 are under 10 words. Every syllabus chunk is labelled with its course, except 5 in `BE_CSE_Year3_Syllabus.pdf` (the PDF stores the text of those pages out of order).

**Coverage check against the brief's example questions:**

| Question | Covered? | Where |
|---|---|---|
| Minimum attendance to sit the end-semester exam | Yes | Handbook p. 19 (`SRE 6.2`, 85% in each course) and p. 21 (`SRE 7.1`) |
| Re-evaluation and its deadline | **No** | Not in any of the 23 PDFs. Refusal test, or add the exam regulations |
| Hostel visiting hours | **No** | Not in any of the 23 PDFs. Refusal test, or add the hostel rules |

---

## 9. Experiments on the chunking (for the bonus points)

Run the same test set (at least 15 questions) with each setting and record the score:

| Experiment | Values to compare |
|---|---|
| Chunking method | clause/unit-based (ours) vs the starter kit's plain 120-word split |
| Chunk size | 80 / 130 / 200 words (`MAX_WORDS`, `WINDOW` in the script) |
| Overlap | 0 / 30 words (`OVERLAP`) |
| Prefix in front of the embedded text | `embed_text` vs `text` only |
| Embedding model | `all-MiniLM-L6-v2` vs `BAAI/bge-small-en-v1.5` |

For each run we record the percentage of questions answered correctly, and how often the correct page appears in the retrieved chunks. The best setting becomes the default, and the table goes into the presentation.

---

## 10. Conflicting information between documents (2A bonus)

Because every chunk stores its document, section and clause, rules that differ between parts show up as chunks from different sections. Examples already in the handbook:

- Attendance: **85%** for B.E. (`SRE 7.1`, p. 21), M.Tech. (`PG 2.1`, p. 27) and MCA (`MCA 8.0`, p. 35), but **75%** for MBA (`MBA 5.1`, p. 41). Asked "what is the minimum attendance?", the assistant should give both and say which program each applies to.
- Academic years differ between the syllabus PDFs (2023-24 to 2026-27), so a question about "the current syllabus" may get answers from different years.

The assistant should show both passages and say which program or year each applies to.

---

## 11. Updating the dataset

When the college publishes a new document or a new version:

1. Put the PDF in the right folder with a clear name, and add or update its entry in `dataset/documents.json`.
2. Run `python scripts/prepare_dataset.py`.
3. Read `dataset/processed/report.md`: the document must be **OK**, and its chunks must name their courses or clauses.
4. Rerun the test set to confirm nothing got worse.

Old versions are removed, so the assistant never answers from an outdated rule.
