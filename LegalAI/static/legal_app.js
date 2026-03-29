/* ═══ LEGAL AI — legal_app.js (video edition) ═══ */
(function (W) {
    'use strict';

    const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isTouch = 'ontouchstart' in W;
    const mobile = () => innerWidth < 768;

    /* ─── Video helper: ensure a looping video starts playing ─── */
    function playVideo(el) {
        if (!el) return;
        el.muted = true;
        el.loop = true;
        el.play().catch(() => { });
    }

    /* ─── Loading Sequence (Advanced Animated) ─── */
    const Loader = (function () {
        const PHASES = [
            { t: 0, pct: 12, msg: 'Initializing System…' },
            { t: 600, pct: 28, msg: 'Connecting to Judicial Matrix…' },
            { t: 1400, pct: 48, msg: 'Synthesizing Precedents…' },
            { t: 2200, pct: 68, msg: 'Calibrating AI Models…' },
            { t: 3000, pct: 85, msg: 'Loading Legal Corpus…' },
            { t: 3800, pct: 95, msg: 'Finalizing Deployment…' },
        ];
        const EXIT_AFTER = 4800;

        function spawnAmbientParticles(container) {
            if (!container || RM) return;
            /* Inject keyframes once */
            if (!document.getElementById('advAmbientStyles')) {
                const s = document.createElement('style');
                s.id = 'advAmbientStyles';
                s.textContent = `
                    @keyframes ambientRise {
                        0%   { transform: translateY(0) scale(0); opacity: 0; }
                        20%  { opacity: 1; transform: translateY(-40px) scale(1.5); }
                        100% { transform: translateY(-200px) scale(0); opacity: 0; }
                    }
                `;
                document.head.appendChild(s);
            }
            for (let i = 0; i < 15; i++) {
                const p = document.createElement('div');
                const dur = 3 + Math.random() * 2;
                p.style.cssText = `
                    position: absolute;
                    width: 4px; height: 4px;
                    background: rgba(6, 182, 212, 0.4);
                    border-radius: 50%;
                    left: ${Math.random() * 100}%;
                    top: ${Math.random() * 100}%;
                    animation: ambientRise ${dur}s ease-out ${Math.random() * 2}s infinite;
                    pointer-events: none;
                `;
                container.appendChild(p);
            }
        }

        function run(done) {
            const screen = document.getElementById('loadingScreen');
            const barEl = document.getElementById('loadingProgressBar');
            const statusEl = document.getElementById('loadingStatus');
            const ambientBox = document.getElementById('advAmbientParticles');
            const bgVideo = screen && screen.querySelector('.adv-bg-video');
            const landingPage = document.getElementById('landingPage');

            /* Hide landing page during loading */
            if (landingPage) { landingPage.style.opacity = '0'; landingPage.style.visibility = 'hidden'; }

            if (RM) { if (screen) screen.style.display = 'none'; if (landingPage) { landingPage.style.opacity = '1'; landingPage.style.visibility = 'visible'; } done(); return; }

            /* Force bg video playback */
            playVideo(bgVideo);
            spawnAmbientParticles(ambientBox);

            /* Phase progression */
            PHASES.forEach(p => {
                setTimeout(() => {
                    if (barEl) barEl.style.width = p.pct + '%';
                    if (statusEl) statusEl.textContent = p.msg;
                }, p.t);
            });

            setTimeout(() => {
                if (barEl) barEl.style.width = '100%';
                if (statusEl) statusEl.textContent = 'System Ready.';
            }, EXIT_AFTER - 600);

            /* Exit */
            setTimeout(() => {
                if (screen) {
                    screen.style.opacity = '0';
                    screen.style.transform = 'scale(1.04)';
                    setTimeout(() => {
                        screen.style.display = 'none';
                        /* Reveal landing page */
                        if (landingPage) {
                            landingPage.style.transition = 'opacity 0.6s ease-out, visibility 0s';
                            landingPage.style.opacity = '1';
                            landingPage.style.visibility = 'visible';
                        }
                        done();
                    }, 850);
                } else { done(); }
            }, EXIT_AFTER);
        }

        return { run };
    }());

    /* ─── 4D Interactive Tilt for Hero Video Card ─── */
    (function init4DTilt() {
        const wrap = document.querySelector('.custom-hero-wrap');
        if (!wrap || RM) return;
        const video = wrap.querySelector('.lj-hero-video');
        if (!video) return;

        const MAX_TILT = 12; // degrees

        wrap.addEventListener('mousemove', function (e) {
            const rect = wrap.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;
            const dx = (e.clientX - cx) / (rect.width / 2);  // -1 to 1
            const dy = (e.clientY - cy) / (rect.height / 2); // -1 to 1
            const rotY = dx * MAX_TILT;
            const rotX = -dy * MAX_TILT;
            video.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(1.04, 1.04, 1.04)`;
        });

        wrap.addEventListener('mouseleave', function () {
            video.style.transform = 'rotateX(0) rotateY(0) scale3d(1, 1, 1)';
        });
    }());


    /* ─── Background Mesh Canvas ─── */
    const BgCanvas = (function () {
        let canvas, ctx, W, H;
        let pts = [], nodes = [];
        let panX = 0, panY = 0, targetX = 0, targetY = 0;
        let tris = [], triTimer = 0;
        let ripples = [], thinkWave = null;

        const PC = () => mobile() ? 100 : 260;
        const NC = () => mobile() ? 35 : 70;
        const rand = (a, b) => a + Math.random() * (b - a);

        function reset() {
            W = canvas.width = innerWidth;
            H = canvas.height = innerHeight;
            targetX = W / 2; targetY = H / 2;
            pts = Array.from({ length: PC() }, () => ({
                x: rand(0, W), y: rand(0, H), vx: rand(-.1, .1), vy: rand(-.08, .08)
            }));
            [[0, 0], [W, 0], [0, H], [W, H], [W / 2, 0], [W / 2, H], [0, H / 2], [W, H / 2]]
                .forEach(([x, y]) => pts.push({ x, y, vx: 0, vy: 0 }));
            nodes = Array.from({ length: NC() }, () => ({
                x: rand(0, W), y: rand(H * .1, H),
                vx: rand(-.3, .3), vy: rand(-.4, -.1),
                r: rand(1, 2.5), b: rand(.4, .9)
            }));
            rebuildTris();
        }

        function rebuildTris() {
            tris = [];
            pts.forEach(p => {
                const near = pts.filter(q => q !== p)
                    .map(q => [q, Math.hypot(q.x - p.x, q.y - p.y)])
                    .sort((a, b) => a[1] - b[1]).slice(0, 2).map(e => e[0]);
                if (near.length === 2) tris.push([p, near[0], near[1]]);
            });
        }

        function frame() {
            panX += (targetX - panX) * 0.04;
            panY += (targetY - panY) * 0.04;
            pts.forEach(p => {
                p.x += p.vx; p.y += p.vy;
                if (p.x < -20) p.x = W + 20; if (p.x > W + 20) p.x = -20;
                if (p.y < -20) p.y = H + 20; if (p.y > H + 20) p.y = -20;
            });
            if (++triTimer >= 120) { rebuildTris(); triTimer = 0; }
            nodes.forEach(n => {
                n.x += n.vx; n.y += n.vy;
                if (n.y < -6) n.y = H + 6;
                if (n.x < -6) n.x = W + 6; if (n.x > W + 6) n.x = -6;
            });
            ripples = ripples.filter(r => r.a > 0.01);
            ripples.forEach(r => { r.rad += 4; r.a *= 0.93; });
            if (thinkWave) {
                thinkWave.r += 3.5; thinkWave.a *= 0.96;
                if (thinkWave.a < 0.005) thinkWave = null;
            }

            ctx.clearRect(0, 0, W, H);
            ctx.save(); ctx.translate(panX, panY);

            tris.forEach(([a, b, c]) => {
                if (Math.hypot(b.x - a.x, b.y - a.y) > 230) return;
                const d = Math.sin(Date.now() * .0004 + a.x * .01) * .06 + .05;
                ctx.beginPath();
                ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.lineTo(c.x, c.y);
                ctx.closePath();
                ctx.fillStyle = `rgba(6,32,64,${d})`; ctx.fill();
                ctx.strokeStyle = 'rgba(74,158,220,0.1)'; ctx.lineWidth = .5; ctx.stroke();
            });

            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const d = Math.hypot(nodes[j].x - nodes[i].x, nodes[j].y - nodes[i].y);
                    if (d < 110) {
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.strokeStyle = `rgba(74,158,220,${(1 - d / 110) * .3})`; ctx.lineWidth = .7; ctx.stroke();
                    }
                }
            }
            nodes.forEach(n => {
                ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(79,195,247,${n.b})`; ctx.fill();
            });
            ctx.restore();

            ripples.forEach(r => {
                ctx.beginPath(); ctx.arc(r.x, r.y, r.rad, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(79,195,247,${r.a})`; ctx.lineWidth = 1.5; ctx.stroke();
            });
            if (thinkWave) {
                ctx.beginPath(); ctx.arc(W / 2, H / 2, thinkWave.r, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(79,195,247,${thinkWave.a})`; ctx.lineWidth = 2.5; ctx.stroke();
            }
            requestAnimationFrame(frame);
        }

        function setup() {
            canvas = document.getElementById('bgCanvas');
            if (!canvas || RM) return;
            ctx = canvas.getContext('2d');
            reset();
            addEventListener('resize', reset, { passive: true });
            if (!isTouch) {
                document.addEventListener('mousemove', e => {
                    const cx = W / 2, cy = H / 2;
                    targetX = (e.clientX - cx) / cx * -14;
                    targetY = (e.clientY - cy) / cy * -14;
                }, { passive: true });
            }
            requestAnimationFrame(frame);
        }

        function addRipple(x, y) { ripples.push({ x, y, rad: 4, a: .5 }); }
        function pulse() { thinkWave = { r: 4, a: .45 }; }
        return { setup, addRipple, pulse };
    }());

    /* ─── Hamburger / Sidebar ─── */
    function initHamburger() {
        const btn = document.getElementById('hamburgerBtn');
        const sidebar = document.getElementById('chatSidebar');
        const overlay = document.getElementById('sidebarOverlay');
        if (!btn || !sidebar || !overlay) return;

        function open() {
            sidebar.removeAttribute('hidden');
            requestAnimationFrame(() => sidebar.classList.add('open'));
            overlay.classList.add('active');
            btn.classList.add('open');
            btn.setAttribute('aria-expanded', 'true');
        }
        function close() {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            btn.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
            sidebar.style.transform = '';
        }
        function toggle() { sidebar.classList.contains('open') ? close() : open(); }

        btn.addEventListener('click', toggle);
        overlay.addEventListener('click', close);
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) close();
        });

        if (!isTouch) {
            sidebar.addEventListener('mousemove', e => {
                if (!sidebar.classList.contains('open')) return;
                const r = sidebar.getBoundingClientRect();
                const x = ((e.clientX - r.left) / r.width - 0.5) * 6;
                const y = ((e.clientY - r.top) / r.height - 0.5) * 6;
                sidebar.style.transform = `translateX(0) rotateY(${x * 0.4}deg) rotateX(${-y * 0.25}deg)`;
            }, { passive: true });

            sidebar.addEventListener('mouseleave', () => {
                if (sidebar.classList.contains('open')) sidebar.style.transform = 'translateX(0)';
            });

            sidebar.addEventListener('mouseover', e => {
                const item = e.target.closest('.session-item, .btn-new-chat, .sidebar-user-panel');
                if (!item) return;
                item.style.transition = 'transform .25s cubic-bezier(.22,1,.36,1)';
                item.style.transform = 'translateY(-1px) scale(1.01)';
            });

            sidebar.addEventListener('mouseout', e => {
                const item = e.target.closest('.session-item, .btn-new-chat, .sidebar-user-panel');
                if (!item) return;
                item.style.transform = '';
            });
        }

        W.LegalAI = W.LegalAI || {};
        W.LegalAI.closeSidebar = close;
        W.LegalAI.openSidebar = open;
    }

    /* ─── Scrollytelling ─── */
    function initScrollytelling() {
        const io = new IntersectionObserver(entries => {
            entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('revealed'); });
        }, { threshold: 0.15 });
        document.querySelectorAll('.reveal-item').forEach(el => io.observe(el));
    }

    /* ─── Landing → Chat transition ─── */
    function enterChat() {
        const landing = document.getElementById('landingPage');
        const chat = document.getElementById('chatApp');
        if (!landing || !chat) return;
        landing.style.transition = 'opacity 0.6s ease';
        landing.style.opacity = '0';
        setTimeout(() => {
            landing.style.display = 'none';
            chat.removeAttribute('hidden');
            chat.removeAttribute('aria-hidden');
            /* Ensure chat ghost video plays */
            playVideo(document.getElementById('ljChatVideo'));
            requestAnimationFrame(() => chat.classList.add('visible'));
            App.loadSessions();
            App.newSession();
        }, 630);
    }

    /* ─── Custom Cursor ─── */
    function initCursor() {
        if (isTouch || mobile()) return;
        ['cursorInner', 'cursorOuter'].forEach(id => {
            if (!document.getElementById(id)) {
                const d = document.createElement('div');
                d.id = id; d.className = 'cursor-dot'; document.body.appendChild(d);
            }
        });
        const inner = document.getElementById('cursorInner');
        const outer = document.getElementById('cursorOuter');
        let mx = -200, my = -200, ox = -200, oy = -200;
        document.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; }, { passive: true });
        (function ani() {
            ox += (mx - ox) * .14; oy += (my - oy) * .14;
            inner.style.left = mx + 'px'; inner.style.top = my + 'px';
            outer.style.left = ox + 'px'; outer.style.top = oy + 'px';
            requestAnimationFrame(ani);
        }());
        const sel = 'button,a,.session-item,.prompt-chip,textarea';
        document.addEventListener('mouseover', e => { if (e.target.closest(sel)) outer.classList.add('hover'); });
        document.addEventListener('mouseout', e => { if (e.target.closest(sel)) outer.classList.remove('hover'); });
    }

    /* ─── App Logic ─── */
    const App = (function () {
        const S = { sessionId: null, sessions: [], loading: false, scrolledUp: false };
        const g = id => document.getElementById(id);

        function esc(s) {
            return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }
        function fmtDate(ts) {
            try { return new Date((ts || '').replace(' ', 'T') + 'Z').toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }); }
            catch { return ''; }
        }

        async function apiFetch(url, options) {
            const res = await fetch(url, options);
            if (res.status === 401) {
                W.location.href = '/login';
                throw new Error('Unauthorized');
            }
            return res;
        }

        async function apiFetchJson(url, options) {
            const res = await apiFetch(url, options);
            return await res.json();
        }

        async function loadSessions() {
            try {
                const data = await apiFetchJson('/api/sessions');
                S.sessions = data.sessions || [];
                renderSessions();
            } catch (e) { console.error(e); }
        }

        function renderSessions() {
            const c = g('sidebarSessions'); if (!c) return;
            c.innerHTML = '';
            if (!S.sessions.length) {
                c.innerHTML = '<div class="sessions-empty"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:12px;opacity:0.5;"><path d="M3 6l3 12h12l3-12H3z"></path><path d="M12 3v3"></path><path d="M12 18v3"></path></svg><p>No research sessions yet</p></div>';
                return;
            }
            S.sessions.forEach((s, i) => {
                const el = buildSessionEl(s);
                el.style.animationDelay = (i * .05) + 's';
                el.classList.add('slide-up');
                c.appendChild(el);
            });
        }

        function buildSessionEl(s) {
            const div = document.createElement('div');
            div.className = 'session-item' + (s.id === S.sessionId ? ' active' : '');
            div.setAttribute('role', 'listitem');
            div.innerHTML = `<div class="session-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6l3 12h12l3-12H3z"></path><path d="M12 3v3"></path></svg></div>
            <div class="session-details">
                <div class="session-title">${esc(s.title)}</div>
                <div class="session-meta">${fmtDate(s.updated_at)}</div>
            </div>
            <button class="session-delete icon-btn" aria-label="Delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>`;
            div.addEventListener('click', e => { if (!e.target.closest('.session-delete')) switchSession(s.id); });
            div.querySelector('.session-delete').addEventListener('click', e => { e.stopPropagation(); deleteSession(s.id, div); });
            return div;
        }

        async function newSession() {
            try {
                const data = await apiFetchJson('/api/new_session', { method: 'POST' });
                S.sessionId = data.session_id;
                const ma = g('messagesArea'); if (ma) ma.innerHTML = '';
                const es = g('emptyState'); if (es) es.style.display = '';
                await loadSessions();
                if (W.LegalAI && W.LegalAI.closeSidebar) W.LegalAI.closeSidebar();
            } catch (e) { console.error(e); }
        }

        async function switchSession(id) {
            if (id === S.sessionId) { if (W.LegalAI) W.LegalAI.closeSidebar(); return; }
            S.sessionId = id;
            const ma = g('messagesArea'); if (ma) ma.innerHTML = '';
            const es = g('emptyState'); if (es) es.style.display = 'none';
            renderSessions();
            if (W.LegalAI) W.LegalAI.closeSidebar();
            try {
                const data = await apiFetchJson(`/api/chat/${id}`);
                (data.history || []).forEach(m => appendMsg(m.role, m.content, false));
                scrollBot(false);
            } catch (e) { console.error(e); }
        }

        async function deleteSession(id, el) {
            el.style.cssText += 'transition:transform .4s ease,opacity .4s ease;transform:scale(0) rotate(360deg);opacity:0;';
            setTimeout(async () => {
                try { await apiFetch(`/api/delete_session/${id}`, { method: 'DELETE' }); } catch (e) { }
                if (id === S.sessionId) {
                    S.sessionId = null;
                    const ma = g('messagesArea'); if (ma) ma.innerHTML = '';
                    const es = g('emptyState'); if (es) es.style.display = '';
                }
                await loadSessions();
            }, 460);
        }

        const THINK_TEXTS = [
            'Analyzing precedents…', 'Reviewing statutes…',
            'Consulting case law…', 'Formulating opinion…', 'Researching judgments…'
        ];
        let _thinkTimer = null;

        function showThinking() {
            BgCanvas.pulse();
            const bub = document.createElement('div');
            bub.className = 'message-bubble ai-message'; bub.id = '_think_bub';
            let idx = 0;
            bub.innerHTML = `
            <div class="msg-avatar"><svg class="ai-avatar-svg" width="36" height="36" viewBox="0 0 36 36" fill="none">
                <polygon points="18,4 30,28 6,28" stroke="#4fc3f7" stroke-width="1.5" fill="rgba(26,110,181,0.15)"/>
                <circle cx="18" cy="4"  r="2" fill="#a8e6ff"/>
                <circle cx="30" cy="28" r="2" fill="#4fc3f7"/>
                <circle cx="6"  cy="28" r="2" fill="#4fc3f7"/>
            </svg></div>
            <div class="msg-content">
                <div class="thinking-indicator">
                    <svg class="thinking-tri" width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <polygon points="12,3 21,18 3,18" stroke="#4fc3f7" stroke-width="1.5" fill="rgba(26,110,181,0.2)"/>
                    </svg>
                    <span class="thinking-text">${THINK_TEXTS[0]}</span>
                </div>
            </div>`;
            const ma = g('messagesArea'); if (ma) { ma.appendChild(bub); autoScroll(); }
            const te = bub.querySelector('.thinking-text');
            _thinkTimer = setInterval(() => {
                if (!te) return;
                te.style.opacity = '0';
                setTimeout(() => {
                    idx = (idx + 1) % THINK_TEXTS.length;
                    te.textContent = THINK_TEXTS[idx];
                    te.style.opacity = '1';
                }, 300);
            }, 2500);
            return bub;
        }

        function hideThinking(bub) {
            clearInterval(_thinkTimer);
            if (bub && bub.parentNode) bub.parentNode.removeChild(bub);
        }

        function appendMsg(role, content, animate = true) {
            const isAI = role === 'assistant' || role === 'ai';
            const es = g('emptyState'); if (es && es.style.display !== 'none') es.style.display = 'none';
            const bub = document.createElement('div');
            bub.className = `message-bubble ${isAI ? 'ai-message' : 'user-message'}`;
            bub.innerHTML = isAI
                ? `<div class="msg-avatar"><svg class="ai-avatar-svg" width="36" height="36" viewBox="0 0 36 36" fill="none">
                    <polygon points="18,4 30,28 6,28" stroke="#4fc3f7" stroke-width="1.5" fill="rgba(26,110,181,0.15)"/>
                    <circle cx="18" cy="4"  r="2" fill="#a8e6ff"/>
                    <circle cx="30" cy="28" r="2" fill="#4fc3f7"/>
                    <circle cx="6"  cy="28" r="2" fill="#4fc3f7"/>
               </svg></div>
               <div class="msg-content"><div class="msg-role-label">Legal AI</div><div class="message-text ai-text"></div></div>`
                : `<div class="msg-content"><div class="msg-role-label">You</div><div class="message-text">${esc(content)}</div></div>`;

            const ma = g('messagesArea'); if (ma) ma.appendChild(bub);

            if (isAI) {
                const t = bub.querySelector('.ai-text');
                if (animate) { animAIText(t, content); BgCanvas.addRipple(innerWidth / 2, innerHeight - 120); }
                else if (t && W.DOMPurify && W.marked) t.innerHTML = DOMPurify.sanitize(marked.parse(content));
            }
            autoScroll();
        }

        function animAIText(container, raw) {
            if (!container || !W.DOMPurify || !W.marked) return;
            const html = DOMPurify.sanitize(marked.parse(raw));
            if (RM) { container.innerHTML = html; return; }
            const tmp = document.createElement('div'); tmp.innerHTML = html;
            let i = 0;
            function wrap(node) {
                if (node.nodeType === 3) {
                    const frag = document.createDocumentFragment();
                    node.textContent.split(/(\s+)/).forEach(w => {
                        if (w.trim()) {
                            const sp = document.createElement('span');
                            sp.className = 'word-token';
                            sp.style.animationDelay = (i++ * 18) + 'ms';
                            sp.textContent = w;
                            frag.appendChild(sp); frag.appendChild(document.createTextNode(' '));
                        } else { frag.appendChild(document.createTextNode(w)); }
                    });
                    node.parentNode.replaceChild(frag, node);
                } else if (node.childNodes) { Array.from(node.childNodes).forEach(wrap); }
            }
            wrap(tmp); container.appendChild(tmp);
        }

        async function sendMessage() {
            const ta = g('cosmicTextarea'), bs = g('btnSend');
            if (!ta || S.loading) return;
            const text = ta.value.trim(); if (!text) return;
            if (!S.sessionId) await newSession();

            S.loading = true;
            ta.value = ''; ta.style.height = ''; updateCounter();
            if (bs) { bs.disabled = true; bs.classList.add('sending'); particleBurst(bs); setTimeout(() => bs.classList.remove('sending'), 550); }

            appendMsg('user', text, true);
            const thinkBub = showThinking();
            try {
                const res = await apiFetch(`/api/chat/${S.sessionId}/message`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text }) });
                const data = await res.json();
                hideThinking(thinkBub);

                if (res.ok && data.status === 'success' && data.response) {
                    appendMsg('assistant', data.response, true);
                    await loadSessions();
                } else {
                    const fallbackErr = data.error || data.details || 'I encountered an error. Please try again.';
                    appendMsg('assistant', String(fallbackErr), true);
                }
            } catch (e) {
                hideThinking(thinkBub);
                appendMsg('assistant', 'Network error. Please try again.', true);
            } finally {
                S.loading = false;
                if (bs) bs.disabled = false;
                if (ta) ta.focus();
            }
        }

        function autoScroll() {
            const cw = g('chatWrapper'); if (!cw) return;
            const atBot = cw.scrollHeight - cw.scrollTop - cw.clientHeight < 80;
            if (!S.scrolledUp || atBot) scrollBot(true);
            else { const p = g('newMsgPill'); if (p) p.hidden = false; }
        }

        function scrollBot(smooth = true) {
            const cw = g('chatWrapper'); if (!cw) return;
            cw.scrollTo({ top: cw.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
            const p = g('newMsgPill'); if (p) p.hidden = true;
            S.scrolledUp = false;
        }

        function updateCounter() {
            const ta = g('cosmicTextarea'), cc = document.querySelector('.char-counter'), bs = g('btnSend');
            if (!ta || !cc) return;
            const n = ta.value.length;
            cc.textContent = n > 0 ? `${n}/4000` : '';
            if (bs) bs.disabled = n === 0 || S.loading;
        }

        function particleBurst(btn) {
            if (RM) return;
            const r = btn.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
            for (let i = 0; i < 8; i++) {
                const p = document.createElement('div'); p.className = 'send-particle';
                document.body.appendChild(p);
                const a = (i / 8) * Math.PI * 2, sp = 40 + Math.random() * 40;
                const vx = Math.cos(a) * sp, vy = Math.sin(a) * sp;
                let lx = cx, ly = cy, op = 1;
                (function an() {
                    lx += vx * .07; ly += vy * .07; op -= .045;
                    p.style.cssText = `position:fixed;left:${lx}px;top:${ly}px;opacity:${op};width:5px;height:5px;border-radius:50%;background:#4fc3f7;pointer-events:none;z-index:9000;`;
                    if (op > 0) requestAnimationFrame(an); else p.remove();
                }());
            }
        }

        function wireEvents() {
            const sa = (id, fn) => { const el = g(id); if (el) el.addEventListener('click', fn); };
            sa('btnNewConsultation', newSession);
            sa('btnNewConsultationTop', newSession);
            sa('btnNavEnterChat', enterChat);
            sa('btnHeroEnterChat', enterChat);
            sa('btnCtaEnterChat', enterChat);
            sa('btnSend', sendMessage);
            sa('newMsgPill', () => scrollBot(true));

            const ta = g('cosmicTextarea');
            if (ta) {
                ta.addEventListener('input', () => {
                    updateCounter();
                    ta.style.height = 'auto';
                    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
                });
                ta.addEventListener('keydown', e => {
                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
                });
            }

            document.addEventListener('click', e => {
                const chip = e.target.closest('.prompt-chip');
                if (chip) {
                    const ta2 = g('cosmicTextarea');
                    if (ta2) {
                        ta2.value = chip.dataset.prompt || '';
                        ta2.focus(); updateCounter();
                        ta2.style.height = 'auto';
                        ta2.style.height = Math.min(ta2.scrollHeight, 160) + 'px';
                        /* If it's a persistent chip, we might want to auto-send? 
                           User said "click to fill", so we'll stop there. */
                    }
                }
            });

            /* Voice Input Logic (Robust Version) */
            const micBtn = g('btnMic');
            if (micBtn && (W.SpeechRecognition || W.webkitSpeechRecognition)) {
                const SpeechAPI = W.SpeechRecognition || W.webkitSpeechRecognition;
                const rec = new SpeechAPI();
                rec.continuous = false;
                rec.interimResults = false;
                rec.lang = 'en-IN';

                let isListening = false;

                function setMicActive(active) {
                    isListening = active;
                    if (active) {
                        micBtn.classList.add('listening');
                    } else {
                        micBtn.classList.remove('listening');
                    }
                }

                micBtn.addEventListener('click', async () => {
                    if (isListening) {
                        try { rec.stop(); } catch(e) {}
                    } else {
                        try {
                            // Explicitly request mic access to trigger prompt
                            await navigator.mediaDevices.getUserMedia({ audio: true });
                            rec.start();
                        } catch (err) {
                            console.warn('Mic Start Error:', err);
                            if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                                alert('Microphone access is blocked in your browser settings.\n\nPlease click the Lock icon (🔒) or Settings icon next to the URL and set Microphone to "Allow".');
                            } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                                alert('No microphone detected on this device.');
                            } else {
                                alert('Could not access microphone. Please try on http://localhost or over HTTPS.');
                            }
                            setMicActive(false);
                        }
                    }
                });

                rec.onstart = () => {
                    setMicActive(true);
                    console.log('Mic Listening...');
                };

                rec.onend = () => {
                    setMicActive(false);
                    console.log('Mic Stopped.');
                };

                rec.onerror = (e) => {
                    console.error('Speech Error:', e.error);
                    setMicActive(false);
                    if (e.error === 'not-allowed') {
                        alert('Mic Access Denied. Please enable microphone permissions in your browser settings.');
                    }
                };

                rec.onresult = (e) => {
                    const result = e.results[0][0].transcript;
                    const ta = g('cosmicTextarea');
                    if (ta) {
                        const prev = ta.value.trim();
                        ta.value = (prev ? prev + ' ' : '') + result;
                        ta.focus();
                        updateCounter();
                        ta.style.height = 'auto';
                        ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
                    }
                    setMicActive(false);
                };
            } else if (micBtn) {
                micBtn.addEventListener('click', () => {
                    alert('Sorry, your browser does not support Speech Recognition. Try Chrome or Edge.');
                });
                micBtn.style.opacity = '0.3';
            }

            const cw = g('chatWrapper');
            if (cw) cw.addEventListener('scroll', () => {
                S.scrolledUp = cw.scrollHeight - cw.scrollTop - cw.clientHeight > 80;
                if (!S.scrolledUp) { const p = g('newMsgPill'); if (p) p.hidden = true; }
            }, { passive: true });
        }

        return { loadSessions, newSession, wireEvents };
    }());

    /* ─── Bootstrap ─── */
    document.addEventListener('DOMContentLoaded', () => {
        BgCanvas.setup();
        initCursor();
        initHamburger();
        initScrollytelling();
        App.wireEvents();

        /* Kick off all loop videos that are currently on-screen */
        ['ljHeroVideo', 'ljCtaVideo'].forEach(id => playVideo(document.getElementById(id)));

        /* Show landing (it starts aria-hidden) */
        const lp = document.getElementById('landingPage');
        if (lp) lp.removeAttribute('aria-hidden');

        if (RM) {
            const ls = document.getElementById('loadingScreen');
            if (ls) ls.style.display = 'none';
        } else {
            Loader.run(() => { /* nothing extra needed — videos auto-play */ });
        }
    });

}(window));
