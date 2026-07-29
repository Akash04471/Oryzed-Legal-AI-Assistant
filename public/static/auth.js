(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function initBackgroundMesh() {
        const canvas = document.getElementById('authBgCanvas');
        if (!canvas || prefersReducedMotion) {
            return;
        }

        const ctx = canvas.getContext('2d');
        let width = 0;
        let height = 0;
        let points = [];
        let nodes = [];
        let panX = 0;
        let panY = 0;
        let targetX = 0;
        let targetY = 0;

        const pointCount = () => (window.innerWidth < 768 ? 80 : 180);
        const nodeCount = () => (window.innerWidth < 768 ? 22 : 52);

        function rand(min, max) {
            return min + Math.random() * (max - min);
        }

        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
            targetX = width / 2;
            targetY = height / 2;

            points = Array.from({ length: pointCount() }, function () {
                return {
                    x: rand(0, width),
                    y: rand(0, height),
                    vx: rand(-0.1, 0.1),
                    vy: rand(-0.08, 0.08)
                };
            });

            nodes = Array.from({ length: nodeCount() }, function () {
                return {
                    x: rand(0, width),
                    y: rand(0, height),
                    vx: rand(-0.25, 0.25),
                    vy: rand(-0.2, 0.2),
                    r: rand(0.7, 2.2),
                    glow: rand(0.25, 0.85)
                };
            });
        }

        function stepParticles() {
            points.forEach(function (p) {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < -10) p.x = width + 10;
                if (p.x > width + 10) p.x = -10;
                if (p.y < -10) p.y = height + 10;
                if (p.y > height + 10) p.y = -10;
            });

            nodes.forEach(function (n) {
                n.x += n.vx;
                n.y += n.vy;
                if (n.x < -6) n.x = width + 6;
                if (n.x > width + 6) n.x = -6;
                if (n.y < -6) n.y = height + 6;
                if (n.y > height + 6) n.y = -6;
            });
        }

        function draw() {
            panX += (targetX - panX) * 0.02;
            panY += (targetY - panY) * 0.02;

            stepParticles();
            ctx.clearRect(0, 0, width, height);

            ctx.save();
            ctx.translate((panX - width / 2) * -0.01, (panY - height / 2) * -0.01);

            for (let i = 0; i < points.length; i++) {
                for (let j = i + 1; j < points.length; j++) {
                    const p1 = points[i];
                    const p2 = points[j];
                    const d = Math.hypot(p2.x - p1.x, p2.y - p1.y);
                    if (d < 120) {
                        const alpha = (1 - d / 120) * 0.18;
                        ctx.strokeStyle = 'rgba(74, 158, 220, ' + alpha + ')';
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
                ctx.fillStyle = 'rgba(127, 214, 255, ' + n.glow + ')';
                ctx.fill();
            });

            ctx.restore();
            requestAnimationFrame(draw);
        }

        window.addEventListener('resize', resize, { passive: true });
        window.addEventListener('mousemove', function (event) {
            targetX = event.clientX;
            targetY = event.clientY;
        }, { passive: true });

        resize();
        requestAnimationFrame(draw);
    }

    function initCard4D() {
        const card = document.querySelector('.auth-shell');
        if (!card || prefersReducedMotion) {
            return;
        }

        const maxTilt = 10;
        const layers = Array.from(card.querySelectorAll('.parallax-layer'));

        function reset() {
            card.style.transform = 'perspective(1100px) rotateX(0deg) rotateY(0deg) translateZ(0)';
            layers.forEach(function (layer) {
                layer.style.transform = 'translate3d(0, 0, 0)';
            });
        }

        card.addEventListener('mousemove', function (event) {
            const rect = card.getBoundingClientRect();
            const x = (event.clientX - rect.left) / rect.width;
            const y = (event.clientY - rect.top) / rect.height;
            const rotateY = (x - 0.5) * maxTilt * 2;
            const rotateX = (0.5 - y) * maxTilt * 2;

            card.style.transform =
                'perspective(1100px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) translateZ(0)';

            layers.forEach(function (layer) {
                const depth = Number(layer.dataset.depth || 8);
                const moveX = (x - 0.5) * depth;
                const moveY = (y - 0.5) * depth;
                layer.style.transform = 'translate3d(' + moveX + 'px, ' + moveY + 'px, 0)';
            });
        });

        card.addEventListener('mouseleave', reset);
        reset();
    }

    function initFocusGlow() {
        const controls = document.querySelectorAll('.auth-input');
        controls.forEach(function (input) {
            input.addEventListener('focus', function () {
                document.body.classList.add('focus-mode');
            });
            input.addEventListener('blur', function () {
                document.body.classList.remove('focus-mode');
            });
        });
    }

    function initAuthLogic() {
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');
        const errorBox = document.getElementById('auth-error-box');

        function showError(msg) {
            if (!errorBox) return;
            errorBox.textContent = msg;
            errorBox.style.display = 'block';
            errorBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        function hideError() {
            if (!errorBox) return;
            errorBox.style.display = 'none';
        }

        async function postData(url, data) {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return response.json();
        }

        // --- Login Logic ---
        if (loginForm) {
            const credentialsStage = document.getElementById('credentials-stage');
            const otpStage = document.getElementById('otp-stage');
            const verifyOtpBtn = document.getElementById('verify-otp-btn');
            const backToLoginBtn = document.getElementById('back-to-login');

            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                hideError();
                const btn = e.submitter;
                const originalText = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Verifying...';

                try {
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const result = await postData('/login', { email, password });

                    if (result.status === 'otp_sent') {
                        credentialsStage.style.display = 'none';
                        otpStage.style.display = 'block';
                    } else {
                        showError(result.message || 'Login failed.');
                    }
                } catch (err) {
                    showError('Server error. Please try again.');
                } finally {
                    btn.disabled = false;
                    btn.textContent = originalText;
                }
            });

            if (verifyOtpBtn) {
                verifyOtpBtn.addEventListener('click', async () => {
                    hideError();
                    verifyOtpBtn.disabled = true;
                    verifyOtpBtn.textContent = 'Verifying OTP...';

                    try {
                        const email = document.getElementById('email').value;
                        const otp = document.getElementById('otp').value;
                        const result = await postData('/verify-login-otp', { email, otp });

                        if (result.status === 'success') {
                            window.location.href = result.redirect;
                        } else {
                            showError(result.message || 'Invalid OTP.');
                        }
                    } catch (err) {
                        showError('Verification failed.');
                    } finally {
                        verifyOtpBtn.disabled = false;
                        verifyOtpBtn.textContent = 'Verify & Login';
                    }
                });
            }

            if (backToLoginBtn) {
                backToLoginBtn.addEventListener('click', () => {
                    otpStage.style.display = 'none';
                    credentialsStage.style.display = 'block';
                    hideError();
                });
            }
        }

        // --- Signup Logic ---
        if (signupForm) {
            const credentialsStage = document.getElementById('credentials-stage');
            const otpStage = document.getElementById('otp-stage');
            const verifyOtpBtn = document.getElementById('verify-otp-btn');
            const backToSignupBtn = document.getElementById('back-to-signup');

            signupForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                hideError();
                const btn = e.submitter;
                const originalText = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Processing...';

                try {
                    const username = document.getElementById('username').value;
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const confirm_password = document.getElementById('confirm_password').value;

                    const result = await postData('/signup', { username, email, password, confirm_password });

                    if (result.status === 'otp_sent') {
                        credentialsStage.style.display = 'none';
                        otpStage.style.display = 'block';
                    } else {
                        showError(result.message || 'Signup failed.');
                    }
                } catch (err) {
                    showError('Server error. Please try again.');
                } finally {
                    btn.disabled = false;
                    btn.textContent = originalText;
                }
            });

            if (verifyOtpBtn) {
                verifyOtpBtn.addEventListener('click', async () => {
                    hideError();
                    verifyOtpBtn.disabled = true;
                    verifyOtpBtn.textContent = 'Creating Account...';

                    try {
                        const username = document.getElementById('username').value;
                        const email = document.getElementById('email').value;
                        const password = document.getElementById('password').value;
                        const otp = document.getElementById('otp').value;
                        
                        const result = await postData('/verify-signup-otp', { username, email, password, otp });

                        if (result.status === 'success') {
                            window.location.href = result.redirect;
                        } else {
                            showError(result.message || 'Verification failed.');
                        }
                    } catch (err) {
                        showError('Signup failed.');
                    } finally {
                        verifyOtpBtn.disabled = false;
                        verifyOtpBtn.textContent = 'Verify & Create Account';
                    }
                });
            }

            if (backToSignupBtn) {
                backToSignupBtn.addEventListener('click', () => {
                    otpStage.style.display = 'none';
                    credentialsStage.style.display = 'block';
                    hideError();
                });
            }
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        initBackgroundMesh();
        initCard4D();
        initFocusGlow();
        initAuthLogic();
    });
})();
