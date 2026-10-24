"""Gradio app for the Campus Regulations Assistant. Adapted from the starter kit.

Run:  python app.py   (prints a local URL and a public *.gradio.live link)
"""
import os

import gradio as gr

import config
import ingest
import rag

gr.close_all()  # close any previous version still running

APP_TITLE = "Campus Regulations Assistant"
APP_DESCRIPTION = ("Ask about college regulations. Answers come only from the official "
                   "documents and cite the document and page. Questions the documents do "
                   "not cover are declined.")

index = rag.build_from_dataset()  # built from the PDFs in dataset/ at startup


def _status():
    docs = sorted({c["doc"] for c in index.chunks})
    return f"**Loaded documents ({len(docs)}):** {', '.join(docs) or 'none'}"


def on_upload(files):
    if not files:
        return _status()
    try:
        for path in files:
            index.chunks.extend(
                ingest.split_into_chunks(ingest.read_pdf(path), os.path.basename(path),
                                         title=os.path.basename(path),
                                         contact=config.DEFAULT_CONTACT))
        index.build(index.chunks)  # re-embed with the added documents
        return _status()
    except Exception as e:
        raise gr.Error(f"The PDF could not be read: {e}")


def on_ask(question):
    if not question.strip():
        raise gr.Error("Enter a question first.")
    reply, found = index.answer(question)
    sources = "\n\n".join(
        f"**{rag._citation(c)}** (similarity {c['score']:.2f})\n> {c['text']}" for c in found)
    return reply, sources


with gr.Blocks(title=APP_TITLE) as demo:
    gr.Markdown(f"# {APP_TITLE}\n{APP_DESCRIPTION}")
    with gr.Row():
        pdf_input = gr.File(label="Add a PDF (optional)", file_types=[".pdf"],
                            file_count="multiple", type="filepath")
        status_md = gr.Markdown(_status())
    question_box = gr.Textbox(label="Question",
                              placeholder="For example: What is the minimum attendance required?")
    ask_btn = gr.Button("Ask", variant="primary")
    gr.Examples([
        "What is the minimum attendance required to sit the end-semester examination?",
        "Can I apply for a re-evaluation, and what is the deadline?",
        "What are the hostel visiting hours?",
    ], inputs=question_box)
    answer_md = gr.Markdown()
    with gr.Accordion("Retrieved passages (the text given to Gemma)", open=False):
        sources_md = gr.Markdown()

    pdf_input.upload(on_upload, inputs=pdf_input, outputs=status_md)
    ask_btn.click(on_ask, inputs=question_box, outputs=[answer_md, sources_md])
    question_box.submit(on_ask, inputs=question_box, outputs=[answer_md, sources_md])

if __name__ == "__main__":
    demo.launch(share=True)
