/**
 * Simplified WebSocket Dashboard for Django Channels Notifications
 * Basic functionality: Connect, Disconnect, View Messages, Ping
 */

class NotificationWebSocket {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.messageCount = 0;
        this.detailedView = true;
        this.sessionId = null;
        this.userId = null;
        this.startTime = Date.now();
        
        this.initializeElements();
        this.setupEventListeners();
        this.startUptime();
        this.logMessage('📱 WebSocket Notification Dashboard initialized', 'info');
    }

    initializeElements() {
        // Connection elements
        this.connectBtn = document.getElementById('connectBtn');
        this.disconnectBtn = document.getElementById('disconnectBtn');
        this.reconnectBtn = document.getElementById('reconnectBtn');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.statusIcon = document.getElementById('statusIcon');
        this.statusText = document.getElementById('statusText');
        this.connectionDetails = document.getElementById('connectionDetails');
        this.userIdDisplay = document.getElementById('userIdDisplay');
        this.sessionIdDisplay = document.getElementById('sessionIdDisplay');
        this.wsUrl = document.getElementById('wsUrl');
        this.authToken = document.getElementById('authToken');
        this.toggleToken = document.getElementById('toggleToken');
        this.tokenEye = document.getElementById('tokenEye');
        
        // Message elements
        this.messagesDiv = document.getElementById('messages');
        this.welcomeMessage = document.getElementById('welcomeMessage');
        this.clearMessagesBtn = document.getElementById('clearMessagesBtn');
        this.toggleDetailBtn = document.getElementById('toggleDetailBtn');
        this.messageCounter = document.getElementById('messageCounter');
        this.uptime = document.getElementById('uptime');
        
        // Test elements
        this.sendPingBtn = document.getElementById('sendPingBtn');
    }

    setupEventListeners() {
        // Connection controls
        this.connectBtn.addEventListener('click', () => this.connect());
        this.disconnectBtn.addEventListener('click', () => this.disconnect());
        this.reconnectBtn.addEventListener('click', () => this.reconnect());
        
        // Token visibility toggle
        this.toggleToken.addEventListener('click', () => this.toggleTokenVisibility());
        
        // Message controls
        this.clearMessagesBtn.addEventListener('click', () => this.clearMessages());
        this.toggleDetailBtn.addEventListener('click', () => this.toggleDetailView());
        
        // Test controls
        this.sendPingBtn.addEventListener('click', () => this.sendPing());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                switch (e.key) {
                    case ' ':
                        if (this.isConnected) {
                            e.preventDefault();
                            this.sendPing();
                        }
                        break;
                    case 'l':
                        e.preventDefault();
                        this.clearMessages();
                        break;
                }
            }
        });
    }

    // UI Helper Methods
    toggleTokenVisibility() {
        const isPassword = this.authToken.type === 'password';
        this.authToken.type = isPassword ? 'text' : 'password';
        this.tokenEye.textContent = isPassword ? '🙈' : '👁️';
    }

    startUptime() {
        setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const hours = Math.floor(elapsed / 3600000).toString().padStart(2, '0');
            const minutes = Math.floor((elapsed % 3600000) / 60000).toString().padStart(2, '0');
            const seconds = Math.floor((elapsed % 60000) / 1000).toString().padStart(2, '0');
            this.uptime.textContent = `${hours}:${minutes}:${seconds}`;
        }, 1000);
    }

    // Connection Management
    connect() {
        if (this.isConnected) {
            this.logMessage('⚠️ Already connected', 'warning');
            return;
        }

        const url = this.wsUrl.value.trim();
        if (!url) {
            this.logMessage('❌ Please enter WebSocket URL', 'error');
            return;
        }

        // Build WebSocket URL with token if provided
        let wsUrl = url;
        const token = this.authToken.value.trim();
        if (token) {
            const separator = url.includes('?') ? '&' : '?';
            wsUrl = `${url}${separator}token=${encodeURIComponent(token)}`;
        }

        this.logMessage(`🔌 Connecting to ${url}${token ? ' (with auth token)' : ' (anonymous)'}...`, 'info');
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = (event) => this.onOpen(event);
            this.socket.onmessage = (event) => this.onMessage(event);
            this.socket.onclose = (event) => this.onClose(event);
            this.socket.onerror = (event) => this.onError(event);
            
        } catch (error) {
            this.logMessage(`❌ Connection failed: ${error.message}`, 'error');
        }
    }

    disconnect() {
        if (this.socket) {
            this.logMessage('🔌 Disconnecting...', 'info');
            this.socket.close(1000, 'User requested disconnect');
        }
    }

    reconnect() {
        this.disconnect();
        setTimeout(() => this.connect(), 1000);
    }

    // WebSocket Event Handlers
    onOpen(event) {
        this.isConnected = true;
        this.updateConnectionStatus('Connected', 'connected');
        this.hideWelcomeMessage();
        this.logMessage('✅ WebSocket connected successfully', 'success');
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.handleIncomingMessage(data);
        } catch (error) {
            this.logMessage(`❌ Failed to parse message: ${error.message}`, 'error');
            if (this.detailedView) {
                this.logMessage(`Raw data: ${event.data}`, 'raw');
            }
        }
    }

    onClose(event) {
        this.isConnected = false;
        this.sessionId = null;
        this.userId = null;
        this.updateConnectionStatus('Disconnected', 'disconnected');
        this.hideConnectionDetails();
        
        const reason = event.reason || 'No reason provided';
        const wasClean = event.wasClean ? '(clean)' : '(unclean)';
        this.logMessage(`🔌 Connection closed ${wasClean}: ${reason} (code: ${event.code})`, 'warning');
    }

    onError(event) {
        this.logMessage('❌ WebSocket error occurred', 'error');
        console.error('WebSocket error:', event);
    }

    // Message Handling
    handleIncomingMessage(data) {
        const messageType = data.type;
        
        if (this.detailedView) {
            this.logMessage(`📥 Received: ${messageType}`, 'received');
        }
        
        switch (messageType) {
            case 'connection_established':
                this.handleConnectionEstablished(data.data);
                break;
                
            case 'pong':
                this.logMessage(`🏓 Pong received`, 'success');
                if (this.detailedView) {
                    this.logMessage(`   Session: ${data.data.session_id}`, 'success');
                    this.logMessage(`   Time: ${data.data.timestamp}`, 'success');
                }
                break;
                
            case 'notification':
                this.handleNotification(data.data);
                break;
                
            case 'error':
                this.logMessage(`❌ Server error: ${data.data.message}`, 'error');
                break;
                
            default:
                this.logMessage(`❓ Unknown message type: ${messageType}`, 'warning');
                if (this.detailedView) {
                    this.logMessage(JSON.stringify(data, null, 2), 'raw');
                }
        }
    }

    handleConnectionEstablished(data) {
        this.userId = data.user_id;
        this.sessionId = data.session_id;
        
        this.logMessage(`🎉 Connection established successfully!`, 'success');
        this.logMessage(`   User ID: ${data.user_id}`, 'success');
        this.logMessage(`   Session ID: ${data.session_id}`, 'success');
        this.logMessage(`   Message: ${data.message}`, 'success');
        this.logMessage('💡 Try keyboard shortcuts: Ctrl+Space (ping), Ctrl+L (clear)', 'info');
        
        this.showConnectionDetails();
    }

    handleNotification(notificationData) {
        this.logMessage(`🔔 NEW NOTIFICATION RECEIVED`, 'notification');
        
        if (this.detailedView) {
            Object.entries(notificationData).forEach(([key, value]) => {
                this.logMessage(`   ${key}: ${value}`, 'notification');
            });
        } else {
            const summary = notificationData.message || notificationData.verb || 'New notification';
            this.logMessage(`   ${summary}`, 'notification');
        }
        
        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('New Notification', {
                body: notificationData.message || notificationData.verb || 'You have a new notification',
                icon: '/static/icon-notification.png'
            });
        }
    }

    // WebSocket Messaging
    sendMessage(message) {
        if (!this.isConnected || !this.socket) {
            this.logMessage('❌ Not connected to WebSocket', 'error');
            return false;
        }

        try {
            this.socket.send(JSON.stringify(message));
            if (this.detailedView) {
                this.logMessage(`📤 Sent: ${JSON.stringify(message)}`, 'sent');
            }
            return true;
        } catch (error) {
            this.logMessage(`❌ Failed to send message: ${error.message}`, 'error');
            return false;
        }
    }

    sendPing() {
        if (this.sendMessage({ type: 'ping', timestamp: new Date().toISOString() })) {
            this.logMessage('🏓 Ping sent', 'sent');
        }
    }

    // UI Helpers
    updateConnectionStatus(status, className) {
        this.statusText.textContent = status;
        this.statusIcon.textContent = className === 'connected' ? '✅' : '❌';
        this.connectionStatus.className = `font-bold text-sm flex items-center justify-center gap-2 ${
            className === 'connected' ? 'text-green-400' : 'text-red-400'
        }`;
    }

    showConnectionDetails() {
        this.userIdDisplay.textContent = this.userId || '-';
        this.sessionIdDisplay.textContent = this.sessionId ? this.sessionId.slice(0, 8) + '...' : '-';
        this.connectionDetails.classList.remove('hidden');
    }

    hideConnectionDetails() {
        this.connectionDetails.classList.add('hidden');
    }

    hideWelcomeMessage() {
        if (this.welcomeMessage) {
            this.welcomeMessage.style.display = 'none';
        }
    }

    logMessage(message, type = 'info') {
        this.displayMessage(message, type);
    }

    displayMessage(message, type = 'info') {
        const count = ++this.messageCount;
        
        const colors = {
            info: 'text-blue-400',
            success: 'text-green-400',
            warning: 'text-yellow-400',
            error: 'text-red-400',
            notification: 'text-purple-400',
            sent: 'text-gray-400',
            received: 'text-cyan-300',
            raw: 'text-gray-500'
        };

        const colorClass = colors[type] || 'text-gray-300';
        
        const messageElement = document.createElement('div');
        messageElement.className = `message-item mb-2 ${colorClass} transition-opacity duration-300 text-center px-4 py-1 rounded`;
        
        messageElement.innerHTML = `<span class="inline-block">${message}</span>`;
        
        this.messagesDiv.appendChild(messageElement);
        this.messageCounter.textContent = this.messageCount;
        
        // Animate new message
        messageElement.style.opacity = '0';
        setTimeout(() => messageElement.style.opacity = '1', 50);
    }

    clearMessages() {
        this.messagesDiv.innerHTML = '';
        this.messageCount = 0;
        this.messageCounter.textContent = '0';
        this.logMessage('🧹 Messages cleared', 'info');
    }

    toggleDetailView() {
        this.detailedView = !this.detailedView;
        this.toggleDetailBtn.textContent = this.detailedView ? '🔍 Simple View' : '🔍 Detailed View';
        this.logMessage(`🔍 Detail view: ${this.detailedView ? 'ON' : 'OFF'}`, 'info');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.notificationWS = new NotificationWebSocket();
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('Notification permission granted');
            }
        });
    }
});