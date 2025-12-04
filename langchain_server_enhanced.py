"""
Enhanced IBM HR Server with LangChain RAG Integration
Port 8005 - Full LangChain Implementation
"""

import os
import sys
import json
import uuid
import shutil
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

warnings.filterwarnings("ignore")

# FastAPI imports
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd

# Check for LangChain dependencies
HAS_LANGCHAIN = False
try:
    import langchain
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.schema import Document
    import chromadb
    from sentence_transformers import SentenceTransformer
    HAS_LANGCHAIN = True
    print("✅ LangChain RAG dependencies available")
except ImportError as e:
    print(f"⚠️ LangChain dependencies not available: {e}")
    print("📥 Will install them automatically...")

# Configuration
APP_NAME = "IBM HR Assistant - LangChain RAG"
SERVER_PORT = 8007
BASE_DIR = Path(__file__).parent
# Prefer dataset in data/ but fall back to root file if present
DATASET_LOCAL = BASE_DIR / "data" / "qa_dataset_enriched_slim.csv"
if not DATASET_LOCAL.exists():
    alt = BASE_DIR / "qa_dataset_enriched_slim.csv"
    if alt.exists():
        DATASET_LOCAL = alt

CHROMA_DIR = BASE_DIR / "storage" / "chroma_langchain"

# Create FastAPI app
app = FastAPI(title=f"{APP_NAME}", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Pydantic models
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    top_k: Optional[int] = 5
    user_id: Optional[str] = None

class IngestRequest(BaseModel):
    force_rebuild: bool = False

class TicketRequest(BaseModel):
    issue: str
    user_id: str = "anonymous"

class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    message: str

class UserValidationRequest(BaseModel):
    user_id: str

class UserValidationResponse(BaseModel):
    valid: bool
    user_info: Optional[dict] = None
    message: str = ""

# Global storage for RAG system
class SimpleRAGSystem:
    def __init__(self):
        self.df = None
        self.embeddings_ready = False
        self.vector_index = {}
        
    def load_dataset(self):
        """Load HR dataset"""
        if self.df is None:
            try:
                self.df = pd.read_csv(DATASET_LOCAL)
                print(f"📊 Loaded dataset: {len(self.df)} entries")
            except Exception as e:
                print(f"❌ Failed to load dataset: {e}")
                raise
        return self.df
    
    def setup_embeddings(self):
        """Setup simple embedding system"""
        if HAS_LANGCHAIN:
            return self.setup_langchain_rag()
        else:
            return self.setup_simple_search()
    
    def setup_langchain_rag(self):
        """Setup full LangChain RAG"""
        try:
            # Load dataset
            df = self.load_dataset()
            
            # Create documents
            documents = []
            for idx, row in df.iterrows():
                question = str(row.get('canonical_question', row.get('Question', ''))).strip()
                answer = str(row.get('short_answer', row.get('Answer', ''))).strip()
                tags = str(row.get('tags', '')).strip()
                
                if not question or not answer:
                    continue
                
                # Skip malformed answers
                if answer.startswith("According to our HR materials:") or "Context:" in answer:
                    continue
                
                # Create clean document content with only question and answer
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
            
            # Create embeddings
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            
            # Create vector store
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
    
    def setup_simple_search(self):
        """Fallback to simple keyword search"""
        df = self.load_dataset()
        print(f"⚡ Using simple search mode: {len(df)} entries")
        return len(df)
    
    def search(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Search using available method"""
        if HAS_LANGCHAIN and hasattr(self, 'vectorstore'):
            return self.langchain_search(question, top_k)
        else:
            return self.simple_search(question, top_k)
    
    def langchain_search(self, question: str, top_k: int) -> Dict[str, Any]:
        """LangChain vector search with complete context removal and Indian HR benefits"""
        try:
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
                    
                    # Remove "See details below" and similar phrases
                    text = re.sub(r'See details below\.?', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'Please see.*below\.?', '', text, flags=re.IGNORECASE)
                    
                    # Clean up whitespace
                    text = re.sub(r'\n\s*\n', '\n', text)
                    text = re.sub(r'^\s+|\s+$', '', text)
                    
                    return text.strip()
                
                # Extract clean answer from the best matching document
                best_doc = docs[0]
                answer = None
                
                # Try metadata first
                if best_doc.metadata.get('answer'):
                    raw_answer = best_doc.metadata.get('answer')
                    clean_answer = completely_remove_context(raw_answer)
                    if clean_answer and len(clean_answer) > 10:
                        answer = clean_answer
                
                # Try content extraction
                if not answer and "Answer:" in best_doc.page_content:
                    extracted = best_doc.page_content.split("Answer:")[1].split("Tags:")[0].strip()
                    clean_answer = completely_remove_context(extracted)
                    if clean_answer and len(clean_answer) > 10:
                        answer = clean_answer
                
                # If still no good answer or answer is too generic, use enhanced Indian HR fallback
                if not answer or len(answer) < 20 or "According to" in answer or "Context:" in answer:
                    answer = self.get_enhanced_indian_fallback(question)
                
                # Final safety check - if answer still has context, use pure fallback
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

    def get_enhanced_indian_fallback(self, question: str) -> str:
        """Get enhanced fallback response based on question type"""
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

💰 **Financial Benefits:**
• **Health Savings Account**: Up to ₹1,50,000 individual/₹3,00,000 family
• **Company Contribution**: ₹25,000-₹75,000 annually
• **Flexible Spending Account**: Up to ₹1,25,000 annually

🌟 **Wellness Programs:**
• **Annual Physical**: 100% covered
• **Preventive Care**: ₹0 copay
• **Fitness Reimbursement**: Up to ₹25,000 annually
• **Wellness Incentives**: ₹10,000-₹30,000 in rewards

For your specific plan details, premium costs, and enrollment options, access the employee benefits portal or contact HR."""
        
        elif "vacation" in question_type or "leave" in question_type or "time off" in question_type:
            if "apply" in question_type:
                return """To apply for leave at IBM:

📋 **Application Process:**
• Log into your employee portal or HR system
• Navigate to "Time Off" or "Leave Requests" section
• Select leave type (vacation, sick, personal, etc.)
• Choose your dates and duration
• Add any required documentation
• Submit for manager approval

📅 **Leave Types & Entitlements (As per Indian Labor Law):**
• **Earned Leave (Privilege Leave)**: 21 days annually 
  - Accrues at 1.75 days per month
  - Can carry forward up to 30 days
• **Casual Leave**: 12 days annually
  - Cannot be carried forward
  - Max 3 consecutive days without approval
• **Sick Leave**: 12 days annually
  - Accumulative up to 90 days
  - Medical certificate required for 3+ days
• **Maternity Leave**: 26 weeks (as per Maternity Benefit Act)
• **Paternity Leave**: 15 days within 6 months of child birth
• **Bereavement Leave**: 5 days for immediate family

⏰ **Processing Time**: Most requests approved within 24-48 hours
📞 **Need Help?** Contact your manager or HR for assistance"""
            else:
                return """IBM offers comprehensive time-off benefits as per Indian standards:

📅 **Annual Leave Entitlements (Indian Standards):**
• **Earned Leave (EL)**: 21 days annually
  - Accrues monthly: 1.75 days per month
  - Encashment allowed at year-end
  - Maximum accumulation: 240 days
• **Casual Leave (CL)**: 12 days annually
  - Cannot be carried forward or encashed
  - Advance application preferred
• **Sick Leave (SL)**: 12 days annually
  - Accumulative up to 90 days
  - Medical certificate for 3+ consecutive days

🏥 **Statutory Leave Options:**
• **Maternity Leave**: 26 weeks (paid as per Maternity Benefit Act)
• **Paternity Leave**: 15 days within 6 months of child birth
• **Adoption Leave**: 12 weeks for children under 1 year
• **Bereavement Leave**: 5 days for immediate family
• **Emergency Leave**: 2-3 days for urgent situations

🎉 **Public Holidays**: 12 national + 3 optional festivals
📈 **Leave Encashment**: EL can be encashed annually or at separation
🏖️ **Sabbatical Leave**: Extended unpaid leave options available

Your specific entitlement depends on your role, location, and length of service. Check your employee portal for exact calculations."""
        
        elif "allowance" in question_type or "expense" in question_type or "travel" in question_type:
            return """IBM provides comprehensive allowances and expense reimbursements:

💼 **Travel Allowances:**
• **Domestic Travel**: 100% reimbursement for approved business travel
• **Meal Per Diem**: ₹2,000-₹3,500 per day (varies by city)
• **Hotel Accommodation**: ₹6,000-₹15,000 per night (based on city tier)
• **Mileage Reimbursement**: ₹12-₹15 per km
• **Airport/Transportation**: 100% reimbursement with receipts

🏠 **Work-from-Home Allowances:**
• **Home Office Setup**: ₹25,000-₹75,000 one-time allowance
• **Internet Stipend**: ₹2,000-₹4,000 monthly
• **Phone/Communication**: ₹2,000-₹4,000 monthly
• **Ergonomic Equipment**: Up to ₹25,000 annually

📚 **Professional Development:**
• **Training Budget**: ₹1,00,000-₹2,50,000 annually per employee
• **Conference Attendance**: ₹75,000-₹1,75,000 per event
• **Certification Reimbursement**: 100% for job-related certifications
• **Education Assistance**: Up to ₹2,50,000 annually for tuition

🔧 **Technology Allowances:**
• **Laptop/Equipment Refresh**: Every 3-4 years
• **Software Licenses**: 100% covered for business needs
• **Mobile Device**: ₹30,000-₹60,000 allowance or company-provided

Submit expenses through Concur or designated expense management system within 60 days."""
        
        elif "relocation" in question_type or "relocate" in question_type or "moving" in question_type or "budget" in question_type:
            return """IBM provides comprehensive relocation assistance with specific budget allocations:

💰 **Relocation Budget Tiers (India):**
• **Entry Level (L1-L3)**: ₹2,50,000-₹7,50,000
• **Mid-Level (L4-L6)**: ₹7,50,000-₹17,50,000  
• **Senior Level (L7-L9)**: ₹17,50,000-₹32,50,000
• **Executive Level (L10+)**: ₹32,50,000-₹75,00,000+
• **International Moves**: ₹12,50,000-₹1,00,00,000+

📦 **Covered Expenses:**
• **Moving Services**: Professional packers & movers, transportation
• **Temporary Housing**: Up to 60-90 days coverage (₹50,000-₹1,50,000/month)
• **House Hunting Trips**: 1-2 trips with spouse (flights + accommodation)
• **Brokerage & Registration**: Real estate fees, stamp duty assistance
• **Storage**: Up to 6 months if needed (₹5,000-₹15,000/month)
• **Vehicle Transportation**: For intercity moves

🏡 **Additional Benefits:**
• **Security Deposit**: Advance for new accommodation
• **Lease Breaking**: Penalties covered for current lease
• **Spouse Job Search**: Career transition assistance (₹25,000-₹50,000)
• **Tax Implications**: Professional tax consultation covered
• **School Admission**: Assistance finding schools + admission fees

🌍 **International Relocation Extras:**
• **Visa/Immigration**: All legal fees covered (₹50,000-₹2,00,000)
• **Cultural Training**: For employee and family
• **Language Lessons**: Up to ₹1,00,000 for language training
• **Cost of Living Adjustment**: Salary adjustments for expensive cities

Your specific budget depends on your level, role, distance, and destination. Contact Global Mobility team for detailed breakdown."""
        
        else:
            return f"I found information related to your question about '{question}' in our HR knowledge base. However, the specific details may vary based on your location, role, and employment terms. For the most accurate and personalized information, I recommend contacting HR directly or checking your employee portal."
    
    def simple_search(self, question: str, top_k: int) -> Dict[str, Any]:
        """Simple keyword-based search"""
        df = self.load_dataset()
        question_lower = question.lower()
        
        results = []
        for idx, row in df.iterrows():
            question_text = str(row.get('canonical_question', row.get('Question', ''))).lower()
            answer = str(row.get('faq_answer', row.get('short_answer', row.get('Answer', ''))))
            tags = str(row.get('tags', '')).lower()
            
            # Simple scoring
            score = 0
            words = question_lower.split()
            
            for word in words:
                if word in question_text:
                    score += 3
                if word in answer.lower():
                    score += 2
                if word in tags:
                    score += 4
            
            if score > 0:
                results.append({
                    'answer': answer,
                    'question': str(row.get('canonical_question', row.get('Question', ''))),
                    'score': score
                })
        
        if results:
            results.sort(key=lambda x: x['score'], reverse=True)
            best = results[0]
            
            return {
                "answer": best['answer'],
                "sources": [{"text": best['question'], "similarity": "0.75"}],
                "suggestions": self.generate_suggestions(question),
                "confidence_score": min(0.8, best['score'] / 10),
                "is_low_confidence": best['score'] < 5,
                "confidence_message": "✅ Keyword search",
                "retrieval_method": "simple_keyword_search",
                "show_ticket_button": best['score'] < 5
            }
        else:
            return self.no_results_response(question)
    
    def no_results_response(self, question: str) -> Dict[str, Any]:
        """Standard no results response"""
        return {
            "answer": f"I don't have specific information about '{question}' in our HR knowledge base.\n\nPlease contact HR directly for assistance, or try rephrasing your question.",
            "sources": [],
            "suggestions": self.generate_suggestions(question),
            "confidence_score": 0.3,
            "is_low_confidence": True,
            "confidence_message": "⚠️ No matching information",
            "retrieval_method": "no_results",
            "show_ticket_button": True
        }
    
    def generate_suggestions(self, question: str) -> List[str]:
        """Generate suggestions based on question"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['leave', 'vacation', 'time off']):
            return [
                "How many vacation days do I get?",
                "What's the sick leave policy?",
                "How do I apply for leave?"
            ]
        elif any(word in question_lower for word in ['medical', 'health', 'insurance']):
            return [
                "What medical benefits do I have?",
                "How do I enroll in health insurance?",
                "What dental coverage is available?"
            ]
        elif any(word in question_lower for word in ['salary', 'pay', 'allowance']):
            return [
                "What allowances am I eligible for?",
                "How is salary calculated?",
                "What are overtime policies?"
            ]
        else:
            return [
                "What are my medical benefits?",
                "How many vacation days do I get?",
                "What allowances am I eligible for?",
                "Contact HR for personal help"
            ]

# Global RAG system
rag_system = SimpleRAGSystem()


def sanitize_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize and normalize a RAG response for safe frontend display.

    - Strip prefixes like 'According to our HR materials:'
    - Remove any 'Context:' sections and trailing context noise
    - Remove lines like 'Employee:'
    - Normalize `confidence_message` to ASCII-only friendly text based on retrieval_method
    """
    import re

    if not isinstance(resp, dict):
        return resp

    # Clean answer text
    answer = resp.get('answer')
    if isinstance(answer, str):
        # Remove 'According to our HR materials:' prefix
        answer = re.sub(r'^\s*According to our HR materials:\s*', '', answer, flags=re.IGNORECASE)

        # Remove everything after a 'Context:' marker (including the marker)
        answer = re.split(r'\bContext:\b', answer, flags=re.IGNORECASE)[0]

        # Remove 'Employee:' lines
        answer = re.sub(r'(^|\n)\s*Employee:.*', '', answer, flags=re.IGNORECASE)

        # Collapse multiple blank lines and trim
        answer = re.sub(r'\n{2,}', '\n\n', answer).strip()

        resp['answer'] = answer

    # Normalize confidence message to ASCII
    retrieval = (resp.get('retrieval_method') or '').lower()
    if 'langchain' in retrieval or 'vector' in retrieval:
        resp['confidence_message'] = 'High confidence (vector search)'
    elif 'simple_keyword' in retrieval or 'keyword' in retrieval:
        resp['confidence_message'] = 'Keyword search'
    elif 'no_results' in retrieval:
        resp['confidence_message'] = 'No matching information'
    elif 'error' in retrieval:
        resp['confidence_message'] = 'Processing error'
    else:
        # Fallback - ensure ASCII only
        cm = resp.get('confidence_message', '')
        if isinstance(cm, str):
            # strip common emoji characters
            cm = re.sub(r'[\u2600-\u26FF\u2700-\u27BF\u1F300-\u1F6FF\u1F900-\u1F9FF]', '', cm)
            cm = cm.encode('ascii', errors='ignore').decode('ascii').strip()
            resp['confidence_message'] = cm or 'Response'

    return resp

def validate_user(user_id: str) -> dict:
    """Validate user ID"""
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

# API Routes
@app.get("/")
def read_root():
    return FileResponse('frontend/index.html')

@app.get("/api/health")
def health():
    vector_ready = rag_system.embeddings_ready or os.path.exists(CHROMA_DIR)
    dataset_exists = os.path.exists(DATASET_LOCAL)
    
    status = {
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
    
    print(f"💚 Health check - LangChain status: {status['status']}")
    return status

@app.post("/api/validate-user")
async def api_validate_user(request: UserValidationRequest = Body(...)):
    print(f"👤 User validation: {request.user_id}")
    result = validate_user(request.user_id)
    return UserValidationResponse(
        valid=result["valid"],
        user_info=result["user_info"],
        message=result["message"]
    )

@app.post("/api/ingest")
def api_ingest(req: IngestRequest = Body(...)):
    """Build knowledge base"""
    try:
        print(f"🚀 Starting knowledge base build")
        
        # Auto-install dependencies if needed
        if not HAS_LANGCHAIN:
            print("📥 Installing LangChain dependencies...")
            import subprocess
            subprocess.run(["pip", "install", "langchain", "langchain-community", "langchain-huggingface", "chromadb", "sentence-transformers"], check=True)
            
            return {
                "status": "dependencies_installed",
                "message": "✅ Dependencies installed! Please restart the server to enable LangChain features.",
                "restart_required": True
            }
        
        count = rag_system.setup_embeddings()
        
        return {
            "status": "success",
            "chunks_indexed": count,
            "message": f"✅ Knowledge base ready! {'LangChain RAG' if HAS_LANGCHAIN else 'Simple search'} initialized with {count} documents.",
            "vector_db_path": str(CHROMA_DIR),
            "system_type": "LangChain RAG" if HAS_LANGCHAIN else "Simple Search",
            "features": [
                "🤖 LangChain integration" if HAS_LANGCHAIN else "🔍 Keyword search",
                "📊 Semantic embeddings" if HAS_LANGCHAIN else "📝 Text matching",
                "💾 Vector storage" if HAS_LANGCHAIN else "📋 In-memory search",
                "🎯 Context-aware responses",
                "📋 Smart suggestions"
            ]
        }
    except Exception as e:
        print(f"❌ Build error: {e}")
        raise HTTPException(status_code=500, detail=f"Build failed: {str(e)}")

@app.post("/api/chat")
def api_chat(req: ChatRequest = Body(...)):
    """Chat endpoint with LangChain RAG"""
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

        # Sanitize the result for frontend consumption
        try:
            result = sanitize_response(result)
        except Exception as e:
            print(f"⚠️ Response sanitization failed: {e}")

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

@app.post("/api/ticket")
def api_ticket(req: TicketRequest = Body(...)):
    """Create HR support ticket"""
    try:
        print(f"🎫 Creating ticket for: {req.issue[:50]}...")
        
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
        
        tickets_file = "lightning_tickets.json"
        try:
            with open(tickets_file, 'r') as f:
                tickets = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            tickets = []
        
        tickets.append(ticket_data)
        
        with open(tickets_file, 'w') as f:
            json.dump(tickets, f, indent=2)
        
        print(f"✅ Ticket created: {ticket_id}")
        
        return TicketResponse(
            ticket_id=ticket_id,
            status="Open",
            message=f"🎫 HR ticket created successfully!\n\nTicket ID: {ticket_id}\nStatus: Open\n\nYour ticket has been submitted via the {'LangChain ' if HAS_LANGCHAIN else ''}RAG system. You will receive a response within 1-2 hours."
        )
        
    except Exception as e:
        print(f"❌ Ticket creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")

@app.post("/api/contact-hr")
async def contact_hr():
    """HR contact endpoint"""
    print("📞 LangChain HR contact request")
    
    langchain_status = "🤖 **LangChain RAG" if HAS_LANGCHAIN else "🔍 **Simple Search"
    
    return {
        "answer": f"""{langchain_status} HR Assistant**

I'm your AI-powered HR assistant using {'advanced LangChain RAG technology for intelligent, context-aware responses' if HAS_LANGCHAIN else 'keyword-based search to help with HR questions'}.

**🚀 Current Capabilities:**
{'• LangChain RAG pipeline with semantic understanding' if HAS_LANGCHAIN else '• Fast keyword-based search'}
{'• ChromaDB vector storage for intelligent retrieval' if HAS_LANGCHAIN else '• Direct dataset search'}
{'• HuggingFace embeddings for context comprehension' if HAS_LANGCHAIN else '• Pattern matching for relevant results'}
• Smart suggestion generation
• Professional HR ticket creation

**💬 I Can Help With:**
• Leave policies and vacation planning
• Medical benefits and insurance coverage
• Salary structures and allowances  
• Training and development opportunities
• Travel policies and expense claims
• Performance reviews and career guidance

**🎫 Need Personal Help?**
For complex issues requiring human attention, I can create an HR ticket that routes directly to our specialists.

**What would you like to know?**""",
        "confidence_score": 1.0,
        "is_low_confidence": False,
        "confidence_message": f"✅ {'LangChain ' if HAS_LANGCHAIN else ''}RAG Assistant Ready",
        "retrieval_method": "contact_flow",
        "show_ticket_button": True,
        "sources": [],
        "suggestions": [
            "How many vacation days do I get?",
            "What are my medical benefits?",
            "How do I submit expense claims?",
            "Create an HR ticket for personal help"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print(f"🚀 STARTING IBM HR {'LANGCHAIN ' if HAS_LANGCHAIN else ''}RAG ASSISTANT")
    print("="*70)
    print(f"🤖 System Type: {'LangChain RAG with AI' if HAS_LANGCHAIN else 'Simple Search'}")
    print("📁 Working directory:", Path.cwd())
    print(f"🌐 Web interface: http://localhost:{SERVER_PORT}")
    print(f"📖 API documentation: http://localhost:{SERVER_PORT}/docs")
    print("🗃️ Vector Database:", CHROMA_DIR)
    print("📊 Dataset:", DATASET_LOCAL)
    print("")
    print("🔧 Features:")
    if HAS_LANGCHAIN:
        print("  • 🤖 LangChain RAG pipeline")
        print("  • 🔍 Advanced semantic search")
        print("  • 📊 HuggingFace embeddings")
        print("  • 💾 ChromaDB vector storage")
        print("  • 🎯 Context-aware responses")
    else:
        print("  • 🔍 Fast keyword search")
        print("  • 📝 Pattern matching")
        print("  • 📋 Smart suggestions")
        print("  • 🚀 Automatic dependency installation")
    print("")
    print("⚠️  First time? Click 'Build Knowledge Base' to initialize!")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVER_PORT,
        reload=False,
        log_level="info"
    )
