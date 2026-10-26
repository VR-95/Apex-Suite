// ─────────────────────────────────────────────────────────────────────────────
//  APEX SUITE  ·  React Frontend  ·  All 11 Modules
//  Design: Warm Reading Room (dark)  |  Accent: Sage #8FAA7A + Warm Gold #D9A054
//  Stack: React 18 · Groq API (openai/gpt-oss-120b) · Supabase Analytics
//  v2.0: Multi-key API fallback · Developer Analytics Dashboard
//  Setup: npm create vite@latest apex-suite -- --template react
//         npm install && copy this file to src/App.jsx && npm run dev
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useEffect, useRef, useCallback } from "react"
import { motion, AnimatePresence, useReducedMotion } from "motion/react"
import logoImg from "./assets/logo.png"

// ── DESIGN TOKENS ─────────────────────────────────────────────────────────────
const CSS = `
  :root {
    --bg:       #14100C;
    --surface:  #1B1510;
    --card:     #221B14;
    --muted:    #2E2419;
    --cyan:     #8FAA7A;
    --purple:   #D9A054;
    --green:    #4A9B6E;
    --amber:    #C2652E;
    --red:      #E0654F;
    --text:     #F0E8DC;
    --dim:      #A8998A;
    --border:   rgba(240,232,220,0.09);
    --sidebar:  240px;
    --sidebar-s:72px;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  /* Respect OS-level reduced-motion preference — collapses every CSS
     animation/transition to effectively instant while still landing on
     the correct final state (opacity, position, etc.), rather than
     leaving elements stuck at their animation-start values. */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
  html { scroll-behavior: smooth; }
  body {
    background:
      radial-gradient(ellipse 800px 600px at 12% -8%, rgba(143,170,122,0.07), transparent 60%),
      radial-gradient(ellipse 900px 700px at 88% 105%, rgba(217,160,84,0.06), transparent 60%),
      var(--bg);
    background-attachment: fixed;
    color: var(--text);
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
    overflow-x: hidden;
    cursor: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiIgdmlld0JveD0iMCAwIDMyIDMyIj4KPHBvbHlnb24gcG9pbnRzPSIyNi41LDkuNyAyOS4zLDYuOSAyNS4xLDIuNyAyMi4zLDUuNSIgZmlsbD0iI0UwNjU0RiIgc3Ryb2tlPSIjMkUyNjIwIiBzdHJva2Utd2lkdGg9IjAuNiIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8cG9seWdvbiBwb2ludHM9IjEzLjgsMjIuNSAyNi41LDkuNyAyMi4zLDUuNSA5LjUsMTguMiIgZmlsbD0iI0Q5QTA1NCIgc3Ryb2tlPSIjMkUyNjIwIiBzdHJva2Utd2lkdGg9IjAuNiIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8cG9seWdvbiBwb2ludHM9IjguNSwyNS43IDEzLjgsMjIuNSA5LjUsMTguMiA2LjQsMjMuNSIgZmlsbD0iI0YwRThEQyIgc3Ryb2tlPSIjMkUyNjIwIiBzdHJva2Utd2lkdGg9IjAuNiIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8cG9seWdvbiBwb2ludHM9IjYsMjYgOC41LDI1LjcgNi40LDIzLjUiIGZpbGw9IiMyRTI2MjAiLz4KPC9zdmc+") 6 26, auto !important;
  }
  /* !important here is deliberate — there are 13+ places across the app
     (buttons, cards, nav items) that set cursor:pointer for standard click
     affordance. Without forcing this, every one of them silently wins over
     the body rule via CSS specificity, which is exactly why the pencil
     wasn't showing on the landing page cards. This one rule fixes all of
     them at the source instead of editing each individually. */
  /* Second, independent layer: every element, including pseudo-elements and
     anything added later, inherits the pencil from body. Universal selector
     has the lowest specificity, so the explicit text-input exceptions
     below (element selectors, more specific) still correctly win for typing. */
  *, *::before, *::after { cursor: inherit !important; }
  input, textarea, select, [contenteditable="true"] { cursor: text !important; }
  select { cursor: pointer !important; }
  ::selection { background: rgba(143,170,122,0.2); }
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--muted); border-radius: 99px; }

  /* ── LAYOUT ── */
  .layout { display: flex; min-height: 100vh; }
  .sidebar {
    position: fixed; left: 0; top: 0;
    width: var(--sidebar); height: 100vh;
    background: linear-gradient(180deg, rgba(27,21,16,0.68) 0%, rgba(27,21,16,0.52) 100%);
    border-right: 1px solid rgba(240,232,220,0.09);
    display: flex; flex-direction: column;
    z-index: 100; overflow: hidden;
    transition: width 0.25s cubic-bezier(0.4,0,0.2,1);
  }
  @supports (backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px)) {
    .sidebar { backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
  }
  @supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
    .sidebar { background: var(--surface); }
  }
  .sidebar.sm { width: var(--sidebar-s); }
  .main {
    margin-left: var(--sidebar);
    flex: 1; padding: 2rem 2.5rem;
    min-height: 100vh;
    transition: margin-left 0.25s cubic-bezier(0.4,0,0.2,1);
  }
  .main.sm { margin-left: var(--sidebar-s); }

  /* ── PAGE TRANSITION ── */
  .page { }
  @keyframes pageIn {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── SIDEBAR INTERNALS ── */
  .sb-top {
    display: flex; align-items: center; gap: 10px;
    padding: 18px 16px; border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }
  .sb-logo {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, var(--cyan) 0%, var(--purple) 100%);
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 15px; color: var(--bg); flex-shrink: 0;
  }
  .sb-title {
    font-size: 15px; font-weight: 800; letter-spacing: -0.03em;
    white-space: nowrap; overflow: hidden;
  }
  .sb-nav { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 8px 0; }
  .sb-section {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--dim); padding: 12px 16px 4px;
    white-space: nowrap; overflow: hidden;
  }
  .nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 12px 9px 14px; margin: 1px 8px;
    border-radius: 8px; cursor: pointer; white-space: nowrap;
    color: var(--dim); font-size: 13px; font-weight: 500;
    transition: all 0.15s; position: relative; overflow: hidden;
  }
  .nav-item:hover { background: var(--muted); color: var(--text); }
  .nav-item.active {
    background: rgba(143,170,122,0.1); color: var(--cyan);
    border-left: 2px solid var(--cyan); margin-left: 6px; padding-left: 12px;
  }
  .nav-icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
  .nav-label { overflow: hidden; white-space: nowrap; }
  .sb-bottom {
    padding: 12px 8px; border-top: 1px solid var(--border); flex-shrink: 0;
  }
  .toggle-btn {
    width: 100%; padding: 8px; border-radius: 8px;
    background: none; border: 1px solid var(--border);
    color: var(--dim); cursor: pointer; font-size: 16px;
    transition: all 0.15s; display: flex; align-items: center; justify-content: center;
  }
  .toggle-btn:hover { background: var(--muted); color: var(--text); }

  /* ── CARD  ·  dark glassmorphism ── */
  .card {
    background: linear-gradient(135deg, rgba(34,27,20,0.62) 0%, rgba(34,27,20,0.42) 100%);
    border: 1px solid rgba(240,232,220,0.10);
    border-radius: 12px; padding: 1.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.18);
    transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
  }
  @supports (backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px)) {
    .card {
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }
  }
  @supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
    /* Older browsers / reduced-transparency settings — solid fallback,
       never left half-transparent with nothing to blur beneath it. */
    .card { background: var(--card); }
  }
  .card.interactive:hover {
    border-color: rgba(143,170,122,0.35);
    box-shadow: 0 4px 24px rgba(143,170,122,0.08);
    transform: translateY(-2px); cursor: pointer;
  }
  .card.glow { border-color: rgba(143,170,122,0.22); }

  /* ── BUTTONS ── */
  .btn {
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px; border: none; border-radius: 8px;
    font-family: inherit; font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all 0.15s; white-space: nowrap;
    padding: 0.6rem 1.25rem;
  }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn-primary {
    background: var(--cyan); color: var(--bg);
  }
  .btn-primary:hover:not(:disabled) { box-shadow: 0 0 20px rgba(143,170,122,0.35); }
  .btn-primary:active:not(:disabled) { transform: scale(0.97); }
  .btn-secondary {
    background: transparent; color: var(--cyan);
    border: 1px solid rgba(143,170,122,0.35);
  }
  .btn-secondary:hover:not(:disabled) { background: rgba(143,170,122,0.08); border-color: var(--cyan); }
  .btn-ghost {
    background: var(--muted); color: var(--dim); border: none;
  }
  .btn-ghost:hover:not(:disabled) { background: var(--card); color: var(--text); }
  .btn-danger { background: rgba(239,68,68,0.15); color: var(--red); border: none; }
  .btn-danger:hover { background: rgba(239,68,68,0.25); }
  .btn-sm { padding: 0.35rem 0.85rem; font-size: 12px; }
  .btn-full { width: 100%; }
  .btn-icon {
    width: 34px; height: 34px; padding: 0; border-radius: 8px;
    background: var(--muted); color: var(--dim); border: none; font-size: 15px;
  }
  .btn-icon:hover { background: var(--card); color: var(--text); }

  /* ── FORM ELEMENTS ── */
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .label {
    font-size: 11px; font-weight: 700; color: var(--dim);
    text-transform: uppercase; letter-spacing: 0.06em;
  }
  .input, .textarea, .select-el {
    background: var(--muted); border: 1px solid var(--border);
    border-radius: 8px; padding: 0.65rem 0.9rem;
    color: var(--text); font-family: inherit; font-size: 13px;
    width: 100%; transition: border-color 0.2s, box-shadow 0.2s;
    appearance: none;
  }
  .input::placeholder, .textarea::placeholder { color: var(--dim); }
  .input:focus, .textarea:focus, .select-el:focus {
    outline: none; border-color: var(--cyan);
    box-shadow: 0 0 0 3px rgba(143,170,122,0.12);
  }
  .textarea { resize: vertical; min-height: 110px; line-height: 1.6; }
  .select-el { cursor: pointer; }

  /* ── PROGRESS ── */
  .progress-bar {
    height: 4px; background: var(--muted); border-radius: 99px; overflow: hidden;
  }
  .progress-fill {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, var(--cyan) 0%, var(--purple) 100%);
    transition: width 0.4s ease;
  }

  /* ── BADGES ── */
  .badge {
    display: inline-flex; align-items: center;
    padding: 3px 10px; border-radius: 99px;
    font-size: 11px; font-weight: 700;
  }
  .badge-cyan   { background: rgba(143,170,122,0.12); color: var(--cyan); }
  .badge-green  { background: rgba(16,185,129,0.12); color: var(--green); }
  .badge-amber  { background: rgba(245,158,11,0.12); color: var(--amber); }
  .badge-red    { background: rgba(239,68,68,0.12);  color: var(--red); }
  .badge-purple { background: rgba(217,160,84,0.15); color: #a78bfa; }
  .badge-dim    { background: rgba(255,255,255,0.07); color: var(--dim); }

  /* ── TABS ── */
  .tabs { display: flex; gap: 2px; background: var(--muted); border-radius: 10px; padding: 3px; }
  .tab {
    flex: 1; padding: 7px 14px; border-radius: 8px;
    background: none; border: none; color: var(--dim);
    font-family: inherit; font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all 0.15s; white-space: nowrap;
  }
  .tab.active { background: var(--card); color: var(--text); }

  /* ── METRIC CARD ── */
  .metric { background: var(--card); border-radius: 10px; padding: 1rem 1.2rem; }
  .metric-label { font-size: 11px; color: var(--dim); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
  .metric-value { font-size: 26px; font-weight: 800; letter-spacing: -0.03em; }
  .metric-sub { font-size: 11px; color: var(--dim); margin-top: 2px; }

  /* ── DIVIDER ── */
  .divider { height: 1px; background: var(--border); margin: 1.5rem 0; }

  /* ── GRID HELPERS ── */
  .g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; }
  .g4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; }
  .g2-heavy { display: grid; grid-template-columns: 1.3fr 1fr; gap: 1.5rem; }
  .col { display: flex; flex-direction: column; gap: 1rem; }
  .row { display: flex; align-items: center; gap: 0.75rem; }

  /* ── SECTION HEADER ── */
  .sh { margin-bottom: 1.75rem; }
  .sh-title { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 4px; }
  .sh-caption { color: var(--dim); font-size: 13px; }
  .sh-icon-badge {
    width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.35rem; margin-top: 2px;
    background: linear-gradient(135deg, rgba(143,170,122,0.18), rgba(217,160,84,0.12));
    border: 1px solid rgba(143,170,122,0.20);
    box-shadow: 0 4px 18px rgba(143,170,122,0.10);
  }

  /* ── SKELETON / LOADING ── */
  .skeleton {
    background: linear-gradient(90deg, var(--card) 25%, var(--muted) 50%, var(--card) 75%);
    background-size: 200% 100%; animation: shimmer 1.4s infinite;
    border-radius: 8px;
  }
  @keyframes shimmer { to { background-position: -200% 0; } }
  .spin { animation: spin 0.8s linear infinite; display: inline-block; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── TOAST ── */
  .toast {
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    background: var(--card); border: 1px solid var(--border);
    border-left: 3px solid var(--cyan); border-radius: 10px;
    padding: 12px 18px; font-size: 13px; font-weight: 500;
    animation: toastIn 0.25s ease-out;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    max-width: 320px;
  }
  @keyframes toastIn { from { opacity:0; transform:translateY(12px); } }

  /* ── MODAL ── */
  .modal-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.7);
    z-index: 200; display: flex; align-items: center; justify-content: center;
    animation: fadeIn 0.15s ease;
  }
  .modal {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 16px; padding: 2rem; width: 420px;
    animation: modalIn 0.2s ease-out;
  }
  @keyframes fadeIn  { from { opacity:0; } }
  @keyframes modalIn { from { opacity:0; transform:translateY(-16px) scale(0.97); } }

  /* ── HUB SPECIFIC ── */
  .hub-hero {
    background: linear-gradient(135deg, rgba(143,170,122,0.05) 0%, rgba(217,160,84,0.05) 100%);
    border: 1px solid rgba(143,170,122,0.1);
    border-radius: 20px; padding: 2.5rem;
    display: flex; align-items: center; gap: 3rem; margin-bottom: 2rem;
    position: relative; overflow: hidden;
  }
  .hub-ring { flex-shrink: 0; position: relative; z-index: 1; }
  .ring-track { fill: none; stroke: rgba(255,255,255,0.07); stroke-width: 8; }
  .ring-fill {
    fill: none; stroke: var(--cyan); stroke-width: 8;
    stroke-linecap: round;
    transform: rotate(-90deg); transform-origin: center;
    transition: stroke-dashoffset 1.1s cubic-bezier(0.16,1,0.3,1);
    filter: drop-shadow(0 0 6px rgba(143,170,122,0.5));
  }
  @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.7;} }
  .ring-pulse { animation: pulse 2.5s ease-in-out infinite; }

  /* ── ALIVE BACKGROUND ORBS ── */
  .hub-orb { position: absolute; border-radius: 50%; filter: blur(60px); pointer-events: none; z-index: 0; }
  .hub-orb-1 {
    width: 320px; height: 320px; opacity: 0.30;
    background: radial-gradient(circle, var(--cyan) 0%, transparent 70%);
    top: -90px; left: -60px; animation: orbFloat1 14s ease-in-out infinite;
  }
  .hub-orb-2 {
    width: 280px; height: 280px; opacity: 0.26;
    background: radial-gradient(circle, var(--purple) 0%, transparent 70%);
    top: 20px; right: -50px; animation: orbFloat2 18s ease-in-out infinite;
  }
  .hub-orb-3 {
    width: 200px; height: 200px; opacity: 0.22;
    background: radial-gradient(circle, var(--green) 0%, transparent 70%);
    bottom: -70px; left: 35%; animation: orbFloat3 16s ease-in-out infinite;
  }
  @keyframes orbFloat1 {
    0%,100% { transform: translate(0,0) scale(1); }
    33%     { transform: translate(30px,20px) scale(1.1); }
    66%     { transform: translate(-15px,30px) scale(0.95); }
  }
  @keyframes orbFloat2 {
    0%,100% { transform: translate(0,0) scale(1); }
    50%     { transform: translate(-25px,25px) scale(1.08); }
  }
  @keyframes orbFloat3 {
    0%,100% { transform: translate(0,0) scale(1); }
    40%     { transform: translate(20px,-15px) scale(1.06); }
    70%     { transform: translate(-20px,-5px) scale(0.96); }
  }

  /* ── GRADIENT TEXT ── */
  .gradient-text {
    background: linear-gradient(90deg, var(--cyan), #a78bfa, var(--cyan));
    background-size: 200% auto;
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; color: transparent;
    animation: gradientShift 6s linear infinite;
  }
  @keyframes gradientShift {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
  }

  /* ── LIVE PULSE DOT ── */
  .live-dot {
    display: inline-block; width: 7px; height: 7px; border-radius: 50%;
    background: var(--green); margin-right: 7px; position: relative; top: -1px;
    animation: livePulse 2s ease-out infinite;
  }
  @keyframes livePulse {
    0%   { box-shadow: 0 0 0 0 rgba(16,185,129,0.55); }
    70%  { box-shadow: 0 0 0 8px rgba(16,185,129,0); }
    100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
  }

  /* ── MODULE CARD ── */
  .mod-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; padding: 1.5rem 1.25rem;
    text-align: center; cursor: pointer;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    opacity: 0;
    animation: cardIn 0.55s cubic-bezier(0.16,1,0.3,1) forwards;
  }
  @keyframes cardIn {
    from { opacity: 0; transform: translateY(18px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
  }
  .mod-card:hover {
    border-color: rgba(143,170,122,0.35);
    transform: translateY(-4px);
    box-shadow: 0 10px 32px rgba(143,170,122,0.10);
  }
  .icon-badge {
    width: 52px; height: 52px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.55rem; margin: 0 auto 0.85rem;
    transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1);
  }
  .mod-card:hover .icon-badge { transform: scale(1.1) rotate(-4deg); }
  .mod-icon { font-size: 2rem; margin-bottom: 0.75rem; display: block; }
  .mod-title { font-size: 14px; font-weight: 700; margin-bottom: 4px; }
  .mod-desc { font-size: 11.5px; color: var(--dim); line-height: 1.5; }

  /* ── FEATURED CARD ── */
  .featured-card {
    background: linear-gradient(135deg, rgba(143,170,122,0.08) 0%, rgba(217,160,84,0.08) 100%);
    border: 1px solid rgba(143,170,122,0.2);
    border-radius: 14px; padding: 1.5rem 2rem;
    display: flex; align-items: center; gap: 1.5rem; cursor: pointer;
    transition: all 0.2s;
  }
  .featured-card:hover { border-color: rgba(143,170,122,0.5); transform: translateY(-2px); }

  /* ── WIZARD ── */
  .wizard-steps {
    display: flex; align-items: center; gap: 0; margin-bottom: 2rem;
  }
  .w-step {
    display: flex; align-items: center; gap: 0;
  }
  .w-dot {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; flex-shrink: 0;
    transition: all 0.2s;
  }
  .w-dot.done { background: var(--cyan); color: var(--bg); }
  .w-dot.active { background: rgba(143,170,122,0.2); color: var(--cyan); border: 2px solid var(--cyan); }
  .w-dot.idle { background: var(--muted); color: var(--dim); }
  .w-line { flex: 1; height: 2px; background: var(--border); min-width: 20px; }
  .w-line.done { background: var(--cyan); }

  /* ── SCORE RING ── */
  .score-ring-fill {
    fill: none; stroke-width: 10; stroke-linecap: round;
    transform: rotate(-90deg); transform-origin: center;
    transition: stroke-dashoffset 0.7s ease;
  }

  /* ── KANBAN ── */
  .kanban { display: flex; gap: 1rem; overflow-x: auto; padding-bottom: 0.5rem; }
  .kb-col { flex: 0 0 210px; }
  .kb-head {
    padding: 8px 12px; border-radius: 8px;
    font-size: 11px; font-weight: 700; margin-bottom: 10px;
    text-align: center;
  }
  .kb-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 12px;
    margin-bottom: 8px; transition: border-color 0.15s;
  }
  .kb-card:hover { border-color: rgba(143,170,122,0.25); }
  .kb-company { font-size: 13px; font-weight: 700; margin-bottom: 2px; }
  .kb-role { font-size: 11px; color: var(--dim); }
  .kb-date { font-size: 10px; color: var(--dim); margin-top: 6px; }

  /* ── SKILL CHIPS ── */
  .chip-row { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip {
    padding: 3px 10px; border-radius: 99px;
    font-size: 11px; font-weight: 600;
  }
  .chip-g { background: rgba(16,185,129,0.12); color: var(--green); }
  .chip-r { background: rgba(239,68,68,0.12);  color: var(--red); }
  .chip-b { background: rgba(143,170,122,0.10);   color: var(--cyan); }
  .chip-y { background: rgba(245,158,11,0.12);  color: var(--amber); }

  /* ── OUTPUT BOX ── */
  .output {
    background: var(--muted); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.25rem;
    font-size: 13px; line-height: 1.75;
    animation: pageIn 0.25s ease;
  }
  .output p { margin-bottom: 0.9em; }
  .output p:last-child { margin-bottom: 0; }
  .output ul { margin: 0.4em 0 0.9em 1.2em; }
  .output li { margin-bottom: 0.4em; }
  .output b { color: var(--text); font-weight: 700; }
  .copy-row { display: flex; justify-content: flex-end; margin-top: 8px; }

  /* ── ROADMAP WEEK ── */
  .week-card {
    border-left: 3px solid; border-radius: 0 10px 10px 0;
    padding: 1rem 1.25rem; background: var(--card);
    margin-bottom: 1rem; transition: all 0.15s;
  }
  .week-card:hover { transform: translateX(3px); }

  /* ── ACCORDION ── */
  .accordion { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin-bottom: 8px; }
  .acc-head {
    width: 100%; text-align: left; padding: 12px 16px;
    background: var(--card); border: none; color: var(--text);
    font-family: inherit; font-size: 13px; font-weight: 600;
    cursor: pointer; display: flex; justify-content: space-between; align-items: center;
  }
  .acc-body { padding: 12px 16px; background: var(--muted); font-size: 13px; line-height: 1.7; }

  /* ══════════════════════════════════════════════════════════════════
     LANDING PAGE  ·  Warm library / academic theme
     Scoped ENTIRELY under .landing-page — cannot affect any other page.
     ══════════════════════════════════════════════════════════════════ */
  .landing-page {
    --lp-bg:         #F7F1E3;
    --lp-bg2:        #FFFDF7;
    --lp-ink:        #2E2620;
    --lp-ink-dim:    #8A7B68;
    --lp-amber:      #C97F4C;
    --lp-amber-soft: #EFD9BE;
    --lp-sage:       #6F8863;
    --lp-sage-soft:  #DCE4D1;
    --lp-border:     rgba(46,38,32,0.11);
    --lp-shadow:     rgba(66,48,28,0.14);

    background: var(--lp-bg);
    color: var(--lp-ink);
    border-radius: 24px;
    padding: 2.75rem 3rem 3.25rem;
    position: relative;
    overflow: hidden;
  }
  .lp-serif { font-family: 'Fraunces', Georgia, serif; font-optical-sizing: auto; }

  .lp-blob { position: absolute; border-radius: 50%; filter: blur(70px); pointer-events: none; z-index: 0; }
  .lp-blob-1 {
    width: 340px; height: 340px; opacity: 0.30;
    background: radial-gradient(circle, var(--lp-sage) 0%, transparent 72%);
    top: -100px; right: -80px; animation: lpFloat1 20s ease-in-out infinite;
  }
  .lp-blob-2 {
    width: 260px; height: 260px; opacity: 0.28;
    background: radial-gradient(circle, var(--lp-amber) 0%, transparent 72%);
    bottom: -90px; left: -60px; animation: lpFloat2 17s ease-in-out infinite;
  }
  @keyframes lpFloat1 {
    0%,100% { transform: translate(0,0) scale(1); }
    50%     { transform: translate(-24px,22px) scale(1.07); }
  }
  @keyframes lpFloat2 {
    0%,100% { transform: translate(0,0) scale(1); }
    50%     { transform: translate(20px,-18px) scale(1.05); }
  }

  .lp-hero {
    display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 3rem;
    align-items: center; position: relative; z-index: 1; margin-bottom: 2.75rem;
  }
  .lp-eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 12px; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase;
    color: var(--lp-amber);
  }
  .lp-eyebrow-dot {
    width: 6px; height: 6px; border-radius: 50%; background: var(--lp-sage);
    animation: lpPulseDot 2.2s ease-out infinite;
  }
  @keyframes lpPulseDot {
    0%   { box-shadow: 0 0 0 0 rgba(111,136,99,0.45); }
    70%  { box-shadow: 0 0 0 8px rgba(111,136,99,0); }
    100% { box-shadow: 0 0 0 0 rgba(111,136,99,0); }
  }
  .lp-title {
    font-size: 2.6rem; line-height: 1.1; font-weight: 600; letter-spacing: -0.02em;
    margin-bottom: 18px; color: var(--lp-ink);
  }
  .lp-title em { font-style: italic; color: var(--lp-amber); }
  .lp-sub { font-size: 14.5px; line-height: 1.75; color: var(--lp-ink-dim); max-width: 440px; margin-bottom: 22px; }
  .lp-badges { display: flex; gap: 8px; flex-wrap: wrap; }
  .lp-badge {
    padding: 5px 13px; border-radius: 99px; font-size: 11.5px; font-weight: 600;
    background: var(--lp-bg2); border: 1px solid var(--lp-border); color: var(--lp-ink);
  }
  .lp-badge-amber { background: var(--lp-amber-soft); color: #8A4E28; border-color: transparent; }
  .lp-badge-sage  { background: var(--lp-sage-soft);  color: #3E5236; border-color: transparent; }

  .lp-illustration { position: relative; display: flex; align-items: center; justify-content: center; height: 260px; }
  .lp-illo-glow {
    position: absolute; width: 220px; height: 220px; border-radius: 50%;
    background: radial-gradient(circle, rgba(201,127,76,0.22) 0%, transparent 70%);
    animation: pulse 3.5s ease-in-out infinite;
  }
  .lp-illo-book { position: relative; z-index: 2; color: var(--lp-ink); }
  .lp-illo-scatter { position: absolute; color: var(--lp-sage); opacity: 0.55; z-index: 1; }
  .lp-illo-scatter.amber { color: var(--lp-amber); }

  .lp-section-label { display: flex; align-items: center; gap: 14px; margin-bottom: 1.4rem; position: relative; z-index: 1; }
  .lp-section-label span {
    font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--lp-ink-dim);
  }
  .lp-section-line { flex: 1; height: 1px; background: var(--lp-border); }

  .lp-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; position: relative; z-index: 1; }
  .lp-card {
    background: var(--lp-bg2); border: 1px solid var(--lp-border);
    border-radius: 16px; padding: 1.5rem 1.25rem; text-align: center; cursor: pointer;
    box-shadow: 0 2px 10px var(--lp-shadow);
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    opacity: 0; animation: lpCardIn 0.55s cubic-bezier(0.16,1,0.3,1) forwards;
  }
  @keyframes lpCardIn {
    from { opacity: 0; transform: translateY(16px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
  }
  .lp-card:hover { transform: translateY(-4px); box-shadow: 0 14px 30px var(--lp-shadow); border-color: var(--lp-amber); }
  .lp-card-icon {
    width: 50px; height: 50px; border-radius: 50%; margin: 0 auto 0.85rem;
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1);
  }
  .lp-card:hover .lp-card-icon { transform: scale(1.1) rotate(-4deg); }
  .lp-card-title { font-size: 13.5px; font-weight: 700; margin-bottom: 4px; color: var(--lp-ink); }
  .lp-card-desc  { font-size: 11px; color: var(--lp-ink-dim); line-height: 1.5; }
  .lp-signature {
    position: relative; z-index: 1;
    display: flex; align-items: center; justify-content: flex-end; gap: 12px;
    margin-top: 2.25rem; padding-top: 1.1rem;
    border-top: 1px solid var(--lp-border);
  }
  .lp-signature span {
    font-size: 11px; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--lp-ink-dim);
  }
  .lp-signature img { height: 46px; width: auto; display: block; }

  @media (max-width: 900px) {
    .lp-hero { grid-template-columns: 1fr; }
    .lp-illustration { display: none; }
    .lp-grid { grid-template-columns: repeat(2,1fr); }
  }

  /* ── SETTINGS ── */
  .settings-row { display: flex; align-items: center; justify-content: space-between; }

  /* ── DEVELOPER DASHBOARD ── */
  .dev-table { width:100%; border-collapse:collapse; font-size:12px; }
  .dev-table th { text-align:left; padding:8px 12px; font-size:10px; font-weight:700;
    color:var(--dim); text-transform:uppercase; letter-spacing:0.06em;
    border-bottom:1px solid var(--border); background:var(--muted); }
  .dev-table td { padding:8px 12px; border-bottom:1px solid var(--border);
    vertical-align:top; max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .dev-table tr:hover td { background:rgba(255,255,255,0.02); }
  .dev-badge { display:inline-flex; align-items:center; gap:4px; padding:2px 8px;
    border-radius:99px; font-size:10px; font-weight:700;
    background:rgba(239,68,68,0.12); color:var(--red); }
  .dev-lock { display:flex; flex-direction:column; align-items:center; justify-content:center;
    min-height:60vh; gap:1.5rem; }
  .stat-bar-row { display:flex; align-items:center; gap:12px; margin-bottom:6px; }
  .stat-bar-label { width:140px; font-size:12px; color:var(--dim); flex-shrink:0;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .stat-bar-track { flex:1; height:7px; background:var(--muted); border-radius:99px; overflow:hidden; }
  .stat-bar-fill { height:100%; background:var(--cyan); border-radius:99px; transition:width 0.4s; }
  .stat-bar-val { font-size:12px; font-weight:700; min-width:24px; text-align:right; }
  .key-status { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }
  .key-ok  { background:var(--green); box-shadow:0 0 6px var(--green); }
  .key-off { background:var(--dim); }
`

// ── GROQ API  ·  Calls FastAPI backend — key is secure on the server ─────────
// The first argument (apiKeys) is kept for compatibility but ignored.
// All AI calls go through /api/groq on the FastAPI backend.
async function groq(_ignored, system, user, json = false) {
  const res = await fetch("/api/groq", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ system, user, json_mode: json })
  })
  if (!res.ok) {
    const e = await res.json().catch(() => ({}))
    throw new Error(e.detail || `Server error ${res.status}`)
  }
  const data = await res.json()
  return data.result   // already parsed if json_mode=true
}

// ── DOCUMENT DOWNLOAD  ·  calls a backend /api/documents/* route, ────────────
// gets back real file bytes, and triggers a browser download — used by
// Resume Builder (PDF), Portfolio Builder (PPTX), and Cheat Sheet (PDF).
async function downloadDocument(endpoint, payload, filename) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  if (!res.ok) {
    const e = await res.json().catch(() => ({}))
    throw new Error(e.detail || `Document generation failed (${res.status})`)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

// ── CONSTANTS ─────────────────────────────────────────────────────────────────
// ── LANDING PAGE ICON SET ── custom line icons, consistent 24×24 grid & stroke
const ip = { viewBox:"0 0 24 24", fill:"none", stroke:"currentColor", strokeWidth:1.6, strokeLinecap:"round", strokeLinejoin:"round" }
const IconBook     = ({size=24}) => (<svg width={size} height={size} {...ip}><path d="M12 6 C10.5 4.8 7.8 4 4 4 V18 C7.8 18 10.5 18.8 12 20 C13.5 18.8 16.2 18 20 18 V4 C16.2 4 13.5 4.8 12 6 Z"/><path d="M12 6 V20"/></svg>)
const IconFrame    = ({size=24}) => (<svg width={size} height={size} {...ip}><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9.5" r="1.4"/><path d="M21 15 L16 10 L12 14 L9 11 L3 17"/></svg>)
const IconCompass  = ({size=24}) => (<svg width={size} height={size} {...ip}><circle cx="12" cy="12" r="9"/><path d="M14.5 9.5 L11 11 L9.5 14.5 L13 13 Z" fill="currentColor" stroke="none"/></svg>)
const IconEnvelope = ({size=24}) => (<svg width={size} height={size} {...ip}><rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="M4 6.5 L12 13 L20 6.5"/></svg>)
const IconNetwork  = ({size=24}) => (<svg width={size} height={size} {...ip}><circle cx="6" cy="17" r="2.1"/><circle cx="18" cy="7" r="2.1"/><circle cx="15" cy="17" r="2.1"/><path d="M8 16.2 L13 17.3"/><path d="M16.5 15.2 L17.3 9.1"/></svg>)
const IconBars     = ({size=24}) => (<svg width={size} height={size} {...ip}><rect x="4" y="13" width="4" height="7" rx="1"/><rect x="10" y="9" width="4" height="11" rx="1"/><rect x="16" y="4" width="4" height="16" rx="1"/></svg>)
const IconPlane    = ({size=24}) => (<svg width={size} height={size} {...ip}><path d="M3 12 L21 4 L14 21 L11 13 L3 12 Z"/><path d="M11 13 L21 4"/></svg>)
const IconChat     = ({size=24}) => (<svg width={size} height={size} {...ip}><rect x="3" y="5" width="13" height="8" rx="3"/><rect x="8" y="14" width="13" height="8" rx="3"/></svg>)
const IconBookmark = ({size=24}) => (<svg width={size} height={size} {...ip}><path d="M6 3 L18 3 L18 21 L12 16 L6 21 Z"/></svg>)
const IconRoadmap  = ({size=24}) => (<svg width={size} height={size} {...ip}><path d="M3 19 Q8 19 8 13 Q8 8 14 8 Q18 8 18 4"/><path d="M18 4 L18 9 L21.5 6.5 Z" fill="currentColor" stroke="none"/></svg>)
const IconKanban   = ({size=24}) => (<svg width={size} height={size} {...ip}><rect x="3" y="4" width="5" height="16" rx="1.5"/><rect x="9.5" y="4" width="5" height="10" rx="1.5"/><rect x="16" y="4" width="5" height="13" rx="1.5"/><line x1="4.5" y1="8" x2="6.5" y2="8"/><line x1="11" y1="8" x2="13" y2="8"/><line x1="17.5" y1="8" x2="19.5" y2="8"/></svg>)
const IconLeaf     = ({size=24}) => (<svg width={size} height={size} {...ip}><path d="M5 19 C5 10 10 4 19 4 C19 13 13 19 5 19 Z"/><path d="M5 19 C9 15 12 12 17 7"/></svg>)


const NAV = [
  { key: "hub",         icon: "⚡", label: "Hub",                group: null },
  { key: "resume",      icon: IconBook,     label: "Resume Builder",     group: "Build" },
  { key: "portfolio",   icon: IconFrame,    label: "Portfolio Builder",  group: "Build" },
  { key: "career",      icon: IconCompass,  label: "Career Intelligence",group: "Analyze" },
  { key: "coverletter", icon: IconEnvelope, label: "Cover Letter",       group: "Analyze" },
  { key: "linkedin",    icon: IconNetwork,  label: "LinkedIn Generator", group: "Analyze" },
  { key: "salary",      icon: IconBars,     label: "Salary Estimator",   group: "Analyze" },
  { key: "coldoutreach",icon: IconPlane,    label: "Cold Outreach",      group: "Outreach" },
  { key: "interview",   icon: IconChat,     label: "Mock Interviewer",   group: "Prepare" },
  { key: "cheatsheet",  icon: IconBookmark, label: "Cheat Sheet",        group: "Prepare" },
  { key: "roadmap",     icon: IconRoadmap,  label: "Skill Roadmap",      group: "Prepare" },
  { key: "tracker",     icon: IconKanban,   label: "App Tracker",        group: "Track" },
]

const AT_STATUSES = ["Applied","Phone Screen","Technical Interview","Final Round","Offer 🎉","Rejected"]
const AT_COLORS   = ["#3b82f6","#f59e0b","#8b5cf6","#ec4899","#10b981","#ef4444"]
const WEEK_COLS   = ["#8FAA7A","#D9A054","#4A9B6E","#C2652E","#B0725A","#A88B5C"]

// ── USAGE ANALYTICS ───────────────────────────────────────────────────────────
// Events go to THIS app's own backend (/api/track). The backend holds the
// Supabase credentials in its environment and does the database write, so
// nothing about Supabase lives in (or is typed into) the browser, and it works
// for every visitor automatically. Fire-and-forget: analytics can never break
// or slow down the app.

// Unique session ID for this browser visit
const SESSION_ID = `s_${Date.now()}_${Math.random().toString(36).slice(2,8)}`

function trackEvent(module, action, extras = {}) {
  try {
    fetch("/api/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      keepalive: true,
      body: JSON.stringify({
        session_id:  SESSION_ID,
        module,
        action,
        job_title:   extras.jobTitle || null,
        user_name:   extras.userName || null,
        meta:        extras.meta     || {},
        device:      /mobile/i.test(navigator.userAgent) ? "mobile" : "desktop",
        browser:     (navigator.userAgent.match(/(Chrome|Firefox|Safari|Edge|Opera)[\/\s][\d.]+/)||["Unknown"])[0],
        screen_size: `${window.screen.width}x${window.screen.height}`
      })
    }).catch(() => {})
  } catch (_) {}
}

// ── UI PRIMITIVES ─────────────────────────────────────────────────────────────
const Btn = ({ children, variant="primary", onClick, disabled, full, sm, icon, style }) => (
  <button
    className={`btn btn-${variant}${full?" btn-full":""}${sm?" btn-sm":""}${icon?" btn-icon":""}`}
    onClick={onClick} disabled={disabled} style={style}
  >{children}</button>
)

const Field = ({ label, children }) => (
  <div className="form-group">
    {label && <label className="label">{label}</label>}
    {children}
  </div>
)

const Inp = ({ label, ...p }) => (
  <Field label={label}><input className="input" {...p} /></Field>
)

const Tex = ({ label, rows=4, ...p }) => (
  <Field label={label}><textarea className="textarea" rows={rows} {...p} /></Field>
)

const Sel = ({ label, options, ...p }) => (
  <Field label={label}>
    <select className="select-el" {...p}>
      {options.map(o => <option key={o.value??o} value={o.value??o}>{o.label??o}</option>)}
    </select>
  </Field>
)

const SectionHead = ({ icon: IconOrEmoji, title, caption, right }) => {
  const isStr = typeof IconOrEmoji === "string"
  return (
    <div className="sh" style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
      <div style={{ display:"flex", alignItems:"flex-start", gap:14 }}>
        <div className="sh-icon-badge">{isStr ? IconOrEmoji : <IconOrEmoji size={22}/>}</div>
        <div>
          <div className="sh-title" style={{ marginBottom: caption ? 2 : 0 }}>{title}</div>
          {caption && <div className="sh-caption">{caption}</div>}
        </div>
      </div>
      {right}
    </div>
  )
}

const Metrics = ({ items }) => (
  <div className={`g${Math.min(items.length,4)}`} style={{ marginBottom:"1.5rem" }}>
    {items.map((m,i) => (
      <div key={i} className="metric">
        <div className="metric-label">{m.label}</div>
        <div className="metric-value" style={m.color?{color:m.color}:{}}>{m.value}</div>
        {m.sub && <div className="metric-sub">{m.sub}</div>}
      </div>
    ))}
  </div>
)

const Accordion = ({ title, badge, children, defaultOpen }) => {
  const [open, setOpen] = useState(defaultOpen||false)
  return (
    <div className="accordion">
      <button className="acc-head" onClick={()=>setOpen(o=>!o)}>
        <span>{title} {badge&&<span className={`badge badge-${badge.c}`} style={{marginLeft:8}}>{badge.v}</span>}</span>
        <span>{open?"▲":"▼"}</span>
      </button>
      {open && <div className="acc-body">{children}</div>}
    </div>
  )
}

const Loader = () => <span className="spin">⟳</span>

const CopyBtn = ({ text }) => {
  const [copied, setCopied] = useState(false)
  const copy = () => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(()=>setCopied(false),1500) }
  return <Btn variant="ghost" sm onClick={copy}>{copied?"✓ Copied":"Copy"}</Btn>
}

// Minimal, safe AI-output formatter. Escapes any literal HTML first (so
// nothing in the model's own text can inject markup), then renders only
// three things on top of that safe text: paragraph breaks, simple "- "/"* "
// bullet lists, and **bold** — covering the overwhelming majority of what
// Groq actually produces, without pulling in a full markdown library for
// what was asked to stay a minimal change.
function formatAiOutput(text) {
  if (!text) return ""
  const esc = String(text).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
  const boldify = s => s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
  // A bullet is "-" or "*" followed by whitespace — so **bold** at the start
  // of a line (asterisk followed by another asterisk) is correctly NOT a bullet.
  const isBullet = l => /^\s*[-*]\s+/.test(l)
  const blocks = esc.split(/\n\s*\n/).filter(b => b.trim())
  return blocks.map(block => {
    // Walk line by line so an intro sentence followed directly by bullets
    // (the most common real AI output shape) becomes a paragraph + a real
    // list, instead of the bullets staying as raw dashes inside a paragraph.
    const lines = block.split("\n").filter(l => l.trim())
    const out = []
    let textBuf = [], listBuf = []
    const flushText = () => {
      if (textBuf.length) { out.push(`<p>${boldify(textBuf.join("<br/>"))}</p>`); textBuf = [] }
    }
    const flushList = () => {
      if (listBuf.length) {
        out.push("<ul>" + listBuf.map(i => `<li>${boldify(i)}</li>`).join("") + "</ul>")
        listBuf = []
      }
    }
    for (const l of lines) {
      if (isBullet(l)) { flushText(); listBuf.push(l.trim().replace(/^[-*]\s+/, "")) }
      else             { flushList(); textBuf.push(l.trim()) }
    }
    flushText(); flushList()
    return out.join("")
  }).join("")
}

const OutputBox = ({ text, loading }) => {
  if (loading) return (
    <div style={{display:"flex",flexDirection:"column",gap:8}}>
      {[1,2,3,4].map(i=><div key={i} className="skeleton" style={{height:18,opacity:1-i*0.15}}/>)}
    </div>
  )
  if (!text) return null
  return (
    <div>
      <div className="output" dangerouslySetInnerHTML={{__html: formatAiOutput(text)}}/>
      <div className="copy-row"><CopyBtn text={text}/></div>
    </div>
  )
}

const WizardSteps = ({ steps, current }) => (
  <div className="wizard-steps">
    {steps.map((s,i)=>(
      <div key={i} className="w-step" style={{flex:i<steps.length-1?1:"none"}}>
        <div className={`w-dot ${i<current?"done":i===current?"active":"idle"}`}>
          {i<current?"✓":i+1}
        </div>
        {i<steps.length-1 && <div className={`w-line ${i<current?"done":""}`}/>}
      </div>
    ))}
  </div>
)

// ── SETTINGS MODAL  ·  backend status only ────────────────────────────────────
// The AI keys AND the usage-analytics database (Supabase) are configured on the
// server, in its environment variables. Nothing about either is entered in, or
// stored by, the browser — so there is deliberately no credentials box here.
const SettingsModal = ({ onClose }) => {
  const [health, setHealth] = useState(null)

  const testConnection = async () => {
    setHealth("checking...")
    try {
      const res = await fetch("/api/health")
      const data = await res.json()
      setHealth(data.status === "ok"
        ? `✅ Connected · ${data.keys_loaded} AI key(s) loaded · model: ${data.model} · usage analytics: ${data.analytics ? "on" : "off (Supabase not configured on the server)"}`
        : `⚠️ ${JSON.stringify(data)}`)
    } catch(e) {
      setHealth(`❌ Cannot reach backend — is it running? (${e.message})`)
    }
  }

  return (
    <div className="modal-overlay" onClick={e=>{if(e.target===e.currentTarget)onClose()}}>
      <div className="modal" style={{width:480,maxWidth:"95vw"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"1.5rem"}}>
          <div style={{fontSize:17,fontWeight:800}}>⚙ Settings</div>
          <Btn variant="ghost" icon onClick={onClose}>×</Btn>
        </div>
        <div className="col">
          <div style={{fontWeight:700,marginBottom:8,fontSize:13}}>🤖 Backend Connection</div>
          <div style={{padding:"10px 14px",background:"rgba(143,170,122,0.07)",
            border:"1px solid rgba(143,170,122,0.15)",borderRadius:8,fontSize:12,lineHeight:1.6}}>
            The AI keys and the usage-analytics database are configured on the
            server, in its environment variables. Nothing needs to be entered in
            the browser.
          </div>
          <Btn variant="secondary" onClick={testConnection} full>🔌 Test Backend Connection</Btn>
          {health && (
            <div style={{fontSize:12,padding:"8px 12px",background:"var(--muted)",
              borderRadius:8,lineHeight:1.6}}>{health}</div>
          )}
          <Btn variant="primary" onClick={onClose} full>Close</Btn>
        </div>
      </div>
    </div>
  )
}

// ── SIDEBAR ───────────────────────────────────────────────────────────────────
const NavIcon = ({ icon }) => {
  const isStr = typeof icon === "string"
  const Icon = icon
  return isStr ? <span className="nav-icon">{icon}</span> : <span className="nav-icon"><Icon size={16}/></span>
}

const Sidebar = ({ current, onNav, expanded, onToggle, onSettings }) => {
  const groups = [...new Set(NAV.filter(n=>n.group).map(n=>n.group))]
  return (
    <div className={`sidebar ${expanded?"":"sm"}`}>
      <div className="sb-top">
        <div className="sb-logo">A</div>
        {expanded && <div className="sb-title">Apex Suite</div>}
      </div>
      <div className="sb-nav">
        {/* Hub first */}
        {[NAV[0]].map(item=>(
          <div key={item.key} className={`nav-item ${current===item.key?"active":""}`}
               onClick={()=>onNav(item.key)}>
            <NavIcon icon={item.icon}/>
            {expanded && <span className="nav-label">{item.label}</span>}
          </div>
        ))}
        {/* Grouped items */}
        {groups.map(g=>(
          <div key={g}>
            {expanded && <div className="sb-section">{g}</div>}
            {NAV.filter(n=>n.group===g).map(item=>(
              <div key={item.key} className={`nav-item ${current===item.key?"active":""}`}
                   onClick={()=>onNav(item.key)}>
                <NavIcon icon={item.icon}/>
                {expanded && <span className="nav-label">{item.label}</span>}
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="sb-bottom">
        <button className="toggle-btn" onClick={onSettings} style={{marginBottom:8}}>⚙</button>
        <button className="toggle-btn" onClick={onToggle}>{expanded?"◀":"▶"}</button>
      </div>
    </div>
  )
}

// ── HUB ───────────────────────────────────────────────────────────────────────
const LP_MODULES = [
  { key:"resume",       Icon:IconBook,     title:"Resume Builder",      desc:"AI-polished resume from rough notes" },
  { key:"portfolio",    Icon:IconFrame,    title:"Portfolio Builder",   desc:"Six-slide deck in under a minute" },
  { key:"career",       Icon:IconCompass,  title:"Career Intelligence", desc:"ATS score & skill-gap analysis" },
  { key:"coverletter",  Icon:IconEnvelope, title:"Cover Letter",        desc:"Tailored letters, never generic" },
  { key:"linkedin",     Icon:IconNetwork,  title:"LinkedIn Generator",  desc:"Headline, About & brand voice" },
  { key:"salary",       Icon:IconBars,     title:"Salary Estimator",    desc:"Market range & negotiation tips" },
  { key:"coldoutreach", Icon:IconPlane,    title:"Cold Outreach",       desc:"Messages that actually get replies" },
  { key:"interview",    Icon:IconChat,     title:"Mock Interviewer",    desc:"Practice rounds with real feedback" },
  { key:"cheatsheet",   Icon:IconBookmark, title:"Cheat Sheet",         desc:"One page, ready before you walk in" },
  { key:"roadmap",      Icon:IconRoadmap,  title:"Skill Roadmap",       desc:"A week-by-week path to close gaps" },
  { key:"tracker",      Icon:IconKanban,   title:"App Tracker",         desc:"Every application, one board" },
]

const HubPage = ({ onNav, visited }) => {
  return (
    <div className="page landing-page">
      <div className="lp-blob lp-blob-1"/>
      <div className="lp-blob lp-blob-2"/>

      <div className="lp-hero">
        <div>
          <div className="lp-eyebrow" style={{marginBottom:20}}><span className="lp-eyebrow-dot"/>Your career, in one quiet place</div>
          <div className="lp-serif lp-title">A library for<br/><em>building your career</em></div>
          <div className="lp-sub">
            Eleven AI-guided tools, from your first draft resume to the offer letter — read,
            write, and practice at your own pace, all in one calm workspace.
          </div>
        </div>

        <div className="lp-illustration">
          <div className="lp-illo-glow"/>
          <div className="lp-illo-book"><IconBook size={130}/></div>
          <div className="lp-illo-scatter amber" style={{top:10, left:14, transform:"rotate(-12deg)"}}><IconEnvelope size={28}/></div>
          <div className="lp-illo-scatter" style={{top:34, right:6, transform:"rotate(9deg)"}}><IconCompass size={26}/></div>
          <div className="lp-illo-scatter amber" style={{bottom:26, left:0, transform:"rotate(7deg)"}}><IconLeaf size={30}/></div>
          <div className="lp-illo-scatter" style={{bottom:6, right:26, transform:"rotate(-9deg)"}}><IconBars size={24}/></div>
        </div>
      </div>

      <div className="lp-section-label">
        <span>The Shelf</span>
        <div className="lp-section-line"/>
      </div>

      <div className="lp-grid">
        {LP_MODULES.map((m,i) => {
          const isAmber = i % 2 === 0
          return (
            <div key={m.key} className="lp-card" style={{animationDelay:`${i*0.05}s`}} onClick={()=>onNav(m.key)}>
              <div className="lp-card-icon" style={{
                background: isAmber ? "var(--lp-amber-soft)" : "var(--lp-sage-soft)",
                color:      isAmber ? "#8A4E28" : "#3E5236",
              }}>
                <m.Icon size={24}/>
              </div>
              <div className="lp-card-title">{m.title}</div>
              <div className="lp-card-desc">{m.desc}</div>
            </div>
          )
        })}
      </div>

      <div className="lp-signature">
        <span>Designed &amp; built by</span>
        <img src={logoImg} alt="VED logo"/>
      </div>
    </div>
  )
}

// ── RESUME BUILDER ────────────────────────────────────────────────────────────
const ResumeBuilderPage = ({ apiKey, toast, setResumeBlob, track }) => {
  const STEPS = ["Contact","Links","Education","Experience","Projects","Generate"]
  const [step, setStep] = useState(0)
  const [form, setForm] = useState({ name:"",email:"",phone:"",linkedin:"",github:"",edu:"",skills:"",exp:"",proj:"" })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const up = k => e => setForm(f=>({...f,[k]:e.target.value}))
  const next = () => setStep(s=>s+1)
  const back = () => setStep(s=>s-1)

  const generate = async () => {
    setLoading(true)
    try {
      const data = await groq(apiKey,
        `Expert resume writer. Output JSON: {"edu":"","skills":"","exp":["","","",""],"proj":["","","",""]}. Wrap metrics in <b>, tools in <i>. Exactly 4 bullets each for exp and proj.`,
        `Education: ${form.edu}\nSkills: ${form.skills}\nExperience: ${form.exp}\nProjects: ${form.proj}`, true)
      const hasContent = (Array.isArray(data?.exp) && data.exp.length > 0) ||
                          (Array.isArray(data?.proj) && data.proj.length > 0)
      if (!hasContent) {
        toast("AI response didn't include resume content — try generating again.")
        setLoading(false)
        return
      }
      setResult(data)
      setResumeBlob(`${form.name} ${data.edu} ${data.skills} ${(data.exp||[]).join(" ")} ${(data.proj||[]).join(" ")}`)
      if (track) track("resume", "resume_generated", { userName: form.name })
      setStep(5)
    } catch(e) { toast(e.message) }
    setLoading(false)
  }

  const stripTags = s => String(s).replace(/<[^>]+>/g,"")
  const [downloading, setDownloading] = useState(false)

  const downloadPdf = async () => {
    if (!result) return
    setDownloading(true)
    try {
      await downloadDocument("/api/documents/resume", {
        name: form.name, email: form.email, phone: form.phone,
        linkedin: form.linkedin, github: form.github,
        edu: stripTags(result.edu || ""),
        skills: stripTags(result.skills || ""),
        exp: (result.exp || []).map(stripTags),
        proj: (result.proj || []).map(stripTags),
      }, `${form.name.replace(/\s+/g, "_") || "Apex"}_Resume.pdf`)
    } catch (e) {
      toast(e.message)
    }
    setDownloading(false)
  }

  return (
    <div className="page">
      <SectionHead icon={IconBook} title="Resume Builder" caption="Turn rough notes into a polished resume in 2 minutes"/>
      <WizardSteps steps={STEPS} current={step}/>
      <div className="card">
        {step===0 && (
          <div className="col">
            <div style={{fontSize:16,fontWeight:700,marginBottom:4}}>Contact Information</div>
            <div className="g2">
              <Inp label="Full Name *" value={form.name} onChange={up("name")} placeholder="e.g. Vedant Sharma"/>
              <Inp label="Email *" value={form.email} onChange={up("email")} type="email" placeholder="you@email.com"/>
              <Inp label="Phone" value={form.phone} onChange={up("phone")} placeholder="+91 9876543210"/>
            </div>
            <div style={{display:"flex",justifyContent:"flex-end"}}>
              <Btn onClick={next} disabled={!form.name||!form.email}>Next →</Btn>
            </div>
          </div>
        )}
        {step===1 && (
          <div className="col">
            <div style={{fontSize:16,fontWeight:700,marginBottom:4}}>Professional Links</div>
            <Inp label="LinkedIn URL" value={form.linkedin} onChange={up("linkedin")} placeholder="https://linkedin.com/in/yourname"/>
            <Inp label="GitHub URL" value={form.github} onChange={up("github")} placeholder="https://github.com/yourusername"/>
            <div className="g2" style={{marginTop:8}}>
              <Btn variant="secondary" onClick={back}>← Back</Btn>
              <Btn onClick={next}>Next →</Btn>
            </div>
          </div>
        )}
        {step===2 && (
          <div className="col">
            <div style={{fontSize:16,fontWeight:700,marginBottom:4}}>Education & Skills</div>
            <Tex label="Education" value={form.edu} onChange={up("edu")} rows={3} placeholder="B.Tech CSE, XYZ University, 2022-2026, CGPA 8.5"/>
            <Tex label="Skills & Technologies" value={form.skills} onChange={up("skills")} rows={3} placeholder="Python, ML, React, SQL, Docker, Power BI..."/>
            <div className="g2">
              <Btn variant="secondary" onClick={back}>← Back</Btn>
              <Btn onClick={next}>Next →</Btn>
            </div>
          </div>
        )}
        {step===3 && (
          <div className="col">
            <div style={{fontSize:16,fontWeight:700,marginBottom:4}}>Work Experience</div>
            <div style={{fontSize:12,color:"var(--dim)",marginBottom:8}}>Rough notes → AI generates 4 polished bullets</div>
            <Tex label="Experience" value={form.exp} onChange={up("exp")} rows={6} placeholder="Intern at ABC Corp, built ML model, reduced churn by 22%..."/>
            <div className="g2">
              <Btn variant="secondary" onClick={back}>← Back</Btn>
              <Btn onClick={next}>Next →</Btn>
            </div>
          </div>
        )}
        {step===4 && (
          <div className="col">
            <div style={{fontSize:16,fontWeight:700,marginBottom:4}}>Projects</div>
            <div style={{fontSize:12,color:"var(--dim)",marginBottom:8}}>Rough notes → AI generates 4 impactful bullets</div>
            <Tex label="Projects" value={form.proj} onChange={up("proj")} rows={6} placeholder="Built NLP fake-news detector, 94% accuracy, deployed on Streamlit..."/>
            <div className="g2">
              <Btn variant="secondary" onClick={back}>← Back</Btn>
              <Btn onClick={generate} disabled={!form.proj||loading}>
                {loading?<><Loader/> Generating...</>:"⚡ Generate with AI"}
              </Btn>
            </div>
          </div>
        )}
        {step===5 && result && (
          <div className="col">
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
              <div style={{fontSize:16,fontWeight:700}}>✅ Resume Generated</div>
              <Btn variant="primary" onClick={downloadPdf} disabled={downloading}>
                {downloading ? <><Loader/> Generating PDF...</> : "📥 Download PDF"}
              </Btn>
            </div>
            <div className="card" style={{background:"var(--muted)"}}>
              <div style={{textAlign:"center",paddingBottom:12,borderBottom:"1px solid var(--border)",marginBottom:12}}>
                <div style={{fontSize:20,fontWeight:900}}>{form.name.toUpperCase()}</div>
                <div style={{fontSize:11,color:"var(--dim)"}}>{form.email} | {form.phone}</div>
              </div>
              {result.edu && <><div style={{fontSize:11,fontWeight:700,color:"var(--cyan)",textTransform:"uppercase",marginBottom:4}}>Education</div><div style={{fontSize:12,marginBottom:12}} dangerouslySetInnerHTML={{__html:result.edu}}/></>}
              {(result.exp||[]).length>0 && <><div style={{fontSize:11,fontWeight:700,color:"var(--cyan)",textTransform:"uppercase",marginBottom:4}}>Experience</div>{result.exp.map((b,i)=><div key={i} style={{fontSize:12,marginBottom:4}} dangerouslySetInnerHTML={{__html:`• ${b}`}}/>)}<div style={{marginBottom:12}}/></>}
              {(result.proj||[]).length>0 && <><div style={{fontSize:11,fontWeight:700,color:"var(--cyan)",textTransform:"uppercase",marginBottom:4}}>Projects</div>{result.proj.map((b,i)=><div key={i} style={{fontSize:12,marginBottom:4}} dangerouslySetInnerHTML={{__html:`• ${b}`}}/>)}<div style={{marginBottom:12}}/></>}
              {result.skills && <><div style={{fontSize:11,fontWeight:700,color:"var(--cyan)",textTransform:"uppercase",marginBottom:4}}>Skills</div><div style={{fontSize:12}} dangerouslySetInnerHTML={{__html:result.skills}}/></>}
            </div>
            <Btn variant="secondary" onClick={()=>{setStep(0);setResult(null)}}>🔄 Start Over</Btn>
          </div>
        )}
      </div>
    </div>
  )
}

// ── CAREER INTELLIGENCE ────────────────────────────────────────────────────────
const CareerPage = ({ apiKey, toast, resumeBlob, track }) => {
  const [tab, setTab] = useState(0)
  const [role, setRole] = useState("")
  const [jd, setJd] = useState("")
  const [resume, setResume] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [jdRaw, setJdRaw] = useState("")
  const [jdResult, setJdResult] = useState(null)
  const [jdLoading, setJdLoading] = useState(false)

  const runATS = async () => {
    if (track) track("career", "ats_started", { jobTitle: role })
    const res = resume || resumeBlob
    if(!jd.trim()||!res.trim()) { toast("Paste JD and your resume first."); return }
    setLoading(true); setResult(null)
    try {
      const jdData = await groq(apiKey,"ATS analyzer. JSON only.",
        `Extract: required_skills (10-15), preferred_skills (5-8), key_responsibilities (4-5), experience_level, domain. JD: ${jd}
        Schema: {"required_skills":[],"preferred_skills":[],"key_responsibilities":[],"experience_level":"","domain":""}`, true)
      if (!Array.isArray(jdData?.required_skills) || jdData.required_skills.length === 0) {
        // Without this, the next two calls run on empty input and produce a
        // misleading "0% match" that looks like a real verdict on the resume.
        toast("Couldn't extract skills from that job description — try pasting more of it.")
        setLoading(false)
        return
      }
      const match = await groq(apiKey,"Strict ATS scanner. JSON only. Mark matched only if clearly in resume.",
        `Resume: ${res}\nRequired: ${JSON.stringify(jdData.required_skills)}\nPreferred: ${JSON.stringify(jdData.preferred_skills)}
        Schema: {"matched_required":[],"missing_required":[],"matched_preferred":[],"missing_preferred":[]}`, true)
      const sugg = await groq(apiKey,"Resume coach. Be specific.",
        `5 numbered improvement tips for ${role||"target role"}. Missing required: ${JSON.stringify(match.missing_required)}. Missing preferred: ${JSON.stringify(match.missing_preferred)}. Key resp: ${JSON.stringify(jdData.key_responsibilities)}`)
      const mreq=match.matched_required||[]; const xreq=match.missing_required||[]
      const mpre=match.matched_preferred||[]; const xpre=match.missing_preferred||[]
      const req=jdData.required_skills||[]; const pre=jdData.preferred_skills||[]
      const rs=(mreq.length/Math.max(req.length,1))*100
      const ps=(mpre.length/Math.max(pre.length,1))*100
      setResult({role,domain:jdData.domain,exp:jdData.experience_level,ov:rs*0.75+ps*0.25,rs,ps,mreq,xreq,mpre,xpre,resp:jdData.key_responsibilities||[],sugg})
    } catch(e) { toast(e.message) }
    setLoading(false)
  }

  const analyzeJD = async () => {
    if(!jdRaw.trim()) { toast("Paste a job description first."); return }
    setJdLoading(true); setJdResult(null)
    try {
      const data = await groq(apiKey,"Career intelligence. JSON only.",
        `Analyze JD: role_title, company_type (startup/mid-size/enterprise), domain, experience_years, hard_skills (8-12), soft_skills (4-6), red_flags (2-3 vague phrases), summary (2 sentences).
        JD: ${jdRaw}
        Schema: {"role_title":"","company_type":"","domain":"","experience_years":"","hard_skills":[],"soft_skills":[],"red_flags":[],"summary":""}`, true)
      setJdResult(data)
    } catch(e) { toast(e.message) }
    setJdLoading(false)
  }

  const ScoreRing = ({ pct }) => {
    const R=40; const C=2*Math.PI*R; const off=C-(pct/100)*C
    const col = pct>=70?"var(--green)":pct>=45?"var(--amber)":"var(--red)"
    return (
      <svg width={100} height={100} viewBox="0 0 100 100">
        <circle cx={50} cy={50} r={R} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={8}/>
        <circle cx={50} cy={50} r={R} className="score-ring-fill" stroke={col}
          strokeDasharray={C} strokeDashoffset={off}/>
        <text x={50} y={55} textAnchor="middle" fill="var(--text)" style={{fontSize:16,fontWeight:800}}>{Math.round(pct)}%</text>
      </svg>
    )
  }

  return (
    <div className="page">
      <SectionHead icon={IconCompass} title="Career Intelligence" caption="ATS match score · Skill-gap analysis · Market insights"/>
      <div className="tabs" style={{marginBottom:"1.5rem"}}>
        {["📊 ATS Score Checker","🔍 JD Analyzer"].map((t,i)=>(
          <button key={i} className={`tab ${tab===i?"active":""}`} onClick={()=>setTab(i)}>{t}</button>
        ))}
      </div>

      {tab===0 && (
        <div className="col">
          <div className="g2" style={{gap:"1.5rem"}}>
            <div className="col">
              <Inp label="Target Role" value={role} onChange={e=>setRole(e.target.value)} placeholder="e.g. Data Scientist at Google"/>
              <Tex label="Job Description" value={jd} onChange={e=>setJd(e.target.value)} rows={9} placeholder="Paste the full JD here..."/>
            </div>
            <div className="col">
              <div style={{fontSize:11,fontWeight:700,color:"var(--dim)",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:4}}>Your Resume</div>
              {resumeBlob && <div style={{padding:"8px 12px",background:"rgba(143,170,122,0.08)",borderRadius:8,fontSize:12,color:"var(--cyan)",marginBottom:8}}>✅ Resume from Resume Builder available</div>}
              <Tex label={resumeBlob?"Or paste different resume":"Paste Resume Text"} value={resume} onChange={e=>setResume(e.target.value)} rows={9} placeholder="Paste resume text here, or use Resume Builder output above..."/>
            </div>
          </div>
          <Btn onClick={runATS} disabled={loading} full>
            {loading?<><Loader/> Analyzing (3 steps)...</>:"🔍 Run ATS Analysis"}
          </Btn>

          {result && (
            <div className="col" style={{marginTop:8}}>
              <div className="divider"/>
              <Metrics items={[
                {label:"Overall ATS Score",value:`${Math.round(result.ov)}%`,color:result.ov>=70?"var(--green)":result.ov>=45?"var(--amber)":"var(--red)",sub:result.ov>=70?"Strong Match 🎯":result.ov>=45?"Fair Match ⚠️":"Weak Match ❌"},
                {label:"Required Skills",value:`${Math.round(result.rs)}%`,sub:`${result.mreq.length}/${result.mreq.length+result.xreq.length} matched`},
                {label:"Preferred Skills",value:`${Math.round(result.ps)}%`,sub:`${result.mpre.length}/${result.mpre.length+result.xpre.length} matched`},
                {label:"Domain",value:result.domain||"—",sub:result.exp||""},
              ]}/>
              <div className="g2" style={{gap:"1.5rem"}}>
                <div>
                  <div style={{fontWeight:700,marginBottom:10}}>✅ Matched Skills</div>
                  {result.mreq.length>0&&<><div style={{fontSize:11,color:"var(--dim)",marginBottom:6}}>Required</div><div className="chip-row">{result.mreq.map((s,i)=><span key={i} className="chip chip-g">{s}</span>)}</div></>}
                  {result.mpre.length>0&&<><div style={{fontSize:11,color:"var(--dim)",margin:"10px 0 6px"}}>Preferred</div><div className="chip-row">{result.mpre.map((s,i)=><span key={i} className="chip chip-b">{s}</span>)}</div></>}
                  {!result.mreq.length&&!result.mpre.length&&<div style={{color:"var(--dim)",fontSize:12}}>No matches found. Try a more detailed resume.</div>}
                </div>
                <div>
                  <div style={{fontWeight:700,marginBottom:10}}>❌ Missing Skills</div>
                  {result.xreq.length>0&&<><div style={{fontSize:11,color:"var(--dim)",marginBottom:6}}>Required (add first)</div><div className="chip-row">{result.xreq.map((s,i)=><span key={i} className="chip chip-r">{s}</span>)}</div></>}
                  {result.xpre.length>0&&<><div style={{fontSize:11,color:"var(--dim)",margin:"10px 0 6px"}}>Preferred</div><div className="chip-row">{result.xpre.map((s,i)=><span key={i} className="chip chip-y">{s}</span>)}</div></>}
                  {!result.xreq.length&&!result.xpre.length&&<div style={{color:"var(--green)",fontSize:12}}>You matched everything — strong resume!</div>}
                </div>
              </div>
              {result.resp.length>0&&(
                <Accordion title="📌 Key Responsibilities"><ul style={{paddingLeft:16}}>{result.resp.map((r,i)=><li key={i} style={{marginBottom:4}}>{r}</li>)}</ul></Accordion>
              )}
              <div className="card">
                <div style={{fontWeight:700,marginBottom:10}}>💡 AI Improvement Suggestions</div>
                <div style={{fontSize:13,lineHeight:1.8,whiteSpace:"pre-line"}}>{result.sugg}</div>
              </div>
              <Btn variant="ghost" onClick={()=>setResult(null)}>🔄 Run Again</Btn>
            </div>
          )}
        </div>
      )}

      {tab===1 && (
        <div className="col">
          <Tex label="Paste Any Job Description" value={jdRaw} onChange={e=>setJdRaw(e.target.value)} rows={9} placeholder="Paste any JD here to get a structured breakdown..."/>
          <Btn onClick={analyzeJD} disabled={jdLoading} full>
            {jdLoading?<><Loader/> Analyzing...</>:"🔍 Analyze JD"}
          </Btn>
          {jdResult && (
            <div className="col">
              <Metrics items={[
                {label:"Role",value:jdResult.role_title||"—"},
                {label:"Company Type",value:jdResult.company_type||"—"},
                {label:"Domain",value:jdResult.domain||"—"},
                {label:"Experience",value:jdResult.experience_years||"—"},
              ]}/>
              <div style={{fontStyle:"italic",color:"var(--dim)",fontSize:13,padding:"12px",background:"var(--muted)",borderRadius:8}}>{jdResult.summary}</div>
              <div className="g2">
                <div>
                  <div style={{fontWeight:700,marginBottom:10}}>🔧 Technical Skills</div>
                  {(jdResult.hard_skills||[]).map((s,i)=><div key={i} style={{padding:"4px 0",fontSize:13,borderBottom:"1px solid var(--border)"}}>→ {s}</div>)}
                </div>
                <div>
                  <div style={{fontWeight:700,marginBottom:10}}>🤝 Soft Skills</div>
                  {(jdResult.soft_skills||[]).map((s,i)=><div key={i} style={{padding:"4px 0",fontSize:13,borderBottom:"1px solid var(--border)"}}>→ {s}</div>)}
                </div>
              </div>
              {(jdResult.red_flags||[]).length>0&&(
                <div style={{padding:"12px 16px",background:"rgba(239,68,68,0.08)",border:"1px solid rgba(239,68,68,0.2)",borderRadius:8,fontSize:13}}>
                  ⚠️ <strong>Watch out for:</strong> {jdResult.red_flags.join(", ")}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── GENERIC SINGLE-OUTPUT MODULE ───────────────────────────────────────────────
const GenericModule = ({ icon, title, caption, fields, system, buildPrompt, apiKey, toast, downloadConfig }) => {
  const [vals, setVals] = useState({})
  const [output, setOutput] = useState("")
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const up = k => e => setVals(v=>({...v,[k]:e.target.value}))

  const run = async () => {
    setLoading(true); setOutput("")
    try { setOutput(await groq(apiKey, system, buildPrompt(vals))) }
    catch(e) { toast(e.message) }
    setLoading(false)
  }

  const download = async () => {
    if (!output || !downloadConfig) return
    setDownloading(true)
    try {
      await downloadDocument(
        downloadConfig.endpoint,
        downloadConfig.buildPayload(vals, output),
        downloadConfig.filename(vals)
      )
    } catch(e) { toast(e.message) }
    setDownloading(false)
  }

  return (
    <div className="page">
      <SectionHead icon={icon} title={title} caption={caption}/>
      <div className="card">
        <div className="col">
          {fields.map((f,i)=>(
            f.type==="textarea"
              ? <Tex key={i} label={f.label} value={vals[f.key]||""} onChange={up(f.key)} rows={f.rows||4} placeholder={f.placeholder}/>
              : <Inp key={i} label={f.label} value={vals[f.key]||""} onChange={up(f.key)} placeholder={f.placeholder}/>
          ))}
          <Btn onClick={run} disabled={loading} full>
            {loading?<><Loader/> Generating...</>:`⚡ Generate`}
          </Btn>
          <OutputBox text={output} loading={loading&&!output}/>
          {output && downloadConfig && (
            <Btn variant="secondary" onClick={download} disabled={downloading} full>
              {downloading ? <><Loader/> Generating PDF...</> : "📥 Download PDF"}
            </Btn>
          )}
        </div>
      </div>
    </div>
  )
}

// ── SALARY ESTIMATOR ───────────────────────────────────────────────────────────
const SalaryPage = ({ apiKey, toast }) => {
  const [form, setForm] = useState({ role:"",exp:"0",location:"",skills:"",company:"Any",edu:"B.Tech / B.E." })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const up = k => e => setForm(f=>({...f,[k]:e.target.value}))

  const run = async () => {
    if(!form.role||!form.location) { toast("Enter role and location."); return }
    setLoading(true); setResult(null)
    try {
      const data = await groq(apiKey,"Compensation intelligence expert. JSON only.",
        `Salary estimate for: Role: ${form.role}, Experience: ${form.exp} years, Location: ${form.location}, Skills: ${form.skills}, Company: ${form.company}, Education: ${form.edu}
        Schema: {"min_salary":"","max_salary":"","median_salary":"","currency":"","factors_positive":[],"factors_negative":[],"negotiation_tips":[],"market_insight":""}`, true)
      if (!data?.median_salary && !data?.min_salary && !data?.max_salary) {
        toast("AI response didn't include a salary estimate — try again.")
        setLoading(false)
        return
      }
      setResult(data)
    } catch(e) { toast(e.message) }
    setLoading(false)
  }

  return (
    <div className="page">
      <SectionHead icon={IconBars} title="Salary Intelligence Estimator" caption="Market-realistic salary range with negotiation tips"/>
      <div className="card">
        <div className="g2" style={{gap:"1.5rem"}}>
          <div className="col">
            <Inp label="Job Title / Role *" value={form.role} onChange={up("role")} placeholder="e.g. Data Scientist"/>
            <div className="form-group">
              <label className="label">Years of Experience</label>
              <div className="row">
                <input type="range" min={0} max={10} value={form.exp} onChange={up("exp")} style={{flex:1}}/>
                <span style={{fontSize:16,fontWeight:700,color:"var(--cyan)",minWidth:28}}>{form.exp}</span>
              </div>
            </div>
            <Inp label="Location *" value={form.location} onChange={up("location")} placeholder="e.g. Bangalore, Mumbai, Remote India"/>
            <Tex label="Key Skills" value={form.skills} onChange={up("skills")} rows={2} placeholder="Python, TensorFlow, MLOps, AWS..."/>
          </div>
          <div className="col">
            <Sel label="Target Company Type" value={form.company} onChange={up("company")} options={["Any","Startup (Series A-B)","Mid-size (500-5000 employees)","Enterprise / MNC","FAANG / Top Tech","Government / PSU"]}/>
            <Sel label="Highest Education" value={form.edu} onChange={up("edu")} options={["B.Tech / B.E.","M.Tech / M.S.","MBA","BCA / B.Sc","MCA / M.Sc","PhD","Diploma / Other"]}/>
            <Btn onClick={run} disabled={loading} full style={{marginTop:"auto"}}>
              {loading?<><Loader/> Analyzing...</>:"💰 Estimate Salary"}
            </Btn>
          </div>
        </div>
      </div>
      {result && (
        <div className="col" style={{marginTop:"1.5rem"}}>
          <Metrics items={[
            {label:"Minimum",value:result.min_salary||"—"},
            {label:"Median ⭐",value:result.median_salary||"—",color:"var(--cyan)",sub:"Most likely for your profile"},
            {label:"Maximum",value:result.max_salary||"—"},
          ]}/>
          <div className="g2">
            <div className="card">
              <div style={{fontWeight:700,marginBottom:10}}>📈 Pushing Your Salary Up</div>
              {(result.factors_positive||[]).map((f,i)=><div key={i} style={{fontSize:12,padding:"4px 0",borderBottom:"1px solid var(--border)",color:"var(--green)"}}>↑ {f}</div>)}
            </div>
            <div className="card">
              <div style={{fontWeight:700,marginBottom:10}}>📉 Pulling Your Salary Down</div>
              {(result.factors_negative||[]).map((f,i)=><div key={i} style={{fontSize:12,padding:"4px 0",borderBottom:"1px solid var(--border)",color:"var(--red)"}}>↓ {f}</div>)}
            </div>
          </div>
          <div className="card">
            <div style={{fontWeight:700,marginBottom:10}}>🤝 Negotiation Tips</div>
            {(result.negotiation_tips||[]).map((t,i)=><div key={i} style={{fontSize:13,padding:"6px 0",borderBottom:"1px solid var(--border)"}}>💡 {t}</div>)}
          </div>
          {result.market_insight&&(
            <div style={{padding:"12px 16px",background:"rgba(143,170,122,0.07)",border:"1px solid rgba(143,170,122,0.15)",borderRadius:8,fontSize:13}}>
              📊 <strong>Market Insight:</strong> {result.market_insight}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── MOCK INTERVIEWER ───────────────────────────────────────────────────────────
const MockInterviewPage = ({ apiKey, toast, resumeBlob, track }) => {
  const [phase, setPhase] = useState("setup") // setup | interview | report
  const [form, setForm] = useState({ role:"",type:"Mixed (Technical + Behavioral)",difficulty:"Medium",numQ:8 })
  const [jd, setJd] = useState("")
  const [questions, setQuestions] = useState([])
  const [curr, setCurr] = useState(0)
  const [answers, setAnswers] = useState([])
  const [scores, setScores] = useState([])
  const [answer, setAnswer] = useState("")
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const up = k => e => setForm(f=>({...f,[k]:e.target.value}))

  const downloadReport = async () => {
    if (!report) return
    setDownloading(true)
    try {
      await downloadDocument("/api/documents/interview-report", {
        role: form.role,
        overall_score: report.overall_score || 0,
        readiness_label: report.readiness_label || "",
        overall_feedback: report.overall_feedback || "",
        top_strengths: report.top_strengths || [],
        critical_gaps: report.critical_gaps || [],
        study_topics: report.study_topics || [],
        next_steps: report.next_steps || [],
        qa: questions.map((q, i) => ({
          question: q.q, category: q.category,
          answer: answers[i] || "",
          score: (scores[i] || {}).score || 0,
          feedback: (scores[i] || {}).feedback || "",
        })),
      }, `${(form.role || "Interview").replace(/\s+/g, "_")}_Report.pdf`)
    } catch (e) {
      toast(e.message)
    }
    setDownloading(false)
  }

  const startInterview = async () => {
    if(!form.role) { toast("Enter target role."); return }
    setLoading(true)
    try {
      const data = await groq(apiKey,"Senior technical interviewer. Specific, non-generic questions. JSON only.",
        `Generate exactly ${form.numQ} questions for ${form.role}. Type: ${form.type}. Difficulty: ${form.difficulty}. JD: ${jd||"Not provided"}. Background: ${resumeBlob||"Not provided"}.
        Schema: {"questions":[{"q":"","category":"Technical or Behavioral","hint":"1 sentence on strong answer"}]}`, true)
      const qs = Array.isArray(data?.questions) ? data.questions : []
      if (qs.length === 0) {
        toast("AI response didn't include interview questions — try again.")
        setLoading(false)
        return
      }
      setQuestions(qs); setAnswers(Array(qs.length).fill("")); setScores(Array(qs.length).fill(null))
      setCurr(0); setAnswer(""); setPhase("interview")
      if (track) track("interview", "interview_started", { jobTitle: form.role })
    } catch(e) { toast(e.message) }
    setLoading(false)
  }

  const submitAnswer = async (skip=false) => {
    const ans = skip?"[Skipped]":answer.trim()
    if(!skip&&!ans) { toast("Type an answer first."); return }
    setLoading(true)
    let sc
    if(skip) { sc={score:0,feedback:"Skipped.",strengths:[],improvements:["Practice this — skipped questions are real gaps."],model_answer_hint:questions[curr]?.hint||""} }
    else {
      try {
        sc = await groq(apiKey,"Strict but fair interviewer. Score honestly: average=5-6, good=7-8, excellent=9-10. JSON only.",
          `Role: ${form.role}. Q: ${questions[curr].q}. Category: ${questions[curr].category}. Answer: ${ans}
          Schema: {"score":0,"feedback":"","strengths":[],"improvements":[],"model_answer_hint":""}`, true)
      } catch(e) { sc={score:5,feedback:"Recorded.",strengths:[],improvements:[],model_answer_hint:""} }
    }
    const newA=[...answers]; newA[curr]=ans; setAnswers(newA)
    const newS=[...scores]; newS[curr]=sc; setScores(newS)
    if(curr+1>=questions.length) { await generateReport(newA,newS); return }
    setCurr(c=>c+1); setAnswer(""); setLoading(false)
  }

  const generateReport = async (ans, scs) => {
    setPhase("report")
    const qa = questions.map((q,i)=>`Q${i+1}[${q.category}]: ${q.q}\nAnswer: ${ans[i]}\nScore: ${(scs[i]||{}).score||0}/10`).join("\n\n")
    try {
      const data = await groq(apiKey,"Senior career coach. Honest, specific analysis. JSON only.",
        `Mock interview for ${form.role}:\n${qa}\nSchema: {"overall_score":0,"readiness_label":"Not Ready or Needs Work or Almost There or Interview Ready","overall_feedback":"","top_strengths":[],"critical_gaps":[],"study_topics":[],"next_steps":[]}`, true)
      setReport(data)
    } catch(e) { const vs=scs.filter(s=>s&&s.score>0); setReport({overall_score:Math.round((vs.reduce((a,s)=>a+s.score,0)/Math.max(vs.length,1))*10),readiness_label:"Review Feedback",overall_feedback:"Interview complete. Review per-question feedback.",top_strengths:[],critical_gaps:[],study_topics:[],next_steps:[]}) }
    setLoading(false)
  }

  const reset = () => { setPhase("setup"); setQuestions([]); setReport(null); setAnswers([]); setScores([]); setCurr(0); setAnswer(""); setJd("") }

  const scoreColor = s => s>=8?"var(--green)":s>=5?"var(--amber)":"var(--red)"

  return (
    <div className="page">
      <SectionHead icon={IconChat} title="Mock Interviewer" caption="Role-specific questions · Per-answer AI scoring · Full PDF-ready report"
        right={phase!=="setup"&&<Btn variant="secondary" sm onClick={reset}>🔄 New Interview</Btn>}/>

      {phase==="setup" && (
        <div className="card">
          <div className="col">
            <div className="g2" style={{gap:"1.5rem"}}>
              <div className="col">
                <Inp label="Target Role *" value={form.role} onChange={up("role")} placeholder="e.g. Data Scientist, ML Engineer"/>
                <Sel label="Interview Type" value={form.type} onChange={up("type")} options={["Mixed (Technical + Behavioral)","Technical Only","Behavioral / HR Only"]}/>
                <Sel label="Difficulty" value={form.difficulty} onChange={up("difficulty")} options={["Easy (Fresher / Entry-level)","Medium (1-3 years)","Hard (Senior / FAANG)"]}/>
                <Sel label="Number of Questions" value={form.numQ} onChange={up("numQ")} options={[{value:5,label:"5 Questions"},{value:8,label:"8 Questions"},{value:10,label:"10 Questions"}]}/>
              </div>
              <div className="col">
                <Tex label="Job Description (optional)" value={jd} onChange={e=>setJd(e.target.value)} rows={5} placeholder="Paste JD for tailored questions..."/>
                {resumeBlob&&<div style={{padding:"8px 12px",background:"rgba(143,170,122,0.07)",borderRadius:8,fontSize:12,color:"var(--cyan)"}}>✅ Resume Builder output will be used for context</div>}
              </div>
            </div>
            <Btn onClick={startInterview} disabled={loading} full>
              {loading?<><Loader/> Generating Questions...</>:"🎤 Generate Questions & Start"}
            </Btn>
          </div>
        </div>
      )}

      {phase==="interview" && questions.length>0 && (
        <div className="col">
          <div className="card">
            <div style={{marginBottom:"1rem"}}>
              <div className="progress-bar"><div className="progress-fill" style={{width:`${(curr/questions.length)*100}%`}}/></div>
              <div style={{display:"flex",justifyContent:"space-between",marginTop:6,fontSize:11,color:"var(--dim)"}}>
                <span>Question {curr+1} of {questions.length}</span>
                <span>{questions[curr]?.category}</span>
              </div>
            </div>
            <div style={{fontSize:18,fontWeight:700,lineHeight:1.5,marginBottom:"1rem"}}>{questions[curr]?.q}</div>
            {questions[curr]?.hint&&(
              <details style={{marginBottom:"1rem"}}>
                <summary style={{fontSize:12,color:"var(--dim)"}}>💡 Show hint</summary>
                <div style={{marginTop:6,fontSize:12,color:"var(--dim)",padding:"8px",background:"var(--muted)",borderRadius:6}}>{questions[curr].hint}</div>
              </details>
            )}
            <Tex label="Your Answer" value={answer} onChange={e=>setAnswer(e.target.value)} rows={7} placeholder={questions[curr]?.category==="Behavioral"?"STAR method: Situation → Task → Action → Result":"Explain your reasoning and thought process, not just the final answer."}/>
            <div className="g3" style={{marginTop:"1rem"}}>
              <Btn variant="primary" onClick={()=>submitAnswer(false)} disabled={loading} full>{loading?<><Loader/> Scoring...</>:"✅ Submit Answer"}</Btn>
              <Btn variant="ghost" onClick={()=>submitAnswer(true)} disabled={loading} full>⏭ Skip</Btn>
              <Btn variant="danger" onClick={()=>generateReport(answers,scores)} disabled={loading} full>🏁 End</Btn>
            </div>
          </div>
          {curr>0&&scores[curr-1]&&(
            <div className="card" style={{borderColor:`${scoreColor(scores[curr-1].score)}33`}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8}}>
                <div style={{fontWeight:700}}>📊 Q{curr} Feedback</div>
                <span style={{fontSize:20,fontWeight:800,color:scoreColor(scores[curr-1].score)}}>{scores[curr-1].score}/10</span>
              </div>
              <div style={{fontSize:12,color:"var(--dim)",marginBottom:8}}>{scores[curr-1].feedback}</div>
              {scores[curr-1].strengths?.map((s,i)=><div key={i} style={{fontSize:12,color:"var(--green)"}}>✓ {s}</div>)}
              {scores[curr-1].improvements?.map((s,i)=><div key={i} style={{fontSize:12,color:"var(--amber)"}}>→ {s}</div>)}
            </div>
          )}
        </div>
      )}

      {phase==="report" && (
        <div className="col">
          {!report ? (
            <div className="card" style={{textAlign:"center",padding:"3rem"}}>
              <div className="spin" style={{fontSize:32}}>⟳</div>
              <div style={{marginTop:12,color:"var(--dim)"}}>Generating your report...</div>
            </div>
          ) : (
            <>
              <div className="card glow">
                <div style={{display:"flex",gap:"2rem",alignItems:"center"}}>
                  <div>
                    <svg width={110} height={110} viewBox="0 0 110 110">
                      {(()=>{const R=44,C=2*Math.PI*R,off=C-((report.overall_score||0)/100)*C,col=(report.overall_score||0)>=75?"var(--green)":(report.overall_score||0)>=50?"var(--amber)":"var(--red)"; return (<>
                        <circle cx={55} cy={55} r={R} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={9}/>
                        <circle cx={55} cy={55} r={R} className="score-ring-fill" stroke={col} strokeDasharray={C} strokeDashoffset={off}/>
                        <text x={55} y={51} textAnchor="middle" fill="var(--text)" style={{fontSize:20,fontWeight:900}}>{report.overall_score||0}</text>
                        <text x={55} y={67} textAnchor="middle" fill="var(--dim)" style={{fontSize:9,textTransform:"uppercase",letterSpacing:1}}>/100</text>
                      </>)})()}
                    </svg>
                  </div>
                  <div>
                    <div style={{fontSize:22,fontWeight:800,marginBottom:4}}>{report.readiness_label}</div>
                    <div style={{fontSize:13,color:"var(--dim)",lineHeight:1.7}}>{report.overall_feedback}</div>
                  </div>
                </div>
              </div>
                <div className="g2">
                <div className="card">
                  <div style={{fontWeight:700,marginBottom:10}}>💪 Top Strengths</div>
                  {(report.top_strengths||[]).map((s,i)=><div key={i} style={{fontSize:12,padding:"5px 0",borderBottom:"1px solid var(--border)",color:"var(--green)"}}>✓ {s}</div>)}
                </div>
                <div className="card">
                  <div style={{fontWeight:700,marginBottom:10}}>⚠️ Critical Gaps</div>
                  {(report.critical_gaps||[]).map((s,i)=><div key={i} style={{fontSize:12,padding:"5px 0",borderBottom:"1px solid var(--border)",color:"var(--red)"}}>✗ {s}</div>)}
                </div>
              </div>
              <div className="g2">
                <div className="card">
                  <div style={{fontWeight:700,marginBottom:10}}>📚 Study Topics</div>
                  {(report.study_topics||[]).map((t,i)=><div key={i} style={{fontSize:12,padding:"4px 0",borderBottom:"1px solid var(--border)"}}><code style={{fontSize:11,background:"var(--muted)",padding:"1px 6px",borderRadius:4}}>{t}</code></div>)}
                </div>
                <div className="card">
                  <div style={{fontWeight:700,marginBottom:10}}>✅ 7-Day Action Plan</div>
                  {(report.next_steps||[]).map((t,i)=><div key={i} style={{fontSize:12,padding:"5px 0",borderBottom:"1px solid var(--border)"}}>→ {t}</div>)}
                </div>
              </div>
              <div>
                <div style={{fontWeight:700,marginBottom:12,fontSize:15}}>📋 Detailed Q&A Review</div>
                {questions.map((q,i)=>{
                  const sc=scores[i]; const sv=(sc||{}).score||0
                  return (
                    <Accordion key={i} title={`Q${i+1} [${q.category}] — ${q.q.slice(0,60)}...`}
                      badge={{c:sv>=8?"green":sv>=5?"amber":"red",v:`${sv}/10`}}>
                      <div style={{marginBottom:8}}><strong>Q:</strong> {q.q}</div>
                      <div style={{marginBottom:8,color:"var(--dim)"}}><strong>Your answer:</strong> {answers[i]}</div>
                      {sc&&<>
                        <div style={{marginBottom:6}}><strong>Feedback:</strong> {sc.feedback}</div>
                        {(sc.strengths||[]).map((s,j)=><div key={j} style={{color:"var(--green)",fontSize:12}}>✓ {s}</div>)}
                        {(sc.improvements||[]).map((s,j)=><div key={j} style={{color:"var(--amber)",fontSize:12}}>→ {s}</div>)}
                        {sc.model_answer_hint&&<div style={{marginTop:8,padding:"8px",background:"var(--card)",borderRadius:6,fontSize:12,color:"var(--cyan)"}}>💡 Ideal: {sc.model_answer_hint}</div>}
                      </>}
                    </Accordion>
                  )
                })}
              </div>
              <Btn variant="primary" onClick={downloadReport} disabled={downloading} full>
                {downloading ? <><Loader/> Generating PDF...</> : "📥 Download Full Report PDF"}
              </Btn>
            </>
          )}
        </div>
      )}
    </div>
  )
}

// ── APP TRACKER ────────────────────────────────────────────────────────────────
const AppTrackerPage = ({ apiKey, toast }) => {
  const [apps, setApps] = useState([])
  const [tab, setTab]   = useState(0)
  const [form, setForm] = useState({
    company:"", role:"", status:"Applied",
    date: new Date().toISOString().slice(0,10),
    salary:"", contact:"", jdUrl:"", notes:"", next:""
  })
  const up = k => e => setForm(f=>({...f,[k]:e.target.value}))
  const [fuText,    setFuText]    = useState({})
  const [fuLoading, setFuLoading] = useState({})

  const add = () => {
    if(!form.company||!form.role){ toast("Company and role required."); return }
    setApps(a=>[...a,{...form,id:Date.now()}])
    setForm({company:"",role:"",status:"Applied",date:new Date().toISOString().slice(0,10),salary:"",contact:"",jdUrl:"",notes:"",next:""})
    toast("Application added!"); setTab(0)
  }

  const move = (id, status) => setApps(a=>a.map(x=>x.id===id?{...x,status}:x))
  const del  = id => setApps(a=>a.filter(x=>x.id!==id))

  const genFollowup = async app => {
    setFuLoading(l=>({...l,[app.id]:true}))
    try {
      const txt = await groq(apiKey,
        "Professional email writer. Concise, specific, no clichés.",
        `Follow-up email for: Company: ${app.company}, Role: ${app.role}, Stage: ${app.status}, Date: ${app.date}, Contact: ${app.contact||"Hiring Team"}. Under 120 words, subject line, stage-specific.`)
      setFuText(t=>({...t,[app.id]:txt}))
    } catch(e){ toast(e.message) }
    setFuLoading(l=>({...l,[app.id]:false}))
  }

  const total    = apps.length
  const offers   = apps.filter(a=>a.status==="Offer 🎉").length
  const active   = apps.filter(a=>!["Offer 🎉","Rejected"].includes(a.status)).length

  return (
    <div className="page">
      <SectionHead icon={IconKanban} title="Application Tracker"
        caption="Kanban board · AI follow-up emails · Analytics"/>
      <div className="tabs" style={{marginBottom:"1.5rem"}}>
        {["📌 Kanban Board","➕ Add Application","📊 Analytics"].map((t,i)=>(
          <button key={i} className={`tab ${tab===i?"active":""}`} onClick={()=>setTab(i)}>{t}</button>
        ))}
      </div>

      {tab===0 && (
        !apps.length
          ? <div className="card" style={{textAlign:"center",padding:"3rem",color:"var(--dim)"}}>
              No applications yet — go to "Add Application" to log your first one.
            </div>
          : <div className="kanban">
              {AT_STATUSES.map((status,si)=>{
                const bucket = apps.filter(a=>a.status===status)
                return (
                  <div key={status} className="kb-col">
                    <div className="kb-head"
                      style={{background:`${AT_COLORS[si]}22`,color:AT_COLORS[si]}}>
                      {status} ({bucket.length})
                    </div>
                    {bucket.map(app=>(
                      <div key={app.id} className="kb-card">
                        <div className="kb-company">{app.company}</div>
                        <div className="kb-role">{app.role}</div>
                        {app.salary&&<div style={{fontSize:10,color:"var(--amber)",marginTop:4}}>💰 {app.salary}</div>}
                        <div className="kb-date">{app.date}</div>
                        {app.notes&&<div style={{fontSize:11,color:"var(--dim)",marginTop:6,borderTop:"1px solid var(--border)",paddingTop:6}}>{app.notes}</div>}
                        {app.next&&<div style={{fontSize:11,color:"var(--cyan)",marginTop:4}}>→ {app.next}</div>}
                        <div style={{marginTop:8}}>
                          <select className="select-el"
                            style={{fontSize:10,padding:"3px 6px"}}
                            value={status} onChange={e=>move(app.id,e.target.value)}>
                            {AT_STATUSES.map(s=><option key={s}>{s}</option>)}
                          </select>
                        </div>
                        <div style={{display:"flex",gap:4,marginTop:6}}>
                          <button className="btn btn-ghost btn-sm"
                            style={{flex:1,fontSize:10}}
                            onClick={()=>genFollowup(app)}
                            disabled={fuLoading[app.id]}>
                            {fuLoading[app.id]?<Loader/>:"✉️ Follow-up"}
                          </button>
                          <button className="btn btn-danger btn-sm"
                            style={{fontSize:10}} onClick={()=>del(app.id)}>🗑️</button>
                        </div>
                        {fuText[app.id]&&(
                          <div style={{marginTop:8,fontSize:11,background:"var(--muted)",
                            borderRadius:6,padding:"8px",whiteSpace:"pre-wrap"}}>
                            {fuText[app.id]}
                            <div style={{marginTop:6}}>
                              <CopyBtn text={fuText[app.id]}/>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )
              })}
            </div>
      )}

      {tab===1 && (
        <div className="card">
          <div className="col">
            <div className="g2" style={{gap:"1.5rem"}}>
              <div className="col">
                <Inp label="Company Name *" value={form.company} onChange={up("company")} placeholder="e.g. Google"/>
                <Inp label="Role Applied For *" value={form.role} onChange={up("role")} placeholder="e.g. Data Scientist"/>
                <Sel label="Current Status" value={form.status} onChange={up("status")} options={AT_STATUSES}/>
                <Inp label="Date Applied" value={form.date} onChange={up("date")} type="date"/>
              </div>
              <div className="col">
                <Inp label="Expected Salary / Range" value={form.salary} onChange={up("salary")} placeholder="e.g. ₹12–15 LPA"/>
                <Inp label="Recruiter / Contact" value={form.contact} onChange={up("contact")} placeholder="e.g. Priya Sharma"/>
                <Inp label="JD URL (optional)" value={form.jdUrl} onChange={up("jdUrl")} placeholder="https://..."/>
                <Inp label="Next Action" value={form.next} onChange={up("next")} placeholder="e.g. Follow up Friday"/>
              </div>
            </div>
            <Tex label="Notes" value={form.notes} onChange={up("notes")} rows={3}
              placeholder="Interview feedback, red flags, prep notes..."/>
            <Btn onClick={add} full>➕ Add Application</Btn>
          </div>
        </div>
      )}

      {tab===2 && (
        <div className="col">
          <Metrics items={[
            {label:"Total Applied",  value:total},
            {label:"Active Pipeline",value:active},
            {label:"Offers",         value:offers, color:"var(--green)"},
            {label:"Success Rate",   value:total?`${Math.round(offers/total*100)}%`:"—"},
          ]}/>
          <div style={{fontWeight:700,marginBottom:12}}>Applications by Stage</div>
          {AT_STATUSES.map((s,i)=>{
            const cnt = apps.filter(a=>a.status===s).length
            return (
              <div key={s} style={{display:"flex",alignItems:"center",gap:12,marginBottom:8}}>
                <div style={{width:150,fontSize:12,color:"var(--dim)",flexShrink:0}}>{s}</div>
                <div style={{flex:1,height:8,background:"var(--muted)",borderRadius:99,overflow:"hidden"}}>
                  <div style={{
                    width: total?`${(cnt/total)*100}%`:"0%",
                    height:"100%", background:AT_COLORS[i],
                    borderRadius:99, transition:"width 0.4s"
                  }}/>
                </div>
                <div style={{fontSize:13,fontWeight:700,minWidth:20}}>{cnt}</div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── SKILL GAP ROADMAP ─────────────────────────────────────────────────────────
const RoadmapPage = ({ apiKey, toast, atsResult }) => {
  const [form, setForm] = useState({
    role:"", skills:"", weeks:"4",
    level:"Intermediate", time:"4-6 hrs", style:"Blend of all"
  })
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const up = k => e => setForm(f=>({...f,[k]:e.target.value}))
  const hasMissing = atsResult?.xreq?.length > 0

  const [downloading, setDownloading] = useState(false)

  const run = async () => {
    if(!form.skills.trim()){ toast("Enter skills to learn."); return }
    setLoading(true); setResult(null)
    try {
      const data = await groq(apiKey,
        "Expert learning coach. Free resources only. JSON only.",
        `${form.weeks}-week roadmap. Role: ${form.role||"general tech"}. Skills: ${form.skills}. Level: ${form.level}. Time: ${form.time}/week. Style: ${form.style}.
Schema: {"summary":"","weeks":[{"week_range":"","focus":"","goal":"","daily_tasks":[],"resources":[],"project":""}],"final_project":"","pro_tips":[]}`, true)
      const receivedWeeks = Array.isArray(data?.weeks) ? data.weeks : []
      if (receivedWeeks.length === 0) {
        toast("AI response didn't include a roadmap — try generating again.")
        setLoading(false)
        return
      }
      setResult(data)
    } catch(e){ toast(e.message) }
    setLoading(false)
  }

  const downloadPdf = async () => {
    if (!result) return
    setDownloading(true)
    try {
      await downloadDocument("/api/documents/roadmap", {
        role: form.role, weeks_count: form.weeks,
        summary: result.summary || "",
        weeks: result.weeks || [],
        final_project: result.final_project || "",
        pro_tips: result.pro_tips || [],
      }, `${(form.role || "Skill").replace(/\s+/g, "_")}_Roadmap.pdf`)
    } catch (e) {
      toast(e.message)
    }
    setDownloading(false)
  }

  return (
    <div className="page">
      <SectionHead icon={IconRoadmap} title="Skill-Gap Learning Roadmap"
        caption="Turn missing skills into a week-by-week plan with free resources"/>
      <div className="card">
        <div className="g2" style={{gap:"1.5rem"}}>
          <div className="col">
            <Inp label="Target Role" value={form.role} onChange={up("role")}
              placeholder="e.g. Data Scientist, ML Engineer"/>
            {hasMissing && (
              <div style={{padding:"10px 12px",background:"rgba(143,170,122,0.07)",borderRadius:8,fontSize:12}}>
                <div style={{color:"var(--cyan)",fontWeight:600,marginBottom:6}}>
                  ✅ Missing skills from your ATS analysis:
                </div>
                <div className="chip-row">
                  {atsResult.xreq.map((s,i)=><span key={i} className="chip chip-r">{s}</span>)}
                </div>
                <div style={{marginTop:8}}>
                  <Btn sm variant="secondary"
                    onClick={()=>setForm(f=>({...f,skills:[...atsResult.xreq,...(atsResult.xpre||[])].join(", ")}))}>
                    Use these →
                  </Btn>
                </div>
              </div>
            )}
            <Tex label="Skills to Learn *" value={form.skills} onChange={up("skills")} rows={4}
              placeholder="e.g. Docker, Kubernetes, MLOps, Apache Spark, Airflow"/>
          </div>
          <div className="col">
            <div className="form-group">
              <label className="label">Duration</label>
              <div className="row">
                <input type="range" min={2} max={12} step={2}
                  value={form.weeks} onChange={up("weeks")} style={{flex:1}}/>
                <span style={{fontSize:15,fontWeight:700,color:"var(--cyan)",minWidth:60}}>
                  {form.weeks} weeks
                </span>
              </div>
            </div>
            <Sel label="Current Level" value={form.level} onChange={up("level")}
              options={["Complete Beginner","Some Basics","Intermediate","Advanced in some areas"]}/>
            <Sel label="Hours per Week" value={form.time} onChange={up("time")}
              options={["2-3 hrs","4-6 hrs","7-10 hrs","10+ hrs"]}/>
            <Sel label="Learning Style" value={form.style} onChange={up("style")}
              options={["Video courses + practice","Documentation + projects","Hands-on projects only","Blend of all"]}/>
          </div>
        </div>
        <div style={{marginTop:"1rem"}}>
          <Btn onClick={run} disabled={loading} full>
            {loading ? <><Loader/> Building Roadmap...</> : "📚 Generate My Roadmap"}
          </Btn>
        </div>
      </div>

      {result && (
        <div className="col" style={{marginTop:"1.5rem"}}>
          <div style={{fontStyle:"italic",color:"var(--dim)",padding:"12px 16px",
            background:"var(--muted)",borderRadius:8,fontSize:13}}>
            {result.summary}
          </div>
          {(result.weeks||[]).map((w,i)=>(
            <div key={i} className="week-card"
              style={{borderLeftColor:WEEK_COLS[i%WEEK_COLS.length]}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                <div style={{fontWeight:700,color:WEEK_COLS[i%WEEK_COLS.length]}}>
                  {w.week_range}
                </div>
                <span className="badge badge-dim">{w.focus}</span>
              </div>
              <div style={{fontSize:12,color:"var(--cyan)",marginBottom:10}}>
                🎯 Goal: {w.goal}
              </div>
              <div className="g2" style={{gap:"1rem"}}>
                <div>
                  <div style={{fontSize:11,fontWeight:700,color:"var(--dim)",
                    textTransform:"uppercase",marginBottom:6}}>Tasks</div>
                  {(w.daily_tasks||[]).map((t,j)=>(
                    <div key={j} style={{fontSize:12,padding:"3px 0"}}>• {t}</div>
                  ))}
                  {w.project&&(
                    <div style={{marginTop:8,fontSize:12,color:"var(--amber)"}}>
                      🛠️ Mini project: {w.project}
                    </div>
                  )}
                </div>
                <div>
                  <div style={{fontSize:11,fontWeight:700,color:"var(--dim)",
                    textTransform:"uppercase",marginBottom:6}}>Free Resources</div>
                  {(w.resources||[]).map((r,j)=>(
                    <div key={j} style={{fontSize:12,padding:"3px 0"}}>→ {r}</div>
                  ))}
                </div>
              </div>
            </div>
          ))}
          {result.final_project && (
            <div style={{padding:"16px",
              background:"rgba(143,170,122,0.07)",
              border:"1px solid rgba(143,170,122,0.2)",
              borderRadius:10}}>
              <div style={{fontWeight:700,marginBottom:6}}>🏆 Capstone Project</div>
              <div style={{fontSize:13}}>{result.final_project}</div>
            </div>
          )}
          {(result.pro_tips||[]).length > 0 && (
            <div className="card">
              <div style={{fontWeight:700,marginBottom:10}}>💡 Pro Tips</div>
              {result.pro_tips.map((t,i)=>(
                <div key={i} style={{fontSize:13,padding:"6px 0",
                  borderBottom:"1px solid var(--border)"}}>• {t}</div>
              ))}
            </div>
          )}
          <div className="g2">
            <Btn variant="ghost" onClick={()=>setResult(null)}>🔄 New Roadmap</Btn>
            <Btn variant="primary" onClick={downloadPdf} disabled={downloading}>
              {downloading ? <><Loader/> Generating...</> : "📥 Download PDF"}
            </Btn>
          </div>
        </div>
      )}
    </div>
  )
}

// ── INTERVIEW CHEAT SHEET ─────────────────────────────────────────────────────
const CheatSheetPage = ({ apiKey, toast, resumeBlob }) => {
  const [form, setForm] = useState({ role:"",company:"",round:"Technical Round",jd:"" })
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const up = k => e => setForm(f=>({...f,[k]:e.target.value}))

  const run = async () => {
    if(!form.role||!form.company||!form.jd){
      toast("Role, company, and JD are required."); return
    }
    setLoading(true); setResult(null)
    try {
      const data = await groq(apiKey,
        "Senior career coach. Specific, practical, concise. JSON only.",
        `Cheat sheet: Role: ${form.role}, Company: ${form.company}, Round: ${form.round}, JD: ${form.jd}, Resume: ${resumeBlob||"Not provided"}.
Schema: {"elevator_pitch":"","company_context":"","key_points":[],"likely_questions":[{"q":"","bullet_answer":[]}],"questions_to_ask":[],"red_flags_to_address":[],"quick_reminders":[]}`, true)
      if (!data?.elevator_pitch && !(data?.key_points||[]).length) {
        toast("AI response didn't include cheat sheet content — try again.")
        setLoading(false)
        return
      }
      setResult(data)
    } catch(e){ toast(e.message) }
    setLoading(false)
  }

  const downloadPdf = async () => {
    if (!result) return
    setDownloading(true)
    try {
      await downloadDocument("/api/documents/cheatsheet", {
        role: form.role, company: form.company, round: form.round,
        elevator_pitch: result.elevator_pitch || "",
        company_context: result.company_context || "",
        key_points: result.key_points || [],
        likely_questions: result.likely_questions || [],
        questions_to_ask: result.questions_to_ask || [],
        red_flags_to_address: result.red_flags_to_address || [],
        quick_reminders: result.quick_reminders || [],
      }, `${(form.company || "Interview").replace(/\s+/g, "_")}_CheatSheet.pdf`)
    } catch (e) {
      toast(e.message)
    }
    setDownloading(false)
  }

  return (
    <div className="page">
      <SectionHead icon={IconBookmark} title="Interview Cheat Sheet"
        caption="1-page AI prep brief — read it 10 minutes before walking in"/>
      <div className="card">
        <div className="g2" style={{gap:"1.5rem"}}>
          <div className="col">
            <Inp label="Role *" value={form.role} onChange={up("role")}
              placeholder="e.g. Data Scientist"/>
            <Inp label="Company *" value={form.company} onChange={up("company")}
              placeholder="e.g. Razorpay"/>
            <Sel label="Interview Round" value={form.round} onChange={up("round")}
              options={["Technical Round","HR / Cultural Fit","Managerial Round","Final Round / Partner"]}/>
            <Tex label="Job Description *" value={form.jd} onChange={up("jd")} rows={6}
              placeholder="Paste the full JD here..."/>
          </div>
          <div className="col">
            {resumeBlob
              ? <div style={{padding:"10px 12px",background:"rgba(143,170,122,0.07)",
                  borderRadius:8,fontSize:12,color:"var(--cyan)"}}>
                  ✅ Resume from Resume Builder will be used for context
                </div>
              : <div style={{fontSize:12,color:"var(--dim)",lineHeight:1.6}}>
                  Build your resume first for best results. The cheat sheet will be tailored to your background.
                </div>
            }
            <Btn onClick={run} disabled={loading} full style={{marginTop:"auto"}}>
              {loading ? <><Loader/> Generating...</> : "📝 Generate Cheat Sheet"}
            </Btn>
          </div>
        </div>
      </div>

      {result && (
        <div className="col" style={{marginTop:"1.5rem"}}>
          <div style={{padding:"16px",
            background:"rgba(143,170,122,0.08)",
            border:"1px solid rgba(143,170,122,0.2)",borderRadius:10}}>
            <div style={{fontSize:11,fontWeight:700,color:"var(--cyan)",
              textTransform:"uppercase",marginBottom:8}}>🎯 Your Opening Pitch</div>
            <div style={{fontSize:14,lineHeight:1.75}}>{result.elevator_pitch}</div>
          </div>
          <div className="g2">
            <div className="card">
              <div style={{fontWeight:700,marginBottom:10}}>🏢 Company Context</div>
              <div style={{fontSize:13,lineHeight:1.7,color:"var(--dim)"}}>
                {result.company_context}
              </div>
            </div>
            <div className="card">
              <div style={{fontWeight:700,marginBottom:10}}>✅ Key Points to Emphasize</div>
              {(result.key_points||[]).map((p,i)=>(
                <div key={i} style={{fontSize:12,padding:"5px 0",
                  borderBottom:"1px solid var(--border)"}}>→ {p}</div>
              ))}
            </div>
          </div>
          <div>
            <div style={{fontWeight:700,marginBottom:12,fontSize:15}}>
              ❓ Likely Questions & How to Answer
            </div>
            {(result.likely_questions||[]).map((lq,i)=>(
              <Accordion key={i} title={`Q${i+1}: ${lq.q}`} defaultOpen={i<2}>
                {(lq.bullet_answer||[]).map((b,j)=>(
                  <div key={j} style={{padding:"4px 0"}}>• {b}</div>
                ))}
              </Accordion>
            ))}
          </div>
          <div className="g3">
            <div className="card">
              <div style={{fontWeight:700,marginBottom:10}}>❓ Ask Them</div>
              {(result.questions_to_ask||[]).map((q,i)=>(
                <div key={i} style={{fontSize:12,padding:"4px 0"}}>→ {q}</div>
              ))}
            </div>
            <div className="card">
              <div style={{fontWeight:700,marginBottom:10}}>⚠️ Address Proactively</div>
              {(result.red_flags_to_address||[]).map((r,i)=>(
                <div key={i} style={{fontSize:12,padding:"4px 0",color:"var(--amber)"}}>! {r}</div>
              ))}
            </div>
            <div className="card">
              <div style={{fontWeight:700,marginBottom:10}}>⚡ Quick Reminders</div>
              {(result.quick_reminders||[]).map((r,i)=>(
                <div key={i} style={{fontSize:12,padding:"4px 0"}}>• {r}</div>
              ))}
            </div>
          </div>
          <div className="g2">
            <Btn variant="secondary" onClick={()=>setResult(null)}>🔄 New Cheat Sheet</Btn>
            <Btn variant="primary" onClick={downloadPdf} disabled={downloading}>
              {downloading ? <><Loader/> Generating...</> : "📥 Download PDF"}
            </Btn>
          </div>
        </div>
      )}
    </div>
  )
}

// ── PORTFOLIO BUILDER ─────────────────────────────────────────────────────────
const PortfolioPage = ({ apiKey, toast }) => {
  const STEPS = ["Identity","Your Story","Review"]
  const [step, setStep]   = useState(0)
  const [form, setForm]   = useState({ name:"",tagline:"",about:"",projects:"" })
  const [slides, setSlides] = useState([])
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const up = k => e => setForm(f=>({...f,[k]:e.target.value}))

  const generate = async () => {
    setLoading(true)
    try {
      const data = await groq(apiKey,
        'JSON only. Schema: {"slides":[{"title":"","content":""}]}',
        `6-slide portfolio for ${form.name}. Tagline: ${form.tagline}. About: ${form.about}. Projects: ${form.projects}. Slides order: About Me, Technical Skills, Project 1, Project 2, Achievements & Impact, Let's Connect`, true)
      const receivedSlides = Array.isArray(data?.slides) ? data.slides : []
      if (receivedSlides.length === 0) {
        // The model responded successfully but not in the shape we asked
        // for — surface that clearly instead of silently showing a blank
        // review screen with no explanation.
        toast("AI response didn't include slide data — try generating again.")
        setLoading(false)
        return
      }
      setSlides(receivedSlides); setStep(2)
    } catch(e){ toast(e.message) }
    setLoading(false)
  }

  const downloadPptx = async () => {
    if (!slides.length) return
    setDownloading(true)
    try {
      await downloadDocument("/api/documents/portfolio", {
        name: form.name, tagline: form.tagline, slides,
      }, `${form.name.replace(/\s+/g, "_") || "Apex"}_Portfolio.pptx`)
    } catch (e) {
      toast(e.message)
    }
    setDownloading(false)
  }

  return (
    <div className="page">
      <SectionHead icon={IconFrame} title="Portfolio Builder"
        caption="Generate a professional 6-slide PowerPoint deck from your notes"/>
      <WizardSteps steps={STEPS} current={step}/>
      <div className="card">
        {step===0 && (
          <div className="col">
            <Inp label="Full Name *" value={form.name} onChange={up("name")}
              placeholder="e.g. Vedant Sharma"/>
            <Inp label="Professional Tagline" value={form.tagline} onChange={up("tagline")}
              placeholder="Data Scientist | ML Engineer | Open Source Contributor"/>
            <Btn onClick={()=>setStep(1)} disabled={!form.name} full>Next →</Btn>
          </div>
        )}
        {step===1 && (
          <div className="col">
            <Tex label="About Me" value={form.about} onChange={up("about")} rows={4}
              placeholder="What drives you? Your background, what you love building..."/>
            <Tex label="Projects & Achievements" value={form.projects} onChange={up("projects")} rows={6}
              placeholder="Describe your 2-3 best projects with outcomes, tools, and measurable impact..."/>
            <div className="g2">
              <Btn variant="secondary" onClick={()=>setStep(0)}>← Back</Btn>
              <Btn onClick={generate} disabled={loading}>
                {loading?<><Loader/> Generating...</>:"⚡ Generate Slides"}
              </Btn>
            </div>
          </div>
        )}
        {step===2 && slides.length>0 && (
          <div className="col">
            <div style={{padding:"8px 12px",background:"rgba(16,185,129,0.1)",
              borderRadius:8,fontSize:12,color:"var(--green)",marginBottom:4}}>
              ✅ 6 slides generated — download the real .pptx below
            </div>
            {slides.map((s,i)=>(
              <div key={i} style={{padding:"14px 16px",background:"var(--muted)",
                borderRadius:8,borderLeft:`3px solid ${WEEK_COLS[i%WEEK_COLS.length]}`}}>
                <div style={{fontWeight:700,marginBottom:6,color:WEEK_COLS[i%WEEK_COLS.length]}}>
                  Slide {i+2}: {s.title}
                </div>
                <div style={{fontSize:12,color:"var(--dim)",lineHeight:1.7}}>
                  {s.content}
                </div>
              </div>
            ))}
            <div className="g2">
              <Btn variant="secondary" onClick={()=>{setStep(0);setSlides([])}}>
                🔄 Rebuild Slides
              </Btn>
              <Btn variant="primary" onClick={downloadPptx} disabled={downloading}>
                {downloading ? <><Loader/> Generating...</> : "📥 Download .pptx"}
              </Btn>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── MAIN APP ───────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage]       = useState("hub")
  const [expanded, setEx]     = useState(true)
  const prefersReducedMotion  = useReducedMotion()
  const [showSettings, setSS] = useState(false)
  const [toast, setToast]     = useState(null)
  const [visited, setVis]     = useState(new Set(["hub"]))
  const [resumeBlob, setRB]   = useState("")
  const [atsResult, setAR]    = useState(null)

  useEffect(() => {
    const el = document.createElement("style")
    el.textContent = CSS
    document.head.appendChild(el)
    return () => document.head.removeChild(el)
  }, [])

  // Count this visit once, as soon as the app loads
  useEffect(() => { trackEvent("app", "session_start") }, [])

  const navigate = useCallback(key => {
    setPage(key)
    setVis(v => new Set([...v, key]))
    trackEvent(key, "page_visit")
  }, [])

  const showToast = useCallback(msg => {
    setToast(msg)
    setTimeout(() => setToast(null), 3500)
  }, [])

  // track helper exposed to page components
  const track = trackEvent

  const shared = { apiKey: null, toast: showToast, track }

  // Inline simple modules using GenericModule
  const CoverLetterPage = () => <GenericModule icon={IconEnvelope} title="Cover Letter Generator"
    caption="Tailored letters matched to any JD — never sounds templated"
    apiKey={null} toast={showToast}
    fields={[
      {key:"name",    label:"Your Name",     placeholder:"e.g. Vedant Sharma"},
      {key:"role",    label:"Target Role",   placeholder:"e.g. Data Scientist"},
      {key:"company", label:"Company Name",  placeholder:"e.g. Razorpay"},
      {key:"jd",      label:"Job Description", type:"textarea", rows:5, placeholder:"Paste the full JD..."},
      {key:"resume",  label:"Your Resume / Highlights", type:"textarea", rows:4, placeholder:"Paste resume text or key achievements..."},
    ]}
    system="Expert cover letter writer. Specific, non-generic, under 350 words. No 'I am writing to express my interest' or other clichés. Start with a strong specific opener."
    buildPrompt={v=>`Cover letter for ${v.name||"the candidate"} applying to ${v.role} at ${v.company}. JD: ${v.jd}. Resume: ${v.resume}. Rules: Strong specific opener, para 1 why role/company, para 2 two achievements, para 3 90-day value, confident close. Under 350 words.`}
    downloadConfig={{
      endpoint: "/api/documents/coverletter",
      buildPayload: (vals, output) => ({
        name: vals.name, role: vals.role, company: vals.company, letter_text: output,
      }),
      filename: (vals) => `${(vals.name || "Cover").replace(/\s+/g, "_")}_CoverLetter.pdf`,
    }}
  />

  const LinkedInPage = () => <GenericModule icon={IconNetwork} title="LinkedIn Generator"
    caption="AI-crafted headline, About section, and brand tagline"
    apiKey={null} toast={showToast}
    fields={[
      {key:"role",    label:"Target Role",      placeholder:"e.g. Data Scientist, ML Engineer"},
      {key:"industry",label:"Industry / Domain",placeholder:"e.g. FinTech, Healthcare AI"},
      {key:"tone",    label:"Tone",             placeholder:"Professional / Bold / Friendly"},
      {key:"resume",  label:"Your Background",  type:"textarea", rows:5, placeholder:"Paste resume or key skills and achievements..."},
    ]}
    system="LinkedIn personal branding expert. Avoid all clichés: passionate, results-driven, synergy, thought leader, rockstar. Be human, specific, and distinctive."
    buildPrompt={v=>`Create LinkedIn content for: Role: ${v.role}, Industry: ${v.industry||"Tech"}, Tone: ${v.tone||"Professional"}, Background: ${v.resume}. Format:\nHEADLINE: [under 220 chars, pipe-separated, role + top skill + value prop]\n\nABOUT: [260-300 words, 3 paragraphs: who you are + what you build / 2-3 achievements with numbers / what you're looking for + CTA]\n\nTAGLINE: [under 60 chars, punchy brand statement]`}
  />

  const ColdOutreachPage = () => <GenericModule icon={IconPlane} title="Cold Outreach Generator"
    caption="Personalized DMs and cold emails that don't sound templated"
    apiKey={null} toast={showToast}
    fields={[
      {key:"role",    label:"Role You're Targeting",  placeholder:"e.g. Data Scientist Intern"},
      {key:"company", label:"Company",                placeholder:"e.g. Razorpay"},
      {key:"contact", label:"Recipient (optional)",   placeholder:"e.g. Rahul Mehta"},
      {key:"type",    label:"Message Type",           placeholder:"LinkedIn DM / Note / Cold Email"},
      {key:"context", label:"Context (optional)",     type:"textarea", rows:2, placeholder:"Saw their Series B, use their product daily, they're expanding ML team..."},
      {key:"bg",      label:"Your Background",        type:"textarea", rows:3, placeholder:"3rd year CS, built churn model, Python/ML/SQL, internship at XYZ..."},
    ]}
    system="Cold outreach expert. Never use: 'I hope this message finds you well', 'I wanted to reach out', 'I am a big fan'. Be specific, human, direct."
    buildPrompt={v=>`Write a ${v.type||"LinkedIn DM"} from a candidate to ${v.contact||"the hiring team"} at ${v.company} about the ${v.role} role. Background: ${v.bg}. Context: ${v.context||"none"}. Rules: Open specific to them (not a compliment), one relevant achievement, low-friction close (not 'Can we jump on a call?'). Include subject line if email.`}
  />

  const pages = {
    hub:          <HubPage onNav={navigate} visited={visited}/>,
    resume:       <ResumeBuilderPage {...shared} setResumeBlob={setRB}/>,
    portfolio:    <PortfolioPage {...shared}/>,
    career:       <CareerPage {...shared} resumeBlob={resumeBlob}/>,
    coverletter:  <CoverLetterPage/>,
    linkedin:     <LinkedInPage/>,
    coldoutreach: <ColdOutreachPage/>,
    salary:       <SalaryPage {...shared}/>,
    interview:    <MockInterviewPage {...shared} resumeBlob={resumeBlob}/>,
    tracker:      <AppTrackerPage {...shared}/>,
    roadmap:      <RoadmapPage {...shared} atsResult={atsResult}/>,
    cheatsheet:   <CheatSheetPage {...shared} resumeBlob={resumeBlob}/>,
  }

  return (
    <div className="layout">
      <Sidebar
        current={page} onNav={navigate}
        expanded={expanded} onToggle={()=>setEx(e=>!e)}
        onSettings={()=>setSS(true)}
      />
      <main className={`main ${expanded?"":"sm"}`}>
        <AnimatePresence mode="wait">
          <motion.div
            key={page}
            initial={{ opacity: 0, y: prefersReducedMotion ? 0 : 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: prefersReducedMotion ? 0 : -8 }}
            transition={{ duration: prefersReducedMotion ? 0.01 : 0.22, ease: [0.16, 1, 0.3, 1] }}
          >
            {pages[page]}
          </motion.div>
        </AnimatePresence>
      </main>
      {showSettings && <SettingsModal onClose={()=>setSS(false)}/>}
      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
