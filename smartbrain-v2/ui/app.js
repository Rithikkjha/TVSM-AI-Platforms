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
        initTheme();
        loadConversations();
        bindEvents();
        renderConversationList();
        autoResizeTextarea();
        refreshAuthState();
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
        elements.themeToggle = document.getElementById('themeToggle');
        // Login state (Azure AD SSO)
        elements.accountUser = document.getElementById('accountUser');
        elements.accountName = document.getElementById('accountName');
        elements.accountEmail = document.getElementById('accountEmail');
        elements.signInLink = document.getElementById('signInLink');
        elements.signOutLink = document.getElementById('signOutLink');
        elements.loginOverlay = document.getElementById('loginOverlay');
        elements.loginBtn = document.getElementById('loginBtn');
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

        // Theme toggle (light / dark)
        if (elements.themeToggle) {
            elements.themeToggle.addEventListener('click', toggleTheme);
        }

        // Login (Azure AD SSO)
        if (elements.signInLink) {
            elements.signInLink.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = ApiClient.loginUrl();
            });
        }
        if (elements.loginBtn) {
            elements.loginBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = ApiClient.loginUrl();
            });
        }
        if (elements.signOutLink) {
            elements.signOutLink.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = ApiClient.logoutUrl();
            });
        }
    }

    // ===== Auth / login state =====

    async function refreshAuthState() {
        const user = await ApiClient.getMe();
        if (user) {
            elements.accountName.textContent = user.name || user.preferred_username || 'Signed in';
            elements.accountEmail.textContent = user.email || user.preferred_username || '';
            elements.accountUser.style.display = '';
            elements.signInLink.style.display = 'none';
            if (elements.loginOverlay) elements.loginOverlay.style.display = 'none';
            // Fresh start whenever a different user signs in on this browser.
            clearHistoryOnNewLogin(user.oid || user.email || user.preferred_username);
        } else {
            elements.accountUser.style.display = 'none';
            elements.signInLink.style.display = '';
            // Not signed in: show the full-screen sign-in page.
            if (elements.loginOverlay) elements.loginOverlay.style.display = 'flex';
        }
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

    // Conversations older than this are dropped automatically on load.
    const CONVERSATION_TTL_DAYS = 30;
    const CONVERSATION_TTL_MS = CONVERSATION_TTL_DAYS * 24 * 60 * 60 * 1000;

    function loadConversations() {
        try {
            const stored = localStorage.getItem('emg_conversations');
            conversations = stored ? JSON.parse(stored) : [];
        } catch {
            conversations = [];
        }
        // 30-day auto-expiry: drop any conversation last touched over the TTL ago.
        const cutoff = Date.now() - CONVERSATION_TTL_MS;
        const before = conversations.length;
        conversations = conversations.filter(c => {
            const ts = c.updatedAt || c.createdAt || 0;
            return ts >= cutoff;
        });
        if (conversations.length !== before) {
            saveConversations();
        }
    }

    // Fresh start per login: when the signed-in user changes (new login), wipe
    // any locally stored conversations so each session begins clean. Called
    // after auth state resolves. For the login-disabled case the user id is a
    // fixed sentinel, so this becomes a one-time purge on first load of the
    // new build (the stored id starts empty).
    function clearHistoryOnNewLogin(userId) {
        const key = 'emg_last_user';
        const prev = localStorage.getItem(key);
        const current = userId || 'anonymous';
        if (prev !== current) {
            conversations = [];
            saveConversations();
            localStorage.setItem(key, current);
            currentConversationId = null;
            if (elements.conversationList) renderConversationList();
            if (currentView === 'chat') newChat();
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
            createdAt: Date.now(),
            updatedAt: Date.now()
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
        conv.updatedAt = Date.now();
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

    // Cached service list (fetched once per session). The Search tab filters
    // this list locally by name + alias; there are only ~47 services.
    let serviceCache = null;

    async function ensureServices() {
        if (serviceCache) return serviceCache;
        const data = await ApiClient.listServices();
        serviceCache = (data && data.services) || [];
        return serviceCache;
    }

    async function performSearch(query) {
        const q = (query || '').trim().toLowerCase();
        if (q.length === 0) {
            elements.searchResults.innerHTML = '';
            return;
        }

        elements.searchResults.innerHTML = '<div class="search-loading">Searching...</div>';

        let services;
        try {
            services = await ensureServices();
        } catch (error) {
            elements.searchResults.innerHTML = `<div class="search-empty">Error: ${escapeHtml(error.message)}</div>`;
            return;
        }

        // Match the query as a case-insensitive substring of the service name,
        // display name, or any of its aliases.
        const matches = services.filter(s => {
            const name = (s.name || '').toLowerCase();
            const display = (s.display_name || '').toLowerCase();
            const aliases = (s.aliases || []).map(a => (a || '').toLowerCase());
            return name.includes(q) || display.includes(q) || aliases.some(a => a.includes(q));
        });

        renderSearchResults(matches);
    }

    function renderSearchResults(services) {
        if (!services || services.length === 0) {
            elements.searchResults.innerHTML = '<div class="search-empty">No services found</div>';
            return;
        }

        elements.searchResults.innerHTML = '';
        services.forEach(service => {
            const el = document.createElement('div');
            el.className = 'search-result-item';

            // The service `name` is what GET /v1/services/{name} resolves.
            const name = service.name || service.display_name || '';
            const title = service.display_name || service.name || 'Unknown';
            const type = service.domain || 'service';
            const description = service.summary || '';

            el.innerHTML = `
                <span class="result-type">${escapeHtml(type)}</span>
                <div class="result-name">${escapeHtml(title)}</div>
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

    function renderServiceDetail(data) {
        // GET /v1/services/{name} returns a wrapper:
        //   { service: {name, summary, domain, languages, frameworks, repo_url,
        //               default_branch, aliases, ...},
        //     owners, upstream_dependencies, downstream_dependents,
        //     linked_tickets, documents, staleness }
        const svc = (data && data.service) ? data.service : (data || {});
        const name = svc.name || svc.display_name || 'Unknown Service';
        const domain = svc.domain || svc.type || 'service';
        const description = svc.summary || svc.description || 'No description available.';

        let html = `
            <h1>${escapeHtml(name)}</h1>
            <span class="service-type-badge">${escapeHtml(domain)}</span>
            <div class="detail-section">
                <h3>Summary</h3>
                <p>${escapeHtml(description)}</p>
            </div>
        `;

        // Key properties (only show the ones that exist)
        const propRows = [];
        const addProp = (label, val) => {
            if (val === undefined || val === null || val === '' ||
                (Array.isArray(val) && val.length === 0)) return;
            const text = Array.isArray(val) ? val.join(', ') : String(val);
            propRows.push(`<span class="detail-tag"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(text)}</span>`);
        };
        addProp('Languages', svc.languages);
        addProp('Frameworks', svc.frameworks);
        addProp('Default branch', svc.default_branch);
        addProp('Repository', svc.repo_url);
        if (propRows.length > 0) {
            html += `<div class="detail-section"><h3>Details</h3><div class="detail-tags">${propRows.join('')}</div></div>`;
        }

        // Aliases
        if (Array.isArray(svc.aliases) && svc.aliases.length > 0) {
            html += `<div class="detail-section"><h3>Also known as</h3><div class="detail-tags">`
                + svc.aliases.map(a => `<span class="detail-tag">${escapeHtml(String(a))}</span>`).join('')
                + `</div></div>`;
        }

        // Dependency sections
        const refName = (r) => r.name || r.display_name || r.source_id || r.key || 'unknown';
        const depSection = (title, list) => {
            if (!Array.isArray(list) || list.length === 0) return '';
            return `<div class="detail-section"><h3>${escapeHtml(title)}</h3><div class="detail-tags">`
                + list.map(r => `<span class="detail-tag">${escapeHtml(String(refName(r)))}</span>`).join('')
                + `</div></div>`;
        };
        html += depSection('Depends on', data.upstream_dependencies);
        html += depSection('Depended on by', data.downstream_dependents);
        html += depSection('Owners', data.owners);

        elements.serviceDetailContent.innerHTML = html;
    }

    // ===== Theme (light / dark) =====

    function applyTheme(theme) {
        const dark = theme === 'dark';
        document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
        const label = document.querySelector('#themeToggle .theme-label');
        if (label) label.textContent = dark ? 'Light mode' : 'Dark mode';
    }

    function initTheme() {
        // Stored choice wins; otherwise follow the OS preference.
        let theme = localStorage.getItem('emg_theme');
        if (!theme) {
            theme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
                ? 'dark' : 'light';
        }
        applyTheme(theme);
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem('emg_theme', next);
        applyTheme(next);
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
                <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                    <defs>
                        <linearGradient id="brainGrad2" x1="0" y1="0" x2="56" y2="56" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#10b981"/>
                            <stop offset="1" stop-color="#059669"/>
                        </linearGradient>
                    </defs>
                    <rect width="56" height="56" rx="14" fill="url(#brainGrad2)"/>
                    <circle cx="20" cy="22" r="3" fill="white"/>
                    <circle cx="36" cy="20" r="3" fill="white"/>
                    <circle cx="28" cy="36" r="3" fill="white"/>
                    <path d="M20 22L36 20M36 20L28 36M28 36L20 22" stroke="white" stroke-width="1.6" stroke-linecap="round" opacity="0.85"/>
                </svg>
            </div>
            <h1>SmartBrain</h1>
            <p>Ask about your engineering systems — services, APIs, dependencies, data flows, and the knowledge behind them.</p>
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
