// =====================================================
// LEGALAI – CHATGPT-STYLE CLIENT (FINAL STABLE)
// =====================================================

// ================= PRELOADER FIXED =================
window.addEventListener("load", () => {
    const preloader = document.getElementById("preloader");
    const sound = document.getElementById("gavelSound");

    if (!preloader) {
        window.legalChatApp = new LegalChatApp();
        return;
    }

    // Sound once, slightly delayed
    setTimeout(() => {
        if (sound) {
            sound.volume = 0.65;
            sound.play().catch(() => {});
        }
    }, 400);

    // Let animation loop visibly
    setTimeout(() => {
        preloader.style.opacity = "0";

        setTimeout(() => {
            preloader.remove();
            document.body.classList.remove("loading");

            // Start app ONLY ONCE
            window.legalChatApp = new LegalChatApp();
        }, 900);
    }, 2200);
});

// ================= CINEMATIC PRELOADER v2 =================
window.addEventListener("load", () => {
    const preloader = document.getElementById("preloader");
    const sound = document.getElementById("gavelSound");

    if (!preloader) {
        window.legalChatApp = new LegalChatApp();
        return;
    }

    // Play sound exactly once at impact moment
    setTimeout(() => {
        if (sound) {
            sound.volume = 0.65;
            sound.play().catch(() => {});
        }
    }, 450);

    // Let animation fully complete
    setTimeout(() => {
        preloader.style.opacity = "0";

        setTimeout(() => {
            preloader.remove();
            document.body.classList.remove("loading");

            // Start app AFTER cinematic ends
            window.legalChatApp = new LegalChatApp();
        }, 900);
    }, 1600);
});

// =====================================================
// LEGAL CHAT APPLICATION
// =====================================================
class LegalChatApp {
    constructor() {
        this.currentSessionId = null;
        this.isLoading = false;
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.createNewSession();
        await this.loadChatHistory();
    }

    // ================= EVENTS =================
    bindEvents() {
        $('#sendButton').on('click', () => this.sendMessage());

        $('#messageInput').on('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        $('#messageInput').on('input', e => this.handleInput(e));
        $('#newChatBtn').on('click', async () => this.createNewSession());
    }

    handleInput(e) {
        const text = e.target.value;
        $('#charCount').text(`${text.length}/2000`);
        $('#sendButton').prop('disabled', !text.trim() || this.isLoading);

        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px';
    }

    // ================= SESSION =================
    async createNewSession() {
        const res = await fetch('/api/new_session', { method: 'POST' });
        const data = await res.json();

        this.currentSessionId = data.session_id;
        this.clearChat(true);
        await this.loadChatHistory();
    }

    async loadChatHistory() {
        const res = await fetch('/api/sessions');
        const data = await res.json();

        const container = $('#chatHistory').empty();
        data.sessions.forEach(s => {
            const item = $(`<div class="chat-item">${s.title}</div>`);
            item.on('click', async () => this.loadSession(s.id));
            container.append(item);
        });
    }

    async loadSession(id) {
        this.currentSessionId = id;

        const res = await fetch(`/api/chat/${id}`);
        const data = await res.json();

        const container = $('#chatMessages').empty();
        if (!data.history.length) return this.showEmptyState();

        data.history.forEach(m => {
            this.displayMessage(m.content, m.role);
        });

        this.scrollBottom();
    }

    // ================= CHAT =================
    async sendMessage() {
        if (!this.currentSessionId || this.isLoading) return;

        const input = $('#messageInput');
        const text = input.val().trim();
        if (!text) return;

        $('.welcome-message').remove();

        this.isLoading = true;
        input.val('');
        $('#charCount').text('0/2000');

        this.displayMessage(text, 'user');
        this.showTypingIndicator();

        try {
            const res = await fetch(`/api/chat/${this.currentSessionId}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await res.json();
            this.removeTypingIndicator();
            await this.typeAssistantResponse(data.response);
        } finally {
            this.isLoading = false;
        }
    }

    displayMessage(content, role) {
        $('#chatMessages').append(`
            <div class="message ${role}-message">
                <div class="message-icon">
                    <i class="fas ${role === 'user' ? 'fa-user' : 'fa-gavel'}"></i>
                </div>
                <div class="message-body">
                    <div class="message-content">
                        ${DOMPurify.sanitize(marked.parse(content))}
                    </div>
                </div>
            </div>
        `);
        this.scrollBottom();
    }

    async typeAssistantResponse(text) {
        const container = $('#chatMessages');
        const msg = $(`
            <div class="message assistant-message">
                <div class="message-icon"><i class="fas fa-gavel"></i></div>
                <div class="message-body">
                    <div class="message-content"></div>
                </div>
            </div>
        `);
        container.append(msg);

        const target = msg.find('.message-content');
        let i = 0;

        return new Promise(resolve => {
            const interval = setInterval(() => {
                target.text(text.slice(0, i++));
                this.scrollBottom();

                if (i > text.length) {
                    clearInterval(interval);
                    target.html(DOMPurify.sanitize(marked.parse(text)));
                    resolve();
                }
            }, 18);
        });
    }

    showTypingIndicator() {
        $('#chatMessages').append(`
            <div class="message assistant-message typing">
                <div class="message-icon"><i class="fas fa-gavel"></i></div>
                <div class="message-content typing-bubble">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `);
    }

    removeTypingIndicator() {
        $('.typing').remove();
    }

    showEmptyState() {
        $('#chatMessages').html(`
            <div class="welcome-message">
                <div class="orb"><div class="orb-inner"></div></div>
                <h2>What legal issue can I help you with?</h2>
            </div>
        `);
    }

    clearChat(showWelcome) {
        $('#chatMessages').empty();
        if (showWelcome) this.showEmptyState();
    }

    scrollBottom() {
        const el = $('#chatMessages')[0];
        el.scrollTop = el.scrollHeight;
    }
}
