# streamlit_app.py (beautiful UI)
import io
import json
import requests
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Doc Summarizer & Q&A", layout="wide")
st.markdown(
    """
    <style>
      .app-title { font-size: 2.0rem; font-weight: 700; margin-bottom: .35rem; }
      .subtle { color: #6b7280; font-size: .95rem; margin-bottom: 1.0rem; }
      .card { background: #111827; border: 1px solid #1f2937; border-radius: 14px; padding: 18px 20px; }
      .pill { display:inline-block; padding: 2px 10px; border-radius: 9999px; font-size:.75rem; border:1px solid #374151; color:#9ca3af; }
      .muted { color:#9ca3af; }
      .section-title { font-size:1.15rem; font-weight:600; margin: 6px 0 12px 0; }
      .summary-box { background: #0b1220; border: 1px solid #1f2937; border-radius: 14px; padding: 16px 18px; }
      .chunk-chip { background:#0f172a; border:1px solid #1f2937; border-radius:10px; padding:8px 10px; margin:4px 0; }
      .small { font-size:.85rem; color:#94a3b8; }
      .btn-row > div button { width: 100%; }
      .caption { color:#94a3b8; font-size:.85rem; }
      /* nicer textarea */
      .stTextArea textarea { background:#0b1220 !important; color:#e5e7eb !important; border-radius:12px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Sidebar: Settings
# ---------------------------
st.sidebar.title("Settings ⚙️")
api_base = st.sidebar.text_input("FastAPI base URL", value="http://localhost:8000")
default_chunk_k = st.sidebar.slider("Retriever top-k (for backend that supports it)", 3, 10, 5)
st.sidebar.markdown("---")
st.sidebar.caption("Tip: keep your backend running. Use a unique doc id on ingest.")

# session state
ss = st.session_state
ss.setdefault("docs", [])
ss.setdefault("selected_doc", None)
ss.setdefault("summary_md", "")
ss.setdefault("qa_history", [])
ss.setdefault("entities", [])
ss.setdefault("raw_summary", None)

# ---------------------------
# Helpers
# ---------------------------
def toast(msg: str, kind="info"):
    getattr(st, kind)(msg)

def api_get(path: str):
    try:
        r = requests.get(f"{api_base}{path}", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        toast(f"GET {path} failed: {e}", "error")

def api_post_json(path: str, payload: dict):
    try:
        r = requests.post(f"{api_base}{path}", json=payload, timeout=180)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        toast(f"POST {path} failed: {e}", "error")

def api_post_multipart(path: str, fields: dict, file_tuple):
    try:
        files = {"file": file_tuple}
        r = requests.post(f"{api_base}{path}", data=fields, files=files, timeout=420)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        toast(f"POST {path} failed: {e}", "error")

def extract_textish(obj):
    """
    Robustly convert backend responses to a clean text string.
    Supports:
      - {"summary": "..."}
      - {"answer": "..."}
      - OpenAI-like: {"choices":[{"message":{"content":"..."}}]}
      - raw string
    """
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        if "summary" in obj and isinstance(obj["summary"], str):
            return obj["summary"]
        if "answer" in obj and isinstance(obj["answer"], str):
            return obj["answer"]
        # OpenAI chat style
        try:
            return obj["choices"][0]["message"]["content"]
        except Exception:
            pass
        # sometimes server returns {"result": "..."}
        if "result" in obj and isinstance(obj["result"], str):
            return obj["result"]
    return json.dumps(obj, ensure_ascii=False, indent=2)

def summarize_pretty_text(summary_text: str) -> str:
    """Light formatting: trim, ensure markdown headings/bullets render nicely."""
    text = summary_text.strip()
    # If it looks like one giant line, add soft wrap hint
    return text

def chunks_section(chunks_used):
    if not chunks_used:
        return
    with st.expander("🔎 Per-chunk highlights (context used)", expanded=False):
        for i, ch in enumerate(chunks_used, 1):
            st.markdown(
                f"""
                <div class="chunk-chip">
                  <div class="small">Chunk {i} • doc <code>{ch.get('doc_id','?')}</code> • distance: {ch.get('distance','')}</div>
                  <div style="margin-top:6px;">{ch.get('chunk','')[:600]}{'…' if len(ch.get('chunk',''))>600 else ''}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# ---------------------------
# Header
# ---------------------------
st.markdown('<div class="app-title">🧠 Doc Summarizer & Q&A</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">Upload → Embed → Select → Summarize / Ask / Extract, all in one place.</div>', unsafe_allow_html=True)

# ---------------------------
# Row: Upload & Pick Doc
# ---------------------------
c_up, c_pick = st.columns([1, 1])

with c_up:
    st.markdown('<div class="section-title">1) Upload & Ingest</div>', unsafe_allow_html=True)
    doc_id = st.text_input("Document ID (unique)")
    file = st.file_uploader("Choose a file (TXT/PDF/DOCX as supported by your backend)")
    ingest = st.button("Ingest Document", type="primary", disabled=not (doc_id and file))
    if ingest:
        file_bytes = file.read()
        file_tuple = (file.name, io.BytesIO(file_bytes), file.type or "application/octet-stream")
        resp = api_post_multipart("/ingest", {"doc_id": doc_id}, file_tuple)
        if resp:
            toast("Ingestion completed.", "success")

with c_pick:
    st.markdown('<div class="section-title">2) Pick a Document</div>', unsafe_allow_html=True)
    if st.button("Refresh list"):
        r = api_get("/documents")
        if r and "documents" in r:
            ss.docs = r["documents"]
            toast(f"Loaded {len(ss.docs)} docs", "success")
    ss.selected_doc = st.selectbox("Documents", options=ss.docs, index=0 if ss.docs else -1)

st.markdown("---")

# ---------------------------
# Task Tabs
# ---------------------------
tab_sum, tab_qa, tab_ent = st.tabs(["📝 Summarize", "❓ Q&A", "🏷️ Entities"])

# === Summarize ===
with tab_sum:
    st.markdown('<div class="section-title">3) Summarize</div>', unsafe_allow_html=True)
    if not ss.selected_doc:
        st.info("Pick a document in step 2.")
    else:
        colA, colB, colC = st.columns([1,1,1])
        with colA:
            if st.button("Generate Summary", use_container_width=True):
                resp = api_post_json(f"/summarize/{ss.selected_doc}", {})
                ss.raw_summary = resp
                text = extract_textish(resp)
                ss.summary_md = summarize_pretty_text(text)
                toast("Summary generated.", "success")
        with colB:
            if st.button("Regenerate", use_container_width=True):
                resp = api_post_json(f"/summarize/{ss.selected_doc}", {})
                ss.raw_summary = resp
                text = extract_textish(resp)
                ss.summary_md = summarize_pretty_text(text)
                toast("Summary regenerated.", "success")
        with colC:
            if ss.summary_md:
                md_name = f"{ss.selected_doc}_summary_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.md"
                st.download_button(
                    "Download .md",
                    data=ss.summary_md.encode("utf-8"),
                    file_name=md_name,
                    mime="text/markdown",
                    use_container_width=True
                )

        if ss.summary_md:
            st.markdown("##### Final Summary")
            st.markdown(f"<div class='summary-box'>{ss.summary_md.replace(chr(10), '<br/>')}</div>", unsafe_allow_html=True)

            st.markdown("##### Edit & Save")
            edited = st.text_area("Make edits (local):", value=ss.summary_md, height=220, key="edit_area")
            colS1, colS2 = st.columns([1,1])
            with colS1:
                if st.button("Apply Edits"):
                    ss.summary_md = edited
                    toast("Edits applied locally.", "success")
            with colS2:
                if st.button("Save to Server (optional)"):
                    # If you add a backend endpoint /save_summary/{doc_id}, wire it here
                    r = api_post_json(f"/save_summary/{ss.selected_doc}", {"summary": ss.summary_md})
                    if r:
                        toast("Saved to server.", "success")

            # show per-chunk context if backend provided it
            chunks = None
            if isinstance(ss.raw_summary, dict):
                chunks = ss.raw_summary.get("chunks_used")
            chunks_section(chunks)

# === Q&A ===
with tab_qa:
    st.markdown('<div class="section-title">Q&A</div>', unsafe_allow_html=True)
    if not ss.selected_doc:
        st.info("Pick a document in step 2.")
    else:
        question = st.text_input("Your question", placeholder="e.g., What obligations are mentioned?")
        if st.button("Ask", type="primary") and question.strip():
            r = api_post_json(f"/qa/{ss.selected_doc}", {"question": question.strip(), "top_k": default_chunk_k})
            ans = extract_textish(r)
            ss.qa_history.insert(0, {"q": question.strip(), "a": ans})
        if ss.qa_history:
            for i, qa in enumerate(ss.qa_history[:12], 1):
                st.markdown(f"**Q{i}.** {qa['q']}")
                st.markdown(f"<div class='card'>{qa['a']}</div>", unsafe_allow_html=True)

# === Entities ===
with tab_ent:
    st.markdown('<div class="section-title">Entities</div>', unsafe_allow_html=True)
    if not ss.selected_doc:
        st.info("Pick a document in step 2.")
    else:
        if st.button("Extract Entities", type="primary"):
            r = api_post_json(f"/entities/{ss.selected_doc}", {})
            # backend might return {"entities":[...]} or text
            if isinstance(r, dict) and "entities" in r:
                ss.entities = r["entities"]
            else:
                ss.entities = r
        if isinstance(ss.entities, list):
            for e in ss.entities:
                st.json(e)
        elif ss.entities:
            st.markdown(f"<div class='card'>{extract_textish(ss.entities)}</div>", unsafe_allow_html=True)
