"""Turn the PDFs in dataset/ into chunks for retrieval.

shortcut: word-count splitting only, no header/footer cleaning and no
section detection; replace split_into_chunks with the section-based chunker
from plans/datasetplan.md once the dataset agent lands it. The chunk schema
here already matches that plan, so retrieval/app/eval won't need changes.
"""
import glob
import os

from pypdf import PdfReader

import config

# Chunk schema (see plans/datasetplan.md section 6):
#   {doc, title, page, section, text, contact}
REQUIRED_KEYS = {"doc", "title", "page", "section", "text", "contact"}


def read_pdf(path):
    """Return a list of page texts from a PDF (index 0 = page 1)."""
    return [page.extract_text() or "" for page in PdfReader(path).pages]


def split_into_chunks(pages, doc, title, contact):
    """Split each page into overlapping word-count chunks. A chunk never
    crosses a page, so its page citation stays correct."""
    chunks = []
    step = max(1, config.CHUNK_SIZE - config.CHUNK_OVERLAP)
    for page_number, text in enumerate(pages, start=1):
        words = text.split()
        for start in range(0, len(words), step):
            chunk_words = words[start:start + config.CHUNK_SIZE]
            if len(chunk_words) > config.MIN_CHUNK_WORDS:
                chunks.append({
                    "doc": doc,
                    "title": title,
                    "page": page_number,
                    "section": "",   # filled by the section-based chunker later
                    "text": " ".join(chunk_words),
                    "contact": contact,
                })
            if start + config.CHUNK_SIZE >= len(words):
                break
    return chunks


def load_dataset(dataset_dir=config.DATASET_DIR):
    """Read every *.pdf in dataset_dir and return all chunks.

    Until dataset/README.md lists per-document titles and contacts, the title
    is the file name and the contact is a generic default.
    """
    chunks = []
    for path in sorted(glob.glob(os.path.join(dataset_dir, "**", "*.pdf"), recursive=True)):
        doc = os.path.basename(path)
        chunks.extend(split_into_chunks(read_pdf(path), doc, title=doc,
                                        contact=config.DEFAULT_CONTACT))
    return chunks


if __name__ == "__main__":
    chunks = load_dataset()
    docs = sorted({c["doc"] for c in chunks})
    print(f"Documents: {len(docs)} -> {docs}")
    print(f"Chunks: {len(chunks)}")

    # self-check
    assert chunks, "No chunks produced. Are there text-based PDFs in dataset/?"
    assert all(REQUIRED_KEYS <= c.keys() for c in chunks), "A chunk is missing a required key."
    assert all(isinstance(c["page"], int) and c["page"] >= 1 for c in chunks), "Bad page number."
    avg = sum(len(c["text"].split()) for c in chunks) / len(chunks)
    print(f"Average words per chunk: {avg:.0f}")
    print("Self-check passed.")
