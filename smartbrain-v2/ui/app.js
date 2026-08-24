/**
 * Engineering Memory Graph - Main Application
 */
const App = (() => {
    // State
    let conversations = [];
    let currentConversationId = null;
    let currentView = 'chat';
    let isLoading = false;

    // DOM Elements
    const elements = {};

    function init() {
        cacheElements();
        loadConversations();
        bindEvents();
        renderConversationList();
        autoResizeTextarea();
    }

    function cacheElements() {
        elements.sidebar = document.getElementById('sidebar');
        elements.mobileToggle = document.getElementById('mobileToggle');
        elements.sidebarOverlay = document.getElementById('sidebarOverlay');
        elements.newChatBtn = document.getElementById('newChatBtn');
        elements.chatTab = document.getElementById('chatTab');
        elements.searchTab = document.getElementById('searchTab');
        elements.conversationList = document.getElementById('conversationList');
        elements.chatView = document.getElementById('chatView');
        elements.searchView = document.getElementById('searchView');
        elements.serviceDetailView = document.getElementById('serviceDetailView');
        elements.chatMessages = document.getElementById('chatMessages');
        elements.welcomeScreen = document.getElementById('welcomeScreen');
        elements.chatInput = document.getElementById('chatInput');
        elements.sendBtn = document.getElementById('sendBtn');
        elements.searchInput = document.getElementById('searchInput');
        elements.searchResults = document.getElementById('searchResults');
        elements.serviceDetailContent = document.getElementById('serviceDetailContent');
        elements.backToSearch = document.getElementById('backToSearch');
        elements.settingsBtn = document.getElementById('settingsBtn');
        elements.settingsModal = document.getElementById('settingsModal');
        elements.closeSettings = document.getElementById('closeSettings');
        elements.cancelSettings = document.getElementById('cancelSettings');
        elements.saveSettings = document.getElementById('saveSettings');
        elements.apiKeyInput = document.getElementById('apiKeyInput');
        elements.apiBaseUrl = document.getElementById('apiBaseUrl');
    }

    function bindEvents() {
        // Mobile sidebar
        elements.mobileToggle.addEventListener('click', toggleSidebar);
        elements.sidebarOverlay.addEventListener('click', closeSidebar);

        // Navigation
        elements.newChatBtn.addEventListener('click', newChat);
        elements.chatTab.addEventListener('click', () => switchView('chat'));
        elements.searchTab.addEventListener('click', () => switchView('search'));

        // Chat
        elements.chatInput.addEventListener('input', onChatInputChange);
        elements.chatInput.addEventListener('keydown', onChatKeydown);
        elements.sendBtn.addEventListener('click', sendMessage);

        // Suggestions
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                elements.chatInput.value = chip.dataset.question;
                onChatInputChange();
                sendMessage();
            });
        });

        // Search
        let searchTimeout;
        elements.searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => performSearch(elements.searchInput.value), 300);
        });
        elements.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                clearTimeout(searchTimeout);
                performSearch(elements.searchInput.value);
            }
        });

        // Service detail
        elements.backToSearch.addEventListener('click', () => showView('searchView'));

        // Settings
        elements.settingsBtn.addEventListener('click', openSettings);
        elements.closeSettings.addEventListener('click', closeSettings);
        elements.cancelSettings.addEventListener('click', closeSettings);
        elements.saveSettings.addEventListener('click', saveSettings);
        elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === elements.settingsModal) closeSettings();
        });
    }

    // ===== Sidebar & Navigation =====

    function toggleSidebar() {
        elements.sidebar.classList.toggle('open');
        elements.sidebarOverlay.classList.toggle('active');
    }

    function closeSidebar() {
        elements.sidebar.classList.remove('open');
        elements.sidebarOverlay.classList.remove('active');
    }

    function switchView(view) {
        currentView = view;
        elements.chatTab.classList.toggle('active', view === 'chat');
        elements.searchTab.classList.toggle('active', view === 'search');

        if (view === 'chat') {
            showView('chatView');
        } else {
            showView('searchView');
        }
        closeSidebar();
    }

    function showView(viewId) {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById(viewId).classList.add('active');
    }

    // ===== Conversations =====

    function loadConversations() {
        try {
            const stored = localStorage.getItem('emg_conversations');
            conversations = stored ? JSON.parse(stored) : [];
        } catch {
            conversations = [];
        }
    }

    function saveConversations() {
        localStorage.setItem('emg_conversations', JSON.stringify(conversations));
    }

    function newChat() {
        currentConversationId = null;
        elements.chatMessages.innerHTML = '';
        elements.chatMessages.appendChild(elements.welcomeScreen || createWelcomeScreen());
        showWelcomeScreen();
        elements.chatInput.value = '';
        onChatInputChange();
        renderConversationList();
        switchView('chat');
    }

    function showWelcomeScreen() {
        const welcome = document.getElementById('welcomeScreen');
        if (welcome) welcome.style.display = 'flex';
    }

    function hideWelcomeScreen() {
        const welcome = document.getElementById('welcomeScreen');
        if (welcome) welcome.style.display = 'none';
    }

    function createConversation(firstMessage) {
        const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
        const title = firstMessage.length > 40 ? firstMessage.slice(0, 40) + '...' : firstMessage;
        const conversation = {
            id,
            title,
            messages: [],
            createdAt: Date.now()
        };
        conversations.unshift(conversation);
        saveConversations();
        currentConversationId = id;
        renderConversationList();
        return conversation;
    }

    function getCurrentConversation() {
        return conversations.find(c => c.id === currentConversationId);
    }

    function loadConversation(id) {
        currentConversationId = id;
        const conv = getCurrentConversation();
        if (!conv) return;

        hideWelcomeScreen();
        elements.chatMessages.innerHTML = '';

        conv.messages.forEach(msg => {
            appendMessage(msg.role, msg.content, msg.citations, false);
        });

        renderConversationList();
        switchView('chat');
        scrollToBottom();
    }

    function deleteConversation(id, event) {
        event.stopPropagation();
        conversations = conversations.filter(c => c.id !== id);
        saveConversations();

        if (currentConversationId === id) {
            newChat();
        }
        renderConversationList();
    }

    function renderConversationList() {
        elements.conversationList.innerHTML = '';
        conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conversation-item' + (conv.id === currentConversationId ? ' active' : '');
            item.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                    <path d="M2 3a1 1 0 011-1h10a1 1 0 011 1v8a1 1 0 01-1 1H5l-3 3V3z" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                <span class="conv-title">${escapeHtml(conv.title)}</span>
                <button class="conv-delete" title="Delete conversation">&times;</button>
            `;
            item.addEventListener('click', () => loadConversation(conv.id));
            item.querySelector('.conv-delete').addEventListener('click', (e) => deleteConversation(conv.id, e));
            elements.conversationList.appendChild(item);
        });
    }

    // ===== Chat =====

    function onChatInputChange() {
        const hasText = elements.chatInput.value.trim().length > 0;
        elements.sendBtn.disabled = !hasText || isLoading;
        autoResizeTextarea();
    }

    function onChatKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!elements.sendBtn.disabled) {
                sendMessage();
            }
        }
    }

    function autoResizeTextarea() {
        const textarea = elements.chatInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }

    async function sendMessage() {
        const question = elements.chatInput.value.trim();
        if (!question || isLoading) return;

        // Create conversation if needed
        if (!currentConversationId) {
            createConversation(question);
        }

        hideWelcomeScreen();

        // Add user message
        const conv = getCurrentConversation();
        conv.messages.push({ role: 'user', content: question });
        saveConversations();
        appendMessage('user', question);

        // Clear input
        elements.chatInput.value = '';
        onChatInputChange();

        // Show loading
        isLoading = true;
        elements.sendBtn.disabled = true;
        const loadingEl = appendLoading();

        try {
            // Build history from last 5 messages for short-term memory
            const conv = getCurrentConversation();
            const history = (conv.messages || []).slice(-5).map(m => ({
                role: m.role,
                content: m.content
            }));

            const response = await ApiClient.ask(question, history);
            removeLoading(loadingEl);

            const answer = response.answer || response.response || response.text || JSON.stringify(response);
            const citations = response.citations || response.sources || [];

            conv.messages.push({ role: 'assistant', content: answer, citations });
            saveConversations();
            appendMessage('assistant', answer, citations);
        } catch (error) {
            removeLoading(loadingEl);
            const errorMsg = `**Error:** ${error.message}`;
            conv.messages.push({ role: 'assistant', content: errorMsg });
            saveConversations();
            appendMessage('assistant', errorMsg);
        } finally {
            isLoading = false;
            onChatInputChange();
            scrollToBottom();
        }
    }

    function appendMessage(role, content, citations = [], animate = true) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${role}`;
        if (!animate) messageEl.style.animation = 'none';

        const avatarContent = role === 'user' ? 'U' : 'E';
        const renderedContent = role === 'assistant' ? MarkdownRenderer.render(content) : escapeHtml(content).replace(/\n/g, '<br>');

        let citationsHtml = '';
        if (citations && citations.length > 0) {
            // Group similar citations & limit to 12 to keep the chip row tidy.
            const shown = citations.slice(0, 12);
            const chips = shown.map(c => {
                const sourceId = c.source_id || c.sourceId || '';
                const type = c.entity_type || c.type || 'Ref';
                const displayName =
                    c.name || c.title ||
                    (sourceId ? sourceId.split(':').slice(-1)[0] : 'ref');

                // Style classes per type for quick visual scanning.
                const typeClass = String(type).toLowerCase().replace(/[^a-z]/g, '');
                return `<span class="citation-chip chip-${typeClass}" title="${escapeHtml(sourceId)}">
                    <span class="chip-type">${escapeHtml(String(type))}</span>
                    ${escapeHtml(String(displayName))}
                </span>`;
            }).join('');
            const more = citations.length > shown.length
                ? `<span class="citation-more">+${citations.length - shown.length} more</span>`
                : '';
            citationsHtml = `<div class="citations">${chips}${more}</div>`;
        }

        messageEl.innerHTML = `
            <div class="message-inner">
                <div class="message-avatar">${avatarContent}</div>
                <div class="message-body">
                    <div class="message-content">${renderedContent}</div>
                    ${citationsHtml}
                </div>
            </div>
        `;

        elements.chatMessages.appendChild(messageEl);
        scrollToBottom();
        return messageEl;
    }

    function appendLoading() {
        const loadingEl = document.createElement('div');
        loadingEl.className = 'message assistant';
        loadingEl.innerHTML = `
            <div class="message-inner">
                <div class="message-avatar">E</div>
                <div class="message-body">
                    <div class="loading-indicator">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                </div>
            </div>
        `;
        elements.chatMessages.appendChild(loadingEl);
        scrollToBottom();
        return loadingEl;
    }

    function removeLoading(el) {
        if (el && el.parentNode) {
            el.parentNode.removeChild(el);
        }
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        });
    }

    // ===== Search =====

    async function performSearch(query) {
        if (!query || query.trim().length === 0) {
            elements.searchResults.innerHTML = '';
            return;
        }

        elements.searchResults.innerHTML = '<div class="search-loading">Searching...</div>';

        try {
            const results = await ApiClient.search(query.trim());
            renderSearchResults(results);
        } catch (error) {
            elements.searchResults.innerHTML = `<div class="search-empty">Error: ${escapeHtml(error.message)}</div>`;
        }
    }

    function renderSearchResults(results) {
        const items = results.results || results.items || results;

        if (!items || items.length === 0) {
            elements.searchResults.innerHTML = '<div class="search-empty">No results found</div>';
            return;
        }

        elements.searchResults.innerHTML = '';
        (Array.isArray(items) ? items : [items]).forEach(item => {
            const el = document.createElement('div');
            el.className = 'search-result-item';

            const name = item.name || item.title || 'Unknown';
            const type = item.type || item.entity_type || 'entity';
            const description = item.description || item.summary || '';

            el.innerHTML = `
                <span class="result-type">${escapeHtml(type)}</span>
                <div class="result-name">${escapeHtml(name)}</div>
                ${description ? `<div class="result-description">${escapeHtml(description)}</div>` : ''}
            `;

            el.addEventListener('click', () => viewServiceDetail(name));
            elements.searchResults.appendChild(el);
        });
    }

    // ===== Service Detail =====

    async function viewServiceDetail(name) {
        showView('serviceDetailView');
        elements.serviceDetailContent.innerHTML = '<div class="search-loading">Loading...</div>';

        try {
            const service = await ApiClient.getService(name);
            renderServiceDetail(service);
        } catch (error) {
            elements.serviceDetailContent.innerHTML = `<div class="search-empty">Error loading service: ${escapeHtml(error.message)}</div>`;
        }
    }

    function renderServiceDetail(service) {
        const name = service.name || service.title || 'Unknown Service';
        const type = service.type || service.entity_type || 'service';
        const description = service.description || service.summary || 'No description available.';
        const properties = service.properties || service.metadata || {};
        const relationships = service.relationships || service.dependencies || [];

        let html = `
            <h1>${escapeHtml(name)}</h1>
            <span class="service-type-badge">${escapeHtml(type)}</span>
            <div class="detail-section">
                <h3>Description</h3>
                <p>${escapeHtml(description)}</p>
            </div>
        `;

        // Properties
        const propKeys = Object.keys(properties);
        if (propKeys.length > 0) {
            html += `<div class="detail-section"><h3>Properties</h3><div class="detail-tags">`;
            propKeys.forEach(key => {
                const val = properties[key];
                html += `<span class="detail-tag"><strong>${escapeHtml(key)}:</strong> ${escapeHtml(String(val))}</span>`;
            });
            html += `</div></div>`;
        }

        // Relationships
        if (relationships.length > 0) {
            html += `<div class="detail-section"><h3>Relationships</h3><div class="detail-tags">`;
            relationships.forEach(rel => {
                const relName = typeof rel === 'string' ? rel : (rel.target || rel.name || JSON.stringify(rel));
                const relType = typeof rel === 'object' ? (rel.type || rel.relationship || '') : '';
                html += `<span class="detail-tag">${relType ? escapeHtml(relType) + ': ' : ''}${escapeHtml(String(relName))}</span>`;
            });
            html += `</div></div>`;
        }

        elements.serviceDetailContent.innerHTML = html;
    }

    // ===== Settings =====

    function openSettings() {
        elements.apiKeyInput.value = localStorage.getItem('emg_api_key') || '';
        elements.apiBaseUrl.value = localStorage.getItem('emg_base_url') || '/';
        elements.settingsModal.classList.add('active');
        closeSidebar();
    }

    function closeSettings() {
        elements.settingsModal.classList.remove('active');
    }

    function saveSettings() {
        const apiKey = elements.apiKeyInput.value.trim();
        const baseUrl = elements.apiBaseUrl.value.trim() || '/';

        if (apiKey) {
            localStorage.setItem('emg_api_key', apiKey);
        } else {
            localStorage.removeItem('emg_api_key');
        }
        localStorage.setItem('emg_base_url', baseUrl);
        closeSettings();
    }

    // ===== Utilities =====

    function escapeHtml(text) {
        if (typeof text !== 'string') return '';
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return text.replace(/[&<>"']/g, c => map[c]);
    }

    function createWelcomeScreen() {
        const div = document.createElement('div');
        div.className = 'welcome-screen';
        div.id = 'welcomeScreen';
        div.innerHTML = `
            <div class="welcome-icon">
                <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                    <rect width="40" height="40" rx="8" fill="#10a37f"/>
                    <path d="M12 20l4 4 12-12" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <h1>Engineering Memory Graph</h1>
            <p>Ask questions about your engineering knowledge base, services, dependencies, and architecture.</p>
        `;
        return div;
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return { newChat, switchView };
})();
