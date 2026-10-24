"""Shared settings for the Campus Regulations Assistant (Theme 2A).

One place to tune the pipeline. The eval harness sweeps these for the bonus
experiments, so keep every knob here rather than inline.
"""

# --- Models -----------------------------------------------------------------
GEMMA_MODEL = "gemma-4-26b-a4b-it"       # writes the answers, via Google AI Studio
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # embeddings, on CPU

# --- Chunking (fallback ingestion; see plans/datasetplan.md for the real one) -
CHUNK_SIZE = 120        # words per chunk
CHUNK_OVERLAP = 30      # words shared by neighbouring chunks
MIN_CHUNK_WORDS = 5     # drop fragments shorter than this

# --- Retrieval & answering --------------------------------------------------
TOP_K = 5               # chunks given to Gemma per question
TEMPERATURE = 0.2       # low -> consistent, close to the document
RELEVANCE_THRESHOLD = 0.30  # decline if the best chunk scores below this
                            # (cosine on normalized embeddings, 1.0 = identical)

DATASET_DIR = "dataset"
CHUNKS_PATH = "dataset/processed/chunks.jsonl"  # prebuilt by scripts/prepare_dataset.py; preferred over on-the-fly chunking
VECTORS_CACHE = "dataset/processed/vectors.npz"  # embedding cache (gitignored); rebuilt when the chunks change
DEFAULT_CONTACT = "the relevant college office"  # used until dataset/README.md lists per-doc contacts

# --- Department isolation (enforced in rag.retrieve, not just the prompt) -----
COLLEGE_WIDE_TYPES = {"handbook"}  # official docs that apply to every department (rules, regulations)
EXCLUDE_TYPES = {"brochure"}       # never answer from these (the upGrad brochure is not an official SSIT document)
# When a department is selected, retrieval sees only that department's syllabus
# plus the college-wide docs above; other departments' documents are filtered out.

REFUSAL_TEMPLATE = "I could not verify this from the available college documents. Please contact {contact}."

# The rules Gemma follows. Context-only prevents invented answers; the fixed
# refusal line is what eval and the app check for.
ANSWER_RULES = """You answer students' questions about college regulations using ONLY the context passages provided.
- Each passage begins with its source, for example [RULE-BOOK.pdf, Page 3].
- After each fact you use, cite the source in brackets, for example (RULE-BOOK.pdf, p. 3).
- Use ONLY the context. Never add facts from general knowledge. If only part of the question is supported, answer only that part and say the rest is not in the documents.
- If the answer is not in the context, reply exactly: "I could not verify this from the available college documents. Please contact {contact}."
- Keep answers concise: 2 to 4 sentences."""
