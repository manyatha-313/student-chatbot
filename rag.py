"""The RAG pipeline: embed chunks, retrieve the closest, answer with citations.

Consumes the chunk schema from ingest.py / plans/datasetplan.md.
"""
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
        # Put the title and section in front so short questions match the right
        # chunk even when the body does not repeat the keyword (datasetplan 6).
        return f"{chunk['title']} | {chunk['section']} | {chunk['text']}"

    def build(self, chunks):
        if not chunks:
            raise ValueError("No chunks to index. Add text-based PDFs to dataset/.")
        self.chunks = chunks
        self.vectors = self.embedder.encode(
            [self._embed_text(c) for c in chunks], normalize_embeddings=True)
        return self

    def retrieve(self, question, top_k=config.TOP_K):
        """Return the top_k chunks with a cosine 'score' (1.0 = identical)."""
        q = self.embedder.encode([question], normalize_embeddings=True)[0]
        scores = self.vectors @ q
        best = np.argsort(scores)[::-1][:top_k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in best]

    def answer(self, question):
        """Return (answer_text, retrieved_chunks). Declines below the
        relevance threshold without calling Gemma."""
        found = self.retrieve(question)
        contact = found[0]["contact"] if found else config.DEFAULT_CONTACT
        if not found or found[0]["score"] < config.RELEVANCE_THRESHOLD:
            return (f'I could not find this in the college documents. '
                    f'Please contact {contact}.', found)

        context = "\n\n".join(f"{_citation(c)} {c['text']}" for c in found)
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        demo = (f"**Demonstration mode:** no API key is set, so Gemma did not write an answer. "
                f"The most relevant passage is {_citation(found[0])}:\n\n> {found[0]['text'][:400]}...")
        reply = llm.generate(prompt, system_text=config.ANSWER_RULES.format(contact=contact),
                             demo_reply=demo)
        return reply, found


def build_from_dataset():
    return RagIndex().build(ingest.load_dataset())


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
