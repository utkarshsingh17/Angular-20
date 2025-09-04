# streamlit_app.py
# -------------------------------------------------------------
# Streamlit UI for the Intelligent Document Summarization & Q&A
# -------------------------------------------------------------
# Features:
# - Upload docs -> POST /ingest (stores chunks + embeddings in pgvector)
# - List docs   -> GET  /docs
# - Summarize   -> POST /summarize/{doc_id}  (editable text, regenerate)
# - Q&A         -> POST /qa/{doc_id}
# - Entities    -> POST /entities/{doc_id}
#
# Backend defaults to http://localhost:8000 (change in sidebar).
# -------------------------------------------------------------

import io
import json
import requests
import streamlit as st

st.set_page_config(page_title="Doc Summarizer & Q&A", layout="wide")

# ---------------------------
# Sidebar: Backend settings
# ---------------------------
st.sidebar.title("Settings")
api_base = st.sidebar.text_input("FastAPI base URL", value="http://localhost:8000")
st.sidebar.markdown("Make sure your backend is running.")

# Session state defaults
if "docs" not in st.session_state:
    st.session_state.docs = []
if "selected_doc" not in st.session_state:
    st.session_state.selected_doc = None
if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""
if "last_entities" not in st.session_state:
    st.session_state.last_entities = []
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

def toast(msg: str, type_: str = "info"):
    if type_ == "error":
        st.error(msg)
    elif type_ == "success":
        st.success(msg)
    elif type_ == "warning":
        st.warning(msg)
    else:
        st.info(msg)

# ---------------------------
# Helpers: API calls
# ---------------------------
def api_get(path: str):
    try:
        r = requests.get(f"{api_base}{path}", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        toast(f"GET {path} failed: {e}", "error")
        return None

def api_post_json(path: str, payload: dict):
    try:
        r = requests.post(f"{api_base}{path}", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        toast(f"POST {path} failed: {e}", "error")
        return None

def api_post_multipart(path: str, fields: dict, file_tuple):
    # file_tuple example: ("filename.txt", file_bytes, "text/plain")
    try:
        files = {"file": file_tuple}
        r = requests.post(f"{api_base}{path}", data=fields, files=files, timeout=300)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        toast(f"POST {path} failed: {e}", "error")
        return None

# ---------------------------
# Header
# ---------------------------
st.title("🧠 Intelligent Document Summarization & Q&A")
st.caption("Upload → Embed → Pick a Doc → Summarize, Ask Questions, Extract Entities")

# ---------------------------
# Row: Upload & Docs list
# ---------------------------
col_up, col_docs = st.columns([1, 1], gap="large")

with col_up:
    st.subheader("1) Upload & Ingest")
    up_doc_id = st.text_input("Document ID (unique)", placeholder="e.g., contract-2025-09-01")
    uploaded = st.file_uploader("Choose a TXT/PDF/DOCX (backend must support your type)", type=None)

    if st.button("Ingest", type="primary", disabled=not (up_doc_id and uploaded)):
        # Send to /ingest (multipart)
        # NOTE: if backend only supports .txt parsing right now, ensure you upload a .txt.
        file_bytes = uploaded.read()
        file_tuple = (uploaded.name, io.BytesIO(file_bytes), uploaded.type or "application/octet-stream")
        resp = api_post_multipart("/ingest", {"doc_id": up_doc_id}, file_tuple)
        if resp:
            toast(f"Ingested: {resp}", "success")

with col_docs:
    st.subheader("2) Pick a Document")
    if st.button("Refresh Docs"):
        resp = api_get("/docs")
        if resp and "documents" in resp:
            st.session_state.docs = resp["documents"]
            toast(f"Loaded {len(st.session_state.docs)} docs", "success")

    st.session_state.selected_doc = st.selectbox(
        "Available documents",
        options=st.session_state.docs,
        index=0 if st.session_state.docs else -1,
        placeholder="Click 'Refresh Docs' first"
    )

# ---------------------------
# Tabs for tasks
# ---------------------------
tab_sum, tab_qa, tab_ent = st.tabs(["📝 Summarize", "❓ Q&A", "🏷️ Entities"])

# ==== Summarize Tab ====
with tab_sum:
    st.subheader("3) Summarize the selected document")
    if not st.session_state.selected_doc:
        st.info("Select a document in the box above.")
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Generate Summary"):
                resp = api_post_json(f"/summarize/{st.session_state.selected_doc}", {})
                if resp and "summary" in resp:
                    st.session_state.summary_text = resp["summary"]
                    toast("Summary generated.", "success")
        with c2:
            if st.button("Regenerate Summary"):
                # Simply call summarize endpoint again (fresh run)
                resp = api_post_json(f"/summarize/{st.session_state.selected_doc}", {})
                if resp and "summary" in resp:
                    st.session_state.summary_text = resp["summary"]
                    toast("Summary regenerated.", "success")

        st.markdown("#### Editable Summary")
        st.session_state.summary_text = st.text_area(
            "You can edit the generated summary here:",
            value=st.session_state.summary_text,
            height=260
        )

        st.caption("Edits are local in the UI. Add a save endpoint if you want to persist user-edited summaries.")

# ==== Q&A Tab ====
with tab_qa:
    st.subheader("4) Ask questions about the selected document")
    if not st.session_state.selected_doc:
        st.info("Select a document in the box above.")
    else:
        question = st.text_input("Your question", placeholder="e.g., Who are the parties and what are the obligations?")
        ask = st.button("Ask")
        if ask and question.strip():
            payload = {"question": question.strip()}
            resp = api_post_json(f"/qa/{st.session_state.selected_doc}", payload)
            if resp and "answer" in resp:
                st.session_state.qa_history.append({"q": question.strip(), "a": resp["answer"]})
                toast("Answer generated.", "success")

        if st.session_state.qa_history:
            st.markdown("#### Q&A History")
            for i, qa in enumerate(reversed(st.session_state.qa_history), 1):
                st.markdown(f"**Q{i}.** {qa['q']}")
                st.write(qa["a"])
                st.divider()

# ==== Entities Tab ====
with tab_ent:
    st.subheader("5) Extract entities from the selected document")
    if not st.session_state.selected_doc:
        st.info("Select a document in the box above.")
    else:
        if st.button("Extract Entities"):
            resp = api_post_json(f"/entities/{st.session_state.selected_doc}", {})
            if resp:
                # accept either structured {"entities": [...]} or text
                entities = resp.get("entities", resp)
                st.session_state.last_entities = entities
                toast("Entities extracted.", "success")

        if st.session_state.last_entities:
            st.markdown("#### Extracted Entities")
            if isinstance(st.session_state.last_entities, list):
                # list of dicts
                for e in st.session_state.last_entities:
                    st.json(e)
            else:
                # raw text / other schema
                st.write(st.session_state.last_entities)
