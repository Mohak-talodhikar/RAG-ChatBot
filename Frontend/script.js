// Enterprise AI Assistant JavaScript
class AIAssistant {
    constructor() {
        this.apiEndpoint = 'http://127.0.0.1:8000/ask';
        this.chatHistory = [];
        this.isDarkTheme = false;
        this.isProcessing = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadTheme();
        this.loadChatHistory();
        this.focusInput();
    }

    setupEventListeners() {
        const questionInput = document.getElementById('question');
        
        // Auto-resize textarea
        questionInput.addEventListener('input', (e) => {
            this.updateCharCount();
            this.autoResize(e.target);
        });

        // Focus management
        questionInput.addEventListener('focus', () => {
            this.hideWelcomeScreen();
        });

        // Initialize
        this.updateCharCount();
    }

    hideWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatMessages = document.getElementById('chatMessages');
        
        if (welcomeScreen && chatMessages) {
            welcomeScreen.style.display = 'none';
            chatMessages.style.display = 'flex';
        }
    }

    showWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatMessages = document.getElementById('chatMessages');
        
        if (welcomeScreen && chatMessages && this.chatHistory.length === 0) {
            welcomeScreen.style.display = 'flex';
            chatMessages.style.display = 'none';
        }
    }

    async askQuestion() {
        if (this.isProcessing) return;

        const questionInput = document.getElementById('question');
        const question = questionInput.value.trim();
        
        if (!question) {
            this.showToast('Please enter a question', 'error');
            return;
        }

        // Hide welcome screen and show chat
        this.hideWelcomeScreen();
        
        // Add user message to chat
        this.addMessage(question, 'user');
        
        // Clear input
        questionInput.value = '';
        this.updateCharCount();
        this.autoResize(questionInput);
        
        // Show processing state
        this.setProcessingState(true);
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: question })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Add assistant response
            this.addMessage(data.answer || 'I apologize, but I couldn\'t generate a response. Please try rephrasing your question.', 'assistant');
            
            // Save to history
            this.saveToHistory(question, data.answer);
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('Sorry, something went wrong. Please try again.', 'assistant', true);
            this.showToast('Connection error. Please check your internet connection.', 'error');
        } finally {
            this.setProcessingState(false);
            this.focusInput();
        }
    }

    addMessage(content, type, isError = false) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        if (isError) {
            messageContent.style.color = 'var(--error-color, #ef4444)';
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    setProcessingState(isProcessing) {
        this.isProcessing = isProcessing;
        const sendBtn = document.getElementById('sendBtn');
        const loadingOverlay = document.getElementById('loadingOverlay');
        
        if (isProcessing) {
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            loadingOverlay.style.display = 'flex';
            
            // Add typing indicator
            this.addTypingIndicator();
        } else {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            loadingOverlay.style.display = 'none';
            
            // Remove typing indicator
            this.removeTypingIndicator();
        }
    }

    addTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = '<i class="fas fa-ellipsis-h"></i> Thinking...';
        
        typingDiv.appendChild(avatar);
        typingDiv.appendChild(content);
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    updateCharCount() {
        const questionInput = document.getElementById('question');
        const charCount = document.getElementById('charCount');
        charCount.textContent = questionInput.value.length;
    }

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    focusInput() {
        setTimeout(() => {
            document.getElementById('question').focus();
        }, 100);
    }

    toggleTheme() {
        this.isDarkTheme = !this.isDarkTheme;
        document.body.classList.toggle('dark-theme');
        
        const themeIcon = document.getElementById('theme-icon');
        themeIcon.className = this.isDarkTheme ? 'fas fa-sun' : 'fas fa-moon';
        
        localStorage.setItem('theme', this.isDarkTheme ? 'dark' : 'light');
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            this.isDarkTheme = true;
            document.body.classList.add('dark-theme');
            document.getElementById('theme-icon').className = 'fas fa-sun';
        }
    }

    clearChat() {
        if (this.chatHistory.length === 0) return;
        
        if (confirm('Are you sure you want to clear the chat history?')) {
            this.chatHistory = [];
            this.saveChatHistory();
            
            // Clear messages
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';
            
            // Show welcome screen
            this.showWelcomeScreen();
            
            this.showToast('Chat history cleared', 'success');
        }
    }

    startNewChat() {
        this.clearChat();
    }

    setQuestion(question) {
        const questionInput = document.getElementById('question');
        questionInput.value = question;
        this.updateCharCount();
        this.focusInput();
        this.hideWelcomeScreen();
    }

    attachFile() {
        document.getElementById('fileInput').click();
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (file.type !== 'application/pdf') {
            this.showToast('Please upload a PDF file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        this.setProcessingState(true);
        this.showToast('Uploading and processing PDF...', 'info');

        try {
            const response = await fetch('http://127.0.0.1:8000/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }

            const data = await response.json();
            this.showToast(data.message || 'PDF processed successfully!', 'success');
            
            // Add a system message to the chat
            this.addMessage(`System: Uploaded "${file.name}" successfully. You can now ask questions about it.`, 'assistant');
            this.hideWelcomeScreen();
            
        } catch (error) {
            console.error('Error:', error);
            this.showToast(error.message || 'Error uploading file', 'error');
        } finally {
            this.setProcessingState(false);
            // Reset input
            event.target.value = '';
        }
    }

    saveToHistory(question, answer) {
        this.chatHistory.push({
            question,
            answer,
            timestamp: new Date().toISOString()
        });
        this.saveChatHistory();
    }

    saveChatHistory() {
        localStorage.setItem('chatHistory', JSON.stringify(this.chatHistory));
    }

    loadChatHistory() {
        const saved = localStorage.getItem('chatHistory');
        if (saved) {
            try {
                this.chatHistory = JSON.parse(saved);
                // Optionally restore previous chat messages
            } catch (e) {
                console.error('Failed to load chat history:', e);
                this.chatHistory = [];
            }
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Global functions for HTML onclick handlers
function askQuestion() {
    if (window.aiAssistant) {
        window.aiAssistant.askQuestion();
    }
}

function toggleTheme() {
    if (window.aiAssistant) {
        window.aiAssistant.toggleTheme();
    }
}

function clearChat() {
    if (window.aiAssistant) {
        window.aiAssistant.clearChat();
    }
}

function startNewChat() {
    if (window.aiAssistant) {
        window.aiAssistant.startNewChat();
    }
}

function setQuestion(question) {
    if (window.aiAssistant) {
        window.aiAssistant.setQuestion(question);
    }
}

function attachFile() {
    if (window.aiAssistant) {
        window.aiAssistant.attachFile();
    }
}

function handleFileUpload(event) {
    if (window.aiAssistant) {
        window.aiAssistant.handleFileUpload(event);
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        askQuestion();
    }
}

function autoResize(textarea) {
    if (window.aiAssistant) {
        window.aiAssistant.autoResize(textarea);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiAssistant = new AIAssistant();
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K to focus on input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('question').focus();
    }
    
    // Ctrl/Cmd + / to clear chat
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        clearChat();
    }
    
    // Escape to clear input
    if (e.key === 'Escape') {
        const questionInput = document.getElementById('question');
        questionInput.value = '';
        window.aiAssistant?.updateCharCount();
    }
});

// Network status monitoring
window.addEventListener('online', () => {
    if (window.aiAssistant) {
        window.aiAssistant.showToast('Connection restored', 'success');
    }
});

window.addEventListener('offline', () => {
    if (window.aiAssistant) {
        window.aiAssistant.showToast('Connection lost', 'error');
    }
});