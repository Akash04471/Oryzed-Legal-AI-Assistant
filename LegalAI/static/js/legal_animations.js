/* ═══════════════════════════════════════════════════════════
   LEGAL AI – 2026 ANTIGRAVITY ANIMATION SYSTEM
   legal_animations.js — LegalAnimations Namespace Module
   
   Hooks: dispatches to/from existing legal_app_v2.js via
   custom DOM events to avoid modifying backend JS.
   ═══════════════════════════════════════════════════════════ */

(function (global) {
    'use strict';

    /* ───────────────────────────────────────────────────────
       SHARED STATE
       ─────────────────────────────────────────────────────── */
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isMobile = () => window.innerWidth < 768;
    const isTouch = 'ontouchstart' in window;

    let _destroyed = false;
    let _paused = false;
    const _cleanups = [];   // array of () => void teardown functions
    const _timelines = [];  // GSAP timelines to kill on destroy

    /* ───────────────────────────────────────────────────────
       UTILITY
       ─────────────────────────────────────────────────────── */
    function raf(fn) {
        if (_destroyed || _paused) return;
        return requestAnimationFrame(fn);
    }

    function lerp(a, b, t) { return a + (b - a) * t; }

    function dist(x1, y1, x2, y2) {
        const dx = x2 - x1, dy = y2 - y1;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

    function on(el, ev, fn, opts) {
        el.addEventListener(ev, fn, opts);
        _cleanups.push(() => el.removeEventListener(ev, fn, opts));
    }

    /* ───────────────────────────────────────────────────────
       1 · SCROLLYTELLING LANDING PAGE
       ─────────────────────────────────────────────────────── */
    function initLanding() {
        const overlay = document.getElementById('landingOverlay');
        if (!overlay) return;

        // Skip if user has visited before (localStorage flag)
        const seenKey = 'legalai_cosmos_seen';
        if (localStorage.getItem(seenKey) === '1') {
            overlay.style.display = 'none';
            dispatchAppReady();
            return;
        }

        if (prefersReducedMotion) {
            overlay.style.display = 'none';
            dispatchAppReady();
            return;
        }

        document.body.style.overflow = 'hidden';

        /* Progress bar */
        const progressBar = overlay.querySelector('.landing-progress');
        function updateProgress() {
            if (!overlay || overlay.style.display === 'none') return;
            const max = overlay.scrollHeight - overlay.clientHeight;
            const pct = max > 0 ? (overlay.scrollTop / max) * 100 : 0;
            if (progressBar) progressBar.style.height = pct + '%';
        }
        on(overlay, 'scroll', updateProgress, { passive: true });

        /* --- Hero parallax (antigravity: scales float UP) --- */
        const heroScales = overlay.querySelector('.hero-scales-svg');
        const heroEyebrow = overlay.querySelector('.hero-eyebrow');
        const heroHeadline = overlay.querySelector('.hero-headline');
        const heroSub = overlay.querySelector('.hero-sub');

        // Reveal hero elements on load
        setTimeout(() => {
            if (heroEyebrow) { heroEyebrow.style.opacity = '1'; heroEyebrow.style.transform = 'translateY(0)'; heroEyebrow.style.transition = 'opacity 0.8s ease, transform 0.8s cubic-bezier(0.34,1.56,0.64,1)'; }
            if (heroHeadline) { heroHeadline.style.opacity = '1'; heroHeadline.style.transform = 'translateY(0)'; heroHeadline.style.transition = 'opacity 1s ease 0.15s, transform 1s cubic-bezier(0.34,1.56,0.64,1) 0.15s'; }
            if (heroSub) { heroSub.style.opacity = '1'; heroSub.style.transform = 'translateY(0)'; heroSub.style.transition = 'opacity 1s ease 0.3s, transform 1s cubic-bezier(0.34,1.56,0.64,1) 0.3s'; }
        }, 300);

        // GSAP ScrollTrigger (if available)
        if (global.gsap && global.ScrollTrigger) {
            global.gsap.registerPlugin(global.ScrollTrigger);

            // Anti-gravity: scales move UP as user scrolls DOWN
            const heroST = global.gsap.timeline({
                scrollTrigger: {
                    scroller: overlay,
                    trigger: overlay.querySelector('.landing-hero'),
                    start: 'top top',
                    end: 'bottom top',
                    scrub: 1
                }
            });
            if (heroScales) {
                heroST.to(heroScales, { y: -180, ease: 'none' }, 0);
            }
            if (heroHeadline) {
                heroST.to(heroHeadline, { y: -60, opacity: 0, ease: 'none' }, 0);
            }
            _timelines.push(heroST);

            // Timeline era build
            const eras = overlay.querySelectorAll('.timeline-era');
            eras.forEach((era, i) => {
                const tl = global.gsap.timeline({
                    scrollTrigger: {
                        scroller: overlay,
                        trigger: era,
                        start: 'top 80%',
                        end: 'bottom 60%',
                        toggleActions: 'play none none reverse'
                    }
                });
                const isOdd = i % 2 === 0;
                tl.fromTo(era,
                    { opacity: 0, y: 60, x: isOdd ? -30 : 30 },
                    {
                        opacity: 1, y: 0, x: 0,
                        duration: 0.9,
                        ease: 'back.out(1.7)'
                    }
                );
                _timelines.push(tl);
            });

            // Heading + CTA reveals
            ['.timeline-heading', '.cta-title', '.cta-sub', '#btnEnterCosmos'].forEach(sel => {
                const el = overlay.querySelector(sel);
                if (!el) return;
                const tl = global.gsap.timeline({
                    scrollTrigger: {
                        scroller: overlay,
                        trigger: el,
                        start: 'top 85%',
                        toggleActions: 'play none none reverse'
                    }
                });
                tl.fromTo(el,
                    { opacity: 0, y: 40 },
                    { opacity: 1, y: 0, duration: 0.8, ease: 'back.out(1.4)' }
                );
                _timelines.push(tl);
            });

        } else {
            // Fallback: IntersectionObserver for eras
            const eras = overlay.querySelectorAll('.timeline-era');
            const revealIO = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.transition = 'opacity 0.9s cubic-bezier(0.34,1.56,0.64,1), transform 0.9s cubic-bezier(0.34,1.56,0.64,1)';
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, { root: overlay, threshold: 0.2 });
            eras.forEach(era => {
                era.style.transform = 'translateY(60px)';
                revealIO.observe(era);
            });
            _cleanups.push(() => revealIO.disconnect());

            // Reveal other elements
            ['.timeline-heading', '.cta-title', '.cta-sub', '#btnEnterCosmos'].forEach(sel => {
                const el = overlay.querySelector(sel);
                if (!el) return;
                const io = new IntersectionObserver(([entry]) => {
                    if (entry.isIntersecting) {
                        el.style.transition = 'opacity 0.8s ease, transform 0.8s cubic-bezier(0.34,1.56,0.64,1)';
                        el.style.opacity = '1';
                        el.style.transform = 'none';
                    }
                }, { root: overlay, threshold: 0.3 });
                io.observe(el);
                _cleanups.push(() => io.disconnect());
            });
        }

        /* --- Scroll-driven counter-particles (200 micro) --- */
        initCounterParticles(overlay);

        /* --- Debris gravity wells --- */
        initDebrisField(overlay);

        /* --- Enter Cosmos button --- */
        const btnEnter = document.getElementById('btnEnterCosmos');
        if (btnEnter) {
            on(btnEnter, 'click', () => enterCosmos(overlay, seenKey));
        }
    }

    function dispatchAppReady() {
        document.dispatchEvent(new CustomEvent('legalai:appReady'));
    }

    /* --- Warp implosion + overlay exit --- */
    function enterCosmos(overlay, seenKey) {
        if (prefersReducedMotion) {
            overlay.style.display = 'none';
            document.body.style.overflow = '';
            localStorage.setItem(seenKey, '1');
            dispatchAppReady();
            return;
        }

        // Spawn expanding rings from button center
        const btn = document.getElementById('btnEnterCosmos');
        if (btn) {
            const rect = btn.getBoundingClientRect();
            for (let i = 0; i < 4; i++) {
                const ring = document.createElement('div');
                ring.className = 'warp-ring';
                ring.style.cssText = `left:${rect.left + rect.width / 2}px;top:${rect.top + rect.height / 2}px;position:fixed;`;
                document.body.appendChild(ring);
                const delay = i * 80;
                setTimeout(() => {
                    ring.style.transition = 'transform 0.7s ease-out, opacity 0.7s ease-out';
                    ring.style.transform = 'translate(-50%,-50%) scale(80)';
                    ring.style.opacity = '0';
                    setTimeout(() => ring.remove(), 800);
                }, delay);
            }
        }

        // Fade overlay
        setTimeout(() => {
            overlay.classList.add('exiting');
            setTimeout(() => {
                overlay.style.display = 'none';
                document.body.style.overflow = '';
                localStorage.setItem(seenKey, '1');
                dispatchAppReady();
            }, 700);
        }, 200);
    }

    /* ───────────────────────────────────────────────────────
       2 · COUNTER-SCROLL PARTICLES (200 micro)
       ─────────────────────────────────────────────────────── */
    function initCounterParticles(scroller) {
        const container = document.getElementById('counterParticleField');
        if (!container) return;

        const COUNT = isMobile() ? 80 : 200;
        const particles = [];

        for (let i = 0; i < COUNT; i++) {
            const p = document.createElement('div');
            p.style.cssText = `
                position: absolute;
                width: ${1 + Math.random() * 2}px;
                height: ${1 + Math.random() * 2}px;
                border-radius: 50%;
                background: ${randomColor()};
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 200}%;
                opacity: ${0.1 + Math.random() * 0.5};
                will-change: transform;
                pointer-events: none;
            `;
            container.appendChild(p);
            particles.push({ el: p, speed: 0.2 + Math.random() * 0.8 });
        }

        let lastScroll = scroller.scrollTop;
        function onCounterScroll() {
            const delta = scroller.scrollTop - lastScroll;
            lastScroll = scroller.scrollTop;
            particles.forEach(par => {
                const currentTop = parseFloat(par.el.style.top);
                par.el.style.top = (currentTop - delta * par.speed) + '%';
            });
        }

        on(scroller, 'scroll', onCounterScroll, { passive: true });
    }

    function randomColor() {
        const cols = ['rgba(201,168,76,', 'rgba(79,195,247,', 'rgba(155,89,182,', 'rgba(0,229,255,'];
        return cols[Math.floor(Math.random() * cols.length)] + (0.3 + Math.random() * 0.5) + ')';
    }

    /* ───────────────────────────────────────────────────────
       3 · DEBRIS FIELD + GRAVITY WELLS
       ─────────────────────────────────────────────────────── */
    const LEGAL_TERMS = [
        'Lex Specialis', 'Habeas Corpus', 'Mens Rea', 'Actus Reus',
        'Stare Decisis', 'Amicus Curiae', 'Pro Bono', 'Res Judicata',
        'Ratio Decidendi', 'Ultra Vires', 'Quid Pro Quo', 'Ex Parte',
        'Prima Facie', 'Nolo Contendere', 'De Facto', 'Caveat Emptor',
        'Force Majeure', 'In Limine', 'Per Curiam', 'Sub Judice'
    ];

    function initDebrisField(scroller) {
        const field = scroller.querySelector('.debris-field');
        if (!field) return;

        const terms = [];

        LEGAL_TERMS.forEach((term, i) => {
            const el = document.createElement('div');
            el.className = 'debris-term';
            el.textContent = term;
            el.style.left = (5 + Math.random() * 85) + '%';
            el.style.top = (5 + Math.random() * 85) + '%';
            el.style.fontSize = (0.8 + Math.random() * 0.6) + 'rem';
            el.style.opacity = (0.3 + Math.random() * 0.6).toString();
            field.appendChild(el);
            terms.push({ el, baseTop: parseFloat(el.style.top), speed: 0.15 + Math.random() * 0.4 });
        });

        // Counter-scroll drift (upward as user scrolls down)
        let lastTop = scroller.scrollTop;
        function onDebrisScroll() {
            const delta = scroller.scrollTop - lastTop;
            lastTop = scroller.scrollTop;
            terms.forEach(t => {
                t.baseTop -= delta * t.speed * 0.05;
                t.el.style.top = t.baseTop + '%';
            });
        }
        on(scroller, 'scroll', onDebrisScroll, { passive: true });

        // Gravity well click
        terms.forEach(t => {
            on(t.el, 'click', () => activateGravityWell(t, terms, scroller));
        });
    }

    function activateGravityWell(clickedTerm, allTerms, scroller) {
        clickedTerm.el.classList.add('gravity-active');
        setTimeout(() => clickedTerm.el.classList.remove('gravity-active'), 800);

        const rect = clickedTerm.el.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;

        allTerms.forEach(t => {
            if (t === clickedTerm) return;
            const tr = t.el.getBoundingClientRect();
            const tx = tr.left + tr.width / 2;
            const ty = tr.top + tr.height / 2;
            const d = dist(cx, cy, tx, ty);

            if (d < 350) {
                const ratio = 1 - d / 350;
                const pullX = (cx - tx) * ratio * 0.3;
                const pullY = (cy - ty) * ratio * 0.3;

                t.el.style.transition = 'transform 0.4s cubic-bezier(0.34,1.56,0.64,1)';
                t.el.style.transform = `translate(${pullX}px, ${pullY}px)`;

                setTimeout(() => {
                    t.el.style.transition = 'transform 0.8s cubic-bezier(0.34,1.56,0.64,1)';
                    t.el.style.transform = 'translate(0,0)';
                }, 500);
            }
        });
    }

    /* ───────────────────────────────────────────────────────
       4 · CONSTELLATION CANVAS STAR FIELD
       ─────────────────────────────────────────────────────── */
    function initConstellation() {
        const canvas = document.getElementById('constellationCanvas');
        if (!canvas || prefersReducedMotion) return;

        const ctx = canvas.getContext('2d');
        let W, H, stars = [];
        let mouseX = -9999, mouseY = -9999;
        let idleTimer = 0;
        let isIdle = false;
        let thinkingPulse = false;
        let pulseRadius = 0;

        function resize() {
            W = canvas.width = window.innerWidth;
            H = canvas.height = window.innerHeight;
            buildStars();
        }

        function buildStars() {
            const count = isMobile() ? 80 : 180;
            stars = Array.from({ length: count }, () => ({
                x: Math.random() * W,
                y: Math.random() * H,
                r: 0.5 + Math.random() * 1.5,
                vx: 0, vy: 0,
                ox: 0, oy: 0,   // home offset for drift-back
                brightness: 0.2 + Math.random() * 0.6,
                color: randomStarColor()
            }));
        }

        function randomStarColor() {
            const r = Math.random();
            if (r < 0.6) return 'rgba(232,234,240,';
            if (r < 0.8) return 'rgba(201,168,76,';
            return 'rgba(79,195,247,';
        }

        // LEGAL SYMBOL CONSTELLATIONS  (scales, gavel, scroll)
        // Normalized [0..1] coordinates
        const CONSTELLATIONS = {
            scales: [
                [0.5, 0.3], [0.5, 0.5],
                [0.3, 0.5], [0.7, 0.5],
                [0.3, 0.65], [0.3, 0.75], [0.2, 0.82], [0.4, 0.82],
                [0.7, 0.65], [0.7, 0.75], [0.6, 0.82], [0.8, 0.82],
                [0.5, 0.5]
            ],
            gavel: [
                [0.35, 0.6], [0.45, 0.5], [0.55, 0.4],
                [0.4, 0.45], [0.5, 0.5], [0.55, 0.4],
                [0.65, 0.3], [0.70, 0.35]
            ],
            scroll: [
                [0.3, 0.4], [0.35, 0.35], [0.45, 0.33],
                [0.55, 0.35], [0.65, 0.4], [0.65, 0.55],
                [0.55, 0.6], [0.45, 0.6], [0.35, 0.55], [0.3, 0.4]
            ]
        };

        const SYMKEYS = Object.keys(CONSTELLATIONS);
        let activeSym = null;
        let symAlpha = 0;
        let symFadeDir = 0; // 1=in, -1=out
        let constellStars = [];

        function buildConstellStars(sym) {
            const pts = CONSTELLATIONS[sym];
            constellStars = pts.map(([nx, ny]) => ({
                tx: nx * W, ty: ny * H
            }));
        }

        // Mouse push physics
        const pushRadius = 100;
        on(document, 'mousemove', (e) => {
            mouseX = e.clientX; mouseY = e.clientY;
            idleTimer = 0;
            if (isIdle) {
                isIdle = false;
                symFadeDir = -1;
            }
        }, { passive: true });

        let lastIdle = 0;
        function checkIdle(now) {
            if (now - lastIdle > 200) {
                lastIdle = now;
                idleTimer += 200;
                if (idleTimer >= 3000 && !isIdle) {
                    isIdle = true;
                    activeSym = SYMKEYS[Math.floor(Math.random() * SYMKEYS.length)];
                    buildConstellStars(activeSym);
                    symFadeDir = 1;
                }
            }
        }

        function draw(now) {
            if (_destroyed) return;
            ctx.clearRect(0, 0, W, H);
            checkIdle(now);

            // Update thinking pulse
            if (thinkingPulse) {
                pulseRadius += 4;
                if (pulseRadius > Math.max(W, H)) { thinkingPulse = false; pulseRadius = 0; }
                const a = Math.max(0, 0.15 - pulseRadius / Math.max(W, H) * 0.15);
                ctx.beginPath();
                ctx.arc(W / 2, H / 2, pulseRadius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(201,168,76,${a})`;
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            // Update & draw stars
            stars.forEach(s => {
                const d = dist(mouseX, mouseY, s.x, s.y);
                if (d < pushRadius) {
                    const angle = Math.atan2(s.y - mouseY, s.x - mouseX);
                    const force = (1 - d / pushRadius) * 2;
                    s.vx += Math.cos(angle) * force;
                    s.vy += Math.sin(angle) * force;
                }
                // Spring back to original position
                s.vx += (s.ox - s.x) * 0.04;
                s.vy += (s.oy - s.y) * 0.04;
                s.vx *= 0.88;
                s.vy *= 0.88;
                s.x += s.vx;
                s.y += s.vy;

                ctx.beginPath();
                ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
                ctx.fillStyle = s.color + s.brightness + ')';
                ctx.fill();
            });

            // Constellation overlay
            if (isIdle || symFadeDir !== 0) {
                symAlpha = clamp(symAlpha + symFadeDir * 0.015, 0, 0.9);
                if (symAlpha === 0) symFadeDir = 0;

                if (symAlpha > 0 && constellStars.length > 1) {
                    ctx.beginPath();
                    ctx.moveTo(constellStars[0].tx, constellStars[0].ty);
                    for (let i = 1; i < constellStars.length; i++) {
                        ctx.lineTo(constellStars[i].tx, constellStars[i].ty);
                    }
                    ctx.strokeStyle = `rgba(201,168,76,${symAlpha * 0.4})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();

                    constellStars.forEach(cs => {
                        ctx.beginPath();
                        ctx.arc(cs.tx, cs.ty, 2.5, 0, Math.PI * 2);
                        ctx.fillStyle = `rgba(201,168,76,${symAlpha})`;
                        ctx.fill();
                        ctx.beginPath();
                        ctx.arc(cs.tx, cs.ty, 6, 0, Math.PI * 2);
                        ctx.fillStyle = `rgba(201,168,76,${symAlpha * 0.15})`;
                        ctx.fill();
                    });
                }
            }

            raf(draw);
        }

        on(window, 'resize', resize);
        resize();

        // Public trigger for thinking pulse
        global.LegalAnimations._triggerThinkingPulse = function () {
            thinkingPulse = true;
            pulseRadius = 0;
        };

        raf(draw);
    }

    /* ───────────────────────────────────────────────────────
       5 · MAGNETIC CURSOR GRAVITY ORB
       ─────────────────────────────────────────────────────── */
    function initMagneticCursor() {
        if (isTouch || prefersReducedMotion || isMobile()) return;

        // Create gravity orb (replaces existing cursor-outer / cursor-inner for new effects)
        const orb = document.createElement('div');
        orb.className = 'cursor-gravity-orb';
        orb.id = 'gravityOrb';
        document.body.appendChild(orb);
        orb.style.display = 'block';
        _cleanups.push(() => orb.remove());

        // Nebula trail dots (5)
        const TRAIL_COUNT = 5;
        const BRAND_COLORS = ['#c9a84c', '#4fc3f7', '#9b59b6', '#00e5ff', '#c9a84c'];
        const trailDots = Array.from({ length: TRAIL_COUNT }, (_, i) => {
            const d = document.createElement('div');
            d.className = 'cursor-nebula-dot';
            d.style.background = BRAND_COLORS[i];
            d.style.width = d.style.height = (5 - i) + 'px';
            d.style.zIndex = (9999 - i).toString();
            document.body.appendChild(d);
            _cleanups.push(() => d.remove());
            return { el: d, x: -100, y: -100 };
        });

        let mouseX = -200, mouseY = -200;
        let orbX = -200, orbY = -200;
        let prevPositions = Array(TRAIL_COUNT).fill({ x: -200, y: -200 });

        on(document, 'mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        }, { passive: true });

        // Magnetic pull on interactive elements
        const MAGNETIC_RADIUS = 120;
        const PULL_STRENGTH = 8;
        let magnetTargets = [];

        function refreshMagnetTargets() {
            magnetTargets = Array.from(
                document.querySelectorAll('button:not(:disabled), a, .session-item, .prompt-chip, .debris-term')
            );
        }

        function getNearest() {
            let nearest = null, nearestDist = Infinity;
            magnetTargets.forEach(el => {
                const r = el.getBoundingClientRect();
                const cx = r.left + r.width / 2;
                const cy = r.top + r.height / 2;
                const d = dist(mouseX, mouseY, cx, cy);
                if (d < nearestDist) { nearestDist = d; nearest = { el, cx, cy, d }; }
            });
            return nearestDist < MAGNETIC_RADIUS ? nearest : null;
        }

        // Hover states
        let isReading = false;
        let isOnButton = false;

        on(document, 'mouseover', (e) => {
            const aiText = e.target.closest('.ai-message .message-text');
            const btn = e.target.closest('button, a, .session-item, .prompt-chip');
            isReading = !!aiText;
            isOnButton = !!btn;
        }, { passive: true });

        on(document, 'mouseout', () => {
            isReading = false;
            isOnButton = false;
        }, { passive: true });

        let frame = 0;
        function animOrb() {
            if (_destroyed) return;

            orbX = lerp(orbX, mouseX, 0.12);
            orbY = lerp(orbY, mouseY, 0.12);

            orb.style.left = orbX + 'px';
            orb.style.top = orbY + 'px';

            // Class switching
            orb.classList.toggle('reading-lens', isReading);
            orb.classList.toggle('on-button', isOnButton && !isReading);

            // Magnetic pull (every 3 frames for perf)
            if (frame % 3 === 0) {
                refreshMagnetTargets();
                const near = getNearest();
                magnetTargets.forEach(el => { el.style.removeProperty('--mag-tx'); el.style.removeProperty('--mag-ty'); });
                if (near) {
                    const dx = mouseX - near.cx;
                    const dy = mouseY - near.cy;
                    const ratio = 1 - near.d / MAGNETIC_RADIUS;
                    const tx = dx * ratio * PULL_STRENGTH / MAGNETIC_RADIUS;
                    const ty = dy * ratio * PULL_STRENGTH / MAGNETIC_RADIUS;
                    near.el.style.transform = `translateX(${tx}px) translateY(${ty}px)`;
                    _cleanups.push(() => { if (near.el) near.el.style.transform = ''; });
                } else {
                    // Reset all
                    magnetTargets.forEach(el => {
                        if (el.style.transform && !el.closest('#cosmicSidebar')) {
                            // don't reset sidebar's tilt transform
                        }
                    });
                }
            }

            // Trail dots
            prevPositions.unshift({ x: mouseX, y: mouseY });
            prevPositions = prevPositions.slice(0, TRAIL_COUNT + 4);
            trailDots.forEach((dot, i) => {
                const pos = prevPositions[i + 1] || prevPositions[0];
                dot.x = lerp(dot.x, pos.x, 0.3 - i * 0.04);
                dot.y = lerp(dot.y, pos.y, 0.3 - i * 0.04);
                dot.el.style.left = dot.x + 'px';
                dot.el.style.top = dot.y + 'px';
                dot.el.style.opacity = ((TRAIL_COUNT - i) / TRAIL_COUNT * 0.6).toString();
            });

            frame++;
            raf(animOrb);
        }

        raf(animOrb);
    }

    /* ───────────────────────────────────────────────────────
       6 · 3D CARD TILT + GRAVITATIONAL FIELD
       ─────────────────────────────────────────────────────── */
    function initCardTilt() {
        if (isTouch || prefersReducedMotion) return;

        const sidebar = document.getElementById('sidebarSessions');
        if (!sidebar) return;

        function applyTilt(e) {
            const cards = Array.from(sidebar.querySelectorAll('.session-item'));
            if (!cards.length) return;

            cards.forEach(card => {
                const rect = card.getBoundingClientRect();
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;
                const d = dist(e.clientX, e.clientY, cx, cy);

                if (d < 200) {
                    // 3D tilt
                    const rx = ((e.clientY - cy) / rect.height) * -12;
                    const ry = ((e.clientX - cx) / rect.width) * 12;
                    card.style.transform = `perspective(600px) rotateX(${rx}deg) rotateY(${ry}deg)`;
                } else if (d < 350) {
                    // Gravitational pull — neighbour cards edge toward magnetically
                    const angle = Math.atan2(cy - e.clientY, cx - e.clientX);
                    const pull = (1 - d / 350) * 6;
                    const tx = -Math.cos(angle) * pull;
                    const ty = -Math.sin(angle) * pull;
                    card.style.transform = `translate(${tx}px, ${ty}px)`;
                } else {
                    card.style.transform = '';
                }
            });
        }

        function resetTilts() {
            Array.from(sidebar.querySelectorAll('.session-item')).forEach(card => {
                card.style.transition = 'transform 0.5s cubic-bezier(0.34,1.56,0.64,1)';
                card.style.transform = '';
                setTimeout(() => card.style.transition = '', 500);
            });
        }

        on(sidebar, 'mousemove', applyTilt, { passive: true });
        on(sidebar, 'mouseleave', resetTilts, { passive: true });
    }

    /* ───────────────────────────────────────────────────────
       7 · ACTIVE CARD GOLD PARTICLE RING (every 3s)
       ─────────────────────────────────────────────────────── */
    function initActiveCardRing() {
        if (prefersReducedMotion) return;

        let ringInterval = null;

        function emitRing() {
            const activeCard = document.querySelector('.session-item.active');
            if (!activeCard) return;

            const rect = activeCard.getBoundingClientRect();
            const PARTICLE_COUNT = 12;

            for (let i = 0; i < PARTICLE_COUNT; i++) {
                const p = document.createElement('div');
                p.className = 'card-particle';
                p.style.cssText = `
                    position: fixed;
                    left: ${rect.left + rect.width / 2}px;
                    top: ${rect.top + rect.height / 2}px;
                    z-index: 200;
                    pointer-events: none;
                `;
                document.body.appendChild(p);

                const angle = (i / PARTICLE_COUNT) * Math.PI * 2;
                const radius = rect.width * 0.7;
                const endX = Math.cos(angle) * radius;
                const endY = Math.sin(angle) * radius;

                if (global.gsap) {
                    global.gsap.fromTo(p,
                        { x: 0, y: 0, opacity: 0.9, scale: 1 },
                        {
                            x: endX, y: endY,
                            opacity: 0,
                            scale: 0,
                            duration: 1.2,
                            ease: 'power2.out',
                            onComplete: () => p.remove()
                        }
                    );
                } else {
                    p.style.transition = 'transform 1.2s ease-out, opacity 1.2s ease-out';
                    requestAnimationFrame(() => {
                        p.style.transform = `translate(${endX}px, ${endY}px) scale(0)`;
                        p.style.opacity = '0';
                    });
                    setTimeout(() => p.remove(), 1300);
                }
            }
        }

        ringInterval = setInterval(emitRing, 3000);
        _cleanups.push(() => clearInterval(ringInterval));
    }

    /* ───────────────────────────────────────────────────────
       8 · PHYSICS-BASED MESSAGE ANIMATIONS
       ─────────────────────────────────────────────────────── */
    function initMessagePhysics() {
        if (prefersReducedMotion) return;

        // Listen for new messages added to DOM via MutationObserver
        const messagesArea = document.getElementById('messagesArea');
        if (!messagesArea) return;

        const observer = new MutationObserver(mutations => {
            mutations.forEach(m => {
                m.addedNodes.forEach(node => {
                    if (node.nodeType !== 1) return;
                    if (node.classList.contains('message-bubble')) {
                        const isAI = node.classList.contains('ai-message');
                        const isUser = node.classList.contains('user-message');

                        // Soft push: push existing last message up
                        const siblings = Array.from(messagesArea.querySelectorAll('.message-bubble'));
                        const prevMsg = siblings[siblings.length - 2];
                        if (prevMsg) {
                            prevMsg.classList.add('soft-push');
                            setTimeout(() => prevMsg.classList.remove('soft-push'), 700);
                        }

                        // Apply new message animation class
                        node.classList.add(isAI ? 'new-ai' : isUser ? 'new-user' : '');
                        setTimeout(() => {
                            node.classList.remove('new-ai', 'new-user');
                        }, 800);
                    }
                });
            });
        });

        observer.observe(messagesArea, { childList: true });
        _cleanups.push(() => observer.disconnect());
    }

    /* ───────────────────────────────────────────────────────
       9 · WARP SPEED SESSION TRANSITION
       ─────────────────────────────────────────────────────── */
    function initWarpTransition() {
        if (prefersReducedMotion) return;

        const canvas = document.createElement('canvas');
        canvas.id = 'warpCanvas';
        document.body.appendChild(canvas);
        _cleanups.push(() => canvas.remove());

        const ctx = canvas.getContext('2d');
        let warpActive = false;
        let warpFrame = 0;
        const WARP_DURATION = 25; // frames

        function resizeWarp() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        on(window, 'resize', resizeWarp);
        resizeWarp();

        function drawWarp() {
            if (!warpActive) return;
            ctx.fillStyle = 'rgba(4,6,15,0.3)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const streakCount = 120;
            for (let i = 0; i < streakCount; i++) {
                const y = Math.random() * canvas.height;
                const len = 20 + Math.random() * 200 * (warpFrame / WARP_DURATION);
                const alpha = (warpFrame / WARP_DURATION) * 0.7;
                const col = randomColor();
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(len, y + (Math.random() - 0.5) * 2);
                ctx.strokeStyle = col.replace(/[\d.]+\)$/, alpha + ')');
                ctx.lineWidth = 0.5 + Math.random();
                ctx.stroke();
            }

            warpFrame++;
            if (warpFrame >= WARP_DURATION) {
                warpActive = false;
                canvas.classList.remove('active');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            } else {
                requestAnimationFrame(drawWarp);
            }
        }

        global.LegalAnimations._triggerWarp = function () {
            if (prefersReducedMotion) return;
            warpActive = true;
            warpFrame = 0;
            canvas.classList.add('active');
            drawWarp();
        };
    }

    /* ───────────────────────────────────────────────────────
       10 · BLACK-HOLE SESSION DELETE
       ─────────────────────────────────────────────────────── */
    function initBlackHoleDelete() {
        if (prefersReducedMotion) return;

        global.LegalAnimations._triggerBlackHole = function (sessionEl) {
            if (!sessionEl) return;
            const rect = sessionEl.getBoundingClientRect();

            // Pull siblings toward deleted card
            const siblings = Array.from(document.querySelectorAll('.session-item')).filter(el => el !== sessionEl);
            siblings.forEach(sib => {
                const sr = sib.getBoundingClientRect();
                const cy = rect.top + rect.height / 2;
                const sy = sr.top + sr.height / 2;
                const d = Math.abs(sy - cy);
                if (d < 200) {
                    const pull = (1 - d / 200) * 20;
                    const dir = sy > cy ? -1 : 1;
                    sib.style.transition = 'transform 0.35s ease-in';
                    sib.style.transform = `translateY(${dir * pull}px)`;
                    setTimeout(() => {
                        sib.style.transition = 'transform 0.5s cubic-bezier(0.34,1.56,0.64,1)';
                        sib.style.transform = '';
                    }, 400);
                }
            });

            // Vortex collapse the target card
            if (global.gsap) {
                global.gsap.to(sessionEl, {
                    scale: 0,
                    rotate: 360,
                    opacity: 0,
                    duration: 0.45,
                    ease: 'power2.in',
                    onComplete: () => { sessionEl.style.display = 'none'; }
                });
            } else {
                sessionEl.style.transition = 'transform 0.4s ease-in, opacity 0.4s ease-in';
                sessionEl.style.transform = 'scale(0) rotate(360deg)';
                sessionEl.style.opacity = '0';
            }
        };
    }

    /* ───────────────────────────────────────────────────────
       11 · LEGAL ANNOTATION CARDS (IntersectionObserver)
       ─────────────────────────────────────────────────────── */
    const LEGAL_DEFS = {
        'habeas corpus': 'A writ requiring a person under arrest to be brought before a judge.',
        'mens rea': 'The mental element of a crime; criminal intent.',
        'stare decisis': 'Legal principle to follow precedent of prior decisions.',
        'ratio decidendi': 'The binding part of a judicial decision.',
        'ultra vires': 'Beyond the powers granted by law.',
        'prima facie': 'Based on first impression; accepted until disproved.',
        'res judicata': 'A matter that has been adjudicated by a court.',
        'ex parte': 'Proceedings involving only one party.',
        'force majeure': 'Superior force; unforeseeable circumstances preventing fulfilment.'
    };

    function initAnnotationCards() {
        if (prefersReducedMotion || isMobile()) return;

        const messagesArea = document.getElementById('messagesArea');
        if (!messagesArea) return;

        const annotations = new Map(); // term → annotation element
        let activeAnnotation = null;

        function scanAndAnnotate() {
            const texts = messagesArea.querySelectorAll('.message-text');
            texts.forEach(textEl => {
                if (textEl.dataset.annotated) return;
                textEl.dataset.annotated = '1';

                let html = textEl.innerHTML;
                Object.keys(LEGAL_DEFS).forEach(term => {
                    const re = new RegExp(`\\b(${term})\\b`, 'gi');
                    html = html.replace(re, `<span class="statute-ref" data-term="${term}">$1<span class="statute-tooltip">${LEGAL_DEFS[term]}</span></span>`);
                });
                textEl.innerHTML = html;
            });
        }

        const observer = new MutationObserver(() => scanAndAnnotate());
        observer.observe(messagesArea, { childList: true, subtree: true });
        _cleanups.push(() => observer.disconnect());

        scanAndAnnotate(); // Initial pass
    }

    /* ───────────────────────────────────────────────────────
       12 · THINKING PULSE (synced to AI thinking indicator)
       ─────────────────────────────────────────────────────── */
    function initThinkingSync() {
        if (prefersReducedMotion) return;

        const messagesArea = document.getElementById('messagesArea');
        if (!messagesArea) return;

        const observer = new MutationObserver(mutations => {
            mutations.forEach(m => {
                m.addedNodes.forEach(node => {
                    if (node.id === 'thinkingIndicator') {
                        if (global.LegalAnimations._triggerThinkingPulse) {
                            global.LegalAnimations._triggerThinkingPulse();
                        }
                    }
                });
            });
        });

        observer.observe(messagesArea, { childList: true });
        _cleanups.push(() => observer.disconnect());
    }

    /* ───────────────────────────────────────────────────────
       CUSTOM EVENT HOOKS (patches existing legal_app_v2.js)
       ─────────────────────────────────────────────────────── */
    function patchExistingApp() {
        // We wrap the global jQuery AJAX patterns by intercepting
        // document custom events that we fire from small MutationObserver patches.

        // Session switching → warp
        document.addEventListener('legalai:sessionSwitching', () => {
            if (global.LegalAnimations._triggerWarp) global.LegalAnimations._triggerWarp();
        });

        // Session deleted → black hole
        document.addEventListener('legalai:sessionDeleting', (e) => {
            const el = e.detail && e.detail.element;
            if (global.LegalAnimations._triggerBlackHole) global.LegalAnimations._triggerBlackHole(el);
        });

        // Observe sidebar for session deletions (MutationObserver approach as fallback)
        const sidebarSessions = document.getElementById('sidebarSessions');
        if (sidebarSessions) {
            const obs = new MutationObserver(mutations => {
                mutations.forEach(m => {
                    m.removedNodes.forEach(node => {
                        if (node.classList && node.classList.contains('session-item')) {
                            // Already handled by _triggerBlackHole above or via event
                        }
                    });
                });
            });
            obs.observe(sidebarSessions, { childList: true });
            _cleanups.push(() => obs.disconnect());
        }

        // Intercept .session-delete click to fire event before existing handler
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.session-delete');
            if (btn) {
                const card = btn.closest('.session-item');
                if (card && global.LegalAnimations._triggerBlackHole) {
                    global.LegalAnimations._triggerBlackHole(card);
                }
            }
        }, { capture: true });

        // Intercept session-item click to fire warp
        document.addEventListener('click', (e) => {
            const item = e.target.closest('.session-item');
            if (item && !e.target.closest('.session-delete')) {
                if (global.LegalAnimations._triggerWarp) global.LegalAnimations._triggerWarp();
            }
        }, { capture: true });
    }

    /* ───────────────────────────────────────────────────────
       PUBLIC API : LegalAnimations
       ─────────────────────────────────────────────────────── */
    const LegalAnimations = {

        init() {
            if (prefersReducedMotion) {
                console.log('⚡ LegalAnimations: reduced-motion detected — skipping animations');
                // Still init landing (it will hide itself)
                initLanding();
                return;
            }

            console.log('🌌 LegalAnimations 2026 — initialising Antigravity system…');

            initLanding();
            initConstellation();
            initMagneticCursor();
            initCardTilt();
            initActiveCardRing();
            initMessagePhysics();
            initWarpTransition();
            initBlackHoleDelete();
            initAnnotationCards();
            initThinkingSync();
            patchExistingApp();

            console.log('✨ LegalAnimations ready');
        },

        destroy() {
            _destroyed = true;
            _timelines.forEach(tl => { try { tl.kill(); } catch (e) {} });
            _cleanups.forEach(fn => { try { fn(); } catch (e) {} });
            _cleanups.length = 0;
            _timelines.length = 0;
            console.log('🗑 LegalAnimations destroyed');
        },

        pauseForPerformance() {
            _paused = true;
            console.log('⏸ LegalAnimations paused for performance');
        },

        resume() {
            _paused = false;
            console.log('▶ LegalAnimations resumed');
        },

        // Internal handles (set by sub-systems)
        _triggerWarp: null,
        _triggerBlackHole: null,
        _triggerThinkingPulse: null
    };

    global.LegalAnimations = LegalAnimations;

    /* Auto-init on DOM ready */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => LegalAnimations.init());
    } else {
        LegalAnimations.init();
    }

}(window));
