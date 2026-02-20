/* ═══════════════════════════════════════════════════════════
   LEGAL AI – JUDICIAL COSMOS INTERFACE
   JavaScript Application Logic
   Version: 2.0 (2026)
   ═══════════════════════════════════════════════════════════ */

(function() {
    'use strict';

    /* ═══════════════════════════════════════════════════════════
       STATE MANAGEMENT
       ═══════════════════════════════════════════════════════════ */

    const AppState = {
        currentSessionId: null,
        sessions: [],
        isLoading: false,
        isMobile: window.innerWidth < 768,
        hasCustomCursor: !('ontouchstart' in window) && window.innerWidth >= 768
    };

    /* ═══════════════════════════════════════════════════════════
       DOM ELEMENTS
       ═══════════════════════════════════════════════════════════ */

    const DOM = {
        // Intro
        introOverlay: document.getElementById('introOverlay'),
        
        // Cursor
        cursorOuter: document.getElementById('cursorOuter'),
        cursorInner: document.getElementById('cursorInner'),
        
        // Header
        scalesIcon: document.getElementById('scalesIcon'),
        btnNewConsultation: document.getElementById('btnNewConsultation'),
        
        // Sidebar
        sidebar: document.getElementById('cosmicSidebar'),
        sidebarSessions: document.getElementById('sidebarSessions'),
        sidebarClose: document.getElementById('sidebarClose'),
        hamburgerMenu: document.getElementById('hamburgerMenu'),
        
        // Main chat
        chatContainer: document.getElementById('chatContainer'),
        emptyState: document.getElementById('emptyState'),
        messagesArea: document.getElementById('messagesArea'),
        
        // Input
        textarea: document.getElementById('cosmicTextarea'),
        btnSend: document.getElementById('btnSend'),
        charCounter: document.getElementById('charCounter'),
        charCount: document.getElementById('charCount'),
        
        // Disclaimer
        disclaimerBanner: document.getElementById('disclaimerBanner'),
        disclaimerClose: document.getElementById('disclaimerClose')
    };

    /* ═══════════════════════════════════════════════════════════
       CINEMATIC INTRO SEQUENCE
       ═══════════════════════════════════════════════════════════ */

    function initCinematicIntro() {
        // Check if user prefers reduced motion
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            DOM.introOverlay.style.display = 'none';
            initApp();
            return;
        }

        // Sequence timeline (2.5s total)
        setTimeout(() => {
            DOM.introOverlay.classList.add('fade-out');
        }, 2000);

        setTimeout(() => {
            DOM.introOverlay.style.display = 'none';
            initApp();
        }, 2800);
    }

    /* ═══════════════════════════════════════════════════════════
       CUSTOM CURSOR
       ═══════════════════════════════════════════════════════════ */

    function initCustomCursor() {
        if (!AppState.hasCustomCursor) return;

        DOM.cursorOuter.style.display = 'block';
        DOM.cursorInner.style.display = 'block';

        let mouseX = 0, mouseY = 0;
        let outerX = 0, outerY = 0;
        let innerX = 0, innerY = 0;

        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        // Smooth follow animation
        function animateCursor() {
            // Inner cursor (instant)
            innerX = mouseX;
            innerY = mouseY;
            DOM.cursorInner.style.left = innerX + 'px';
            DOM.cursorInner.style.top = innerY + 'px';

            // Outer cursor (lagged)
            outerX += (mouseX - outerX) * 0.15;
            outerY += (mouseY - outerY) * 0.15;
            DOM.cursorOuter.style.left = outerX + 'px';
            DOM.cursorOuter.style.top = outerY + 'px';

            requestAnimationFrame(animateCursor);
        }

        animateCursor();

        // Hover effect on interactive elements
        const interactiveElements = 'button, a, .session-item, .prompt-chip, textarea';
        
        document.addEventListener('mouseover', (e) => {
            if (e.target.closest(interactiveElements)) {
                DOM.cursorOuter.classList.add('hover');
            }
        });

        document.addEventListener('mouseout', (e) => {
            if (e.target.closest(interactiveElements)) {
                DOM.cursorOuter.classList.remove('hover');
            }
        });
    }

    /* ═══════════════════════════════════════════════════════════
       STAR FIELD GENERATION
       ═══════════════════════════════════════════════════════════ */

    function generateStarField() {
        const starField = document.getElementById('starField');
        const starCount = AppState.isMobile ? 75 : 150;

        for (let i = 0; i < starCount; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 3 + 's';
            star.style.animationDuration = (2 + Math.random() * 2) + 's';
            
            // Random sizes
            const size = Math.random() > 0.7 ? 2 : 1;
            star.style.width = size + 'px';
            star.style.height = size + 'px';
            
            starField.appendChild(star);
        }
    }

    /* ═══════════════════════════════════════════════════════════
       SESSION MANAGEMENT
       ═══════════════════════════════════════════════════════════ */

    async function loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            const data = await response.json();
            AppState.sessions = data.sessions || [];
            renderSessions();
        } catch (error) {
            console.error('Error loading sessions:', error);
            showError('Failed to load consultation history');
        }
    }

    function renderSessions() {
        DOM.sidebarSessions.innerHTML = '';

        if (AppState.sessions.length === 0) {
            DOM.sidebarSessions.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem;">
                    <i class="fas fa-balance-scale" style="font-size: 2rem; opacity: 0.3; margin-bottom: 1rem;"></i>
                    <p>No consultations yet</p>
                </div>
            `;
            return;
        }

        AppState.sessions.forEach((session, index) => {
            const sessionEl = createSessionElement(session);
            sessionEl.style.animationDelay = (index * 0.05) + 's';
            sessionEl.classList.add('slide-up');
            DOM.sidebarSessions.appendChild(sessionEl);
        });
    }

    function createSessionElement(session) {
        const div = document.createElement('div');
        div.className = 'session-item';
        div.dataset.sessionId = session.id;
        
        if (session.id === AppState.currentSessionId) {
            div.classList.add('active');
        }

        const timestamp = new Date(session.updated_at).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        div.innerHTML = `
            <div class="session-title">${escapeHtml(session.title)}</div>
            <div class="session-timestamp">${timestamp}</div>
            <button class="session-delete" data-session-id="${session.id}" title="Delete session">
                <i class="fas fa-trash"></i>
            </button>
        `;

        div.addEventListener('click', (e) => {
            if (!e.target.closest('.session-delete')) {
                loadSession(session.id);
                if (AppState.isMobile) {
                    closeSidebar();
                }
            }
        });

        const deleteBtn = div.querySelector('.session-delete');
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm('Delete this consultation? This action cannot be undone.')) {
                await deleteSession(session.id);
            }
        });

        return div;
    }

    async function createNewSession() {
        try {
            const response = await fetch('/api/new_session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                await loadSessions();
                loadSession(data.session_id);
            }
        } catch (error) {
            console.error('Error creating session:', error);
            showError('Failed to create new consultation');
        }
    }

    async function loadSession(sessionId) {
        AppState.currentSessionId = sessionId;
        
        // Update active state in sidebar
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.toggle('active', item.dataset.sessionId === sessionId);
        });

        try {
            const response = await fetch(`/api/chat/${sessionId}`);
            const data = await response.json();
            renderMessages(data.history || []);
            
            if (data.history && data.history.length > 0) {
                DOM.emptyState.style.display = 'none';
            } else {
                DOM.emptyState.style.display = 'flex';
            }
        } catch (error) {
            console.error('Error loading session:', error);
            showError('Failed to load consultation');
        }
    }

    async function deleteSession(sessionId) {
        try {
            const response = await fetch(`/api/delete_session/${sessionId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // Animate session removal
                const sessionEl = document.querySelector(`[data-session-id="${sessionId}"]`);
                if (sessionEl) {
                    sessionEl.style.height = sessionEl.offsetHeight + 'px';
                    sessionEl.style.overflow = 'hidden';
                    sessionEl.style.transition = 'all 0.3s ease-out';
                    setTimeout(() => {
                        sessionEl.style.height = '0';
                        sessionEl.style.padding = '0';
                        sessionEl.style.margin = '0';
                        sessionEl.style.opacity = '0';
                    }, 10);
                    
                    setTimeout(() => {
                        sessionEl.remove();
                    }, 300);
                }

                // If deleted session was active, clear chat
                if (sessionId === AppState.currentSessionId) {
                    AppState.currentSessionId = null;
                    DOM.messagesArea.innerHTML = '';
                    DOM.emptyState.style.display = 'flex';
                }

                await loadSessions();
            }
        } catch (error) {
            console.error('Error deleting session:', error);
            showError('Failed to delete consultation');
        }
    }

    /* ═══════════════════════════════════════════════════════════
       MESSAGE RENDERING
       ═══════════════════════════════════════════════════════════ */

    function renderMessages(messages) {
        DOM.messagesArea.innerHTML = '';

        messages.forEach((msg, index) => {
            const messageEl = createMessageElement(msg);
            messageEl.style.animationDelay = (index * 0.1) + 's';
            DOM.messagesArea.appendChild(messageEl);
        });

        scrollToBottom();
    }

    function createMessageElement(message) {
        const div = document.createElement('div');
        div.className = `message-bubble ${message.role}-message`;
        div.dataset.messageId = message.id;

        const isUser = message.role === 'user';
        const avatarContent = isUser ? 
            '<span>U</span>' : 
            `<svg viewBox="0 0 200 200" width="24" height="24">
                <defs>
                    <linearGradient id="avatarGrad${message.id}" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#c9a84c;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#4fc3f7;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <line x1="40" y1="100" x2="160" y2="100" stroke="url(#avatarGrad${message.id})" stroke-width="4"/>
                <line x1="100" y1="60" x2="100" y2="100" stroke="url(#avatarGrad${message.id})" stroke-width="4"/>
                <circle cx="60" cy="100" r="4" fill="#c9a84c"/>
                <line x1="60" y1="100" x2="60" y2="125" stroke="#c9a84c" stroke-width="3"/>
                <rect x="42" y="125" width="36" height="20" fill="none" stroke="#c9a84c" stroke-width="3" rx="3"/>
                <circle cx="140" cy="100" r="4" fill="#4fc3f7"/>
                <line x1="140" y1="100" x2="140" y2="125" stroke="#4fc3f7" stroke-width="3"/>
                <rect x="122" y="125" width="36" height="20" fill="none" stroke="#4fc3f7" stroke-width="3" rx="3"/>
                <circle cx="100" cy="60" r="5" fill="url(#avatarGrad${message.id})"/>
            </svg>`;

        const timestamp = new Date(message.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const editButton = isUser ? 
            `<button class="message-edit-btn" data-message-id="${message.id}">
                <i class="fas fa-edit"></i> Edit
            </button>` : '';

        // Render markdown for AI messages
        const content = isUser ? 
            escapeHtml(message.content) : 
            DOMPurify.sanitize(marked.parse(message.content));

        div.innerHTML = `
            <div class="message-avatar">${avatarContent}</div>
            <div class="message-wrapper">
                <div class="message-content">
                    <div class="message-text">${content}</div>
                </div>
                <div class="message-meta">
                    <span class="message-timestamp">${timestamp}</span>
                    ${editButton}
                </div>
            </div>
        `;

        // Add edit functionality
        if (isUser) {
            const editBtn = div.querySelector('.message-edit-btn');
            editBtn.addEventListener('click', () => editMessage(message.id, message.content));
        }

        return div;
    }

    function addUserMessage(content) {
        const message = {
            id: Date.now(),
            role: 'user',
            content: content,
            timestamp: new Date().toISOString()
        };

        const messageEl = createMessageElement(message);
        DOM.messagesArea.appendChild(messageEl);
        DOM.emptyState.style.display = 'none';
        scrollToBottom();
    }

    function addThinkingIndicator() {
        const div = document.createElement('div');
        div.className = 'thinking-indicator';
        div.id = 'thinkingIndicator';
        div.innerHTML = `
            <div class="message-avatar" style="background: var(--glass-1); border: 2px solid var(--neon-ice); animation: thinkingAvatarPulse 1.5s ease-in-out infinite;">
                <svg viewBox="0 0 200 200" width="24" height="24">
                    <defs>
                        <linearGradient id="thinkingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#c9a84c;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#4fc3f7;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <line x1="40" y1="100" x2="160" y2="100" stroke="url(#thinkingGrad)" stroke-width="4"/>
                    <line x1="100" y1="60" x2="100" y2="100" stroke="url(#thinkingGrad)" stroke-width="4"/>
                    <circle cx="100" cy="60" r="5" fill="url(#thinkingGrad)"/>
                </svg>
            </div>
            <div class="thinking-dots">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
            <span class="thinking-text" id="thinkingText">Analyzing legal precedents...</span>
        `;

        DOM.messagesArea.appendChild(div);
        scrollToBottom();

        // Cycle through thinking phrases
        const phrases = [
            'Analyzing legal precedents...',
            'Researching case law...',
            'Reviewing statutory provisions...',
            'Consulting legal databases...',
            'Formulating response...'
        ];
        
        let phraseIndex = 0;
        const phraseInterval = setInterval(() => {
            const thinkingText = document.getElementById('thinkingText');
            if (thinkingText) {
                phraseIndex = (phraseIndex + 1) % phrases.length;
                thinkingText.textContent = phrases[phraseIndex];
            } else {
                clearInterval(phraseInterval);
            }
        }, 2500);
    }

    function removeThinkingIndicator() {
        const indicator = document.getElementById('thinkingIndicator');
        if (indicator) {
            indicator.style.opacity = '0';
            indicator.style.transform = 'translateY(-10px)';
            indicator.style.transition = 'all 0.3s ease-out';
            setTimeout(() => indicator.remove(), 300);
        }
    }

    function addAIMessage(content) {
        const message = {
            id: Date.now(),
            role: 'assistant',
            content: content,
            timestamp: new Date().toISOString()
        };

        const messageEl = createMessageElement(message);
        DOM.messagesArea.appendChild(messageEl);
        
        // Typewriter effect for first 200 characters
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            typewriterEffect(messageEl.querySelector('.message-text'), content);
        }
        
        scrollToBottom();
    }

    function typewriterEffect(element, fullContent) {
        const sanitizedHtml = DOMPurify.sanitize(marked.parse(fullContent));
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = sanitizedHtml;
        const plainText = tempDiv.textContent || tempDiv.innerText;
        
        // Only typewrite first 200 chars for performance
        const typewriteLength = Math.min(200, plainText.length);
        const displayText = plainText.substring(0, typewriteLength);
        const remainingText = plainText.substring(typewriteLength);
        
        element.textContent = '';
        let charIndex = 0;
        
        const typeInterval = setInterval(() => {
            if (charIndex < displayText.length) {
                element.textContent += displayText[charIndex];
                charIndex++;
                scrollToBottom();
            } else {
                clearInterval(typeInterval);
                // Show full formatted content
                element.innerHTML = sanitizedHtml;
                scrollToBottom();
            }
        }, 15);
    }

    /* ═══════════════════════════════════════════════════════════
       MESSAGE SENDING
       ═══════════════════════════════════════════════════════════ */

    async function sendMessage() {
        if (!AppState.currentSessionId) {
            // Create new session if none exists
            await createNewSession();
            // Wait for session to be created
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        const message = DOM.textarea.value.trim();
        if (!message || AppState.isLoading) return;

        AppState.isLoading = true;
        DOM.btnSend.disabled = true;
        DOM.textarea.disabled = true;

        // Add user message to UI
        addUserMessage(message);
        
        // Clear textarea with sweep animation
        DOM.textarea.value = '';
        DOM.textarea.style.height = 'auto';
        updateCharCounter();

        // Show thinking indicator
        addThinkingIndicator();

        // Send pulse animation
        DOM.btnSend.classList.add('sending');
        setTimeout(() => DOM.btnSend.classList.remove('sending'), 600);

        try {
            const response = await fetch(`/api/chat/${AppState.currentSessionId}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            removeThinkingIndicator();

            if (data.status === 'success') {
                addAIMessage(data.response);
                await loadSessions(); // Refresh session list (title may have updated)
            } else {
                showError(data.error || 'Failed to get response');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            removeThinkingIndicator();
            showError('Failed to send message. Please try again.');
        } finally {
            AppState.isLoading = false;
            DOM.btnSend.disabled = false;
            DOM.textarea.disabled = false;
            DOM.textarea.focus();
        }
    }

    async function editMessage(messageId, currentContent) {
        const newContent = prompt('Edit your message:', currentContent);
        if (!newContent || newContent.trim() === currentContent) return;

        AppState.isLoading = true;

        try {
            const response = await fetch(`/api/chat/${AppState.currentSessionId}/edit/${messageId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: newContent.trim() })
            });

            const data = await response.json();

            if (data.status === 'success') {
                // Reload session to show updated messages
                await loadSession(AppState.currentSessionId);
            } else {
                showError(data.error || 'Failed to edit message');
            }
        } catch (error) {
            console.error('Error editing message:', error);
            showError('Failed to edit message');
        } finally {
            AppState.isLoading = false;
        }
    }

    /* ═══════════════════════════════════════════════════════════
       UI INTERACTIONS
       ═══════════════════════════════════════════════════════════ */

    function setupEventListeners() {
        // New consultation button
        DOM.btnNewConsultation.addEventListener('click', createNewSession);

        // Send button
        DOM.btnSend.addEventListener('click', sendMessage);

        // Textarea interactions
        DOM.textarea.addEventListener('input', () => {
            autoExpandTextarea();
            updateCharCounter();
            DOM.btnSend.disabled = !DOM.textarea.value.trim();
        });

        DOM.textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (DOM.textarea.value.trim()) {
                    sendMessage();
                }
            }
        });

        // Prompt chips (example queries)
        document.querySelectorAll('.prompt-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                DOM.textarea.value = chip.textContent;
                DOM.textarea.focus();
                autoExpandTextarea();
                updateCharCounter();
                DOM.btnSend.disabled = false;
            });
        });

        // Sidebar mobile
        DOM.hamburgerMenu.addEventListener('click', toggleSidebar);
        DOM.sidebarClose.addEventListener('click', closeSidebar);

        // Disclaimer banner
        DOM.disclaimerClose.addEventListener('click', () => {
            DOM.disclaimerBanner.classList.add('hidden');
            localStorage.setItem('disclaimerDismissed', 'true');
        });

        // Check if disclaimer was previously dismissed
        if (localStorage.getItem('disclaimerDismissed') === 'true') {
            DOM.disclaimerBanner.style.display = 'none';
        }

        // Resize handler
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                AppState.isMobile = window.innerWidth < 768;
                if (!AppState.isMobile) {
                    closeSidebar();
                }
            }, 250);
        });
    }

    function autoExpandTextarea() {
        DOM.textarea.style.height = 'auto';
        const maxHeight = 150;
        const newHeight = Math.min(DOM.textarea.scrollHeight, maxHeight);
        DOM.textarea.style.height = newHeight + 'px';
    }

    function updateCharCounter() {
        const count = DOM.textarea.value.length;
        DOM.charCount.textContent = count;
        
        if (count > 5000) {
            DOM.charCounter.style.display = 'block';
        } else {
            DOM.charCounter.style.display = 'none';
        }

        // Warning color when approaching limit
        if (count > 9000) {
            DOM.charCount.style.color = '#ff4d4d';
        } else if (count > 8000) {
            DOM.charCount.style.color = '#ffaa00';
        } else {
            DOM.charCount.style.color = 'var(--neon-gold)';
        }
    }

    function toggleSidebar() {
        DOM.sidebar.classList.toggle('open');
        DOM.hamburgerMenu.classList.toggle('active');
    }

    function closeSidebar() {
        DOM.sidebar.classList.remove('open');
        DOM.hamburgerMenu.classList.remove('active');
    }

    function scrollToBottom(smooth = true) {
        setTimeout(() => {
            DOM.messagesArea.lastElementChild?.scrollIntoView({ 
                behavior: smooth ? 'smooth' : 'auto',
                block: 'end'
            });
        }, 100);
    }

    function showError(message) {
        // Simple error display - could be enhanced with toast notifications
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: rgba(255, 77, 77, 0.15);
            border: 1px solid rgba(255, 77, 77, 0.5);
            border-radius: 12px;
            padding: 16px 24px;
            color: #ff4d4d;
            font-family: var(--font-body);
            font-size: 0.9rem;
            backdrop-filter: blur(24px);
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        `;
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle"></i> ${escapeHtml(message)}
        `;

        document.body.appendChild(errorDiv);

        setTimeout(() => {
            errorDiv.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => errorDiv.remove(), 300);
        }, 4000);
    }

    /* ═══════════════════════════════════════════════════════════
       UTILITY FUNCTIONS
       ═══════════════════════════════════════════════════════════ */

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /* ═══════════════════════════════════════════════════════════
       INITIALIZATION
       ═══════════════════════════════════════════════════════════ */

    function initApp() {
        console.log('🎯 Initializing Judicial Cosmos Interface...');
        
        // Setup all event listeners
        setupEventListeners();
        
        // Initialize custom cursor
        initCustomCursor();
        
        // Generate star field
        generateStarField();
        
        // Load sessions
        loadSessions();
        
        // Show empty state initially
        DOM.emptyState.style.display = 'flex';
        
        // Configure Marked.js options
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false
        });
        
        console.log('✨ Judicial Cosmos Interface Ready');
    }

    /* ═══════════════════════════════════════════════════════════
       APP START
       ═══════════════════════════════════════════════════════════ */

    // Wait for DOM to be fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCinematicIntro);
    } else {
        initCinematicIntro();
    }

    // Add CSS animations for error notifications
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
        @keyframes thinkingAvatarPulse {
            0%, 100% {
                box-shadow: 0 0 0 rgba(79, 195, 247, 0);
            }
            50% {
                box-shadow: 0 0 20px rgba(79, 195, 247, 0.5);
            }
        }
    `;
    document.head.appendChild(style);

})();
