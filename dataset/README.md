# Dataset

Official documents of **Sri Siddhartha Institute of Technology (SSIT), Tumakuru**, a constituent college of Sri Siddhartha Academy of Higher Education (SSAHE), used by the Campus Regulations Assistant (problem statement 2A).

How the PDFs are checked, cleaned and split into chunks is described in [`plans/datasetplan.md`](../plans/datasetplan.md).

**Current totals:** 23 documents (22 SSIT documents and 1 upGrad brochure), 1,153 pages, **3,651 chunks**, of which 27 were read from images (OCR).

## Folder layout

```
dataset/
  documents.json          <- what each PDF is (type, program, branch, year, contact office)
  images.json             <- every image found in the PDFs: which are read (OCR) and which are skipped, and why
  pdfs/
    handbook/             <- college rules and regulations
    syllabus/BE/          <- B.E. syllabus, one PDF per branch and year
    syllabus/MTech/       <- M.Tech. syllabus, one PDF per specialisation and year
    other/                <- documents that are not from SSIT (the upGrad brochure)
  ocr/
    ocr_text.json         <- text read from the kept images (generated)
  processed/
    chunks.jsonl          <- the chunks, one JSON object per line (generated)
    report.md             <- checks and statistics (generated)
```

Never edit the generated files by hand. Change a PDF, `documents.json` or `images.json`, then run:

```bash
pip install -r requirements.txt
python scripts/ocr_images.py        # only needed when images.json changes
python scripts/prepare_dataset.py
```

## Branch short forms

| Short form | Full name | Department |
|---|---|---|
| CSE | Computer Science and Engineering | Computer Science and Engineering |
| CSE-CY | Computer Science and Engineering (Cyber Security) | Computer Science and Engineering (Cyber Security) |
| CSE-DS | Computer Science and Engineering (Data Science) | Computer Science and Engineering (Data Science) |
| ECE | Electronics and Communication Engineering | Electronics and Communication Engineering |
| ME | Mechanical Engineering | Mechanical Engineering |
| CV | Civil Engineering | Civil Engineering |
| IT | Computer Science group, common first year (CSE, ISE, AI&ML, CS(AI&ML), Data Science, Cyber Security) | Computer Science and Engineering |
| VLSI-ES | M.Tech. VLSI and Embedded Systems | Electronics and Communication Engineering |
| DE | M.Tech. Digital Electronics | Electronics and Communication Engineering |
| PDM | M.Tech. Product Design and Manufacturing | Mechanical Engineering |
| TPE | M.Tech. Thermal Power Engineering | Mechanical Engineering |
| CADS | M.Tech. Computer Aided Design of Structures (the PDF only says "CADS"; this is the usual full form) | Civil Engineering |

## Documents

| File | Original name | What it is | Academic year | Pages | Chunks | Pages read from images |
|---|---|---|---|---|---|---|
| handbook/SSIT_Handbook_2025-26.pdf | RULE-BOOK.pdf | Hand Book cum Work Planner: B.E., M.Tech., MCA and MBA regulations, NEP and activity points, anti-ragging, scholarships, holidays, faculty list | 2025-26 | 68 | 310 | - |
| syllabus/BE/BE_IT_Year1_Syllabus.pdf | IT BRANCH YR1.pdf | B.E. Computer Science group, 1st year (Sem 1) | 2026-27 | 24 | 63 | - |
| syllabus/BE/BE_CSE_Year2_Syllabus.pdf | CSE YR2.pdf | B.E. CSE, 2nd year (Sem 3-4) | 2024-25 | 47 | 137 | 2 |
| syllabus/BE/BE_CSE_Year3_Syllabus.pdf | CSE-YR3.pdf | B.E. CSE, 3rd year (Sem 5-6) | 2024-25 | 62 | 193 | 2 |
| syllabus/BE/BE_CSE_Year4_Syllabus.pdf | CSE-YR4.pdf | B.E. CSE, 4th year (Sem 7-8) | 2024-25 | 54 | 171 | 2 |
| syllabus/BE/BE_CSE-CY_Year4_Syllabus.pdf | CSE(Cy) Scheme & Syallabus 4th Year (2022 Scheme).pdf | B.E. CSE (Cyber Security), 4th year (Sem 7-8) | 2025-26 | 80 | 183 | 75 |
| syllabus/BE/BE_CSE-DS_Year4_Syllabus.pdf | CSE(DS) Scheme and Syllabus 4th Year (NEP-160 Credits).pdf | B.E. CSE (Data Science), 4th year (Sem 7-8) | 2025-26 | 54 | 172 | - |
| syllabus/BE/BE_ECE_Year1_Syllabus.pdf | EC-YR1.pdf | B.E. ECE, 1st year (Sem 1-2) | 2026-27 | 82 | 196 | - |
| syllabus/BE/BE_ECE_Year2_Syllabus.pdf | EC YR2.pdf | B.E. ECE, 2nd year (Sem 3-4) | 2023-24 | 46 | 145 | 2 |
| syllabus/BE/BE_ECE_Year3_Syllabus.pdf | EC-YR3.pdf | B.E. ECE, 3rd year (Sem 5-6) | 2024-25 | 57 | 193 | 2 |
| syllabus/BE/BE_ECE_Year4_Syllabus.pdf | EC-YR4.pdf | B.E. ECE, 4th year (Sem 7-8) | 2024-25 | 48 | 158 | 2 |
| syllabus/BE/BE_ME_Year2_Syllabus.pdf | ME YR2.pdf | B.E. ME, 2nd year (Sem 3-4) | 2026-27 | 72 | 218 | 4, 39 |
| syllabus/BE/BE_CV_Year2_Syllabus.pdf | CV YR 2.pdf | B.E. Civil, 2nd year (Sem 3-4) | 2024-25 | 43 | 138 | 2 |
| syllabus/BE/BE_CV_Year3_Syllabus.pdf | CV YR 3.pdf | B.E. Civil, 3rd year (Sem 5-6) | 2024-25 | 63 | 221 | 2 |
| syllabus/BE/BE_CV_Year4_Syllabus.pdf | CV YR 4.pdf | B.E. Civil, 4th year (Sem 7-8) | not stated | 53 | 160 | 2 |
| syllabus/MTech/MTech_CSE_Year1_Syllabus.pdf | CSE MTech YR I.pdf | M.Tech. CSE, 1st year | 2024-25 | 51 | 175 | - |
| syllabus/MTech/MTech_CSE_Year2_Syllabus.pdf | CSE MTech YR 2.pdf | M.Tech. CSE, 2nd year (scheme only) | 2024-25 | 2 | 6 | - |
| syllabus/MTech/MTech_VLSI-ES_Year1_Syllabus.pdf | EC MTech_Y1.pdf | M.Tech. VLSI and Embedded Systems, 1st year | 2024-25 | 65 | 200 | - |
| syllabus/MTech/MTech_DE_Year1_Syllabus.pdf | MTech_Year-I_DE.pdf | M.Tech. Digital Electronics, 1st year | 2024-25 | 55 | 208 | - |
| syllabus/MTech/MTech_PDM_Year1_Syllabus.pdf | MTech YR I PDM(ME).pdf | M.Tech. Product Design and Manufacturing, 1st year | 2024-25 | 49 | 153 | - |
| syllabus/MTech/MTech_TPE_Year2_Syllabus.pdf | MTech YR II TPE(ME).pdf | M.Tech. Thermal Power Engineering, 2nd year (scheme only) | 2024-25 | 3 | 5 | - |
| syllabus/MTech/MTech_CADS_Year1_Syllabus.pdf | MTech_Year-I_CADS(CV).pdf | M.Tech. Computer Aided Design of Structures, 1st year | 2024-25 | 51 | 194 | - |
| other/upGrad_SoT_Brochure.pdf | Principle_Brochure.pdf | **Not an SSIT document.** Marketing brochure of upGrad School of Technology: its 4-year CSE degree, curriculum, campus life, faculty, admission process | not stated | 24 | 51 | 14, 15 |

Contact offices: handbook chunks use the office of their part (e.g. Office of the Dean (Academics), the Anti-ragging Committee), syllabus chunks use the Head of the Department, and brochure chunks use upGrad's admissions contact.

### The upGrad brochure

It was added on request, but it is **not** an official SSIT document and does not mention SSIT. To stop the assistant presenting upGrad's claims as SSIT rules, every brochure chunk has:

- `"type": "brochure"` and `"publisher": "upGrad School of Technology"` (every other chunk has `"publisher": "SSIT / SSAHE"`),
- the title "upGrad School of Technology Brochure (not an SSIT document)" at the front of its `embed_text`, and
- upGrad's admissions contact as its `contact`.

The app can exclude it, or say "according to the upGrad brochure (not SSIT)" when it uses one of these chunks. Academic years are read from the PDFs themselves and differ between documents (2023-24 to 2026-27).

## Images (OCR)

Some information is only in images. Every image-only page and every embedded image covering at least 8% of a page was looked at, and the decision is recorded in [`images.json`](images.json):

- **Read (14 images, 27 chunks):** the SSAHE curriculum notifications (page 2 of the CSE, ECE and Civil syllabus, years 2-4), the ME 3rd and 4th semester scheme tables (ME Year 2, pages 4 and 39), the SSAHE internship guidelines notice (CSE-CY Year 4, page 75), and the brochure's 7-semester startup and research journey timelines (pages 14-15).
- **Skipped (30 images):** the Preamble to the Constitution poster at the start of nine syllabus (national, not college information), founders' portraits, photos, company and university logos, background images whose text is already in the PDF, covers, a blank page, and the handbook's plain 2025/2026 month calendars (no events; the holidays are already in the handbook's text on pages 64-65).

Chunks read from images have `"extraction": "ocr"`, and their heading starts with "Text read from an image: ...". OCR text can contain reading errors. The internship notice in particular is a low-resolution scan, so some of its words are run together, but its main facts are readable.

## Documents left out

| File | Why |
|---|---|
| Calendar-of-events-25-26.pdf | It is the calendar of events of **Sri Siddhartha Dental College & Hospital** (BDS/MDS exams), not SSIT. Using it would give engineering students wrong dates. |

## Known gaps

These topics are **not covered** by the current documents, so the assistant must decline them and point to the office:

- Re-evaluation / revaluation of answer scripts, and its deadline -> Office of the Dean (Examinations)
- Hostel rules and visiting hours -> Hostel Warden (Boys / Girls hostel)
- Library rules
- SSIT's own calendar of events for 2025-26

Two of the brief's three example questions (re-evaluation, hostel visiting hours) fall into these gaps. Either add the exam and hostel regulations, or use these questions as refusal tests.

## Adding a new PDF

1. Copy it into the right folder with a clear name, e.g. `syllabus/BE/BE_ME_Year3_Syllabus.pdf`.
2. Add one entry to `documents.json` (copy a similar entry and change `file`, `original_name`, `branch`, `year`).
3. If it has pages or parts that are only images, look at them and add each to `images.json` under `keep` (college information) or `skip` (photos, logos, covers), then run `python scripts/ocr_images.py`.
4. Run `python scripts/prepare_dataset.py` and read `processed/report.md`: the new file must show **OK**, and its chunks should name their courses.
