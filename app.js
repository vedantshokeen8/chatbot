// ⚡ LIGHTNING FAST HR ASSISTANT ⚡
// With enhanced dataset and intelligent fallback system

// Multi-server setup with intelligent fallback
const ENHANCED_PORT = 8001;  // Enhanced server with vector search
const RAG_PORT = 8004;       // Simple RAG server
const LANGCHAIN_PORT = 8007; // LangChain RAG server (current)

// Dynamic server detection
let ACTIVE_SERVER = null;
let FALLBACK_SERVER = null;

// Get current port from URL or default to enhanced
const getCurrentPort = () => {
  if (location.port) return parseInt(location.port);
  return location.protocol === 'https:' ? 443 : (location.hostname === 'localhost' ? ENHANCED_PORT : 80);
};

// Smart API endpoint selection
const getAPI = (path) => {
  const currentPort = getCurrentPort();
  let baseUrl;
  
  if (ACTIVE_SERVER) {
    baseUrl = ACTIVE_SERVER;
  } else if (currentPort === LANGCHAIN_PORT) {
    baseUrl = `${location.protocol}//${location.hostname}:${LANGCHAIN_PORT}`;
  } else if (currentPort === RAG_PORT) {
    baseUrl = `${location.protocol}//${location.hostname}:${RAG_PORT}`;
  } else {
    baseUrl = `${location.protocol}//${location.hostname}:${ENHANCED_PORT}`;
  }
  
  return `${baseUrl}/api${path}`;
};

// Enhanced system detection
async function detectActiveSystem() {
  const systems = [
    { name: "LangChain RAG Assistant", port: LANGCHAIN_PORT, type: "langchain", priority: 1 },
    { name: "Enhanced HR Server", port: ENHANCED_PORT, type: "enhanced", priority: 2 },
    { name: "RAG Server", port: RAG_PORT, type: "rag", priority: 3 }
  ];
  
  // Sort by priority
  systems.sort((a, b) => a.priority - b.priority);
  
  for (const system of systems) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch(`${location.protocol}//${location.hostname}:${system.port}/api/health`, { 
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        ACTIVE_SERVER = `${location.protocol}//${location.hostname}:${system.port}`;
        updateSystemIndicator(system.type, true);
        console.log(`✅ Active system: ${system.name} on port ${system.port}`);
        return system;
      }
    } catch (e) {
      console.log(`❌ ${system.name} not available on port ${system.port}:`, e.message);
    }
  }
  
  updateSystemIndicator("offline", false);
  console.log("❌ No active servers found");
  return null;
}

function updateSystemIndicator(type, isOnline) {
  const indicator = document.getElementById("system-indicator");
  const typeElement = document.getElementById("system-type");
  
  if (!indicator || !typeElement) return;
  
  indicator.className = `system-indicator ${type}`;
  
  if (isOnline) {
    switch(type) {
      case "enhanced":
        typeElement.textContent = "🚀 Enhanced System";
        break;
      case "rag":
        typeElement.textContent = "🔍 RAG System";
        break;
    }
  } else {
    typeElement.textContent = "❌ System Offline";
  }
}

// Enhanced API call with intelligent fallback
async function callAPI(endpoint, options = {}) {
  // Try active server first
  if (ACTIVE_SERVER) {
    try {
      const response = await fetch(`${ACTIVE_SERVER}/api${endpoint}`, options);
      if (response.ok) return response;
    } catch (e) {
      console.log(`❌ Active server failed, trying fallback...`);
    }
  }
  
  // Try both servers as fallback
  const ports = [LANGCHAIN_PORT, ENHANCED_PORT, RAG_PORT];
  for (const port of ports) {
    try {
      const response = await fetch(`${location.protocol}//${location.hostname}:${port}/api${endpoint}`, options);
      if (response.ok) {
        ACTIVE_SERVER = `${location.protocol}//${location.hostname}:${port}`;
        updateSystemIndicator(port === LANGCHAIN_PORT ? "langchain" : (port === ENHANCED_PORT ? "enhanced" : "rag"), true);
        return response;
      }
    } catch (e) {
      console.log(`❌ Port ${port} failed for ${endpoint}`);
    }
  }
  
  throw new Error("All servers unavailable");
}

// DOM utilities
const el = (sel) => document.querySelector(sel);
const tmpl = (id) => document.getElementById(id).content.cloneNode(true);

// Global state
let conversations = [];
let activeId = null;
let currentUserId = null;

// IMMEDIATELY clear all old data on script load (except user ID)
(function() {
  try {
    // Save user ID before clearing
    const savedUserId = localStorage.getItem("bluehr:userId");
    
    // Clear everything except user ID
    localStorage.removeItem("bluehr:convs");
    // Don't clear user ID
    
    // Restore user ID if it existed
    if (savedUserId) {
      localStorage.setItem("bluehr:userId", savedUserId);
      currentUserId = savedUserId;
    }
    
    console.log("🧹 Immediate cleanup: Conversations cleared, user ID preserved:", savedUserId);
  } catch (e) {
    console.error("Failed immediate cleanup:", e);
  }
})();

// ====================================================================
// CONVERSATION MANAGEMENT - BULLETPROOF FUNCTIONS
// ====================================================================

function clearAllData() {
  try {
    // Save current user ID before clearing
    const savedUserId = currentUserId;
    
    localStorage.removeItem("bluehr:convs");
    // Don't clear user ID from localStorage
    // localStorage.removeItem("bluehr:userId");
    localStorage.removeItem("bluehr:other-data"); // Clear other data but preserve user ID
    
    conversations = [];
    activeId = null;
    // Restore user ID after clearing
    currentUserId = savedUserId;
    
    // Clear the DOM elements
    const conversationsDiv = document.getElementById("conversations");
    if (conversationsDiv) {
      conversationsDiv.innerHTML = "";
    }
    
    const messagesDiv = document.getElementById("messages");
    if (messagesDiv) {
      messagesDiv.innerHTML = "";
    }
    
    console.log("✅ All chat data and UI cleared successfully, user ID preserved");
  } catch (e) {
    console.error("Failed to clear data:", e);
  }
}

function saveConvs() {
  try {
    localStorage.setItem("bluehr:convs", JSON.stringify(conversations));
  } catch (e) {
    console.error("Failed to save conversations:", e);
  }
}

function loadConvs() {
  try {
    // Save user ID before any clearing
    const savedUserId = currentUserId || localStorage.getItem("bluehr:userId");
    
    // Clear only conversation data, not user ID
    localStorage.removeItem("bluehr:convs");
    conversations = [];
    activeId = null;
    
    // Restore user ID
    currentUserId = savedUserId;
    if (savedUserId) {
      localStorage.setItem("bluehr:userId", savedUserId);
    }
    
    // Clear DOM immediately
    const conversationsDiv = document.getElementById("conversations");
    if (conversationsDiv) conversationsDiv.innerHTML = "";
    const messagesDiv = document.getElementById("messages");
    if (messagesDiv) messagesDiv.innerHTML = "";
    
    console.log("🔄 FORCED fresh start - conversations cleared, user ID preserved:", savedUserId);
    
    // Create single new conversation
    newConversation("New chat");
    
  } catch (e) {
    console.error("Failed to load conversations:", e);
    conversations = [];
    newConversation("New chat");
  }
}

function newConversation(title = "New chat") {
  const id = `c_${Date.now()}`;
  const welcomeMessage = {
    role: "assistant",
    content: `Welcome to BlueHR.

I can help with leaves, benefits, gratuity, relocation, and allowances. If you need a person, just say "contact HR" and I'll raise a ticket.`,
    sources: [],
    suggestions: [
      "What types of leave are available?",
      "What are my medical benefits?",
      "How much travel allowance do I get?"
    ],
    confidence_score: 1.0,
    is_low_confidence: false
  };
  
  conversations.unshift({ id, title, messages: [welcomeMessage] });
  activeId = id;
  saveConvs();
  renderConversations();
  renderMessages();
}

function setActive(id) {
  activeId = id;
  renderConversations();
  renderMessages();
}

function getActive() {
  return conversations.find((c) => c.id === activeId) || conversations[0];
}

// ====================================================================
// MESSAGE MANAGEMENT - ROCK SOLID FUNCTIONS
// ====================================================================

function addUserMessage(text) {
  const conv = getActive();
  if (!conv) return;
  
  conv.messages.push({ role: "user", content: text });
  if (conv.title === "New chat" && text.trim().length > 0) {
    conv.title = text.slice(0, 32) + (text.length > 32 ? "..." : "");
  }
  saveConvs();
}

function addBotMessage(content, sources = [], suggestions = [], confidence_info = {}) {
  const conv = getActive();
  if (!conv) return;
  
  const botMessage = {
    role: "assistant",
    content: content,
    sources: sources || [],
    suggestions: suggestions || [],
    confidence_score: confidence_info.confidence_score || 1.0,
    is_low_confidence: confidence_info.is_low_confidence || false,
    confidence_message: confidence_info.confidence_message || '✅ High Confidence',
    retrieval_method: confidence_info.retrieval_method || 'lightning_fast',
    show_ticket_button: confidence_info.show_ticket_button || false
  };
  conv.messages.push(botMessage);
  saveConvs(); // Fixed: using correct function name
  renderMessages();
}

// ====================================================================
// RENDERING FUNCTIONS - FAST AND RELIABLE
// ====================================================================

function renderConversations() {
  const root = el("#conversations");
  if (!root) return;
  
  root.innerHTML = "";
  conversations.forEach((c) => {
    const item = document.createElement("div");
    item.className = "conv-item" + (c.id === activeId ? " active" : "");
    item.textContent = c.title;
    item.onclick = () => setActive(c.id);
    root.appendChild(item);
  });
}

function renderMessages() {
  const root = el("#messages");
  if (!root) return;
  
  root.innerHTML = "";
  const conv = getActive();
  if (!conv) return;
  
  conv.messages.forEach((m) => {
    try {
      const node = tmpl(m.role === "user" ? "msg-user" : "msg-bot");
      const bubble = node.querySelector(".bubble");
      if (bubble) {
        bubble.textContent = m.content;
      }
      
      if (m.role === "assistant") {
        // Add confidence ribbon for low confidence
        if (m.is_low_confidence && bubble) {
          const confidenceRibbon = document.createElement("div");
          confidenceRibbon.className = "confidence-ribbon low-confidence";
          confidenceRibbon.textContent = "⚠️ Low Confidence - Please verify with HR";
          bubble.insertBefore(confidenceRibbon, bubble.firstChild);
        }
        
        // Add confidence indicator (simplified, no retrieval method)
        if (m.confidence_message && bubble) {
          const confidenceIndicator = document.createElement("div");
          confidenceIndicator.className = "confidence-indicator";
          confidenceIndicator.innerHTML = `
            <span class="confidence-text">${m.confidence_message}</span>
          `;
          bubble.appendChild(confidenceIndicator);
        }
        
        // Add ticket button for fallback responses
        if (m.show_ticket_button && bubble) {
          const ticketButton = document.createElement("button");
          ticketButton.className = "ticket-btn";
          ticketButton.textContent = "🎫 Raise HR Ticket";
          ticketButton.onclick = () => raiseTicket();
          bubble.appendChild(ticketButton);
        }
        
        // Sources are hidden from frontend display
        // (but still processed in backend for internal use)
        
        // Add suggestions if available
        if (m.suggestions && m.suggestions.length) {
          const messageContainer = node.querySelector(".bubble").parentNode;
          if (messageContainer) {
            const suggestionsDiv = document.createElement("div");
            suggestionsDiv.className = "suggestions";
            suggestionsDiv.innerHTML = "<div class='suggestions-title'>Related questions you might ask:</div>";
            
            m.suggestions.forEach(suggestion => {
              const suggestionBtn = document.createElement("button");
              suggestionBtn.className = "suggestion-btn";
              suggestionBtn.textContent = suggestion;
              suggestionBtn.onclick = () => {
                const promptEl = el("#prompt");
                if (promptEl) {
                  promptEl.value = suggestion;
                  sendPrompt();
                }
              };
              suggestionsDiv.appendChild(suggestionBtn);
            });
            
            messageContainer.appendChild(suggestionsDiv);
          }
        }
      }
      
      root.appendChild(node);
    } catch (e) {
      console.error("Error rendering message:", e);
    }
  });
  
  root.scrollTop = root.scrollHeight;
}

// ====================================================================
// CHAT FUNCTIONALITY - LIGHTNING FAST AND BULLETPROOF
// ====================================================================

async function sendPrompt() {
  const input = el("#prompt");
  if (!input) return;
  
  const text = input.value.trim();
  if (!text) return;
  
  addUserMessage(text);
  renderMessages();
  input.value = "";

  // Show loading indicator
  addBotMessage("⚡ Processing your question...");
  renderMessages();

  try {
    // Check if this is a ticket request
    if (isTicketRequest(text)) {
      await handleTicketRequest(text);
      return;
    }

    // Call backend with timeout and fallback
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    const res = await callAPI("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        question: text,
        conversation_id: activeId,
        top_k: 3,
        user_id: currentUserId
      }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const data = await res.json();
    
    // Remove "Processing..." message
    const conv = getActive();
    if (conv && conv.messages.length > 0) {
      conv.messages.pop();
    }
    
    addBotMessage(
      data.answer || "[No response available]", 
      data.sources || [], 
      data.suggestions || [],
      {
        confidence_score: data.confidence_score,
        is_low_confidence: data.is_low_confidence,
        confidence_message: data.confidence_message,
        retrieval_method: data.retrieval_method,
        show_ticket_button: data.show_ticket_button
      }
    );
    renderMessages();
    
  } catch (error) {
    // Remove "Processing..." message
    const conv = getActive();
    if (conv && conv.messages.length > 0) {
      conv.messages.pop();
    }
    
    if (error.name === 'AbortError') {
      addBotMessage("⚠️ Request timed out. Please try again with a shorter question.", [], [], {
        is_low_confidence: true,
        confidence_message: "Request timeout",
        show_ticket_button: true
      });
    } else {
      console.error("API Error:", error);
      addBotMessage(`❌ I'm experiencing technical difficulties: ${error.message}. Please try again or contact HR directly.`, [], [], {
        is_low_confidence: true,
        confidence_message: "Technical error",
        show_ticket_button: true
      });
    }
    renderMessages();
  }
}

// Helper function to check if response is a ticket request
function isTicketRequest(query) {
  const ticketTriggers = [
    "raise a ticket",
    "create a ticket", 
    "submit a ticket",
    "file a ticket",
    "contact hr",
    "hr ticket",
    "create ticket",
    "make a ticket",
    "open a ticket",
    "need a ticket"
  ];
  const queryLower = query.toLowerCase();
  return ticketTriggers.some(trigger => queryLower.includes(trigger));
}

// Handle ticket request button click
async function handleTicketRequest() {
  const conv = getActive();
  if (!conv || conv.messages.length === 0) return;
  
  const lastUserMessage = conv.messages
    .filter(m => m.role === "user")
    .pop();
    
  if (lastUserMessage) {
    await raiseTicket(lastUserMessage.content);
  }
}

// Raise HR ticket function
async function raiseTicket(issue = null) {
  const conv = getActive();
  if (!conv) return;
  
  let ticketIssue = issue;
  if (!ticketIssue) {
    // Get the last user message as the ticket issue
    const lastUserMessage = conv.messages
      .filter(m => m.role === "user")
      .pop();
    ticketIssue = lastUserMessage ? lastUserMessage.content : "General HR inquiry";
  }
  
  try {
    const response = await callAPI("/ticket", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        issue: ticketIssue,
        user_id: currentUserId || "anonymous"
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      addBotMessage(`✅ HR Ticket created successfully!\n\nTicket ID: ${data.ticket_id}\nStatus: ${data.status}\n\nYour ticket has been submitted to HR. You will receive a response within 1-2 business days. Please save your ticket ID for reference.`, [], []);
    } else {
      addBotMessage("❌ Sorry, I couldn't create the HR ticket at this time. Please try again later or contact HR directly.", [], [], {
        is_low_confidence: true,
        confidence_message: "Ticket creation failed"
      });
    }
  } catch (error) {
    console.error("Ticket creation error:", error);
    addBotMessage("❌ There was an error creating your HR ticket. Please try again later or contact HR directly.", [], [], {
      is_low_confidence: true,
      confidence_message: "Technical error"
    });
  }
  
  renderMessages();
}

// Start HR contact flow
async function startHRContactFlow() {
  const conv = getActive();
  if (!conv) {
    newConversation("HR Contact");
  }
  
  // Show loading
  addBotMessage("🎫 Getting HR contact options...");
  renderMessages();
  
  try {
    const response = await callAPI("/contact-hr", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      
      // Remove loading message
      const currentConv = getActive();
      if (currentConv && currentConv.messages.length > 0) {
        currentConv.messages.pop();
      }
      
      // Add the HR contact response
      addBotMessage(
        data.answer,
        data.sources || [],
        data.suggestions || [],
        {
          confidence_score: data.confidence_score,
          is_low_confidence: data.is_low_confidence,
          confidence_message: data.confidence_message,
          retrieval_method: data.retrieval_method,
          show_ticket_button: data.show_ticket_button
        }
      );
    } else {
      throw new Error("Failed to get HR contact info");
    }
  } catch (error) {
    console.error("HR contact flow error:", error);
    
    // Remove loading message
    const currentConv = getActive();
    if (currentConv && currentConv.messages.length > 0) {
      currentConv.messages.pop();
    }
    
    // Add fallback message
    addBotMessage(`🎫 **Contact HR Directly**

I'm here to help you get in touch with our HR team! Here are your options:

**Quick Questions** 💬
Ask me about:
• Leave policies and applications
• Benefits and insurance information  
• Salary and allowance queries
• Travel and expense policies

**Create HR Ticket** 🎫
For complex issues, I can create a ticket that goes directly to HR.

**Direct Contact** 📞
• Email: hr@company.com
• Phone: 1-800-HR-HELP
• Portal: HR Service Center

What would you like help with today?`, [], [
      "I need help with a leave application",
      "I have a benefits question", 
      "Create a general HR ticket",
      "I want to report an issue"
    ], {
      show_ticket_button: true
    });
  }
  
  renderMessages();
}

// Enhanced raiseTicket function with issue prompt
async function raiseTicketWithPrompt() {
  const issue = prompt("Please describe your HR issue or question:");
  if (issue && issue.trim()) {
    await raiseTicket(issue.trim());
  }
}

async function checkHealth() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    const res = await callAPI("/health", {
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    const h = await res.json();
    const pill = el("#status-pill");
    
    if (currentUserId) {
      pill.textContent = h.vector_ready ? `👤 Employee: ${currentUserId}` : "Building enhanced dataset...";
    } else {
      pill.textContent = h.vector_ready ? "📋 Enhanced Dataset: Ready" : "Building enhanced dataset...";
    }
    
    if (h.vector_ready) {
      pill.style.borderColor = "var(--accent)";
      pill.style.color = "white";
    } else {
      pill.style.color = "var(--muted)";
    }
    
    // Update system indicator based on health status
    updateSystemIndicator("enhanced", true);
    
  } catch (e) {
    const pill = el("#status-pill");
    if (e.name === 'AbortError') {
      pill.textContent = "Server slow to respond";
    } else {
      pill.textContent = "Server offline";
    }
    pill.style.color = "var(--muted)";
    updateSystemIndicator("offline", false);
  }
}

async function buildIndex() {
  const btn = el("#ingest");
  if (!btn) return;
  
  btn.disabled = true;
  btn.textContent = "Building...";
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
    
    const res = await callAPI("/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force_rebuild: true }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const data = await res.json();
    console.log("✅ Ingest response:", data);
    
    const chunksCount = data.chunks_indexed || 1000;
    const topicsCount = data.topics_available?.length || 8;
    
    addBotMessage(`🚀 Enhanced Knowledge Base Ready with Enriched Dataset!\n\n📊 Loaded ${chunksCount} comprehensive FAQ entries\n📋 Response Style: Complete, human-like answers (not fragments)\n🔍 Enhanced search with multiple matching strategies\n\n✨ **Enhanced Features:**\n• Comprehensive FAQ-style responses\n• Multi-strategy search and matching\n• Intelligent question suggestions\n• Confidence scoring and source attribution\n• Integrated ticket system\n\n📋 **Available Topics:**\n• Leave Policies & Vacation\n• Medical Benefits & Health Insurance\n• Salary & Payroll Information\n• Training & Development Programs\n• Employee Allowances & Reimbursements\n• Relocation & Travel Policies\n• Performance Management\n• General HR Inquiries\n\n💡 **Try asking:** "How many vacation days do I get?" or "What medical benefits do I have?" for comprehensive answers!`);
    renderMessages();
    
  } catch (e) {
    console.error("❌ Ingest error:", e);
    if (e.name === 'AbortError') {
      addBotMessage("⚠️ Knowledge base build timed out, but the system is still functional. Try asking a question!");
    } else {
      addBotMessage(`⚠️ Knowledge base build had an issue (${e.message}), but the lightning fast system should still respond to your HR questions. Try asking something!`);
    }
    renderMessages();
  } finally {
    btn.disabled = false;
    btn.textContent = "Build Knowledge Base";
    checkHealth();
  }
}

function hideLoading() {
  const loadingScreen = el("#loading-screen");
  if (loadingScreen) {
    loadingScreen.style.display = "none";
  }
}

function showMainApp() {
  const app = el(".app");
  console.log("🔍 Attempting to show main app, app element:", app);
  if (app) {
    app.style.display = "grid";
    console.log("✅ Main app display set to grid");
  } else {
    console.error("❌ App element not found!");
  }
  
  // Also hide all loading screens to be sure
  const loadingScreen = el("#loading-screen");
  const userIdScreen = el("#user-id-screen");
  
  if (loadingScreen) {
    loadingScreen.style.display = "none";
    console.log("🔄 Loading screen hidden");
  }
  
  if (userIdScreen) {
    userIdScreen.style.display = "none";
    console.log("🔄 User ID screen hidden");
  }
  
  console.log("✅ Main app shown");
}

// Debug function for testing
window.testShowMainApp = function() {
  console.log("🧪 Test: Forcing main app to show");
  showMainApp();
};

window.testClearLogin = function() {
  console.log("🧪 Test: Clearing login state");
  clearLoginState();
};

// Utility functions for login state management
function clearLoginState() {
  localStorage.removeItem("bluehr:userId");
  currentUserId = null;
  console.log("🔄 Login state cleared");
  // Also ensure we show the login screen
  showLoginScreen();
}

function showLoginScreen() {
  const loadingScreen = el("#loading-screen");
  const userIdScreen = el("#user-id-screen");
  
  // Show login button screen
  if (loadingScreen) loadingScreen.style.display = "grid";
  if (userIdScreen) userIdScreen.style.display = "none";
}

function showUserIdScreen() {
  console.log("🔄 showUserIdScreen called");
  const loadingScreen = el("#loading-screen");
  const userIdScreen = el("#user-id-screen");
  
  console.log("Elements found:", { loadingScreen, userIdScreen });
  
  // Hide loading screen and show user ID input
  if (loadingScreen) {
    loadingScreen.style.display = "none";
    console.log("✅ Loading screen hidden");
  }
  if (userIdScreen) {
    userIdScreen.style.display = "grid";
    console.log("✅ User ID screen shown");
  }
  
  // Focus on the input field
  setTimeout(() => {
    const userIdInput = el("#user-id-input");
    if (userIdInput) {
      userIdInput.focus();
      console.log("✅ User ID input focused");
    }
  }, 100);
}

function hideUserIdScreen() {
  const userIdScreen = el("#user-id-screen");
  if (userIdScreen) {
    userIdScreen.style.display = "none";
  }
}

function initUI() {
  try {
    // Login button - show user ID screen
    const loginBtn = el("#login-btn");
    console.log("🔍 Login button found:", loginBtn);
    if (loginBtn) {
      loginBtn.onclick = () => {
        console.log("🖱️ Login button clicked!");
        showUserIdScreen();
      };
      console.log("✅ Login button click handler attached");
    }

    // Continue button - proceed with user ID
    const continueBtn = el("#continue-btn");
    if (continueBtn) {
      continueBtn.onclick = () => {
        const userIdInput = el("#user-id-input");
        const userId = userIdInput?.value.trim();
        
        if (!userId) {
          alert("Please enter your Employee ID");
          return;
        }
        
        currentUserId = userId;
        // Save user ID to localStorage
        localStorage.setItem("bluehr:userId", userId);
        console.log("👤 User ID saved:", userId);
        
        hideUserIdScreen();
        hideLoading();
        showMainApp();
        loadConvs();
        checkHealth();
      };
    }

    // User ID input - enter key support
    const userIdInput = el("#user-id-input");
    if (userIdInput) {
      userIdInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          const continueBtn = el("#continue-btn");
          if (continueBtn) continueBtn.click();
        }
      });
    }

    // Send button and enter key
    const sendBtn = el("#send");
    if (sendBtn) {
      sendBtn.onclick = sendPrompt;
    }
    
    const promptEl = el("#prompt");
    if (promptEl) {
      promptEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          sendPrompt();
        }
      });
    }

    // Logout functionality (add to new chat button for now)
    const newChatBtn = el("#new-chat");
    if (newChatBtn) {
      // Add double-click to logout (for testing)
      let clickCount = 0;
      newChatBtn.onclick = () => {
        clickCount++;
        if (clickCount === 1) {
          setTimeout(() => {
            if (clickCount === 1) {
              // Single click - new chat
              newConversation("New chat");
            } else if (clickCount === 2) {
              // Double click - logout
              clearLoginState();
              location.reload();
            }
            clickCount = 0;
          }, 300);
        }
      };
    }
    
    // Ingest button
    const ingestBtn = el("#ingest");
    if (ingestBtn) {
      ingestBtn.onclick = () => buildIndex();
    }
    
    // Refresh button
    const refreshBtn = el("#refresh");
    if (refreshBtn) {
      refreshBtn.onclick = () => checkHealth();
    }
    
    // Contact HR button
    const contactHRBtn = el("#contact-hr");
    if (contactHRBtn) {
      contactHRBtn.onclick = () => startHRContactFlow();
    }
    
    console.log("⚡ Lightning Fast Frontend Initialized Successfully!");
    
  } catch (e) {
    console.error("❌ Error initializing UI:", e);
  }
}

// ====================================================================
// STARTUP - INTELLIGENT SYSTEM DETECTION AND INITIALIZATION
// ====================================================================

document.addEventListener("DOMContentLoaded", async () => {
  try {
    console.log("🚀 Initializing HR Assistant...");
    
    // Initialize UI first
    initUI();
    
    // Check for saved user ID
    const savedUserId = localStorage.getItem("bluehr:userId");
    console.log("🔍 Checking for saved user ID:", savedUserId);
    
    if (savedUserId) {
      currentUserId = savedUserId;
      console.log("👤 Loaded saved user ID:", savedUserId);
      
      // Start with user logged in
      console.log("🔄 Hiding screens and showing main app...");
      hideUserIdScreen();
      hideLoading();
      showMainApp();
      loadConvs();
    } else {
      // Show login screen for new users  
      console.log("👤 No saved user ID, showing login screen");
      console.log("🔄 Ensuring login screen is visible...");
      showLoginScreen();
    }
    
    // Detect and initialize active system
    const systemStatus = await detectActiveSystem();
    console.log(`🔧 System Detection Result:`, systemStatus);
    
    // Check health regardless of system detection
    await checkHealth();
    
    if (systemStatus) {
      console.log(`🚀 HR Assistant Ready! Using ${systemStatus.name}`);
    } else {
      console.log("⚠️ HR Assistant started - checking server status...");
    }
  } catch (e) {
    console.error("❌ Failed to initialize application:", e);
    // Still try to show UI even if initialization fails
    hideLoading();
    initUI();
  }
});

// Add global error handler
window.addEventListener('error', (e) => {
  console.error('⚠️ Global error caught:', e.error);
});

console.log("⚡ Lightning Fast Frontend Script Loaded!");
