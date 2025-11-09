// AI Code Generator Web Application - Frontend JavaScript

class CodeGeneratorApp {
    constructor() {
        this.sessionId = null;
        this.ws = null;
        this.isConnected = false;
        this.isGenerating = false;
        this.generationTimeout = null; // Timeout to reset isGenerating if stuck
        
        this.initializeElements();
        this.attachEventListeners();
        this.generateSessionId();
        this.connectWebSocket();
        this.loadTools();
    }
    
    initializeElements() {
        this.promptInput = document.getElementById('prompt-input');
        this.sendBtn = document.getElementById('send-btn');
        this.messagesArea = document.getElementById('messages-area');
        this.statusText = document.getElementById('status-text');
        this.connectionStatus = document.getElementById('connection-status');
        this.sessionIdDisplay = document.getElementById('session-id-display');
        this.toolsModal = document.getElementById('tools-modal');
        this.closeToolsModal = document.getElementById('close-tools-modal');
        this.showToolsBtn = document.getElementById('show-tools-btn');
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.toolsList = document.getElementById('tools-list');
    }
    
    attachEventListeners() {
        // Send button
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send (Shift+Enter for new line)
        this.promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Example buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.getAttribute('data-prompt');
                this.promptInput.value = prompt;
                this.sendMessage();
            });
        });
        
        // Tools modal
        this.showToolsBtn.addEventListener('click', () => {
            this.toolsModal.classList.add('active');
        });
        
        this.closeToolsModal.addEventListener('click', () => {
            this.toolsModal.classList.remove('active');
        });
        
        // Close modal on outside click
        this.toolsModal.addEventListener('click', (e) => {
            if (e.target === this.toolsModal) {
                this.toolsModal.classList.remove('active');
            }
        });
        
        // New session button
        this.newSessionBtn.addEventListener('click', () => {
            this.newSession();
        });
    }
    
    generateSessionId() {
        this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        this.sessionIdDisplay.textContent = this.sessionId;
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus(true);
                this.updateStatus('Connected', 'success');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
                this.updateStatus('Connection error', 'error');
                
                // Reset generation state on error
                if (this.isGenerating) {
                    this.resetGenerationState();
                }
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.updateStatus('Disconnected', 'error');
                
                // Reset generation state if connection closes during generation
                if (this.isGenerating) {
                    this.resetGenerationState();
                    this.updateStatus('Connection closed. Generation stopped.', 'error');
                }
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connectWebSocket();
                    }
                }, 3000);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    resetGenerationState() {
        this.isGenerating = false;
        this.sendBtn.disabled = false;
        this.removeThinkingIndicator();
        if (this.generationTimeout) {
            clearTimeout(this.generationTimeout);
            this.generationTimeout = null;
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'status':
                this.updateStatus(data.message, 'success');
                break;
                
            case 'thinking':
                this.addThinkingIndicator();
                this.updateStatus(data.message, 'thinking');
                break;
                
            case 'response':
                this.removeThinkingIndicator();
                this.addMessage('assistant', data.content);
                break;
                
            case 'tool_result':
                this.addToolResult(data.tool_name, data.result);
                break;
                
            case 'complete':
                this.resetGenerationState();
                this.updateStatus('Generation complete', 'success');
                break;
                
            case 'error':
                this.resetGenerationState();
                this.addMessage('assistant', `❌ Error: ${data.message}`, true);
                this.updateStatus('Error occurred', 'error');
                break;
                
            case 'pong':
                // Heartbeat response
                break;
        }
    }
    
    async sendMessage() {
        const prompt = this.promptInput.value.trim();
        
        if (!prompt) {
            return;
        }
        
        if (!this.isConnected) {
            this.updateStatus('Not connected. Please wait...', 'error');
            return;
        }
        
        if (this.isGenerating) {
            this.updateStatus('Already generating. Please wait...', 'error');
            return;
        }
        
        // Add user message to UI
        this.addMessage('user', prompt);
        
        // Clear input
        this.promptInput.value = '';
        
        // Disable send button
        this.isGenerating = true;
        this.sendBtn.disabled = true;
        this.updateStatus('Generating code...', 'thinking');
        
        // Set a safety timeout to reset generation state after 5 minutes
        // This prevents the UI from getting stuck if something goes wrong
        this.generationTimeout = setTimeout(() => {
            if (this.isGenerating) {
                console.warn('Generation timeout - resetting state');
                this.resetGenerationState();
                this.updateStatus('Generation timeout. You can try again.', 'error');
                this.addMessage('assistant', '⏱️ Generation took too long. Please try again or refresh the page.', true);
            }
        }, 5 * 60 * 1000); // 5 minutes
        
        // Send via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'generate',
                prompt: prompt
            }));
        } else {
            // Fallback to REST API
            await this.sendViaREST(prompt);
        }
    }
    
    async sendViaREST(prompt) {
        try {
            this.updateStatus('Sending request...', 'thinking');
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Update session ID if provided
            if (data.session_id) {
                this.sessionId = data.session_id;
                this.sessionIdDisplay.textContent = this.sessionId;
            }
            
            // Add response
            this.addMessage('assistant', data.response);
            
            // Add tool results
            if (data.tool_calls && data.tool_calls.length > 0) {
                data.tool_calls.forEach(tool => {
                    this.addToolResult(tool.name, tool.result);
                });
            }
            
            // Add files created
            if (data.files_created && data.files_created.length > 0) {
                this.addFilesCreated(data.files_created);
            }
            
            this.resetGenerationState();
            this.updateStatus('Generation complete', 'success');
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('assistant', `❌ Error: ${error.message}`, true);
            this.resetGenerationState();
            this.updateStatus('Error occurred', 'error');
        }
    }
    
    addMessage(role, content, isError = false) {
        // Remove welcome message if it exists
        const welcomeMsg = this.messagesArea.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${role}`;
        
        const header = document.createElement('div');
        header.className = 'message-header';
        header.innerHTML = role === 'user' 
            ? '<span>👤 You</span>' 
            : '<span>🤖 AI Code Generator</span>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isError) {
            contentDiv.innerHTML = `<p style="color: var(--error);">${this.escapeHtml(content)}</p>`;
        } else {
            // Convert markdown-like formatting to HTML
            contentDiv.innerHTML = this.formatMessage(content);
        }
        
        messageDiv.appendChild(header);
        messageDiv.appendChild(contentDiv);
        
        this.messagesArea.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addThinkingIndicator() {
        const existing = this.messagesArea.querySelector('.thinking-indicator');
        if (existing) return;
        
        const indicator = document.createElement('div');
        indicator.className = 'thinking-indicator';
        indicator.innerHTML = '<div class="spinner"></div><span>🤔 Generating code...</span>';
        this.messagesArea.appendChild(indicator);
        this.scrollToBottom();
    }
    
    removeThinkingIndicator() {
        const indicator = this.messagesArea.querySelector('.thinking-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    addToolResult(toolName, result) {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'tool-result';
        
        const header = document.createElement('div');
        header.className = 'tool-result-header';
        header.innerHTML = `<span>🔧</span><span>${toolName || 'Tool Execution'}</span>`;
        
        const content = document.createElement('div');
        content.textContent = result;
        content.style.fontFamily = 'var(--font-mono)';
        content.style.fontSize = '0.875rem';
        content.style.color = 'var(--text-secondary)';
        
        toolDiv.appendChild(header);
        toolDiv.appendChild(content);
        
        // Append to last assistant message or create new one
        const lastMessage = this.messagesArea.querySelector('.message-assistant:last-child');
        if (lastMessage) {
            lastMessage.appendChild(toolDiv);
        } else {
            this.messagesArea.appendChild(toolDiv);
        }
        
        this.scrollToBottom();
    }
    
    addFilesCreated(files) {
        const filesDiv = document.createElement('div');
        filesDiv.className = 'files-created';
        
        const header = document.createElement('div');
        header.className = 'files-created-header';
        header.innerHTML = '<span>📁</span><span>Files Created</span>';
        
        const filesList = document.createElement('div');
        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `<span>📄</span><span>${file}</span>`;
            filesList.appendChild(fileItem);
        });
        
        filesDiv.appendChild(header);
        filesDiv.appendChild(filesList);
        
        // Append to last assistant message or create new one
        const lastMessage = this.messagesArea.querySelector('.message-assistant:last-child');
        if (lastMessage) {
            lastMessage.appendChild(filesDiv);
        } else {
            this.messagesArea.appendChild(filesDiv);
        }
        
        this.scrollToBottom();
    }
    
    formatMessage(text) {
        // Simple markdown-like formatting
        let html = this.escapeHtml(text);
        
        // Code blocks
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang || 'text'}">${this.escapeHtml(code.trim())}</code></pre>`;
        });
        
        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        
        // Headers
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
        
        // Lists
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
        html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
        
        // Wrap consecutive list items in ul/ol
        html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => {
            return '<ul>' + match + '</ul>';
        });
        
        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');
        
        // Wrap in paragraph if not already wrapped
        if (!html.startsWith('<')) {
            html = '<p>' + html + '</p>';
        }
        
        return html;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateStatus(text, type = '') {
        this.statusText.textContent = text;
        this.statusText.className = 'status ' + type;
    }
    
    updateConnectionStatus(connected) {
        if (connected) {
            this.connectionStatus.textContent = 'Connected';
            this.connectionStatus.className = 'badge badge-success';
        } else {
            this.connectionStatus.textContent = 'Disconnected';
            this.connectionStatus.className = 'badge badge-error';
        }
    }
    
    scrollToBottom() {
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
    }
    
    async loadTools() {
        try {
            const response = await fetch('/api/tools');
            const data = await response.json();
            
            let html = '';
            
            if (data.code_tools && data.code_tools.length > 0) {
                html += '<div class="tool-category">';
                html += '<h3>💻 Code Generation Tools</h3>';
                data.code_tools.forEach(tool => {
                    html += `
                        <div class="tool-item">
                            <div class="tool-item-name">${tool.name}</div>
                            <div class="tool-item-description">${tool.description}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            if (data.file_tools && data.file_tools.length > 0) {
                html += '<div class="tool-category">';
                html += '<h3>📁 File Operation Tools</h3>';
                data.file_tools.forEach(tool => {
                    html += `
                        <div class="tool-item">
                            <div class="tool-item-name">${tool.name}</div>
                            <div class="tool-item-description">${tool.description}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            this.toolsList.innerHTML = html || '<div class="loading">No tools available</div>';
            
        } catch (error) {
            console.error('Error loading tools:', error);
            this.toolsList.innerHTML = '<div class="loading">Error loading tools</div>';
        }
    }
    
    newSession() {
        if (confirm('Start a new session? This will clear the current conversation.')) {
            // Reset generation state when starting new session
            this.resetGenerationState();
            
            this.generateSessionId();
            this.messagesArea.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">✨</div>
                    <h2>Welcome to AI Code Generator</h2>
                    <p>Describe what code you'd like to generate, and I'll create it for you!</p>
                </div>
            `;
            
            if (this.ws) {
                this.ws.close();
            }
            
            this.connectWebSocket();
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new CodeGeneratorApp();
});

