# HR RAG Chatbox (LangChain + FastAPI)

Production-ready HR assistant for IBM-style policies with Retrieval-Augmented Generation (RAG) using LangChain + ChromaDB + HuggingFace embeddings. Frontend is a lightweight vanilla JS single-page app served by FastAPI.

---
## 🔧 Core Components

| Layer | File / Folder | Purpose |
|-------|---------------|---------|
| API Server | `langchain_server_enhanced.py` | FastAPI app, endpoints, LangChain RAG logic, ticketing |
| Frontend UI | `frontend/index.html` | HTML shell for login + chat interface |
| Frontend Logic | `frontend/app.js` | Login, API calls, chat rendering, suggestion buttons |
| Styling | `frontend/styles.css` | Responsive chat + form styling |
| Dataset | `data/qa_dataset_enriched_slim.csv` | Clean HR Q/A seed knowledge base |
| Vector Store | `storage/chroma_langchain/` | Persisted ChromaDB embeddings |
| Tickets | `lightning_tickets.json` | Stored generated HR tickets |

---
## 🧠 High-Level Architecture

1. User opens `http://localhost:8007/` (served `index.html`).
2. User enters Employee ID → `/api/validate-user` checks format + demo users.
3. User clicks Build Knowledge Base → `/api/ingest` loads dataset → builds LangChain docs → embeds into Chroma (or uses existing persistent store).
4. User asks a question → `/api/chat`:
   - If LangChain available → `rag_system.langchain_search()` (semantic similarity search)
   - Else fallback keyword search
   - Context scrubber removes any leftover dataset artifacts (`Context:`, `According to...`, etc.)
   - Dynamic suggestions generated
5. Optional ticket creation via `/api/ticket` stores metadata in `lightning_tickets.json`.

---
## 📂 Server Breakdown (`langchain_server_enhanced.py`)

Key internal class: `SimpleRAGSystem`

| Method | Role |
|--------|------|
| `load_dataset()` | Loads CSV once (lazy) |
| `setup_embeddings()` | Chooses LangChain vs simple search |
| `setup_langchain_rag()` | Builds `Document` objects and persists Chroma vector store |
| `search()` | Delegates to vector or keyword search |
| `langchain_search()` | Main semantic retrieval + answer cleaning + fallback |
| `simple_search()` | Plain keyword scoring (fallback mode) |
| `get_enhanced_indian_fallback()` | Thematic canned answers for policy domains |
| `generate_suggestions()` | Contextual quick-reply suggestions |
| `no_results_response()` | Standardized low-confidence structure |

### Document Creation (RAG)
```python
for idx, row in df.iterrows():
    question = str(row.get('canonical_question', row.get('Question', ''))).strip()
    answer = str(row.get('short_answer', row.get('Answer', ''))).strip()
    if not question or not answer: continue
    if answer.startswith('According to our HR materials:') or 'Context:' in answer: continue
    doc = Document(
        page_content=f"Question: {question}\nAnswer: {answer}",
        metadata={'question': question, 'answer': answer, 'row_id': idx}
    )
    documents.append(doc)
```

### Embedding + Chroma Persistence
```python
embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
self.vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=str(CHROMA_DIR))
self.vectorstore.persist()
```

### Vector Search + Clean Answer
```python
docs = self.vectorstore.similarity_search(question, k=top_k)
best_doc = docs[0]
raw_answer = best_doc.metadata.get('answer')
clean = completely_remove_context(raw_answer)
if not clean or len(clean) < 20:
    clean = self.get_enhanced_indian_fallback(question)
```

### Aggressive Context Removal
```python
text = re.sub(r'Context:.*$', '', text, flags=re.IGNORECASE|re.DOTALL)
text = re.sub(r'^According to our HR materials:\\s*', '', text, flags=re.IGNORECASE)
text = re.sub(r'Employee:.*$', '', text, flags=re.MULTILINE|re.IGNORECASE)
```

---
## 🌐 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serves UI |
| GET | `/api/health` | Status (dataset + vector state) |
| POST | `/api/validate-user` | Validates Employee ID format |
| POST | `/api/ingest` | Builds or loads vector store |
| POST | `/api/chat` | Answers a user query |
| POST | `/api/ticket` | Creates HR support ticket |
| POST | `/api/contact-hr` | Returns assistant capabilities summary |

---
## 💻 Frontend Flow (`frontend/app.js`)

1. On load: hides chat until user validated.
2. Login form submission → `fetch('/api/validate-user')` → unlocks build button.
3. Build KB button calls `/api/ingest` then enables chat controls.
4. Chat form sends `/api/chat` with `{ question, user_id }`.
5. Renders answer + suggestions + ticket button if low confidence.

### Example Chat Request
```javascript
const res = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: input.value, user_id: window.employeeId })
});
```

### Rendering Suggestions
```javascript
(result.suggestions || []).forEach(s => {
  const btn = document.createElement('button');
  btn.textContent = s;
  btn.onclick = () => sendQuestion(s);
  suggestionsDiv.appendChild(btn);
});
```

---
## 🚀 Running Locally

Windows CMD:
```bat
pip install -r requirements.txt
python langchain_server_enhanced.py
```
Open: `http://localhost:8007/`

First time: click "Build Knowledge Base" (creates `storage/chroma_langchain/`).

---
## 🧪 Quick cURL Tests
```bash
curl http://localhost:8007/api/health
curl -X POST http://localhost:8007/api/validate-user -H "Content-Type: application/json" -d "{\"user_id\":\"EMP001234\"}"
curl -X POST http://localhost:8007/api/chat -H "Content-Type: application/json" -d "{\"question\":\"What are my medical benefits?\"}"
```

---
## 🛡️ Confidence & Fallback Logic

Priority: Vector answer → Cleaned → Validated → Indian fallback domain answer → Generic message.
Ticket button appears when `is_low_confidence` true or retrieval fails.

---
## 🗃️ Persistent Assets

| Path | Contents |
|------|----------|
| `storage/chroma_langchain/` | Embedding DB (safe to delete to rebuild) |
| `lightning_tickets.json` | Saved tickets |

To reset vector store: delete `storage/chroma_langchain/` and re-run ingest.

---
## 🧩 Extending

Add policy domain:
```python
elif 'gratuity' in question_type:
    return "Gratuity is payable after 5 years continuous service..."
```
Swap embedding model:
```python
HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')
```
Add OpenAI LLM re-ranking (future): chain retrieved docs → call LLM.

---
## 🧹 Housekeeping

Safe to delete if unused: `qa_dataset.csv` (using enriched_slim), old experimental server scripts, `__pycache__/`.

---
## ❓ Troubleshooting

| Issue | Fix |
|-------|-----|
| Health shows needs_setup | Check dataset file exists in `data/` |
| Chat always fallback | Delete vector dir → rebuild KB |
| Port conflict | Change `SERVER_PORT` constant |
| Dependency errors | Reinstall: `pip install -r requirements.txt` |

---
## 📄 License
Internal demo / educational use.

---
## ✅ Summary
FastAPI + LangChain RAG HR assistant with persistent Chroma vector store, aggressive context sanitization, domain-aware fallbacks, and simple vanilla frontend.

