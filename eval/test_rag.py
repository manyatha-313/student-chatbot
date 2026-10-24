"""Automated QA tests for the RAG pipeline (department isolation, refusals,
exclusions, citation validity). Assert-based so it runs without pytest:

    python eval/test_rag.py

Refusals are checked at the retrieval/answer layer, which decides them before
calling the model, so these pass with or without GOOGLE_API_KEY.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import rag

idx = rag.build_from_dataset()
ALL_DOCS = {c["doc"] for c in idx.chunks}
# page range per doc, to validate citations
PAGES = {}
for c in idx.chunks:
    PAGES.setdefault(c["doc"], set()).add(c["page"])

_fail = []
def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail and not ok else ""))
    if not ok:
        _fail.append(name)

def docs_of(found):   return sorted({c["doc"] for c in found})
def refused(reply):   return reply.startswith("I could not verify")

print("=== Department isolation ===")
# CSE-specific course asked under other departments must not return CSE documents.
_, me = idx.answer("Automata Theory and Computation course", branch="ME", program="B.E.")
check("CSE course under ME returns no CSE docs", not any(c.get("branch") == "CSE" for c in me), docs_of(me))
_, cv = idx.answer("Automata Theory and Computation course", branch="CV", program="B.E.")
check("CSE course under CV returns no CSE docs", not any(c.get("branch") == "CSE" for c in cv), docs_of(cv))
# Positive: under CSE it is found.
_, cse = idx.answer("Automata Theory and Computation course", branch="CSE", program="B.E.")
check("CSE course under CSE returns CSE docs", any(c.get("branch") == "CSE" for c in cse), docs_of(cse))
# Isolation holds for every retrieved chunk: only the selected branch or college-wide.
_, ece = idx.answer("list the course outcomes", branch="ECE", program="B.E.")
check("ECE query returns only ECE or college-wide",
      all(c.get("branch") in (None, "", "ECE") for c in ece), docs_of(ece))

print("=== College-wide (handbook) available under any branch ===")
_, att = idx.answer("What is the minimum attendance required in each course?", branch="ME", program="B.E.")
check("attendance under ME answered from handbook",
      any(c["doc"] == "SSIT_Handbook_2025-26.pdf" for c in att), docs_of(att))

print("=== Refusals (document-only) ===")
_, wc = idx.answer("Who won the 2022 FIFA World Cup?", branch="CSE", program="B.E.")
check("general-knowledge question refused", refused(idx.answer("Who won the 2022 FIFA World Cup?", branch="CSE")[0]))
check("general-knowledge returns no answer (answered=False path)",
      not wc or wc[0]["score"] < config.RELEVANCE_THRESHOLD)
check("capital-of-France refused", refused(idx.answer("What is the capital of France?")[0]))

print("=== Invalid / empty department ===")
# AIML has no syllabus in the repo: only college-wide docs may appear, never another branch.
_, aiml = idx.answer("Automata Theory and Computation course", branch="AIML", program="B.E.")
check("unknown branch AIML yields only college-wide docs (no leakage)",
      all(not c.get("branch") for c in aiml), docs_of(aiml))

print("=== Excluded non-official source (brochure) ===")
broad = idx.retrieve("upGrad School of Technology programs fees placements accelerator", top_k=25)
check("brochure never retrieved", "upGrad_SoT_Brochure.pdf" not in docs_of(broad), docs_of(broad))

print("=== Calendar (no dedicated calendar PDFs exist) ===")
# A specific calendar question should pull from the handbook if present, or refuse - never invent.
reply, cal = idx.answer("What is the academic calendar of events for 2026 for the CSE department?", branch="CSE")
cal_ok = refused(reply) or all(c.get("branch") in (None, "", "CSE") for c in cal)
check("calendar question refuses or stays in scope (no invention)", cal_ok, docs_of(cal))

print("=== Citation validity ===")
ok = True
for q in ["minimum attendance", "punishments for ragging", "how is CGPA converted to percentage"]:
    _, f = idx.answer(q)
    for c in f:
        if c["doc"] not in ALL_DOCS or c["page"] not in PAGES[c["doc"]]:
            ok = False
check("every returned source is a real doc + valid page", ok)

print(f"\n{'ALL TESTS PASSED' if not _fail else str(len(_fail)) + ' TEST(S) FAILED: ' + ', '.join(_fail)}")
sys.exit(1 if _fail else 0)
