(function () {
    'use strict';

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function initConstellation() {
        const canvas = document.getElementById('termsCanvas');
        if (!canvas || reduceMotion) {
            return;
        }

        const ctx = canvas.getContext('2d');
        let w = 0;
        let h = 0;
        let points = [];
        let nodes = [];
        let tx = 0;
        let ty = 0;
        let px = 0;
        let py = 0;

        function rand(min, max) {
            return min + Math.random() * (max - min);
        }

        function resize() {
            w = canvas.width = window.innerWidth;
            h = canvas.height = window.innerHeight;
            tx = w / 2;
            ty = h / 2;
            points = Array.from({ length: w < 800 ? 95 : 220 }, function () {
                return { x: rand(0, w), y: rand(0, h), vx: rand(-0.12, 0.12), vy: rand(-0.09, 0.09) };
            });
            nodes = Array.from({ length: w < 800 ? 24 : 54 }, function () {
                return { x: rand(0, w), y: rand(0, h), vx: rand(-0.2, 0.2), vy: rand(-0.2, 0.2), r: rand(0.9, 2.6), a: rand(0.35, 0.9) };
            });
        }

        function tick() {
            px += (tx - px) * 0.02;
            py += (ty - py) * 0.02;

            points.forEach(function (p) {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < -12) p.x = w + 12;
                if (p.x > w + 12) p.x = -12;
                if (p.y < -12) p.y = h + 12;
                if (p.y > h + 12) p.y = -12;
            });

            nodes.forEach(function (n) {
                n.x += n.vx;
                n.y += n.vy;
                if (n.x < -8) n.x = w + 8;
                if (n.x > w + 8) n.x = -8;
                if (n.y < -8) n.y = h + 8;
                if (n.y > h + 8) n.y = -8;
            });

            ctx.clearRect(0, 0, w, h);
            ctx.save();
            ctx.translate((px - w / 2) * -0.014, (py - h / 2) * -0.014);

            for (let i = 0; i < points.length; i++) {
                for (let j = i + 1; j < points.length; j++) {
                    const p1 = points[i];
                    const p2 = points[j];
                    const d = Math.hypot(p2.x - p1.x, p2.y - p1.y);
                    if (d < 122) {
                        const alpha = (1 - d / 122) * 0.18;
                        ctx.strokeStyle = 'rgba(79, 195, 247, ' + alpha + ')';
                        ctx.lineWidth = 0.7;
                        ctx.beginPath();
                        ctx.moveTo(p1.x, p1.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                    }
                }
            }

            nodes.forEach(function (n) {
                ctx.beginPath();
                ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(127, 214, 255, ' + n.a + ')';
                ctx.fill();
            });

            ctx.restore();
            requestAnimationFrame(tick);
        }

        window.addEventListener('resize', resize, { passive: true });
        window.addEventListener('mousemove', function (e) {
            tx = e.clientX;
            ty = e.clientY;
        }, { passive: true });

        resize();
        requestAnimationFrame(tick);
    }

    function initReveal() {
        const items = document.querySelectorAll('.reveal-item');
        if (!items.length) {
            return;
        }

        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        items.forEach(function (item, idx) {
            item.style.transitionDelay = Math.min(idx * 25, 200) + 'ms';
            observer.observe(item);
        });
    }

    function initTiltCards() {
        if (reduceMotion) {
            return;
        }

        const cards = document.querySelectorAll('.terms-card, .terms-hero');
        cards.forEach(function (card) {
            card.addEventListener('mousemove', function (e) {
                const r = card.getBoundingClientRect();
                const x = (e.clientX - r.left) / r.width - 0.5;
                const y = (e.clientY - r.top) / r.height - 0.5;
                card.style.transform = 'perspective(1100px) rotateX(' + (-y * 1.8) + 'deg) rotateY(' + (x * 1.8) + 'deg)';
            });
            card.addEventListener('mouseleave', function () {
                card.style.transform = '';
            });
        });
    }

    function initScrollTop() {
        const btn = document.getElementById('scrollTopBtn');
        if (!btn) {
            return;
        }

        function toggle() {
            if (window.scrollY > 220) btn.classList.add('show');
            else btn.classList.remove('show');
        }

        window.addEventListener('scroll', toggle, { passive: true });
        btn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        toggle();
    }

    document.addEventListener('DOMContentLoaded', function () {
        initConstellation();
        initReveal();
        initTiltCards();
        initScrollTop();
    });
})();
