"""Quick verification script for LegalAI 2026 animation files."""
import sys

results = []

def check(label, condition):
    status = "OK" if condition else "MISSING"
    results.append((status, label))

# ── legal_animations.js ──────────────────────────────────────
with open("static/js/legal_animations.js", encoding="utf-8") as f:
    js = f.read()

for token in [
    "LegalAnimations", "init()", "destroy()", "pauseForPerformance()",
    "initLanding", "initConstellation", "initMagneticCursor",
    "initCardTilt", "initActiveCardRing", "initMessagePhysics",
    "initWarpTransition", "initBlackHoleDelete", "initAnnotationCards",
    "prefersReducedMotion", "_triggerWarp", "_triggerBlackHole",
    "_triggerThinkingPulse", "window.LegalAnimations",
]:
    check(f"JS: {token}", token in js)

# ── legal_animations.css ─────────────────────────────────────
with open("static/css/legal_animations.css", encoding="utf-8") as f:
    css = f.read()

for token in [
    "#landingOverlay", ".landing-section", ".hero-scales-svg",
    "#constellationCanvas", ".cursor-gravity-orb", ".cursor-nebula-dot",
    "@keyframes breathe", "@keyframes aiBounceIn", "@keyframes userArcLaunch",
    "prefers-reduced-motion", "#warpCanvas", ".legal-annotation",
    ".timeline-era", ".debris-term",
]:
    check(f"CSS: {token}", token in css)

# ── legal_chat_v3.html ───────────────────────────────────────
with open("templates/legal_chat_v3.html", encoding="utf-8") as f:
    html = f.read()

for token in [
    "landingOverlay", "constellationCanvas", "btnEnterCosmos",
    "legal_animations.css", "legal_animations.js", "legal_app_v2.js",
    "gsap.min.js", "ScrollTrigger.min.js",
    "timeline-era", "debris-field", "landing-hero", "landing-cta",
    "messagesArea", "cosmicTextarea", "btnSend", "sidebarSessions",
    "counterParticleField",
]:
    check(f"HTML: {token}", token in html)

# ── app.py ───────────────────────────────────────────────────
with open("app.py", encoding="utf-8") as f:
    app_src = f.read()

check("app.py: serves legal_chat_v3.html", "legal_chat_v3.html" in app_src)

# ── Report ───────────────────────────────────────────────────
ok_count = sum(1 for s, _ in results if s == "OK")
miss_count = sum(1 for s, _ in results if s == "MISSING")

print(f"\n{'='*55}")
print(f" LegalAI 2026 Animation System — Verification Report")
print(f"{'='*55}")
for status, label in results:
    icon = "✓" if status == "OK" else "✗"
    print(f"  {icon}  {label}")
print(f"{'='*55}")
print(f"  PASSED: {ok_count}   MISSING: {miss_count}")
print(f"{'='*55}\n")

sys.exit(0 if miss_count == 0 else 1)
