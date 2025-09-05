# 📄 Intelligent Document Summarization & Q&A Platform

## 🚀 Overview
This project is a **multi-agent system** that ingests documents (contracts, research papers, policies, etc.), **summarizes** them, **extracts entities**, and enables **natural language Q&A** over the document corpus.  

It combines:
- 🧑‍🤝‍🧑 **Autogen Agents** for orchestrated workflows  
- ⚡ **FastAPI** backend for APIs  
- 🎨 **Streamlit** UI for user interaction  
- 🔌 **MCP Servers** for modular tools (summarization, Q&A, entities, file ops, KB, web search)  
- 📦 **pgvector** for document embeddings storage  
- 📊 **LangSmith** for logging and observability  

---

## ✨ Features
- 📤 **Document Ingestion** → Upload TXT/DOCX/PDF, store embeddings in `pgvector`  
- 📝 **Summarization Agent** → Generate concise, coherent summaries (single doc / corpus)  
- 🔎 **Entity Extraction Agent** → Extract entities (names, dates, orgs, locations, etc.)  
- ❓ **Q&A Agent** → Answer natural language questions over selected docs  
- ✅ **Validator Agent** → Validate and rollback incorrect outputs  
- 👨‍💻 **Human-in-the-loop** → Edit AI summaries before saving  
- 📊 **Streamlit Dashboard** → Upload, summarize, query, extract entities, and monitor  
- 🔌 **Extensible MCP Tools** → File ops, knowledge base, web search  

---

## 🛠️ Tech Stack
- **[Autogen 0.7+](https://github.com/microsoft/autogen)** – Multi-agent orchestration  
- **[FastAPI](https://fastapi.tiangolo.com/)** – REST backend  
- **[Streamlit](https://streamlit.io/)** – UI  
- **[FastMCP](https://pypi.org/project/fastmcp/)** – Modular tool execution  
- **[pgvector](https://github.com/pgvector/pgvector)** – Vector DB  
- **[LangChain + HuggingFace](https://www.langchain.com/)** – Embeddings & retrieval  
- **[LangSmith](https://smith.langchain.com/)** – Logging & observability  
- **[OpenAI/Azure OpenAI](https://platform.openai.com/)** – LLMs  

---

## 📂 Project Structure
