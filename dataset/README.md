# Dataset

Official documents of **Sri Siddhartha Institute of Technology (SSIT), Tumakuru**, a constituent college of Sri Siddhartha Academy of Higher Education (SSAHE), used by the Campus Regulations Assistant (problem statement 2A).

How the PDFs are checked, cleaned and split into chunks is described in [`plans/datasetplan.md`](../plans/datasetplan.md).

## Folder layout

```
dataset/
  documents.json          <- what each PDF is (type, program, branch, year, contact office)
  pdfs/
    handbook/             <- college rules and regulations
    syllabus/BE/          <- B.E. syllabi, one PDF per branch and year
    syllabus/MTech/       <- M.Tech. syllabi, one PDF per specialisation and year
  processed/
    chunks.jsonl          <- the chunks, one JSON object per line (generated)
    report.md             <- checks and statistics (generated)
```

Never edit the files in `processed/` by hand. Change a PDF or `documents.json`, then run:

```bash
pip install pypdf
python scripts/prepare_dataset.py
```

## Branch short forms

| Short form | Full name | Department |
|---|---|---|
| CSE | Computer Science and Engineering | Computer Science and Engineering |
| ECE | Electronics and Communication Engineering | Electronics and Communication Engineering |
| ME | Mechanical Engineering | Mechanical Engineering |
| IT | Computer Science group, common first year (CSE, ISE, AI&ML, CS(AI&ML), Data Science, Cyber Security) | Computer Science and Engineering |
| VLSI-ES | M.Tech. VLSI and Embedded Systems | Electronics and Communication Engineering |
| DE | M.Tech. Digital Electronics | Electronics and Communication Engineering |
| PDM | M.Tech. Product Design and Manufacturing | Mechanical Engineering |
| TPE | M.Tech. Thermal Power Engineering | Mechanical Engineering |

## Documents

| File | Original name | What it is | Academic year | Pages | Chunks | Office to contact |
|---|---|---|---|---|---|---|
| handbook/SSIT_Handbook_2025-26.pdf | RULE-BOOK.pdf | Hand Book cum Work Planner: B.E., M.Tech., MCA and MBA regulations, NEP and activity points, anti-ragging, scholarships, holidays, faculty list | 2025-26 | 68 | 310 | Depends on the section (see `documents.json`), e.g. Office of the Dean (Academics) |
| syllabus/BE/BE_IT_Year1_Syllabus.pdf | IT BRANCH YR1.pdf | B.E. Computer Science group, 1st year (Sem 1) | 2026-27 | 24 | 63 | HoD, Computer Science and Engineering |
| syllabus/BE/BE_CSE_Year2_Syllabus.pdf | CSE YR2.pdf | B.E. CSE, 2nd year (Sem 3-4) | 2024-25 | 47 | 135 | HoD, Computer Science and Engineering |
| syllabus/BE/BE_CSE_Year3_Syllabus.pdf | CSE-YR3.pdf | B.E. CSE, 3rd year (Sem 5-6) | 2024-25 | 62 | 191 | HoD, Computer Science and Engineering |
| syllabus/BE/BE_CSE_Year4_Syllabus.pdf | CSE-YR4.pdf | B.E. CSE, 4th year (Sem 7-8) | 2024-25 | 54 | 170 | HoD, Computer Science and Engineering |
| syllabus/BE/BE_ECE_Year1_Syllabus.pdf | EC-YR1.pdf | B.E. ECE, 1st year (Sem 1-2) | 2026-27 | 82 | 196 | HoD, Electronics and Communication Engineering |
| syllabus/BE/BE_ECE_Year2_Syllabus.pdf | EC YR2.pdf | B.E. ECE, 2nd year (Sem 3-4) | 2023-24 | 46 | 143 | HoD, Electronics and Communication Engineering |
| syllabus/BE/BE_ECE_Year3_Syllabus.pdf | EC-YR3.pdf | B.E. ECE, 3rd year (Sem 5-6) | 2024-25 | 57 | 191 | HoD, Electronics and Communication Engineering |
| syllabus/BE/BE_ECE_Year4_Syllabus.pdf | EC-YR4.pdf | B.E. ECE, 4th year (Sem 7-8) | 2024-25 | 48 | 156 | HoD, Electronics and Communication Engineering |
| syllabus/BE/BE_ME_Year2_Syllabus.pdf | ME YR2.pdf | B.E. ME, 2nd year (Sem 3-4) | 2026-27 | 72 | 212 | HoD, Mechanical Engineering |
| syllabus/MTech/MTech_CSE_Year1_Syllabus.pdf | CSE MTech YR I.pdf | M.Tech. CSE, 1st year | 2024-25 | 51 | 175 | HoD, Computer Science and Engineering |
| syllabus/MTech/MTech_CSE_Year2_Syllabus.pdf | CSE MTech YR 2.pdf | M.Tech. CSE, 2nd year (scheme only) | 2024-25 | 2 | 6 | HoD, Computer Science and Engineering |
| syllabus/MTech/MTech_VLSI-ES_Year1_Syllabus.pdf | EC MTech_Y1.pdf | M.Tech. VLSI and Embedded Systems, 1st year | 2024-25 | 65 | 200 | HoD, Electronics and Communication Engineering |
| syllabus/MTech/MTech_DE_Year1_Syllabus.pdf | MTech_Year-I_DE.pdf | M.Tech. Digital Electronics, 1st year | 2024-25 | 55 | 208 | HoD, Electronics and Communication Engineering |
| syllabus/MTech/MTech_PDM_Year1_Syllabus.pdf | MTech YR I PDM(ME).pdf | M.Tech. Product Design and Manufacturing, 1st year | 2024-25 | 49 | 152 | HoD, Mechanical Engineering |
| syllabus/MTech/MTech_TPE_Year2_Syllabus.pdf | MTech YR II TPE(ME).pdf | M.Tech. Thermal Power Engineering, 2nd year (scheme only) | 2024-25 | 3 | 5 | HoD, Mechanical Engineering |

Academic years are read from the PDFs themselves. Note that they differ between documents (2023-24 to 2026-27).

## Known gaps

These topics are **not covered** by the current documents, so the assistant must decline them and point to the office:

- Re-evaluation / revaluation of answer scripts, and its deadline -> Office of the Dean (Examinations)
- Hostel rules and visiting hours -> Hostel Warden (Boys / Girls hostel)
- Library rules
- Calendar of events (the copy we have, `Calendar-of-events-25-26.pdf`, is a scanned image with no text, so it cannot be used until a text-based copy is found)

Two of the brief's three example questions (re-evaluation, hostel visiting hours) fall into these gaps. Either add the exam and hostel regulations, or use these questions as refusal tests.

## Adding a new PDF

1. Copy it into the right folder with a clear name, e.g. `syllabus/BE/BE_ME_Year3_Syllabus.pdf`.
2. Add one entry to `documents.json` (copy a similar entry and change `file`, `original_name`, `branch`, `year`).
3. Run `python scripts/prepare_dataset.py` and read `processed/report.md`: the new file must show **OK**, and its chunks should name their courses.
