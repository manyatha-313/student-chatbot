# Dataset Plan: Preparing the College PDFs

**Problem statement:** 2A, Campus Regulations Assistant (Theme 2: RAG Application with Gemma)

This plan covers only the documents: which PDFs we use, how we check them, how we clean them, how we split them into chunks, and what each chunk stores. The model, prompt and app are planned separately.

---

## 1. Rules the data must follow (from the hack day brief)

| Rule | What it means for us |
|---|---|
| Official, publicly available regulations from our own college | Use only official documents: student handbook, exam regulations, hostel rules, library policy, etc. No notes or summaries written by us. |
| At least two documents | The knowledge base must hold two or more PDFs, and every citation names its document. |
| Text-based PDFs only | Scanned image-only PDFs are not supported. Every PDF is checked before use (section 3). |
| Each answer cites the document and page | Each chunk keeps its document name and page number, and a chunk never crosses a page boundary. |
| Runs in Google Colab on CPU | Chunking and embedding must stay light. Our documents are small, so this is fine. |
| Embedding model `all-MiniLM-L6-v2` | It reads at most 256 tokens (about 180–200 words) per chunk and ignores the rest, so chunks stay under that. |

---

## 2. Folder layout

```
dataset/
  RULE-BOOK.pdf              <- original PDFs, never edited
  ...                        <- one file per official document
plans/
  datasetplan.md             <- this file
```

Naming: each PDF is renamed to a short, clear name before it is added, because the file name appears in citations. For example `Examination_Regulations.pdf`, `Hostel_Rules.pdf`, `Student_Handbook.pdf`.

We also keep a small table of every document (`dataset/README.md`, to be added):

| File | Official title | Source (link or office) | Year / version | Pages | Office to contact |
|---|---|---|---|---|---|
| RULE-BOOK.pdf | (to fill) | (to fill) | (to fill) | (to fill) | (to fill) |

The **office to contact** column is used when the assistant cannot answer, e.g. "Contact the Examination Cell".

---

## 3. Step 1: check each PDF

For each PDF:

1. Extract the text of every page with `pypdf`.
2. Count the words per page.
3. Flag the PDF if:
   - most pages have fewer than about 20 words, which means it is scanned and has no usable text, or
   - the text comes out garbled (broken characters, words joined together).
4. A flagged PDF is either replaced with a text-based copy from the college, or left out. OCR is a last resort and is not part of the starter kit.

Result: a list of pages per document, with the page number from the PDF (1, 2, 3 …).

---

## 4. Step 2: clean the text

Done page by page, so page numbers stay correct.

| Problem | Fix |
|---|---|
| The same header or footer on every page (college name, document title, "Page 3 of 40") | Find lines repeated on most pages and remove them. |
| Words split by hyphens across lines ("exami-\nnation") | Join them back together. |
| Line breaks in the middle of sentences | Join lines into paragraphs, but keep breaks before headings and list items. |
| Extra spaces and blank lines | Collapse them to single spaces and line breaks. |
| Tables (e.g. fee tables, timetables) | Keep each table row on one line and keep the whole table in one chunk where possible. |
| Index pages and blank pages | Drop pages with almost no text. Keep the page numbering unchanged. |

We do not rewrite or summarise the rules. The words stay exactly as in the official document.

---

## 5. Step 3: split into chunks

### 5.1 Main method: split by section or clause

Regulations are usually numbered ("4.2 Attendance", "Rule 7", "Chapter III"). One rule should end up in one chunk, so:

1. Within each page, find heading lines with simple patterns, for example:
   - numbered clauses: `1.`, `4.2`, `4.2.1`, `(a)`, `(i)`
   - words like `Rule`, `Regulation`, `Section`, `Chapter`, `Clause`
   - short lines in capitals, e.g. `HOSTEL VISITING HOURS`
2. Each heading starts a new chunk, and the chunk runs until the next heading.
3. If a section is **longer than about 150 words**, split it further by word count (section 5.2), keeping the section's heading on every part.
4. If a section is **shorter than about 30 words**, join it with the next section on the same page, so we don't get tiny chunks with no context.

### 5.2 Fallback method: split by word count

For pages with no clear headings, we use the starter kit's method:

| Setting | Starting value | Reason |
|---|---|---|
| `CHUNK_SIZE` | 120 words | Big enough to hold one complete rule, and well under the embedding model's limit. |
| `CHUNK_OVERLAP` | 30 words | A sentence cut at a chunk's edge still appears whole in the neighbouring chunk. |
| Minimum length | 5 words | Very short fragments are dropped (as in the starter kit). |

### 5.3 Rules for every chunk

- A chunk **never crosses a page**, so its page citation is always correct.
- A chunk **never mixes two documents**.
- A table is not split in the middle of a row.

---

## 6. Step 4: what each chunk stores

```python
{
  "doc":     "Examination_Regulations.pdf",   # used in citations
  "title":   "Examination Regulations 2025",  # official title, from dataset/README.md
  "page":    12,                              # PDF page number
  "section": "4.2 Attendance Requirement",    # heading the chunk belongs to (empty if none)
  "text":    "A student must have a minimum of 75% attendance ...",  # cleaned original text
  "contact": "Examination Cell",              # office to contact for this document
}
```

### Text that gets embedded

The embedding model only sees text, so the document title and section heading are put in front of the chunk text before embedding:

```
Examination Regulations 2025 | 4.2 Attendance Requirement | A student must have a minimum of 75% attendance ...
```

This helps short questions like "minimum attendance?" match the right chunk, even when the chunk text itself does not repeat the word "attendance".

The text given to Gemma, and shown to the user, is formatted for citation:

```
[Examination_Regulations.pdf, Page 12, 4.2 Attendance Requirement] A student must have ...
```

---

## 7. Step 5: check the chunks before using them

1. **Totals:** documents, pages, chunks per document, average words per chunk.
2. **Length:** no chunk longer than about 200 words (the embedding model's limit), and none that is just a heading.
3. **Spot check:** read 10 random chunks next to the original PDF pages and confirm that the page number and section are right and the text is not garbled.
4. **Coverage:** for each test question with a known answer, confirm the correct passage exists as one chunk and is not split in half.

---

## 8. Experiments on the chunking (for the bonus points)

Run the same test set (at least 15 questions) with each setting and record the score:

| Experiment | Values to compare |
|---|---|
| Chunking method | section-based vs word-count only |
| Chunk size (word-count method) | 80 / 120 / 200 words |
| Overlap | 0 / 30 words |
| Title and heading in front of the embedded text | with vs without |
| Embedding model | `all-MiniLM-L6-v2` vs `BAAI/bge-small-en-v1.5` |

For each run we record: the percentage of questions answered correctly, and how often the correct page appears in the retrieved chunks. The best setting becomes the default, and the table goes into the presentation.

---

## 9. Conflicting information between documents (2A bonus)

Because every chunk stores its document and section, when two documents state different values for the same rule (e.g. the handbook says 75% attendance and the exam regulations say 80%), the retrieved chunks will come from both documents. These cases are listed in `dataset/README.md` when we find them, so we can test that the assistant shows both passages.

---

## 10. Updating the dataset

When the college publishes a new version of a document:

1. Replace the PDF in `dataset/` and update its row in `dataset/README.md` (year/version).
2. Rerun the checks, cleaning and chunking (steps 1–5).
3. Rerun the test set to confirm nothing got worse.

Old versions are removed, so the assistant never answers from an outdated rule.
