"""Campus Regulations Assistant - guided chat UI (Gradio).

Text-only. The user drills down Degree -> Branch -> Year (keyword-style
suggestions, Aspen-portal style), or just types a question. Answers come only
from the official documents, cite document + page, and show the retrieved
passages. Conversation memory handles follow-ups ("what about for MBA?").

Run:  python app.py   (prints a local URL and a public *.gradio.live link)
"""
import collections
import json

import gradio as gr
import numpy as np

import config
import rag

index = rag.build_from_dataset()

# --- Catalog of what documents actually exist, for the cascading pickers -----
BRANCH_NAMES = {}
try:
    BRANCH_NAMES = json.load(open("dataset/documents.json")).get("branches", {})
except Exception:
    pass

CATALOG = collections.defaultdict(lambda: collections.defaultdict(set))  # program -> branch -> {years}
for c in index.chunks:
    if c.get("program") and c.get("branch"):
        CATALOG[c["program"]][c["branch"]].add(c.get("year"))

DEGREES = ["BE", "MTech", "MSc", "BSc", "BCA", "MCA"]  # full list; those without docs are refused
DEG2PROG = {"BE": "B.E.", "MTech": "M.Tech."}          # only these have documents in the repo

OFF_TOPIC = "I can only help with questions about SSIT rules, syllabus and documents."


def branch_choices(degree):
    prog = DEG2PROG.get(degree)
    if not prog or prog not in CATALOG:
        return []
    return [(f"{b} - {BRANCH_NAMES.get(b, b)}", b) for b in sorted(CATALOG[prog])]


def year_choices(degree, branch):
    prog = DEG2PROG.get(degree)
    if not (prog and branch in CATALOG.get(prog, {})):
        return []
    return [str(y) for y in sorted(y for y in CATALOG[prog][branch] if y)]


def suggestions(branch=None, year=None):
    s = ["What is the minimum attendance to write the SEE?",
         "How is CGPA converted to percentage of marks?",
         "What are the punishments for ragging?"]
    if branch and year:
        s = [f"What subjects are in the {branch} year {year} syllabus?",
             f"List the course outcomes for a {branch} year {year} course."] + s
    return s


# --- Retrieval scoped to the selected department (college-wide docs always in) -
def _in_scope(chunk, program, branch):
    ctype = chunk.get("type")
    if ctype in ("handbook", "brochure"):
        return True  # college-wide rules, and the (labelled) brochure
    if not branch:
        return True
    if chunk.get("branch") != branch:
        return False
    return not (program and chunk.get("program") and chunk.get("program") != program)


def scoped_retrieve(question, program, branch, top_k=config.TOP_K):
    q = index.embedder.encode([question], normalize_embeddings=True)[0]
    scores = index.vectors @ q
    idx = [i for i, c in enumerate(index.chunks) if _in_scope(c, program, branch)]
    idx.sort(key=lambda i: scores[i], reverse=True)
    return [{**index.chunks[i], "score": float(scores[i])} for i in idx[:top_k]]


def _sources_md(found):
    rows = []
    for c in found:
        tag = "  *(upGrad brochure - not an official SSIT document)*" if c.get("type") == "brochure" else ""
        head = f" - {c['heading']}" if c.get("heading") else (f" - {c['section']}" if c.get("section") else "")
        rows.append(f"**{c['doc']}, p. {c['page']}**{head}  (similarity {c['score']:.2f}){tag}\n> {c['text']}")
    return "\n\n".join(rows) or "_No passages retrieved._"


def respond(message, history, degree, branch, year):
    message = (message or "").strip()
    if not message:
        return history, gr.update(), gr.update(), ""
    program = DEG2PROG.get(degree)

    # Follow-ups ("what about for MBA?") retrieve better with the previous question's words.
    query = message
    prev = [m["content"] for m in (history or []) if m["role"] == "user"]
    if prev and len(message.split()) <= 5:
        query = prev[-1] + " " + message
    year_hint = f" (for {branch} year {year})" if branch and year else ""
    found = scoped_retrieve(query + year_hint, program, branch)

    if not found or found[0]["score"] < config.RELEVANCE_THRESHOLD:
        reply, found = OFF_TOPIC, []
    else:
        contact = found[0]["contact"]
        context = "\n\n".join(f"[{c['doc']}, Page {c['page']}] {c['text']}" for c in found)
        convo = "\n".join(f"{m['role']}: {m['content']}" for m in (history or [])[-4:])
        prompt = (f"Conversation so far:\n{convo}\n\n" if convo else "") + \
                 f"Context:\n{context}\n\nQuestion: {message}"
        demo = (f"**Demo mode (no API key):** most relevant passage - "
                f"[{found[0]['doc']}, p. {found[0]['page']}]:\n\n> {found[0]['text'][:300]}...")
        reply = rag.llm.generate(prompt, system_text=config.ANSWER_RULES.format(contact=contact),
                                 demo_reply=demo)
        if any(c.get("type") == "brochure" for c in found):
            reply += "\n\n_(This is from the upGrad brochure, not an official SSIT document.)_"

    history = (history or []) + [{"role": "user", "content": message},
                                 {"role": "assistant", "content": reply}]
    return history, _sources_md(found), gr.update(open=bool(found)), ""


with gr.Blocks(title="Campus Regulations Assistant") as demo:
    gr.Markdown("# Campus Regulations Assistant\nAsk about SSIT rules, regulations and syllabus. "
                "Answers come only from the official documents, with page citations.")
    with gr.Row():
        degree = gr.Dropdown(DEGREES, label="Degree", value=None)
        branch = gr.Dropdown([], label="Branch", value=None, interactive=False)
        year = gr.Dropdown([], label="Year", value=None, interactive=False)
    status = gr.Markdown("Pick a degree to see its branches, or just type a question below.")
    suggest = gr.Dropdown(suggestions(), label="Suggested questions", value=None)

    chat = gr.Chatbot(label="Chat", height=360)
    with gr.Row():
        box = gr.Textbox(placeholder="Ask anything about SSIT rules or syllabus...", scale=5, show_label=False)
        send = gr.Button("Ask", variant="primary", scale=1)
    with gr.Accordion("Sources (retrieved passages)", open=False) as src_acc:
        sources = gr.Markdown()

    def on_degree(d):
        bc = branch_choices(d)
        if DEG2PROG.get(d) in CATALOG:
            msg = f"Select a branch for **{d}**."
        else:
            msg = f"No documents are available for **{d}** yet. You can still ask general questions below."
        return (gr.update(choices=bc, value=None, interactive=bool(bc)),
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=suggestions()), msg)

    def on_branch(d, b):
        yc = year_choices(d, b)
        return gr.update(choices=yc, value=None, interactive=bool(yc)), gr.update(choices=suggestions(b))

    def on_year(b, y):
        return gr.update(choices=suggestions(b, y))

    degree.change(on_degree, degree, [branch, year, suggest, status])
    branch.change(on_branch, [degree, branch], [year, suggest])
    year.change(on_year, [branch, year], suggest)

    send.click(respond, [box, chat, degree, branch, year], [chat, sources, src_acc, box])
    box.submit(respond, [box, chat, degree, branch, year], [chat, sources, src_acc, box])
    suggest.select(lambda s, h, d, b, y: respond(s, h, d, b, y),
                   [suggest, chat, degree, branch, year], [chat, sources, src_acc, box])

if __name__ == "__main__":
    demo.launch(share=True)
