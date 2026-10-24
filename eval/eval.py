"""Evaluation harness (deliverable section 7).

Each test question is either answerable or a refusal test.
  - answerable: passes if the expected (doc, page) is in the retrieved top-k
    AND every expected keyword appears in the answer.
  - refusal (expect_refusal: true): passes if the assistant declines.

Reported measures:
  - retrieval hit: expected page in top-k (works without an API key)
  - keyword hit:   answer contains the expected facts (needs GOOGLE_API_KEY;
                   in demo mode the "answer" is just the passage, so ignore it)
  - refusal accuracy: out-of-scope questions correctly declined

shortcut: these are a proxy for "answered correctly"; expand the test set to
>=15 real Q&A from the final documents and spot-check answers by hand. Run the
chunk-size/top-k/model sweeps (bonus) by editing config.py and re-running.

Run:  python eval/eval.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rag

TESTSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testset.json")
REFUSAL_MARK = "could not verify"


def run(testset_path=TESTSET):
    with open(testset_path, encoding="utf-8") as f:
        tests = json.load(f)

    index = rag.build_from_dataset()
    answerable = [t for t in tests if not t.get("expect_refusal")]
    refusals = [t for t in tests if t.get("expect_refusal")]
    retrieval_hits = keyword_hits = refusal_ok = 0
    failures = []

    for t in tests:
        reply, found = index.answer(t["question"])
        if t.get("expect_refusal"):
            ok = REFUSAL_MARK in reply.lower()
            refusal_ok += ok
            if not ok:
                failures.append(f"{t['question']}  (should have declined) | {reply[:100]}")
            continue
        pages = {(c["doc"], c["page"]) for c in found}
        got_page = (t.get("expect_doc"), t.get("expect_page")) in pages
        got_kw = all(k.lower() in reply.lower() for k in t.get("expect_keywords", []))
        retrieval_hits += got_page
        keyword_hits += got_kw
        if not (got_page and got_kw):
            failures.append(f"{t['question']}  (page={'ok' if got_page else 'MISS'}, "
                            f"keywords={'ok' if got_kw else 'MISS'}) | {reply[:100]}")

    na = len(answerable) or 1
    print(f"Test questions: {len(tests)}  ({len(answerable)} answerable, {len(refusals)} refusal)")
    print(f"Retrieval hit:     {retrieval_hits}/{len(answerable)} = {retrieval_hits / na:.0%}")
    print(f"Keyword hit:       {keyword_hits}/{len(answerable)} = {keyword_hits / na:.0%}"
          f"{'   (demo mode - ignore, set GOOGLE_API_KEY)' if rag.llm.DEMO_MODE else ''}")
    if refusals:
        print(f"Refusal accuracy:  {refusal_ok}/{len(refusals)} = {refusal_ok / len(refusals):.0%}")
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")
    if len(tests) < 15:
        print(f"\nNote: only {len(tests)} questions. The brief requires at least 15 for the showcase.")


if __name__ == "__main__":
    run()
