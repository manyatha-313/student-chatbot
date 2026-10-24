# App Plan: RAG Pipeline, Model, UI and Evaluation (Theme 2A)

Companion to [`datasetplan.md`](datasetplan.md). That plan owns **data prep**
(PDF cleaning, section-based chunking, the `dataset/README.md` metadata table).
This plan owns the **application** that consumes its chunks. Split so multiple
contributors don't edit the same files.

## Chunk contract (shared with datasetplan.md section 6)

```python
{"doc": str, "title": str, "page": int, "section": str, "text": str, "contact": str}
```

Embedded as `title | section | text`. Cited as `[doc, Page N, section]`.
The app treats this as the interface — swap in the section-based chunker and
nothing downstream changes.

## Modules (branch `ullas`)

| File | Responsibility |
|---|---|
| `config.py` | All tunable settings + `ANSWER_RULES`. One place to change for experiments. |
| `ingest.py` | **Fallback** word-count chunker producing the chunk contract. `shortcut`: replace with datasetplan's section chunker. |
| `llm.py` | Gemma 4 client via Google AI Studio; demo mode with no API key. |
| `rag.py` | `RagIndex`: embed, retrieve (cosine), answer with citations + relevance-threshold refusal. |
| `app.py` | Gradio UI: dataset loaded on startup, optional upload, answer + retrieved passages. |
| `eval/eval.py` + `eval/testset.json` | Deliverable 7: retrieval-hit %, keyword %, refusal accuracy; seed Q&A to expand to >=15. |

## Open seams for the bonus items

- `config.RELEVANCE_THRESHOLD` already gives "decline when nothing is relevant".
- `config.py` knobs (`CHUNK_SIZE`, `TOP_K`, `EMBED_MODEL_NAME`) + `eval.py` →
  the chunk-size / top-k / model sweeps and RAG-vs-no-RAG comparison.
- Per-document `title`/`contact` will come from `dataset/README.md` once it
  exists; `ingest.load_dataset` uses the file name + a default until then.

## Not in this plan

Section chunking, cleaning, `dataset/README.md`, conflict detection and
conversation memory — see `datasetplan.md` / later work.
