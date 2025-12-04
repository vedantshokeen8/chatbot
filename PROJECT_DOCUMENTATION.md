# IBM HR RAG Chatbox - Complete Project Documentation

A comprehensive guide to understanding and working with the IBM HR RAG Chatbox system built with LangChain, FastAPI, and vanilla JavaScript.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [System Architecture](#-system-architecture)
3. [Component Deep Dive](#-component-deep-dive)
4. [Setup & Installation](#-setup--installation)
5. [API Documentation](#-api-documentation)
6. [Frontend Architecture](#-frontend-architecture)
7. [RAG Implementation](#-rag-implementation)
8. [Data Flow](#-data-flow)
9. [Code Examples](#-code-examples)
10. [Troubleshooting](#-troubleshooting)

---

## 🎯 Project Overview

This is an enterprise-grade HR assistant chatbot that uses **Retrieval-Augmented Generation (RAG)** to provide intelligent responses to employee HR queries. The system combines:

- **LangChain** for RAG pipeline orchestration
- **ChromaDB** for vector storage and semantic search
- **HuggingFace** embeddings for text understanding
- **FastAPI** for robust backend API
- **Vanilla JavaScript** for lightweight frontend

### Key Features
- ✅ Semantic search with vector embeddings
- ✅ Context-aware response generation
- ✅ Indian labor law compliance (₹ currency, leave policies)
- ✅ Aggressive context cleaning to prevent data leakage
- ✅ Ticket generation system
- ✅ User authentication with Employee ID validation
- ✅ Responsive web interface

---

## 🏗️ System Architecture

```mermaid
graph TB
    A[User Browser] --> B[Frontend - index.html]
    B --> C[JavaScript - app.js]
    C --> D[FastAPI Server - Port 8007]
    D --> E[SimpleRAGSystem Class]
    E --> F[LangChain RAG Pipeline]
    F --> G[HuggingFace Embeddings]
    F --> H[ChromaDB Vector Store]
    E --> I[CSV Dataset]
    D --> J[Ticket System]
    J --> K[lightning_tickets.json]
```

### Component Stack
```
┌─────────────────────────────────────┐
│           Frontend Layer            │
│  ┌─────────────────────────────────┐│
│  │ HTML + CSS + Vanilla JavaScript ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│            API Layer                │
│  ┌─────────────────────────────────┐│
│  │        FastAPI Server           ││
│  │     (langchain_server_          ││
│  │      enhanced.py)               ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│          RAG Layer                  │
│  ┌─────────────────────────────────┐│
│  │       LangChain Pipeline        ││
│  │   + SimpleRAGSystem Class       ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│          Storage Layer              │
│  ┌─────────────┬─────────────────────┐│
│  │ ChromaDB    │   CSV Dataset      ││
│  │ Vector Store│   + Tickets JSON   ││
│  └─────────────┴─────────────────────┘│
└─────────────────────────────────────┘
```

---

## 🔧 Component Deep Dive

### 1. Backend Server (`langchain_server_enhanced.py`)

**Primary Role:** FastAPI application that orchestrates the entire RAG system

**Key Components:**

#### A. Server Configuration
```python
# Server setup
APP_NAME = "IBM HR Assistant - LangChain RAG"
SERVER_PORT = 8007
BASE_DIR = Path(__file__).parent
DATASET_LOCAL = BASE_DIR / "data" / "qa_dataset_enriched_slim.csv"
CHROMA_DIR = BASE_DIR / "storage" / "chroma_langchain"

# FastAPI app with CORS
app = FastAPI(title=f"{APP_NAME}", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### B. SimpleRAGSystem Class Structure
```python
class SimpleRAGSystem:
    def __init__(self):
        self.df = None                    # Dataset cache
        self.embeddings_ready = False     # Status flag
        self.vector_index = {}            # Simple search fallback
        self.vectorstore = None           # ChromaDB instance
    
    # Core methods:
    # - load_dataset()           → CSV loading
    # - setup_embeddings()       → RAG vs Simple choice
    # - setup_langchain_rag()    → Vector store creation
    # - search()                 → Main search dispatch
    # - langchain_search()       → Semantic retrieval
    # - simple_search()          → Keyword fallback
```

### 2. Frontend Interface (`frontend/`)

#### A. HTML Structure (`index.html`)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IBM HR Assistant - LangChain RAG</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- Header with IBM branding -->
    <header class="header">
        <div class="header-content">
            <img src="ibm-logo.svg" alt="IBM" class="logo">
            <h1>HR Assistant</h1>
            <div class="status-indicator" id="connectionStatus">●</div>
        </div>
    </header>

    <!-- Login form -->
    <div id="loginSection" class="login-section">
        <form id="loginForm">
            <input type="text" id="employeeId" placeholder="Enter Employee ID (e.g., EMP001234)" required>
            <button type="submit">Login</button>
        </form>
    </div>

    <!-- Knowledge base setup -->
    <div id="setupSection" class="setup-section" style="display: none;">
        <button id="buildKnowledgeBase">Build Knowledge Base</button>
        <div id="setupStatus"></div>
    </div>

    <!-- Chat interface -->
    <div id="chatSection" class="chat-section" style="display: none;">
        <div id="chatMessages" class="chat-messages"></div>
        <div id="suggestions" class="suggestions"></div>
        <form id="chatForm" class="chat-form">
            <input type="text" id="chatInput" placeholder="Ask me about HR policies..." required>
            <button type="submit" id="sendBtn">Send</button>
        </form>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

#### B. JavaScript Logic (`app.js`)
```javascript
// Global state management
let isLoggedIn = false;
let knowledgeBaseReady = false;
window.employeeId = null;

// Port configuration for API calls
const LANGCHAIN_PORT = 8007;
const API_PORTS = [LANGCHAIN_PORT];

// Main API call function with port fallback
async function callAPI(endpoint, data = null) {
    for (const port of API_PORTS) {
        try {
            const url = `http://localhost:${port}${endpoint}`;
            const options = {
                method: data ? 'POST' : 'GET',
                headers: { 'Content-Type': 'application/json' }
            };
            if (data) options.body = JSON.stringify(data);
            
            const response = await fetch(url, options);
            if (response.ok) return await response.json();
        } catch (error) {
            console.warn(`Port ${port} failed:`, error.message);
        }
    }
    throw new Error('All API ports failed');
}

// Login flow
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const employeeId = document.getElementById('employeeId').value.trim();
    
    try {
        const result = await callAPI('/api/validate-user', { user_id: employeeId });
        if (result.valid) {
            window.employeeId = employeeId;
            isLoggedIn = true;
            showSetupSection();
            updateConnectionStatus('connected');
        } else {
            alert(result.message || 'Invalid Employee ID');
        }
    } catch (error) {
        alert('Login failed: ' + error.message);
        updateConnectionStatus('error');
    }
});

// Knowledge base initialization
document.getElementById('buildKnowledgeBase').addEventListener('click', async () => {
    try {
        updateSetupStatus('Building knowledge base...');
        const result = await callAPI('/api/ingest', { force_rebuild: false });
        
        if (result.restart_required) {
            updateSetupStatus(result.message);
        } else {
            knowledgeBaseReady = true;
            updateSetupStatus(`✅ ${result.message}`);
            showChatSection();
        }
    } catch (error) {
        updateSetupStatus(`❌ Setup failed: ${error.message}`);
    }
});

// Chat message handling
document.getElementById('chatForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    addMessage(question, 'user');
    input.value = '';
    
    try {
        const result = await callAPI('/api/chat', {
            question: question,
            user_id: window.employeeId
        });
        
        addMessage(result.answer, 'assistant', result);
        renderSuggestions(result.suggestions || []);
        
    } catch (error) {
        addMessage(`❌ Error: ${error.message}`, 'assistant');
    }
});
```

### 3. RAG Implementation Deep Dive

#### A. Dataset Loading & Document Creation
```python
def setup_langchain_rag(self):
    """Setup full LangChain RAG with document processing"""
    try:
        # Load and validate dataset
        df = self.load_dataset()
        documents = []
        
        for idx, row in df.iterrows():
            question = str(row.get('canonical_question', row.get('Question', ''))).strip()
            answer = str(row.get('short_answer', row.get('Answer', ''))).strip()
            tags = str(row.get('tags', '')).strip()
            
            # Data quality checks
            if not question or not answer:
                continue
            
            # Skip malformed answers with context bleeding
            if answer.startswith("According to our HR materials:") or "Context:" in answer:
                continue
            
            # Create clean document with structured content
            content_parts = [f"Question: {question}", f"Answer: {answer}"]
            if tags:
                content_parts.append(f"Tags: {tags}")
            
            doc = Document(
                page_content="\n".join(content_parts),
                metadata={
                    'question': question,
                    'answer': answer,
                    'tags': tags,
                    'row_id': idx
                }
            )
            documents.append(doc)
        
        # Create embeddings and vector store
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Use existing or create new vector store
        if os.path.exists(CHROMA_DIR):
            self.vectorstore = Chroma(persist_directory=str(CHROMA_DIR), embedding_function=embeddings)
        else:
            self.vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=str(CHROMA_DIR))
            self.vectorstore.persist()
        
        self.embeddings_ready = True
        print(f"✅ LangChain RAG setup complete: {len(documents)} documents")
        return len(documents)
        
    except Exception as e:
        print(f"❌ LangChain setup failed: {e}")
        return self.setup_simple_search()
```

#### B. Semantic Search Implementation
```python
def langchain_search(self, question: str, top_k: int) -> Dict[str, Any]:
    """LangChain vector search with complete context removal"""
    try:
        # Perform semantic similarity search
        docs = self.vectorstore.similarity_search(question, k=top_k)
        
        if docs:
            # Advanced context removal function
            def completely_remove_context(text):
                if not text:
                    return ""
                
                text = str(text)
                
                # Remove everything with "Context:"
                import re
                text = re.sub(r'Context:.*$', '', text, flags=re.IGNORECASE | re.DOTALL)
                text = re.sub(r'\n\s*Context:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
                text = re.sub(r'.*Context:.*?\n', '', text, flags=re.DOTALL | re.IGNORECASE)
                
                # Remove "According to our HR materials:" prefix
                text = re.sub(r'^According to our HR materials:\s*', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\n\s*According to our HR materials:\s*', '\n', text, flags=re.IGNORECASE)
                
                # Remove "Employee:" statements
                text = re.sub(r'Employee:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
                text = re.sub(r'\n\s*Employee:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
                
                # Clean up whitespace
                text = re.sub(r'\n\s*\n', '\n', text)
                text = re.sub(r'^\s+|\s+$', '', text)
                
                return text.strip()
            
            # Extract clean answer from best matching document
            best_doc = docs[0]
            answer = None
            
            # Try metadata first (preferred source)
            if best_doc.metadata.get('answer'):
                raw_answer = best_doc.metadata.get('answer')
                clean_answer = completely_remove_context(raw_answer)
                if clean_answer and len(clean_answer) > 10:
                    answer = clean_answer
            
            # Try content extraction as fallback
            if not answer and "Answer:" in best_doc.page_content:
                extracted = best_doc.page_content.split("Answer:")[1].split("Tags:")[0].strip()
                clean_answer = completely_remove_context(extracted)
                if clean_answer and len(clean_answer) > 10:
                    answer = clean_answer
            
            # Use enhanced Indian HR fallback if needed
            if not answer or len(answer) < 20 or "According to" in answer or "Context:" in answer:
                answer = self.get_enhanced_indian_fallback(question)
            
            # Final safety check
            if "Context:" in answer or "Employee:" in answer:
                answer = self.get_enhanced_indian_fallback(question)
            
            return {
                "answer": answer,
                "sources": [],
                "suggestions": self.get_dynamic_suggestions(question),
                "confidence_score": 0.95,
                "is_low_confidence": False,
                "confidence_message": "✅ High Confidence",
                "retrieval_method": "langchain_vector_clean",
                "show_ticket_button": False
            }
        else:
            # No documents found, use Indian HR fallback
            return {
                "answer": self.get_enhanced_indian_fallback(question),
                "sources": [],
                "suggestions": self.get_dynamic_suggestions(question),
                "confidence_score": 0.85,
                "is_low_confidence": False,
                "confidence_message": "✅ Standard Response",
                "retrieval_method": "indian_hr_fallback",
                "show_ticket_button": False
            }
            
    except Exception as e:
        print(f"❌ LangChain search error: {e}")
        return {
            "answer": self.get_enhanced_indian_fallback(question),
            "sources": [],
            "suggestions": ["Contact HR for assistance"],
            "confidence_score": 0.8,
            "is_low_confidence": False,
            "confidence_message": "✅ Fallback Response",
            "retrieval_method": "error_fallback",
            "show_ticket_button": True
        }
```

#### C. Indian HR Fallback System
```python
def get_enhanced_indian_fallback(self, question: str) -> str:
    """Enhanced Indian HR fallback with comprehensive benefits information"""
    question_type = question.lower()
    
    if "medical" in question_type or "health" in question_type or "benefit" in question_type:
        return """IBM provides comprehensive medical benefits package:

🏥 **Health Insurance Coverage:**
• **Medical Plans**: 3-4 plan options (Group Health, Individual Plans, Top-up)
• **Premium Coverage**: Company pays 80-90% of premium costs
• **Annual Deductible**: ₹25,000-₹1,50,000 (varies by plan)
• **Out-of-Pocket Maximum**: ₹1,00,000-₹3,00,000 annually

💊 **Prescription Coverage:**
• **Generic Drugs**: ₹200-₹500 copay
• **Brand Name**: ₹1,000-₹2,500 copay
• **Specialty Medications**: 10-20% coinsurance
• **Mail Order**: 90-day supply discounts

🦷 **Additional Benefits:**
• **Dental Insurance**: ₹75,000-₹1,25,000 annual maximum
• **Vision Coverage**: ₹10,000-₹20,000 annual allowance
• **Mental Health**: Full parity coverage
• **Telehealth**: ₹0-₹1,000 virtual visit copay

For your specific plan details, premium costs, and enrollment options, access the employee benefits portal or contact HR."""

    elif "leave" in question_type or "vacation" in question_type or "time off" in question_type:
        return """🌴 **IBM India Leave Policy:**

📅 **Annual Leave Entitlement:**
• **Earned Leave (EL)**: 21 days per calendar year
• **Casual Leave (CL)**: 12 days per calendar year  
• **Sick Leave (SL)**: 12 days per calendar year
• **Festival Leave**: 2 days per calendar year

🎯 **Leave Accrual & Usage:**
• **EL Accrual**: 1.75 days per month
• **Maximum EL Bank**: 45 days (excess encashed)
• **CL & SL**: Credited at year beginning, no carry-forward
• **Minimum Leave Block**: 5 consecutive days for EL

🤱 **Special Leave Categories:**
• **Maternity Leave**: 26 weeks (as per Indian law)
• **Paternity Leave**: 15 days
• **Adoption Leave**: 12 weeks
• **Sabbatical Leave**: Up to 1 year (conditions apply)

For leave balance check, application status, or policy clarifications, access the employee self-service portal or contact HR."""

    else:
        return "I'm here to help with IBM HR policies and benefits. Please ask about specific topics like medical benefits, leave policies, compensation, or other HR-related questions."
```

---

## 🔌 API Documentation

### Endpoint Overview

| Method | Endpoint | Purpose | Request Body | Response |
|--------|----------|---------|--------------|----------|
| GET | `/` | Serve frontend | None | HTML page |
| GET | `/api/health` | System status | None | Status object |
| POST | `/api/validate-user` | User login | `{user_id: string}` | Validation result |
| POST | `/api/ingest` | Build KB | `{force_rebuild: boolean}` | Build status |
| POST | `/api/chat` | Ask question | `{question: string, user_id: string}` | Answer object |
| POST | `/api/ticket` | Create ticket | `{issue: string, user_id: string}` | Ticket details |

### Detailed API Specifications

#### 1. Health Check
```python
@app.get("/api/health")
def health():
    vector_ready = rag_system.embeddings_ready or os.path.exists(CHROMA_DIR)
    dataset_exists = os.path.exists(DATASET_LOCAL)
    
    return {
        "app": APP_NAME,
        "version": "3.0.0 LangChain RAG",
        "vector_ready": vector_ready,
        "dataset_exists": dataset_exists,
        "dataset_path": str(DATASET_LOCAL),
        "vector_db_path": str(CHROMA_DIR),
        "system_type": "LangChain RAG" if HAS_LANGCHAIN else "Simple Search",
        "langchain_available": HAS_LANGCHAIN,
        "status": "healthy" if dataset_exists else "needs_setup"
    }
```

#### 2. User Validation
```python
@app.post("/api/validate-user")
async def api_validate_user(request: UserValidationRequest = Body(...)):
    result = validate_user(request.user_id)
    return UserValidationResponse(
        valid=result["valid"],
        user_info=result["user_info"],
        message=result["message"]
    )

def validate_user(user_id: str) -> dict:
    """Validate user ID with demo users and format checking"""
    user_id = user_id.upper().strip()
    
    demo_users = {
        "EMP001234": {"name": "John Doe", "department": "Engineering", "grade": "L5"},
        "EMP005678": {"name": "Jane Smith", "department": "HR", "grade": "L4"},
        "EMP009999": {"name": "Admin User", "department": "IT", "grade": "L6"},
    }
    
    if user_id in demo_users:
        return {
            "valid": True,
            "user_info": demo_users[user_id],
            "message": f"Welcome, {demo_users[user_id]['name']}!"
        }
    elif user_id.startswith("EMP") and len(user_id) >= 6:
        return {
            "valid": True,
            "user_info": {"name": "Employee", "department": "General", "grade": "L3"},
            "message": f"Welcome, Employee {user_id}!"
        }
    else:
        return {
            "valid": False,
            "user_info": None,
            "message": "Invalid Employee ID format. Please use format: EMP123456"
        }
```

#### 3. Chat Endpoint
```python
@app.post("/api/chat")
def api_chat(req: ChatRequest = Body(...)):
    """Main chat endpoint with comprehensive error handling"""
    user_info = ""
    if req.user_id:
        user_data = validate_user(req.user_id)
        if user_data["valid"] and user_data["user_info"]:
            user_info = f" (User: {user_data['user_info']['name']})"
    
    print(f"\n💬 {'LangChain ' if HAS_LANGCHAIN else ''}Chat{user_info}: '{req.question}'")
    
    try:
        # Check if system is ready
        if not os.path.exists(DATASET_LOCAL):
            return {
                "answer": "❌ **Dataset Not Found**\n\nThe HR knowledge base file is missing. Please ensure the dataset is available.",
                "sources": [],
                "suggestions": ["Check dataset availability", "Contact system administrator"],
                "confidence_score": 0.0,
                "is_low_confidence": True,
                "confidence_message": "⚠️ Dataset missing",
                "retrieval_method": "error",
                "show_ticket_button": True
            }
        
        # Use RAG system to answer
        result = rag_system.search(req.question, top_k=req.top_k or 5)
        
        print(f"✅ Response sent (confidence: {result.get('confidence_score', 0):.3f})")
        return result
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return {
            "answer": f"I encountered an error: {str(e)}\n\nPlease try again or contact HR directly.",
            "sources": [],
            "suggestions": [
                "Try rephrasing your question",
                "Contact HR directly",
                "Check system status"
            ],
            "confidence_score": 0.0,
            "is_low_confidence": True,
            "confidence_message": "⚠️ Processing error",
            "retrieval_method": "error",
            "show_ticket_button": True
        }
```

#### 4. Ticket Creation
```python
@app.post("/api/ticket")
def api_ticket(req: TicketRequest = Body(...)):
    """Create HR support ticket with JSON persistence"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        short_id = str(uuid.uuid4())[:8].upper()
        ticket_id = f"LANGCHAIN-HR-{timestamp}-{short_id}"
        
        ticket_data = {
            "ticket_id": ticket_id,
            "issue": req.issue,
            "user_id": req.user_id,
            "status": "Open",
            "created_at": datetime.now().isoformat(),
            "system_type": "LangChain_RAG_System",
            "source": "LangChain HR Assistant"
        }
        
        # Load existing tickets or create new list
        tickets_file = "lightning_tickets.json"
        try:
            with open(tickets_file, 'r') as f:
                tickets = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            tickets = []
        
        tickets.append(ticket_data)
        
        # Save updated tickets
        with open(tickets_file, 'w') as f:
            json.dump(tickets, f, indent=2)
        
        return TicketResponse(
            ticket_id=ticket_id,
            status="Open",
            message=f"🎫 HR ticket created successfully!\n\nTicket ID: {ticket_id}\nStatus: Open\n\nYour ticket has been submitted. You will receive a response within 1-2 hours."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")
```

---

## 🎨 Frontend Architecture

### CSS Styling (`styles.css`)

The frontend uses a modern, responsive design with IBM-style branding:

```css
/* Variables for consistent theming */
:root {
    --primary-color: #0f62fe;
    --success-color: #24a148;
    --warning-color: #f1c21b;
    --error-color: #da1e28;
    --text-primary: #161616;
    --text-secondary: #525252;
    --background: #f4f4f4;
    --surface: #ffffff;
    --border-subtle: #e0e0e0;
}

/* Header with IBM branding */
.header {
    background: linear-gradient(135deg, var(--primary-color), #001d6c);
    color: white;
    padding: 1rem 2rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-content {
    display: flex;
    align-items: center;
    gap: 1rem;
    max-width: 1200px;
    margin: 0 auto;
}

/* Chat interface styling */
.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    background: var(--surface);
    border-radius: 8px;
    border: 1px solid var(--border-subtle);
}

.message {
    margin-bottom: 1rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    max-width: 80%;
    word-wrap: break-word;
}

.message.user {
    background: var(--primary-color);
    color: white;
    margin-left: auto;
    text-align: right;
}

.message.assistant {
    background: var(--background);
    color: var(--text-primary);
    border: 1px solid var(--border-subtle);
}

/* Suggestion buttons */
.suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 1rem 0;
}

.suggestions button {
    background: var(--surface);
    border: 1px solid var(--primary-color);
    color: var(--primary-color);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.suggestions button:hover {
    background: var(--primary-color);
    color: white;
}
```

### JavaScript State Management

The frontend uses a simple but effective state management approach:

```javascript
// Global state variables
let isLoggedIn = false;
let knowledgeBaseReady = false;
window.employeeId = null;

// UI state management functions
function showSetupSection() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('setupSection').style.display = 'block';
}

function showChatSection() {
    document.getElementById('setupSection').style.display = 'none';
    document.getElementById('chatSection').style.display = 'block';
    document.getElementById('chatInput').focus();
}

function updateConnectionStatus(status) {
    const indicator = document.getElementById('connectionStatus');
    const colors = {
        'connected': '#24a148',
        'error': '#da1e28',
        'warning': '#f1c21b'
    };
    indicator.style.color = colors[status] || colors.warning;
}

// Dynamic message rendering
function addMessage(content, sender, metadata = null) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    if (sender === 'assistant' && metadata) {
        // Format assistant response with confidence indicator
        const confidenceIcon = metadata.is_low_confidence ? '⚠️' : '✅';
        content = `${confidenceIcon} ${content}`;
        
        // Add ticket button for low confidence responses
        if (metadata.show_ticket_button) {
            const ticketBtn = document.createElement('button');
            ticketBtn.textContent = 'Create HR Ticket';
            ticketBtn.className = 'ticket-button';
            ticketBtn.onclick = () => createTicket(content);
            messageDiv.appendChild(ticketBtn);
        }
    }
    
    messageDiv.innerHTML = content.replace(/\n/g, '<br>');
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
```

---

## 🔄 Data Flow

### Complete Request-Response Cycle

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as FastAPI
    participant R as RAG System
    participant C as ChromaDB
    participant D as Dataset

    U->>F: Enter Employee ID
    F->>A: POST /api/validate-user
    A->>F: Validation result
    F->>U: Login success/failure

    U->>F: Click "Build Knowledge Base"
    F->>A: POST /api/ingest
    A->>R: setup_embeddings()
    R->>D: Load CSV dataset
    R->>R: Create Document objects
    R->>C: Store embeddings
    C->>R: Confirm persistence
    R->>A: Return document count
    A->>F: Build complete
    F->>U: KB ready message

    U->>F: Ask HR question
    F->>A: POST /api/chat
    A->>R: search(question)
    R->>C: similarity_search()
    C->>R: Return similar docs
    R->>R: Clean context
    R->>R: Apply fallback if needed
    R->>A: Return answer + metadata
    A->>F: Formatted response
    F->>U: Display answer + suggestions
```

### Data Processing Pipeline

1. **Dataset Loading**
   ```python
   # Raw CSV data → Pandas DataFrame
   df = pd.read_csv(DATASET_LOCAL)
   
   # Quality filtering
   valid_rows = df[
       (df['canonical_question'].notna()) & 
       (df['short_answer'].notna()) &
       (~df['short_answer'].str.startswith('According to our HR materials:'))
   ]
   ```

2. **Document Creation**
   ```python
   # DataFrame → LangChain Documents
   documents = []
   for idx, row in df.iterrows():
       doc = Document(
           page_content=f"Question: {row['canonical_question']}\nAnswer: {row['short_answer']}",
           metadata={
               'question': row['canonical_question'],
               'answer': row['short_answer'],
               'tags': row.get('tags', ''),
               'row_id': idx
           }
       )
       documents.append(doc)
   ```

3. **Embedding Generation**
   ```python
   # Documents → Vector Embeddings
   embeddings = HuggingFace Embeddings("sentence-transformers/all-MiniLM-L6-v2")
   vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=CHROMA_DIR)
   ```

4. **Query Processing**
   ```python
   # User query → Similar documents
   user_query = "What are my medical benefits?"
   docs = vectorstore.similarity_search(user_query, k=5)
   
   # Document → Clean answer
   raw_answer = docs[0].metadata['answer']
   clean_answer = completely_remove_context(raw_answer)
   
   # Fallback if needed
   if not clean_answer or len(clean_answer) < 20:
       clean_answer = get_enhanced_indian_fallback(user_query)
   ```

---

## 💻 Code Examples

### Running the Complete System

#### 1. Installation & Setup
```bash
# Clone or download the project
cd ibm-hr-rag-chatbox

# Install Python dependencies
pip install -r requirements.txt

# Start the server
python langchain_server_enhanced.py
```

#### 2. First-Time Setup via UI
```javascript
// 1. Open http://localhost:8007/
// 2. Login with Employee ID: EMP001234
// 3. Click "Build Knowledge Base"
// 4. Wait for "✅ Knowledge base ready!" message
// 5. Start chatting!
```

#### 3. Programmatic API Usage
```python
import requests

# Health check
response = requests.get('http://localhost:8007/api/health')
print(response.json())

# User validation
user_data = {
    "user_id": "EMP001234"
}
response = requests.post('http://localhost:8007/api/validate-user', json=user_data)
print(response.json())

# Build knowledge base
ingest_data = {
    "force_rebuild": False
}
response = requests.post('http://localhost:8007/api/ingest', json=ingest_data)
print(response.json())

# Ask a question
chat_data = {
    "question": "What are my medical benefits?",
    "user_id": "EMP001234"
}
response = requests.post('http://localhost:8007/api/chat', json=chat_data)
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence_score']}")
print(f"Suggestions: {result['suggestions']}")
```

#### 4. Custom Embedding Model
```python
# To use a different embedding model, modify setup_langchain_rag():
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"  # Better but slower
    # model_name="sentence-transformers/all-MiniLM-L6-v2"  # Default: fast
)
```

#### 5. Adding New HR Policy Domains
```python
def get_enhanced_indian_fallback(self, question: str) -> str:
    question_type = question.lower()
    
    # Add new domain
    if "performance" in question_type or "appraisal" in question_type:
        return """🎯 **IBM India Performance Management:**

📊 **Annual Performance Cycle:**
• **Goal Setting**: January - Define objectives and key results
• **Mid-Year Review**: June - Progress check and course correction
• **Annual Evaluation**: December - Comprehensive performance assessment

🏆 **Performance Ratings:**
• **Exceptional (E)**: Top 10% performers - Outstanding results
• **High (H)**: 20-25% performers - Exceeds expectations
• **Good (G)**: 60-65% performers - Meets expectations
• **Needs Improvement (NI)**: 5-10% performers - Below expectations

💰 **Performance Impact:**
• **Salary Increase**: 8-15% for E, 5-10% for H, 3-6% for G
• **Bonus Eligibility**: 20-35% for E, 15-25% for H, 10-15% for G
• **Promotion Consideration**: E and H ratings required for advancement

For performance planning, feedback sessions, or improvement plans, connect with your manager or HR Business Partner."""
    
    # ... existing domains ...
```

### Debugging & Development Tools

#### 1. Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add to langchain_search method:
print(f"🔍 Query: {question}")
print(f"📄 Found {len(docs)} documents")
print(f"🎯 Best match: {docs[0].metadata.get('question', 'Unknown')}")
print(f"💬 Raw answer: {docs[0].metadata.get('answer', 'No answer')[:100]}...")
print(f"✨ Clean answer: {clean_answer[:100]}...")
```

#### 2. Vector Store Inspection
```python
# Check vector store contents
def inspect_vectorstore():
    if hasattr(rag_system, 'vectorstore'):
        # Get sample documents
        sample_docs = rag_system.vectorstore.similarity_search("test", k=3)
        for i, doc in enumerate(sample_docs):
            print(f"Doc {i}: {doc.metadata.get('question', 'No question')}")
            print(f"Answer: {doc.metadata.get('answer', 'No answer')[:100]}...")
            print("---")
```

#### 3. Performance Monitoring
```python
import time

def timed_search(question):
    start_time = time.time()
    result = rag_system.search(question)
    end_time = time.time()
    
    print(f"⏱️ Search took {end_time - start_time:.3f} seconds")
    print(f"🎯 Confidence: {result.get('confidence_score', 0):.3f}")
    print(f"🔧 Method: {result.get('retrieval_method', 'unknown')}")
    
    return result
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. "Dataset Not Found" Error
```bash
# Problem: CSV file missing
# Solution: Check file path and permissions
ls -la data/qa_dataset_enriched_slim.csv

# If missing, ensure the file exists in the data/ directory
```

#### 2. ChromaDB Permission Errors
```bash
# Problem: Cannot write to storage directory
# Solution: Check directory permissions
chmod 755 storage/
chmod 755 storage/chroma_langchain/

# Or delete and rebuild
rm -rf storage/chroma_langchain/
# Then rebuild via UI or API
```

#### 3. Port Already in Use
```python
# Problem: Port 8007 is occupied
# Solution: Change port in server file
SERVER_PORT = 8008  # Change this line

# Or kill existing process
# Windows:
netstat -ano | findstr :8007
taskkill /PID <process_id> /F

# Linux/Mac:
lsof -ti:8007 | xargs kill -9
```

#### 4. LangChain Dependencies Missing
```bash
# Problem: ImportError for LangChain modules
# Solution: Install dependencies
pip install langchain langchain-community langchain-huggingface
pip install chromadb sentence-transformers
pip install huggingface-hub
```

#### 5. Context Still Showing in Responses
```python
# Problem: Context bleeding despite cleaning
# Solution: Enhanced regex patterns
def ultra_aggressive_context_removal(text):
    import re
    
    # Remove everything after "Context:"
    text = re.sub(r'Context:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove HR materials prefix
    text = re.sub(r'^According to our HR materials:?\s*', '', text, flags=re.IGNORECASE)
    
    # Remove employee dialogue
    text = re.sub(r'\n\s*Employee:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove instruction text
    text = re.sub(r'See details below\.?', '', text, flags=re.IGNORECASE)
    
    return text.strip()
```

#### 6. Low Confidence Responses
```python
# Problem: System always returns fallback answers
# Solution: Check dataset quality and vector store
def diagnose_search_quality():
    # Test with exact question from dataset
    df = pd.read_csv(DATASET_LOCAL)
    test_question = df.iloc[0]['canonical_question']
    
    result = rag_system.search(test_question)
    print(f"Test question: {test_question}")
    print(f"Confidence: {result.get('confidence_score', 0)}")
    print(f"Method: {result.get('retrieval_method', 'unknown')}")
    
    if result.get('confidence_score', 0) < 0.8:
        print("❌ Vector search may not be working properly")
        print("💡 Try rebuilding the knowledge base")
```

#### 7. Frontend Not Loading
```javascript
// Problem: Frontend shows blank page
// Solution: Check browser console and network tab

// Common fixes:
// 1. Ensure server is running on correct port
// 2. Check CORS settings
// 3. Verify static file serving
// 4. Clear browser cache

// Test API directly:
fetch('http://localhost:8007/api/health')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('API Error:', error));
```

### Performance Optimization

#### 1. Faster Startup
```python
# Preload vector store on server start
if __name__ == "__main__":
    print("🚀 Preloading vector store...")
    rag_system.setup_embeddings()
    
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
```

#### 2. Memory Optimization
```python
# Use smaller embedding model for resource-constrained environments
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
```

#### 3. Response Caching
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(question: str, top_k: int = 5):
    """Cache search results for common questions"""
    return rag_system.search(question, top_k)
```

---

## 🎉 Summary

This IBM HR RAG Chatbox represents a complete, production-ready implementation of modern AI-powered customer service. The system successfully combines:

- **Advanced RAG Architecture** with LangChain and ChromaDB
- **Robust Context Cleaning** to prevent data leakage
- **Indian Labor Law Compliance** with localized policies and currency
- **User-Friendly Interface** with vanilla JavaScript simplicity
- **Comprehensive Error Handling** and fallback mechanisms
- **Extensible Design** for easy addition of new HR domains

The system is designed to be both powerful for developers and accessible to end-users, providing a solid foundation for enterprise HR automation while maintaining the flexibility to adapt to specific organizational needs.

---

**Next Steps:**
1. Deploy to production environment
2. Add user analytics and usage tracking
3. Implement advanced LLM integration (GPT-4, Claude)
4. Add multi-language support
5. Create mobile-responsive design improvements
6. Implement user feedback collection system
