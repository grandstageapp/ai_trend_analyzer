// AI Trends Analyzer - Chat Interface

// Chat management system
const ChatInterface = {
    currentTrendId: null,
    isProcessing: false,
    messageHistory: [],
    
    config: {
        maxMessages: 50,
        typingDelay: 1000,
        scrollDelay: 100
    },
    
    elements: {
        chatMessages: null,
        chatInput: null,
        sendButton: null
    }
};

// Initialize chat interface
function initializeChatInterface(trendId) {
    ChatInterface.currentTrendId = trendId;
    
    // Get DOM elements
    ChatInterface.elements.chatMessages = document.getElementById('chatMessages');
    ChatInterface.elements.chatInput = document.getElementById('chatInput');
    ChatInterface.elements.sendButton = document.getElementById('sendChatBtn');
    
    if (!ChatInterface.elements.chatMessages || !ChatInterface.elements.chatInput) {
        console.warn('Chat interface elements not found');
        return;
    }
    
    // Setup event listeners
    setupChatEventListeners();
    
    // Initialize chat state
    loadChatHistory();
    
    console.log(`Chat interface initialized for trend ID: ${trendId}`);
}

function setupChatEventListeners() {
    const { chatInput, sendButton } = ChatInterface.elements;
    
    // Send button click
    if (sendButton) {
        sendButton.addEventListener('click', sendChatMessage);
    }
    
    // Enter key to send message
    if (chatInput) {
        chatInput.addEventListener('keypress', handleChatKeyPress);
        
        // Auto-resize textarea as user types
        chatInput.addEventListener('input', function() {
            autoResizeTextarea(this);
        });
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

// Send chat message
function sendChatMessage() {
    const message = ChatInterface.elements.chatInput.value.trim();
    
    if (!message || ChatInterface.isProcessing) {
        return;
    }
    
    if (!ChatInterface.currentTrendId) {
        showError('No trend selected for chat');
        return;
    }
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    ChatInterface.elements.chatInput.value = '';
    ChatInterface.elements.chatInput.style.height = 'auto';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Set processing state
    ChatInterface.isProcessing = true;
    updateSendButtonState();
    
    // Send message to API
    sendMessageToAPI(message)
        .then(response => {
            hideTypingIndicator();
            addMessageToChat('ai', response);
        })
        .catch(error => {
            hideTypingIndicator();
            addMessageToChat('ai', 'I apologize, but I encountered an error processing your message. Please try again.');
            console.error('Chat API error:', error);
        })
        .finally(() => {
            ChatInterface.isProcessing = false;
            updateSendButtonState();
            focusChatInput();
        });
}

// Send message to API
function sendMessageToAPI(message) {
    return fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            trend_id: ChatInterface.currentTrendId,
            message: message
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        return data.response;
    });
}

// Add message to chat display
function addMessageToChat(sender, message) {
    const chatMessages = ChatInterface.elements.chatMessages;
    if (!chatMessages) return;
    
    // Create message element
    const messageElement = createMessageElement(sender, message);
    
    // Add to chat
    chatMessages.appendChild(messageElement);
    
    // Animate message appearance
    setTimeout(() => {
        messageElement.classList.add('message-appear');
    }, 10);
    
    // Scroll to bottom
    setTimeout(() => {
        scrollToBottom();
    }, ChatInterface.config.scrollDelay);
    
    // Store in history
    ChatInterface.messageHistory.push({
        sender: sender,
        message: message,
        timestamp: new Date()
    });
    
    // Limit message history
    if (ChatInterface.messageHistory.length > ChatInterface.config.maxMessages) {
        ChatInterface.messageHistory.shift();
        removeOldestMessage();
    }
    
    // Save to localStorage
    saveChatHistory();
}

function createMessageElement(sender, message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Format message content
    if (sender === 'ai') {
        messageContent.innerHTML = formatAIMessage(message);
    } else {
        messageContent.textContent = message;
    }
    
    messageDiv.appendChild(messageContent);
    
    // Add timestamp for AI messages
    if (sender === 'ai') {
        const timestamp = document.createElement('small');
        timestamp.className = 'message-timestamp text-muted d-block mt-1';
        timestamp.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        messageContent.appendChild(timestamp);
    }
    
    return messageDiv;
}

function formatAIMessage(message) {
    // Basic markdown-style formatting
    let formatted = message
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    
    return formatted;
}

// Typing indicator
function showTypingIndicator() {
    const chatMessages = ChatInterface.elements.chatMessages;
    if (!chatMessages) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message ai-message typing-indicator';
    typingDiv.id = 'typingIndicator';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'message-content';
    typingContent.innerHTML = `
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    typingDiv.appendChild(typingContent);
    chatMessages.appendChild(typingDiv);
    
    scrollToBottom();
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Quick questions
function askQuickQuestion(question) {
    ChatInterface.elements.chatInput.value = question;
    sendChatMessage();
}

// Chat utilities
function scrollToBottom() {
    const chatMessages = ChatInterface.elements.chatMessages;
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function focusChatInput() {
    if (ChatInterface.elements.chatInput && !ChatInterface.isProcessing) {
        ChatInterface.elements.chatInput.focus();
    }
}

function updateSendButtonState() {
    const sendButton = ChatInterface.elements.sendButton;
    if (!sendButton) return;
    
    if (ChatInterface.isProcessing) {
        sendButton.disabled = true;
        sendButton.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
    } else {
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="material-icons">send</i>';
    }
}

function removeOldestMessage() {
    const chatMessages = ChatInterface.elements.chatMessages;
    if (!chatMessages) return;
    
    const messages = chatMessages.querySelectorAll('.chat-message:not(.system-message)');
    if (messages.length > 0) {
        messages[0].remove();
    }
}

// Chat history management
function saveChatHistory() {
    if (!ChatInterface.currentTrendId) return;
    
    const historyKey = `chat_history_${ChatInterface.currentTrendId}`;
    try {
        localStorage.setItem(historyKey, JSON.stringify(ChatInterface.messageHistory));
    } catch (error) {
        console.warn('Failed to save chat history:', error);
    }
}

function loadChatHistory() {
    if (!ChatInterface.currentTrendId) return;
    
    const historyKey = `chat_history_${ChatInterface.currentTrendId}`;
    try {
        const savedHistory = localStorage.getItem(historyKey);
        if (savedHistory) {
            ChatInterface.messageHistory = JSON.parse(savedHistory);
            
            // Restore messages to chat display
            ChatInterface.messageHistory.forEach(item => {
                if (item.sender !== 'system') {
                    const messageElement = createMessageElement(item.sender, item.message);
                    ChatInterface.elements.chatMessages.appendChild(messageElement);
                }
            });
            
            scrollToBottom();
        }
    } catch (error) {
        console.warn('Failed to load chat history:', error);
        ChatInterface.messageHistory = [];
    }
}

function clearChatHistory() {
    if (!ChatInterface.currentTrendId) return;
    
    const historyKey = `chat_history_${ChatInterface.currentTrendId}`;
    localStorage.removeItem(historyKey);
    
    // Clear display
    const messages = ChatInterface.elements.chatMessages.querySelectorAll('.chat-message:not(.system-message)');
    messages.forEach(msg => msg.remove());
    
    // Clear memory
    ChatInterface.messageHistory = [];
    
    showInfo('Chat Cleared', 'Chat history has been cleared.');
}

// Chat commands
function processChatCommand(message) {
    const command = message.toLowerCase().trim();
    
    switch (command) {
        case '/clear':
            clearChatHistory();
            return true;
        case '/help':
            addMessageToChat('ai', `
                Available commands:
                • /clear - Clear chat history
                • /help - Show this help message
                
                You can ask me anything about this trend, including:
                • What is this trend about?
                • Why is this trending?
                • What are the business implications?
                • How does this relate to other AI developments?
            `);
            return true;
        default:
            return false;
    }
}

// Enhanced send message function with command processing
const originalSendChatMessage = sendChatMessage;
sendChatMessage = function() {
    const message = ChatInterface.elements.chatInput.value.trim();
    
    if (!message || ChatInterface.isProcessing) {
        return;
    }
    
    // Check for commands
    if (message.startsWith('/')) {
        const isCommand = processChatCommand(message);
        if (isCommand) {
            ChatInterface.elements.chatInput.value = '';
            return;
        }
    }
    
    // Call original function for regular messages
    originalSendChatMessage();
};

// Auto-focus chat input when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        focusChatInput();
    }, 500);
});

// Export global functions
window.initializeChatInterface = initializeChatInterface;
window.sendChatMessage = sendChatMessage;
window.handleChatKeyPress = handleChatKeyPress;
window.askQuickQuestion = askQuickQuestion;
window.clearChatHistory = clearChatHistory;

console.log('Chat.js loaded successfully');
