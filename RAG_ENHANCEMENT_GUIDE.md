# 🚀 RAG Enhancement Installation & Usage Guide

## 📋 **Available Approaches**

### **1. 🎯 Hybrid Search (Recommended)**
- **File**: `enhanced_hr_server_with_rag.py`
- **Features**: Keyword + Vector + LLM generation
- **Complexity**: Medium
- **Performance**: Best

### **2. 🔧 Simple Vector Addition**
- **File**: `simple_vector_enhancement.py`
- **Features**: Adds vector search to existing code
- **Complexity**: Low
- **Performance**: Good

### **3. 🦜 LangChain Integration**
- **File**: `langchain_rag_integration.py`
- **Features**: Full LangChain RAG pipeline
- **Complexity**: High
- **Performance**: Excellent

### **4. 🧩 Modular Plugin**
- **File**: `rag_plugin.py`
- **Features**: Drop-in enhancement
- **Complexity**: Low
- **Performance**: Configurable

---

## 🛠️ **Installation Steps**

### **Step 1: Basic Installation**
```bash
# Install basic vector support
pip install sentence-transformers chromadb numpy scikit-learn

# Test installation
python -c "from sentence_transformers import SentenceTransformer; print('✅ Basic RAG ready')"
```

### **Step 2: Optional LLM Support**
```bash
# For OpenAI integration
pip install openai

# Set API key
export OPENAI_API_KEY="your-api-key-here"
# Or on Windows: set OPENAI_API_KEY=your-api-key-here
```

### **Step 3: Advanced Features**
```bash
# For LangChain integration
pip install langchain langchain-community langchain-openai

# For full requirements
pip install -r requirements_rag.txt
```

---

## 🚀 **Implementation Options**

### **Option 1: Replace Existing Server**
```bash
# Backup current server
cp enhanced_hr_server.py enhanced_hr_server_backup.py

# Use new hybrid server
cp enhanced_hr_server_with_rag.py enhanced_hr_server.py

# Install dependencies
pip install sentence-transformers chromadb

# Run new server
python enhanced_hr_server.py
```

### **Option 2: Run Parallel Server**
```bash
# Keep existing server on port 8000
# Run RAG-enhanced server on port 8001

python enhanced_hr_server_with_rag.py
# Access at: http://localhost:8001
```

### **Option 3: Gradual Enhancement**
```python
# Add to your existing enhanced_hr_server.py:

# At the top, add:
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_VECTOR_SUPPORT = True
except ImportError:
    HAS_VECTOR_SUPPORT = False

# In your EnrichedHRKnowledgeBase class, add:
def __init__(self):
    self.knowledge_data = []
    self.embeddings = None
    self.embedding_model = None
    
    self.load_enriched_dataset()
    
    if HAS_VECTOR_SUPPORT:
        self.initialize_embeddings()

def initialize_embeddings(self):
    """Add vector search capability"""
    try:
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        texts = [f"{entry['canonical_question']} {entry['faq_answer']}" 
                for entry in self.knowledge_data]
        self.embeddings = self.embedding_model.encode(texts)
        print(f"✅ Vector search ready with {len(texts)} embeddings")
    except Exception as e:
        print(f"❌ Vector initialization failed: {e}")

def vector_search(self, query: str, top_k: int = 3):
    """Vector similarity search"""
    if not HAS_VECTOR_SUPPORT or self.embeddings is None:
        return self.search_knowledge(query, top_k)  # Fallback to keyword
    
    try:
        query_embedding = self.embedding_model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.3:
                result = self.knowledge_data[idx].copy()
                result['similarity_score'] = float(similarities[idx])
                results.append(result)
        
        return results if results else self.search_knowledge(query, top_k)
        
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return self.search_knowledge(query, top_k)  # Fallback
```

---

## 🎮 **Usage Examples**

### **Basic Vector Enhancement**
```python
# Your existing code works the same
results = hr_knowledge.search_knowledge(query, top_k=3)

# Now also supports vector search
vector_results = hr_knowledge.vector_search(query, top_k=3)
```

### **Hybrid Search**
```python
# Combines keyword + vector + LLM
response = hr_knowledge.search_and_respond(
    query="How much travel allowance do I get?",
    use_llm=True  # Optional LLM enhancement
)

print(f"Answer: {response.answer}")
print(f"Method: {response.retrieval_method}")
print(f"Confidence: {response.confidence_score}")
```

### **Plugin Approach**
```python
# Drop-in enhancement
from rag_plugin import RAGPlugin, SearchMethod

# Initialize plugin with existing knowledge base
rag_plugin = RAGPlugin(hr_knowledge)

# Enhanced search
results = rag_plugin.enhanced_search(
    query="What are my medical benefits?",
    method=SearchMethod.HYBRID,  # KEYWORD, VECTOR, HYBRID, LLM
    top_k=3
)
```

---

## 📊 **Performance Comparison**

| Method | Speed | Accuracy | Setup | Features |
|--------|-------|----------|--------|----------|
| **Keyword Only** | ⚡⚡⚡ | ⭐⭐⭐ | ✅ Simple | Basic matching |
| **Vector Only** | ⚡⚡ | ⭐⭐⭐⭐ | 🔧 Medium | Semantic understanding |
| **Hybrid** | ⚡⚡ | ⭐⭐⭐⭐⭐ | 🔧 Medium | Best of both |
| **LLM Enhanced** | ⚡ | ⭐⭐⭐⭐⭐ | 🔧🔧 Complex | Natural responses |

---

## 🔧 **Configuration Options**

### **Environment Variables**
```bash
# OpenAI API (optional)
export OPENAI_API_KEY="your-key"

# Anthropic API (optional)  
export ANTHROPIC_API_KEY="your-key"

# Vector database path
export CHROMA_DB_PATH="./chroma_enhanced"

# Embedding model
export EMBEDDING_MODEL="all-MiniLM-L6-v2"
```

### **Runtime Configuration**
```python
# In your server startup
hr_knowledge = HybridHRKnowledgeBase()

# Configure search weights
hr_knowledge.configure_hybrid_weights(
    keyword_weight=0.4,
    vector_weight=0.6,
    llm_boost=0.2
)

# Set confidence thresholds
hr_knowledge.set_thresholds(
    min_similarity=0.3,
    high_confidence=0.7,
    enable_llm_threshold=0.5
)
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

1. **ImportError: sentence-transformers**
   ```bash
   pip install sentence-transformers
   ```

2. **CUDA not available**
   ```python
   # Use CPU-only version
   pip install sentence-transformers[cpu]
   ```

3. **ChromaDB permission errors**
   ```bash
   # Fix permissions
   chmod -R 755 ./chroma_enhanced
   ```

4. **OpenAI API errors**
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   
   # Test connection
   python -c "import openai; print(openai.Model.list())"
   ```

### **Performance Tuning**

1. **Faster embeddings**
   ```python
   # Use smaller model for speed
   model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast
   # vs
   model = SentenceTransformer('all-mpnet-base-v2')  # Accurate
   ```

2. **Caching**
   ```python
   # Cache embeddings
   @lru_cache(maxsize=1000)
   def get_embedding(self, text):
       return self.model.encode([text])[0]
   ```

3. **Batch processing**
   ```python
   # Process multiple queries at once
   embeddings = model.encode(queries)  # Batch
   # vs
   embeddings = [model.encode([q])[0] for q in queries]  # Individual
   ```

---

## 🎯 **Recommended Setup**

For best results with minimal complexity:

1. **Start with Approach 2** (Simple Vector Addition)
2. **Install basic requirements**: `pip install sentence-transformers scikit-learn`
3. **Test with existing data**
4. **Gradually add LLM support** if needed
5. **Monitor performance** and adjust thresholds

This gives you 80% of the benefits with 20% of the complexity!
