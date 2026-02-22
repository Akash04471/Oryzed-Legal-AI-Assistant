/* ═══ ORYZED LEGAL AI — legal_app.js ═══ */
(function (W) {
    'use strict';

    const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isTouch = 'ontouchstart' in W;
    const mobile = () => innerWidth < 768;

    /* ─── Lady Justice Node Data (normalized 0-1) ───
       Format: [x, y]  — portrait canvas aspect */
    const LJ = {
        // nodes: [x, y]
        N: [
            [.44, .02], [.50, .00], [.56, .02], [.47, .04], [.53, .04],   // 0-4  crown
            [.43, .06], [.57, .06], [.40, .10], [.60, .10], [.50, .08],   // 5-9  head
            [.42, .13], [.58, .13], [.50, .16],                        // 10-12 chin/cheeks
            [.50, .17], [.47, .19], [.53, .19],                        // 13-15 neck
            [.38, .21], [.33, .24], [.62, .21], [.67, .24],              // 16-19 shoulders
            [.29, .24], [.24, .29], [.21, .35], [.22, .41], [.23, .47],   // 20-24 left arm
            [.20, .49], [.15, .51], [.25, .51], [.20, .57], [.20, .67], [.21, .77], [.21, .85], // 25-31 sword
            [.71, .22], [.78, .18], [.83, .22], [.86, .27], [.87, .31],   // 32-36 right arm
            [.87, .29], [.78, .32], [.87, .32], [.96, .30],             // 37-40 scale beam
            [.74, .35], [.80, .35], [.77, .40],                        // 41-43 left pan
            [.92, .33], [.98, .33], [.95, .38],                        // 44-46 right pan
            [.40, .25], [.60, .25], [.50, .28], [.42, .32], [.58, .32],   // 47-51 chest
            [.40, .38], [.60, .38], [.50, .40],                        // 52-54 torso
            [.42, .46], [.50, .47], [.58, .46],                        // 55-57 waist
            [.39, .52], [.50, .53], [.61, .52],                        // 58-60 hips
            [.31, .57], [.28, .64], [.30, .72], [.32, .80], [.35, .88],   // 61-65 robe left-outer
            [.38, .58], [.36, .66], [.38, .74], [.39, .84],             // 66-69 robe left-mid
            [.50, .57], [.48, .65], [.51, .73], [.50, .82], [.50, .91],   // 70-74 robe center
            [.62, .58], [.64, .66], [.63, .74], [.62, .83],             // 75-78 robe right-mid
            [.69, .57], [.72, .64], [.70, .72], [.68, .80], [.65, .88],   // 79-83 robe right-outer
            [.37, .94], [.44, .96], [.50, .97], [.56, .96], [.63, .94],   // 84-88 base
        ],
        // edges: [i, j]
        E: [
            [0, 1], [1, 2], [0, 3], [3, 1], [1, 4], [4, 2],
            [3, 5], [4, 6], [5, 9], [9, 6], [5, 7], [6, 8], [7, 10], [8, 11], [9, 7], [9, 8], [10, 12], [11, 12],
            [12, 13], [13, 14], [13, 15], [14, 16], [15, 18], [16, 17], [18, 19],
            [17, 20], [20, 21], [21, 22], [22, 23], [23, 24],
            [24, 25], [26, 25], [27, 25], [26, 27], [25, 28], [28, 29], [29, 30], [30, 31],
            [19, 32], [32, 33], [33, 34], [34, 35], [35, 36],
            [36, 37], [37, 38], [38, 39], [38, 40], [38, 41], [40, 44],
            [41, 42], [41, 43], [42, 43], [44, 45], [44, 46], [45, 46],
            [16, 47], [18, 48], [47, 49], [48, 49], [47, 50], [48, 51], [49, 50], [49, 51],
            [50, 52], [51, 53], [52, 54], [53, 54], [50, 52], [51, 53],
            [52, 55], [53, 56], [54, 57], [55, 58], [56, 60], [57, 59],
            [58, 61], [58, 66], [59, 70], [60, 75], [60, 79],
            [61, 62], [62, 63], [63, 64], [64, 65], [66, 67], [67, 68], [68, 69],
            [70, 71], [71, 72], [72, 73], [73, 74], [75, 76], [76, 77], [77, 78],
            [79, 80], [80, 81], [81, 82], [82, 83],
            [61, 66], [62, 67], [63, 68], [64, 69], [66, 70], [67, 71], [68, 72], [69, 73],
            [70, 75], [71, 76], [72, 77], [73, 78], [75, 79], [76, 80], [77, 81], [78, 82],
            [65, 84], [69, 85], [74, 86], [78, 87], [83, 88],
            [84, 85], [85, 86], [86, 87], [87, 88],
        ],
        // triangles: [i, j, k]
        T: [
            [3, 1, 5], [4, 1, 6], [5, 9, 7], [6, 9, 8], [7, 9, 10], [8, 9, 11], [10, 9, 12], [11, 9, 12],
            [14, 16, 47], [15, 18, 48], [16, 18, 49], [47, 48, 49],
            [47, 49, 50], [48, 49, 51], [50, 51, 54], [50, 52, 54], [51, 53, 54],
            [52, 54, 55], [53, 54, 57], [55, 56, 59], [55, 58, 59], [56, 57, 60],
            [58, 61, 66], [59, 70, 75], [60, 75, 79], [58, 59, 70], [59, 60, 75],
            [61, 62, 66], [62, 66, 67], [62, 63, 67], [63, 67, 68], [63, 64, 68], [64, 68, 69], [64, 65, 69],
            [66, 67, 70], [67, 70, 71], [67, 68, 71], [68, 71, 72], [68, 69, 72], [69, 72, 73],
            [70, 71, 75], [71, 75, 76], [71, 72, 76], [72, 76, 77], [72, 73, 77], [73, 77, 78],
            [75, 76, 79], [76, 79, 80], [76, 77, 80], [77, 80, 81], [77, 78, 81], [78, 81, 82],
            [65, 84, 85], [69, 85, 86], [74, 86, 87], [78, 87, 88], [83, 82, 88],
            [41, 42, 43], [44, 45, 46],
            [20, 21, 22], [22, 23, 24], [32, 33, 34], [34, 35, 36],
        ],
    };

    /* ─── Shared LJ Renderer ─── */
    function drawLJ(ctx, cw, ch, opts = {}) {
        const { alpha = 1, glow = true, scaleSwayAngle = 0, particleT = 1 } = opts;
        const N = LJ.N.map(([nx, ny]) => ({ x: nx * cw, y: ny * ch }));

        ctx.save();
        ctx.globalAlpha = alpha;

        // Triangles
        LJ.T.forEach(([a, b, c]) => {
            ctx.beginPath();
            ctx.moveTo(N[a].x, N[a].y); ctx.lineTo(N[b].x, N[b].y); ctx.lineTo(N[c].x, N[c].y);
            ctx.closePath();
            ctx.fillStyle = 'rgba(6,32,64,0.72)';
            ctx.fill();
            ctx.strokeStyle = 'rgba(74,158,220,0.28)'; ctx.lineWidth = 0.7; ctx.stroke();
        });

        // Edges
        LJ.E.forEach(([a, b]) => {
            ctx.beginPath(); ctx.moveTo(N[a].x, N[a].y); ctx.lineTo(N[b].x, N[b].y);
            ctx.strokeStyle = 'rgba(79,195,247,0.5)'; ctx.lineWidth = 0.9; ctx.stroke();
        });

        // Nodes
        const bright = new Set([0, 1, 2, 9, 12, 36, 37, 40, 31, 84, 85, 86, 87, 88]);
        N.forEach((p, i) => {
            const r = bright.has(i) ? 3 : 1.8;
            const col = bright.has(i) ? '#a8e6ff' : '#4fc3f7';
            if (glow && bright.has(i)) {
                ctx.beginPath(); ctx.arc(p.x, p.y, r + 6, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(168,230,255,0.12)'; ctx.fill();
            }
            ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
            ctx.fillStyle = col; ctx.fill();
        });

        // Scale sway (nodes 37-46)
        if (scaleSwayAngle !== 0) {
            const pivot = N[37];
            ctx.save(); ctx.translate(pivot.x, pivot.y); ctx.rotate(scaleSwayAngle);
            ctx.strokeStyle = 'rgba(201,168,76,0.9)'; ctx.lineWidth = 1.5;
            [[38, -9, 0], [40, 9, 0]].forEach(([ni, dx]) => {
                const off = N[ni];
                ctx.beginPath(); ctx.moveTo(0, 0);
                ctx.lineTo(off.x - pivot.x, off.y - pivot.y); ctx.stroke();
            });
            ctx.restore();
        }

        // Stars scattered through figure
        ctx.globalAlpha = alpha * Math.min(particleT, 1) * 0.65;
        const stars = [
            [.46, .12], [.52, .20], [.44, .30], [.56, .35], [.48, .44], [.53, .50], [.46, .60], [.54, .68], [.49, .76], [.51, .84],
            [.35, .27], [.65, .27], [.38, .40], [.62, .40], [.36, .54], [.64, .54], [.40, .65], [.60, .65], [.38, .75], [.62, .75],
            [.32, .62], [.70, .62], [.30, .72], [.72, .70], [.43, .92], [.57, .92],
            [.22, .32], [.20, .50], [.84, .25], [.82, .38], [.77, .30], [.93, .35],
        ];
        stars.forEach(([sx, sy]) => {
            ctx.beginPath(); ctx.arc(sx * cw, sy * ch, .9, 0, Math.PI * 2);
            ctx.fillStyle = '#7dd4fc'; ctx.fill();
        });
        ctx.restore();
    }

    /* ─── Loading Sequence ─── */
    const Loader = (function () {
        let canvas, ctx, CW, CH;
        const statusEl = document.getElementById('loadingStatus');
        const barEl = document.getElementById('loadingBar');
        const brandEl = document.getElementById('loadingBrand');

        function setBar(p) { if (barEl) barEl.style.width = p + '%'; }
        function setStatus(t) { if (statusEl) statusEl.textContent = t; }

        function run(done) {
            canvas = document.getElementById('ladyJusticeCanvas');
            if (!canvas || RM) { document.getElementById('loadingScreen').style.display = 'none'; done(); return; }
            CW = canvas.width = canvas.offsetWidth; CH = canvas.height = canvas.offsetHeight;
            ctx = canvas.getContext('2d');

            const N = LJ.N.map(([nx, ny]) => ({ x: nx * CW, y: ny * CH }));
            const cx = CW / 2, cy = CH * 0.38;

            // Phase 1: single point
            setStatus('Awakening…'); setBar(5);
            ctx.clearRect(0, 0, CW, CH);
            ctx.beginPath(); ctx.arc(cx, cy, 3, 0, Math.PI * 2);
            ctx.fillStyle = '#a8e6ff'; ctx.fill();

            setTimeout(() => {
                // Phase 2: scatter nodes
                setStatus('Summoning the figure…'); setBar(22);
                const parts = N.map(p => ({ ...p, px: cx, py: cy }));
                let t = 0, rafId;
                function scatter() {
                    t += 0.018;
                    const e = Math.min(t, 1);
                    const ease = 1 - Math.pow(1 - e, 3);
                    ctx.clearRect(0, 0, CW, CH);
                    parts.forEach((p, i) => {
                        const px = cx + (p.x - cx) * ease, py = cy + (p.y - cy) * ease;
                        ctx.beginPath(); ctx.arc(px, py, 2, 0, Math.PI * 2);
                        ctx.fillStyle = `rgba(168,230,255,${0.3 + ease * 0.7})`; ctx.fill();
                    });
                    if (e < 1) rafId = requestAnimationFrame(scatter);
                    else { cancelAnimationFrame(rafId); drawEdges(); }
                }
                requestAnimationFrame(scatter);
            }, 600);

            function drawEdges() {
                setStatus('Weaving skeleton…'); setBar(48);
                let i = 0;
                function next() {
                    if (i >= LJ.E.length) { fillFaces(); return; }
                    const [a, b] = LJ.E[i++];
                    ctx.beginPath(); ctx.moveTo(N[a].x, N[a].y); ctx.lineTo(N[b].x, N[b].y);
                    ctx.strokeStyle = 'rgba(74,158,220,0.55)'; ctx.lineWidth = 0.9; ctx.stroke();
                    [a, b].forEach(idx => {
                        ctx.beginPath(); ctx.arc(N[idx].x, N[idx].y, 2, 0, Math.PI * 2);
                        ctx.fillStyle = '#4fc3f7'; ctx.fill();
                    });
                    setTimeout(next, 14);
                }
                next();
            }

            function fillFaces() {
                setStatus('Filling the form…'); setBar(70);
                let i = 0;
                function next() {
                    if (i >= LJ.T.length) { finalize(); return; }
                    const [a, b, c] = LJ.T[i++];
                    ctx.beginPath();
                    ctx.moveTo(N[a].x, N[a].y); ctx.lineTo(N[b].x, N[b].y); ctx.lineTo(N[c].x, N[c].y);
                    ctx.closePath(); ctx.fillStyle = 'rgba(6,32,64,0.75)'; ctx.fill();
                    ctx.strokeStyle = 'rgba(74,158,220,0.3)'; ctx.lineWidth = 0.7; ctx.stroke();
                    setTimeout(next, 22);
                }
                next();
            }

            function finalize() {
                setStatus('Calibrating scales…'); setBar(88);
                // Draw complete figure then type brand
                ctx.clearRect(0, 0, CW, CH);
                let sway = 0, t2 = 0;
                function breathe() {
                    t2 += 0.045;
                    sway = Math.sin(t2) * 0.08 * Math.max(0, 1 - t2 / 5);
                    ctx.clearRect(0, 0, CW, CH);
                    drawLJ(ctx, CW, CH, { scaleSwayAngle: sway, particleT: Math.min(t2 / 3, 1) });
                    if (t2 < 4) requestAnimationFrame(breathe);
                    else typeOryzed();
                }
                requestAnimationFrame(breathe);
            }

            function typeOryzed() {
                setStatus(''); setBar(100);
                const txt = 'ORYZED';
                let i = 0; if (brandEl) brandEl.textContent = '';
                function t() {
                    if (i >= txt.length) { setTimeout(() => exitLoader(done), 600); return; }
                    if (brandEl) brandEl.textContent += txt[i++];
                    setTimeout(t, 90);
                }
                t();
            }

            function exitLoader(done) {
                setStatus('Entering the Judicial Cosmos…');
                fetch('/api/health').catch(() => { }).finally(() => {
                    setTimeout(() => {
                        const ls = document.getElementById('loadingScreen');
                        ls.classList.add('fade-out');
                        setTimeout(() => { ls.style.display = 'none'; done(); }, 700);
                    }, 300);
                });
            }
        }
        return { run };
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

        function rand(a, b) { return a + Math.random() * (b - a); }

        function reset() {
            W = canvas.width = innerWidth;
            H = canvas.height = innerHeight;
            targetX = W / 2; targetY = H / 2;
            pts = Array.from({ length: PC() }, () => ({ x: rand(0, W), y: rand(0, H), vx: rand(-.1, .1), vy: rand(-.08, .08) }));
            [[0, 0], [W, 0], [0, H], [W, H], [W / 2, 0], [W / 2, H], [0, H / 2], [W, H / 2]].forEach(([x, y]) => pts.push({ x, y, vx: 0, vy: 0 }));
            nodes = Array.from({ length: NC() }, () => ({ x: rand(0, W), y: rand(H * .1, H), vx: rand(-.3, .3), vy: rand(-.4, -.1), r: rand(1, 2.5), b: rand(.4, .9) }));
            rebuildTris();
        }

        function rebuildTris() {
            tris = [];
            pts.forEach(p => {
                const near = pts.filter(q => q !== p).map(q => [q, Math.hypot(q.x - p.x, q.y - p.y)]).sort((a, b) => a[1] - b[1]).slice(0, 2).map(e => e[0]);
                if (near.length === 2) tris.push([p, near[0], near[1]]);
            });
        }

        function frame() {
            panX += (targetX - panX) * 0.04; panY += (targetY - panY) * 0.04;
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
            if (thinkWave) { thinkWave.r += 3.5; thinkWave.a *= 0.96; if (thinkWave.a < 0.005) thinkWave = null; }

            ctx.clearRect(0, 0, W, H);
            ctx.save(); ctx.translate(panX, panY);
            tris.forEach(([a, b, c]) => {
                if (Math.hypot(b.x - a.x, b.y - a.y) > 230) return;
                const d = Math.sin(Date.now() * .0004 + a.x * .01) * .06 + .05;
                ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.lineTo(c.x, c.y); ctx.closePath();
                ctx.fillStyle = `rgba(6,32,64,${d})`; ctx.fill();
                ctx.strokeStyle = 'rgba(74,158,220,0.1)'; ctx.lineWidth = .5; ctx.stroke();
            });
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const d = Math.hypot(nodes[j].x - nodes[i].x, nodes[j].y - nodes[i].y);
                    if (d < 110) {
                        const a = (1 - d / 110) * .3;
                        ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.strokeStyle = `rgba(74,158,220,${a})`; ctx.lineWidth = .7; ctx.stroke();
                    }
                }
            }
            nodes.forEach(n => { ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2); ctx.fillStyle = `rgba(79,195,247,${n.b})`; ctx.fill(); });
            ctx.restore();
            ripples.forEach(r => { ctx.beginPath(); ctx.arc(r.x, r.y, r.rad, 0, Math.PI * 2); ctx.strokeStyle = `rgba(79,195,247,${r.a})`; ctx.lineWidth = 1.5; ctx.stroke(); });
            if (thinkWave) { ctx.beginPath(); ctx.arc(W / 2, H / 2, thinkWave.r, 0, Math.PI * 2); ctx.strokeStyle = `rgba(79,195,247,${thinkWave.a})`; ctx.lineWidth = 2.5; ctx.stroke(); }
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

    /* ─── Hero LJ Canvas (animated) ─── */
    function setupHeroCanvas() {
        const canvas = document.getElementById('heroLJCanvas');
        if (!canvas || RM) return;
        const parent = canvas.parentElement;
        canvas.width = parent.offsetWidth;
        canvas.height = Math.round(parent.offsetWidth * 1.35);
        canvas.style.height = canvas.height + 'px';
        const ctx = canvas.getContext('2d');
        let t = 0;
        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const sway = Math.sin(t * 0.7) * 0.04;
            drawLJ(ctx, canvas.width, canvas.height, { scaleSwayAngle: sway, particleT: 1 });
            // Pulse glow on crown
            const N = LJ.N.map(([nx, ny]) => ({ x: nx * canvas.width, y: ny * canvas.height }));
            const gp = ctx.createRadialGradient(N[1].x, N[1].y, 0, N[1].x, N[1].y, 40);
            gp.addColorStop(0, `rgba(168,230,255,${.12 + Math.sin(t) * 0.06})`);
            gp.addColorStop(1, 'transparent');
            ctx.fillStyle = gp; ctx.beginPath(); ctx.arc(N[1].x, N[1].y, 40, 0, Math.PI * 2); ctx.fill();
            // Scale glow
            const sp = N[37];
            const sg = ctx.createRadialGradient(sp.x, sp.y, 0, sp.x, sp.y, 25);
            sg.addColorStop(0, `rgba(201,168,76,${.18 + Math.cos(t * 1.2) * 0.06})`);
            sg.addColorStop(1, 'transparent');
            ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(sp.x, sp.y, 25, 0, Math.PI * 2); ctx.fill();
            t += 0.012;
            requestAnimationFrame(loop);
        }
        requestAnimationFrame(loop);
    }

    /* ─── CTA Mini LJ ─── */
    function setupCtaMini() {
        const canvas = document.getElementById('ctaLJMini');
        if (!canvas || RM) return;
        const ctx = canvas.getContext('2d');
        let t = 0;
        function loop() {
            ctx.clearRect(0, 0, 180, 180);
            drawLJ(ctx, 180, 180, { alpha: .85, glow: true, scaleSwayAngle: Math.sin(t * .6) * .05, particleT: 1 });
            t += 0.012; requestAnimationFrame(loop);
        }
        requestAnimationFrame(loop);
    }

    /* ─── Chat Ghost LJ Canvas ─── */
    function setupChatGhost() {
        const canvas = document.getElementById('chatLJCanvas');
        if (!canvas || RM) return;
        const SIZE = Math.min(600, innerWidth * 0.85);
        canvas.width = SIZE;
        canvas.height = Math.round(SIZE * 1.35);
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawLJ(ctx, canvas.width, canvas.height, { alpha: 1, glow: false, particleT: 1 });
    }

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
        }
        function toggle() { sidebar.classList.contains('open') ? close() : open(); }

        btn.addEventListener('click', toggle);
        overlay.addEventListener('click', close);
        W.LegalAI = W.LegalAI || {};
        W.LegalAI.closeSidebar = close;
        W.LegalAI.openSidebar = open;
    }

    /* ─── Scrollytelling ─── */
    function initScrollytelling() {
        const io = new IntersectionObserver((entries) => {
            entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('revealed'); });
        }, { threshold: 0.15 });
        document.querySelectorAll('.reveal-item').forEach(el => io.observe(el));
    }

    /* ─── Transition: Landing → Chat ─── */
    function enterChat() {
        const landing = document.getElementById('landingPage');
        const chat = document.getElementById('chatApp');
        if (!landing || !chat) return;
        landing.classList.add('fade-out');
        setTimeout(() => {
            landing.style.display = 'none';
            chat.removeAttribute('hidden');
            chat.removeAttribute('aria-hidden');
            requestAnimationFrame(() => chat.classList.add('visible'));
            setupChatGhost();
            App.loadSessions();
            App.newSession();
        }, 620);
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
            inner.style.cssText += `;left:${mx}px;top:${my}px`;
            outer.style.cssText += `;left:${ox}px;top:${oy}px`;
            requestAnimationFrame(ani);
        }());
        document.addEventListener('mouseover', e => { if (e.target.closest('button,a,.session-item,.prompt-chip,textarea')) outer.classList.add('hover'); });
        document.addEventListener('mouseout', e => { if (e.target.closest('button,a,.session-item,.prompt-chip,textarea')) outer.classList.remove('hover'); });
    }

    /* ─── App State & Chat Logic ─── */
    const App = (function () {
        const S = { sessionId: null, sessions: [], loading: false, scrolledUp: false };
        const g = id => document.getElementById(id);

        function esc(s) {
            return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }
        function fmtDate(ts) {
            try { const d = new Date((ts || '').replace(' ', 'T') + 'Z'); return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }); } catch { return ''; }
        }

        async function loadSessions() {
            try {
                const res = await fetch('/api/sessions');
                const data = await res.json();
                S.sessions = data.sessions || [];
                renderSessions();
            } catch (e) { console.error(e); }
        }

        function renderSessions() {
            const c = g('sidebarSessions'); if (!c) return;
            c.innerHTML = '';
            if (!S.sessions.length) {
                c.innerHTML = '<div class="sessions-empty"><i class="fas fa-balance-scale"></i><p>No consultations yet</p></div>';
                return;
            }
            S.sessions.forEach((s, i) => { const el = buildSessionEl(s); el.style.animationDelay = (i * .05) + 's'; el.classList.add('slide-up'); c.appendChild(el); });
        }

        function buildSessionEl(s) {
            const div = document.createElement('div');
            div.className = 'session-item' + (s.id === S.sessionId ? ' active' : '');
            div.setAttribute('role', 'listitem');
            div.innerHTML = `<div class="session-icon"><i class="fas fa-balance-scale"></i></div>
            <div class="session-details"><div class="session-title">${esc(s.title)}</div><div class="session-meta">${fmtDate(s.updated_at)}</div></div>
            <button class="session-delete icon-btn" aria-label="Delete"><i class="fas fa-times"></i></button>`;
            div.addEventListener('click', e => { if (!e.target.closest('.session-delete')) switchSession(s.id); });
            div.querySelector('.session-delete').addEventListener('click', e => { e.stopPropagation(); deleteSession(s.id, div); });
            return div;
        }

        async function newSession() {
            try {
                const res = await fetch('/api/new_session', { method: 'POST' });
                const data = await res.json();
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
                const res = await fetch(`/api/chat/${id}`);
                const data = await res.json();
                (data.history || []).forEach(m => appendMsg(m.role, m.content, false));
                scrollBot(false);
            } catch (e) { console.error(e); }
        }

        async function deleteSession(id, el) {
            el.style.cssText += 'transition:transform .4s ease,opacity .4s ease;transform:scale(0) rotate(360deg);opacity:0;';
            setTimeout(async () => {
                try { await fetch(`/api/delete_session/${id}`, { method: 'DELETE' }); } catch (e) { }
                if (id === S.sessionId) { S.sessionId = null; const ma = g('messagesArea'); if (ma) ma.innerHTML = ''; const es = g('emptyState'); if (es) es.style.display = ''; }
                await loadSessions();
            }, 460);
        }

        const THINK_TEXTS = ['Analyzing precedents…', 'Reviewing statutes…', 'Consulting case law…', 'Formulating opinion…', 'Researching judgments…'];
        let _ti = null;

        function showThinking() {
            BgCanvas.pulse();
            const bub = document.createElement('div');
            bub.className = 'message-bubble ai-message'; bub.id = '_think_bub';
            let idx = 0;
            bub.innerHTML = `<div class="msg-avatar"><svg class="ai-avatar-svg" width="36" height="36" viewBox="0 0 36 36" fill="none"><polygon points="18,4 30,28 6,28" stroke="#4fc3f7" stroke-width="1.5" fill="rgba(26,110,181,0.15)"/><circle cx="18" cy="4" r="2" fill="#a8e6ff"/><circle cx="30" cy="28" r="2" fill="#4fc3f7"/><circle cx="6" cy="28" r="2" fill="#4fc3f7"/></svg></div>
            <div class="msg-content"><div class="thinking-indicator"><svg class="thinking-tri" width="24" height="24" viewBox="0 0 24 24" fill="none"><polygon points="12,3 21,18 3,18" stroke="#4fc3f7" stroke-width="1.5" fill="rgba(26,110,181,0.2)"/></svg><span class="thinking-text">${THINK_TEXTS[0]}</span></div></div>`;
            const ma = g('messagesArea'); if (ma) { ma.appendChild(bub); autoScroll(); }
            const te = bub.querySelector('.thinking-text');
            _ti = setInterval(() => { if (!te) return; te.style.opacity = '0'; setTimeout(() => { idx = (idx + 1) % THINK_TEXTS.length; te.textContent = THINK_TEXTS[idx]; te.style.opacity = '1'; }, 300); }, 2500);
            return bub;
        }

        function hideThinking(bub) { clearInterval(_ti); if (bub && bub.parentNode) bub.parentNode.removeChild(bub); }

        function appendMsg(role, content, animate = true) {
            const isAI = role === 'assistant' || role === 'ai';
            const es = g('emptyState'); if (es && es.style.display !== 'none') es.style.display = 'none';
            const bub = document.createElement('div');
            bub.className = `message-bubble ${isAI ? 'ai-message' : 'user-message'}`;
            const safeHTML = isAI ? DOMPurify.sanitize(marked.parse(content)) : esc(content);
            bub.innerHTML = isAI
                ? `<div class="msg-avatar"><svg class="ai-avatar-svg" width="36" height="36" viewBox="0 0 36 36" fill="none"><polygon points="18,4 30,28 6,28" stroke="#4fc3f7" stroke-width="1.5" fill="rgba(26,110,181,0.15)"/><circle cx="18" cy="4" r="2" fill="#a8e6ff"/><circle cx="30" cy="28" r="2" fill="#4fc3f7"/><circle cx="6" cy="28" r="2" fill="#4fc3f7"/></svg></div><div class="msg-content"><div class="msg-role-label">Oryzed AI</div><div class="message-text ai-text"></div></div>`
                : `<div class="msg-content"><div class="msg-role-label">You</div><div class="message-text">${safeHTML}</div></div>`;
            const ma = g('messagesArea'); if (ma) ma.appendChild(bub);
            if (animate && isAI) { animAIText(bub.querySelector('.ai-text'), content); BgCanvas.addRipple(innerWidth / 2, innerHeight - 120); }
            else if (isAI) { const t = bub.querySelector('.ai-text'); if (t) t.innerHTML = DOMPurify.sanitize(marked.parse(content)); }
            autoScroll();
        }

        function animAIText(container, raw) {
            const html = DOMPurify.sanitize(marked.parse(raw));
            if (RM || !container) { if (container) container.innerHTML = html; return; }
            const tmp = document.createElement('div'); tmp.innerHTML = html;
            let i = 0;
            function wrap(node) {
                if (node.nodeType === 3) {
                    const frag = document.createDocumentFragment();
                    node.textContent.split(/(\s+)/).forEach(w => {
                        if (w.trim()) {
                            const sp = document.createElement('span'); sp.className = 'word-token';
                            sp.style.animationDelay = (i++ * 18) + 'ms'; sp.textContent = w;
                            frag.appendChild(sp); frag.appendChild(document.createTextNode(' '));
                        } else { frag.appendChild(document.createTextNode(w)); }
                    });
                    node.parentNode.replaceChild(frag, node);
                } else if (node.childNodes) { Array.from(node.childNodes).forEach(wrap); }
            }
            wrap(tmp); container.appendChild(tmp);
        }

        async function sendMessage() {
            const ta = g('cosmicTextarea'); const bs = g('btnSend');
            if (!ta || S.loading) return;
            const text = ta.value.trim(); if (!text) return;

            if (!S.sessionId) await newSession();
            S.loading = true; ta.value = ''; if (ta) { ta.style.height = ''; } updateCounter();
            if (bs) { bs.disabled = true; bs.classList.add('sending'); particleBurst(bs); setTimeout(() => bs.classList.remove('sending'), 550); }
            appendMsg('user', text, true);
            const thinkBub = showThinking();
            try {
                const res = await fetch(`/api/chat/${S.sessionId}/message`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text }) });
                const data = await res.json();
                hideThinking(thinkBub);
                appendMsg('assistant', data.response || 'I encountered an error. Please try again.', true);
                await loadSessions();
            } catch (e) { hideThinking(thinkBub); appendMsg('assistant', 'Network error. Please try again.', true); }
            finally { S.loading = false; if (bs) bs.disabled = false; if (ta) ta.focus(); }
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
            const ta = g('cosmicTextarea'), cc = g('charCount'), bs = g('btnSend');
            if (!ta || !cc) return; const n = ta.value.length; cc.textContent = n;
            if (bs) bs.disabled = n === 0 || S.loading;
        }

        function particleBurst(btn) {
            if (RM) return;
            const r = btn.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
            for (let i = 0; i < 8; i++) {
                const p = document.createElement('div'); p.className = 'send-particle'; p.style.cssText = `left:${cx}px;top:${cy}px;`;
                document.body.appendChild(p);
                const a = (i / 8) * Math.PI * 2, sp = 40 + Math.random() * 40, vx = Math.cos(a) * sp, vy = Math.sin(a) * sp;
                let lx = cx, ly = cy, op = 1;
                (function an() {
                    lx += vx * .07; ly += vy * .07; op -= .045; p.style.cssText = `position:fixed;left:${lx}px;top:${ly}px;opacity:${op};width:5px;height:5px;border-radius:50%;background:#4fc3f7;pointer-events:none;z-index:9000;`;
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
                ta.addEventListener('input', () => { updateCounter(); ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'; });
                ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
            }

            document.addEventListener('click', e => {
                const chip = e.target.closest('.prompt-chip');
                if (chip) { const ta2 = g('cosmicTextarea'); if (ta2) { ta2.value = chip.dataset.prompt || ''; ta2.focus(); updateCounter(); ta2.style.height = 'auto'; ta2.style.height = Math.min(ta2.scrollHeight, 160) + 'px'; } }
            });

            const cw = g('chatWrapper');
            if (cw) cw.addEventListener('scroll', () => {
                S.scrolledUp = cw.scrollHeight - cw.scrollTop - cw.clientHeight > 80;
                if (!S.scrolledUp) { const p = g('newMsgPill'); if (p) p.hidden = true; }
            }, { passive: true });
        }

        return { loadSessions, newSession, wireEvents, sendMessage };
    }());

    /* ─── Bootstrap ─── */
    document.addEventListener('DOMContentLoaded', () => {
        BgCanvas.setup();
        initCursor();
        initHamburger();
        initScrollytelling();
        App.wireEvents();

        // Show landing page
        const lp = document.getElementById('landingPage');
        if (lp) { lp.removeAttribute('aria-hidden'); }

        if (RM) {
            const ls = document.getElementById('loadingScreen');
            if (ls) ls.style.display = 'none';
            initScrollytelling();
            setupHeroCanvas(); setupCtaMini();
        } else {
            Loader.run(() => {
                setupHeroCanvas();
                setupCtaMini();
            });
        }
    });

}(window));
