"""The RAG pipeline: embed chunks, retrieve the closest, answer with citations.

Consumes the chunk schema from ingest.py / plans/datasetplan.md.
"""
import hashlib
import json
import os

import numpy as np
from sentence_transformers import SentenceTransformer

import config
import ingest
import llm


def _citation(chunk):
    """[RULE-BOOK.pdf, Page 3, 4.2 Attendance]  (section omitted if empty)"""
    tail = f", {chunk['section']}" if chunk["section"] else ""
    return f"[{chunk['doc']}, Page {chunk['page']}{tail}]"


class RagIndex:
    def __init__(self, embed_model_name=config.EMBED_MODEL_NAME):
        self.embedder = SentenceTransformer(embed_model_name)  # runs on CPU
        self.chunks = []
        self.vectors = None

    def _embed_text(self, chunk):
        # Prebuilt chunks carry their own embed_text (title|section|heading|text);
        # otherwise build the title|section|text form (datasetplan 6).
        return chunk.get("embed_text") or f"{chunk['title']} | {chunk.get('section', '')} | {chunk['text']}"

    def build(self, chunks):
        if not chunks:
            raise ValueError("No chunks to index. Add text-based PDFs to dataset/.")
        self.chunks = chunks
        texts = [self._embed_text(c) for c in chunks]
        # Cache the vectors so startup is fast; the key invalidates when the
        # texts or the embedding model change (e.g. the dataset is regenerated).
        key = hashlib.md5((config.EMBED_MODEL_NAME + "\n".join(texts)).encode("utf-8")).hexdigest()
        try:
            cached = np.load(config.VECTORS_CACHE, allow_pickle=False)
            if str(cached["key"]) == key:
                self.vectors = cached["vectors"]
                return self
        except (FileNotFoundError, OSError, KeyError):
            pass
        self.vectors = self.embedder.encode(texts, normalize_embeddings=True)
        os.makedirs(os.path.dirname(config.VECTORS_CACHE), exist_ok=True)
        np.savez(config.VECTORS_CACHE, vectors=self.vectors, key=np.array(key))
        return self

    def _candidate(self, chunk, branch, program):
        """Department isolation: decide whether a chunk may be retrieved for the
        selected branch/program. College-wide docs are always allowed; excluded
        types never are; otherwise the branch (and program, if given) must match."""
        ctype = chunk.get("type")
        if ctype in config.EXCLUDE_TYPES:
            return False
        if ctype in config.COLLEGE_WIDE_TYPES or not chunk.get("branch"):
            return True  # handbook / regulations apply to every department
        if branch is None:
            return True  # no department selected -> search everything (minus excluded)
        if chunk.get("branch") != branch:
            return False
        if program and chunk.get("program") and chunk.get("program") != program:
            return False
        return True

    def retrieve(self, question, top_k=config.TOP_K, branch=None, program=None):
        """Return the top_k chunks with a cosine 'score' (1.0 = identical),
        restricted to the selected department plus college-wide documents."""
        q = self.embedder.encode([question], normalize_embeddings=True)[0]
        scores = self.vectors @ q
        allowed = [i for i, c in enumerate(self.chunks) if self._candidate(c, branch, program)]
        if not allowed:
            return []
        allowed.sort(key=lambda i: scores[i], reverse=True)
        return [{**self.chunks[i], "score": float(scores[i])} for i in allowed[:top_k]]

    def answer(self, question, branch=None, program=None):
        """Return (answer_text, retrieved_chunks). Declines below the relevance
        threshold (or when the selected department has no evidence) without
        calling Gemma."""
        found = self.retrieve(question, branch=branch, program=program)
        contact = found[0]["contact"] if found else config.DEFAULT_CONTACT
        if not found or found[0]["score"] < config.RELEVANCE_THRESHOLD:
            return config.REFUSAL_TEMPLATE.format(contact=contact), found

        context = "\n\n".join(f"{_citation(c)} {c['text']}" for c in found)
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        demo = (f"**Demonstration mode:** no API key is set, so Gemma did not write an answer. "
                f"The most relevant passage is {_citation(found[0])}:\n\n> {found[0]['text'][:400]}...")
        reply = llm.generate(prompt, system_text=config.ANSWER_RULES.format(contact=contact),
                             demo_reply=demo)
        return reply, found

    def available_scopes(self):
        """Distinct (program, branch) pairs that have their own documents, for
        the department picker. Excludes college-wide and excluded types."""
        seen = {}
        for c in self.chunks:
            if c.get("branch") and c.get("type") not in config.EXCLUDE_TYPES \
                    and c.get("type") not in config.COLLEGE_WIDE_TYPES:
                seen[(c.get("program") or "", c["branch"])] = True
        return [{"program": p, "branch": b} for (p, b) in sorted(seen)]


def load_chunks():
    """Prefer the prebuilt chunks from scripts/prepare_dataset.py; fall back to
    chunking the PDFs directly if that file is absent."""
    if os.path.exists(config.CHUNKS_PATH):
        with open(config.CHUNKS_PATH, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    return ingest.load_dataset()


def build_from_dataset():
    return RagIndex().build(load_chunks())


if __name__ == "__main__":
    index = build_from_dataset()
    print(f"Indexed {len(index.chunks)} chunks.\n")
    for q in ["What is the minimum attendance required?",
              "Who won the 2022 World Cup?"]:   # second should be declined
        reply, found = index.answer(q)
        print(f"Q: {q}\nA: {reply}\n")
        for c in found:
            print(f"   {_citation(c)} score={c['score']:.2f}  {c['text'][:80]}...")
        print()
