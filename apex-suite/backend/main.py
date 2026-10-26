# ─────────────────────────────────────────────────────────────────────────────
#  APEX SUITE  ·  FastAPI Backend
#  Securely proxies all Groq API calls — key never leaves the server
#  Also serves a backend-only /admin dashboard (never shipped in the React
#  bundle — this is the ONLY way to view analytics; there is no frontend route).
#  Run: uvicorn main:app --reload --port 8000
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import time
import logging
import urllib.request
import urllib.error
import hmac
import re
import threading
from collections import deque
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from documents import (
    build_resume_pdf, build_portfolio_pptx, build_cheatsheet_pdf,
    build_coverletter_pdf, build_interview_report_pdf, build_roadmap_pdf,
)

load_dotenv()

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)
log = logging.getLogger("apex")

# ── APP ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Apex Suite API",
    description="Secure backend for Apex Suite — AI career intelligence platform",
    version="2.0.0"
)

# Allow the React frontend (Vite dev server + production build) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── GROQ CLIENT ───────────────────────────────────────────────────────────────
# Supports up to 3 API keys — rotates automatically on rate limit
GROQ_KEYS = [
    k for k in [
        os.getenv("GROQ_API_KEY_1") or os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
    ] if k
]

if not GROQ_KEYS:
    log.warning("No GROQ_API_KEY found in environment — AI features will fail")

MODEL = "openai/gpt-oss-120b"  # llama-3.3-70b-versatile was deprecated by Groq
                                 # on June 17, 2026 — this is Groq's own
                                 # recommended same-tier replacement.

# ── ADMIN DASHBOARD CONFIG ────────────────────────────────────────────────────
# Server-side only — none of this is ever sent to the browser bundle.
# URL: tolerate a pasted trailing slash or "/rest/v1" suffix.
SUPABASE_URL      = re.sub(r"/rest/v1/?$", "", os.getenv("SUPABASE_URL", "").strip().rstrip("/"))
# Key: SUPABASE_SERVICE_KEY (a secret / service_role key — most secure, bypasses
# row-level security) wins if set. Otherwise SUPABASE_ANON_KEY, which may hold
# either the new sb_publishable_... key or the legacy anon JWT.
SUPABASE_KEY      = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
                     or os.getenv("SUPABASE_PUBLISHABLE_KEY") or "").strip()
ADMIN_PASSWORD    = os.getenv("DEV_DASHBOARD_PASSWORD", "")

if not (SUPABASE_URL and SUPABASE_KEY):
    log.warning("Supabase not configured — usage analytics and the /admin data are disabled.")

if not ADMIN_PASSWORD:
    log.warning("DEV_DASHBOARD_PASSWORD not set — /admin will refuse all logins until it is.")

# ── REQUEST / RESPONSE MODELS ─────────────────────────────────────────────────
class GroqRequest(BaseModel):
    system:    str
    user:      str
    json_mode: bool = False

class GroqResponse(BaseModel):
    result: object          # str or dict depending on json_mode
    key_used: Optional[int] # which key index was used (1-indexed)
    latency_ms: Optional[int]

# ── CORE GROQ CALL WITH KEY ROTATION ─────────────────────────────────────────
def call_groq_sync(system: str, user: str, json_mode: bool = False):
    """
    Try each configured API key in order.
    On 429 / overload: pause 700ms and try next key.
    On other errors: retry once with 400ms pause.
    Returns (result_text, key_index_used).
    """
    import urllib.request
    import urllib.error

    if not GROQ_KEYS:
        raise HTTPException(status_code=503,
            detail="No Groq API key configured on server. Add GROQ_API_KEY to .env")

    last_error = None

    for idx, key in enumerate(GROQ_KEYS):
        for attempt in range(2):
            try:
                payload = json.dumps({
                    "model":      MODEL,
                    "max_tokens": 2048,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user}
                    ],
                    **({"response_format": {"type": "json_object"}} if json_mode else {})
                }).encode()

                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type":  "application/json",
                        # Without a real User-Agent, urllib sends
                        # "Python-urllib/X.Y" by default — a well-known bot
                        # signature that Cloudflare's edge protection (sitting
                        # in front of api.groq.com) blocks before the request
                        # ever reaches Groq's own key-validation logic. That
                        # produces a 403 "error code: 1010" that looks like an
                        # auth failure but has nothing to do with the key.
                        "User-Agent":    "ApexSuite/2.0 (+https://github.com)",
                        "Accept":        "application/json",
                    },
                    method="POST"
                )

                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
                    text = data["choices"][0]["message"]["content"]
                    return text, idx + 1

            except urllib.error.HTTPError as e:
                status = e.code
                raw_body = e.read().decode("utf-8", errors="replace")
                try:
                    body = json.loads(raw_body)
                    msg = body.get("error", {}).get("message", raw_body[:300])
                except json.JSONDecodeError:
                    msg = raw_body.strip()[:300] if raw_body.strip() else f"HTTP {status} with an empty response body"

                if status in (429, 503):
                    # Rate limit — try next key
                    log.warning(f"Key {idx+1} rate-limited ({status}), trying next key")
                    time.sleep(0.7)
                    last_error = msg
                    break   # break inner retry loop, move to next key
                else:
                    last_error = f"Groq error {status}: {msg}"
                    if attempt == 0:
                        time.sleep(0.4)   # brief pause before retry

            except Exception as e:
                last_error = str(e)
                if attempt == 0:
                    time.sleep(0.4)

    raise HTTPException(
        status_code=503,
        detail=f"All API keys exhausted. Last error: {last_error}"
    )

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Health check — also verifies at least one API key is configured."""
    return {
        "status":      "ok",
        "model":       MODEL,
        "keys_loaded": len(GROQ_KEYS),
        "analytics":   bool(SUPABASE_URL and SUPABASE_KEY),
        "timestamp":   datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/groq", response_model=GroqResponse)
async def groq_proxy(req: GroqRequest, request: Request):
    """
    Single secure endpoint for all Groq calls.
    The React frontend sends system + user prompts.
    API key never leaves this server.
    """
    client_ip = request.client.host if request.client else "unknown"
    log.info(f"Groq call from {client_ip} | json={req.json_mode} | "
             f"system_len={len(req.system)} | user_len={len(req.user)}")

    t0 = time.time()
    text, key_idx = call_groq_sync(req.system, req.user, req.json_mode)
    latency = int((time.time() - t0) * 1000)

    log.info(f"Groq response | key={key_idx} | latency={latency}ms | "
             f"response_len={len(text)}")

    if req.json_mode:
        try:
            parsed = json.loads(text)
            return GroqResponse(result=parsed, key_used=key_idx, latency_ms=latency)
        except json.JSONDecodeError as e:
            log.error(f"JSON parse error: {e} | text={text[:200]}")
            raise HTTPException(status_code=500,
                detail=f"Model returned invalid JSON: {e}")

    return GroqResponse(result=text, key_used=key_idx, latency_ms=latency)

# NOTE: no @app.get("/") here on purpose — that path is now served by the
# StaticFiles mount at the bottom of this file (the actual React app).
# /api/health already covers the "is the API alive" check this used to do.

# ── DOCUMENT GENERATION  ·  real PDF/PPTX files, generated server-side ──────────
from typing import List, Dict, Any

class ResumeDocRequest(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    edu: str = ""
    skills: str = ""
    exp: List[str] = []
    proj: List[str] = []

class PortfolioDocRequest(BaseModel):
    name: str = ""
    tagline: str = ""
    slides: List[Dict[str, Any]] = []

class CheatSheetDocRequest(BaseModel):
    role: str = ""
    company: str = ""
    round: str = ""
    elevator_pitch: str = ""
    company_context: str = ""
    key_points: List[str] = []
    likely_questions: List[Dict[str, Any]] = []
    questions_to_ask: List[str] = []
    red_flags_to_address: List[str] = []
    quick_reminders: List[str] = []

class CoverLetterDocRequest(BaseModel):
    name: str = ""
    role: str = ""
    company: str = ""
    letter_text: str = ""

class InterviewReportDocRequest(BaseModel):
    role: str = ""
    overall_score: int = 0
    readiness_label: str = ""
    overall_feedback: str = ""
    top_strengths: List[str] = []
    critical_gaps: List[str] = []
    study_topics: List[str] = []
    next_steps: List[str] = []
    qa: List[Dict[str, Any]] = []

class RoadmapDocRequest(BaseModel):
    role: str = ""
    weeks_count: str = ""
    summary: str = ""
    weeks: List[Dict[str, Any]] = []
    final_project: str = ""
    pro_tips: List[str] = []


@app.post("/api/documents/resume")
async def documents_resume(req: ResumeDocRequest):
    try:
        pdf_bytes = build_resume_pdf(req.model_dump())
    except Exception as e:
        log.error(f"Resume PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"{(req.name or 'Resume').replace(' ', '_')}_Resume.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/documents/portfolio")
async def documents_portfolio(req: PortfolioDocRequest):
    try:
        pptx_bytes = build_portfolio_pptx(req.model_dump())
    except Exception as e:
        log.error(f"Portfolio PPTX generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PPTX generation failed: {e}")

    filename = f"{(req.name or 'Portfolio').replace(' ', '_')}_Portfolio.pptx"
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/documents/cheatsheet")
async def documents_cheatsheet(req: CheatSheetDocRequest):
    try:
        pdf_bytes = build_cheatsheet_pdf(req.model_dump())
    except Exception as e:
        log.error(f"Cheat sheet PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"{(req.company or 'Interview').replace(' ', '_')}_CheatSheet.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/documents/coverletter")
async def documents_coverletter(req: CoverLetterDocRequest):
    try:
        pdf_bytes = build_coverletter_pdf(req.model_dump())
    except Exception as e:
        log.error(f"Cover letter PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"{(req.name or 'Cover').replace(' ', '_')}_CoverLetter.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/documents/interview-report")
async def documents_interview_report(req: InterviewReportDocRequest):
    try:
        pdf_bytes = build_interview_report_pdf(req.model_dump())
    except Exception as e:
        log.error(f"Interview report PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"{(req.role or 'Interview').replace(' ', '_')}_Report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/documents/roadmap")
async def documents_roadmap(req: RoadmapDocRequest):
    try:
        pdf_bytes = build_roadmap_pdf(req.model_dump())
    except Exception as e:
        log.error(f"Roadmap PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"{(req.role or 'Skill').replace(' ', '_')}_Roadmap.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

# ── SUPABASE  ·  usage analytics (writes) + admin dashboard (reads) ────────────
# ALL Supabase traffic goes through this server. The browser never sees the
# Supabase URL or key — it just POSTs to /api/track and the credentials stay in
# this server's environment. That is what makes analytics work for every visitor
# of the deployed site, instead of only someone who pasted keys into a settings box.

SB_USER_AGENT = "ApexSuite/2.0 (analytics)"
SB_OK_STATUSES = (200, 201, 204)


def _sb_headers(prefer: Optional[str] = None) -> dict:
    h = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        # urllib's default "Python-urllib" agent is a known bot signature that
        # CDNs in front of APIs can block (this exact thing broke the Groq calls).
        "User-Agent": SB_USER_AGENT,
    }
    # Legacy JWT keys (eyJ...) are also sent as a bearer token. The newer
    # sb_publishable_ / sb_secret_ keys are NOT JWTs and must go in the apikey
    # header ONLY — sent as a bearer they get rejected as "Invalid JWT".
    if SUPABASE_KEY.startswith("eyJ"):
        h["Authorization"] = f"Bearer {SUPABASE_KEY}"
    if prefer:
        h["Prefer"] = prefer
    return h


def sb_request(method: str, path: str, body=None, prefer: Optional[str] = None, timeout: int = 8):
    """One Supabase REST call. Never raises — returns (status, parsed_body).
    status 0 means no HTTP response at all (DNS failure, timeout, paused project)."""
    if not (SUPABASE_URL and SUPABASE_KEY):
        return 0, "Supabase is not configured on the server"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}", data=data, method=method, headers=_sb_headers(prefer)
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, raw = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, f"could not reach Supabase ({type(e).__name__}: {e})"
    if not raw.strip():
        return status, None
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, raw[:300]


def _explain(status: int, detail) -> str:
    """Turn a failed Supabase response into a plain-English next step."""
    text = detail if isinstance(detail, str) else (json.dumps(detail)[:240] if detail is not None else "")
    low = text.lower()
    if status == 0:
        return f"{text}. A free Supabase project pauses after 7 days idle — check its dashboard."
    if status == 403 and "1010" in low:
        return "blocked at the network edge (bot filter), not by Supabase's own rules"
    if "row-level security" in low or "42501" in low:
        return "a row-level-security policy is missing — run backend/supabase_setup.sql"
    if "invalid jwt" in low:
        return "Supabase rejected how the key was sent (Invalid JWT) — use the sb_publishable_ key or a legacy anon key"
    if status == 401 or "invalid api key" in low:
        return "Supabase rejected the API key — copy it again from Settings > API Keys (legacy keys can disappear when a project is restored)"
    if status == 404 or "pgrst205" in low or "42p01" in low:
        return "table not found — run backend/supabase_setup.sql in the Supabase SQL editor"
    if status in (502, 503, 504, 520, 521, 522, 523, 525):
        return "Supabase is unreachable or paused (free projects pause after 7 days idle) — open its dashboard and click Restore project"
    return (text or "unexpected response")[:160]


def sb_insert(table: str, row: dict, ignore_duplicates: bool = False) -> bool:
    path = f"{table}?on_conflict=id" if ignore_duplicates else table
    prefer = "return=minimal" + (",resolution=ignore-duplicates" if ignore_duplicates else "")
    status, detail = sb_request("POST", path, row, prefer)
    if status in SB_OK_STATUSES:
        return True
    log.warning(f"Supabase insert into {table} failed (HTTP {status}): {_explain(status, detail)}")
    return False


def sb_fetch(table: str):
    """Returns (rows, error_message_or_None) — failures are reported, not hidden."""
    status, detail = sb_request("GET", f"{table}?order=created_at.desc&limit=500")
    if status == 200 and isinstance(detail, list):
        return detail, None
    msg = f"{table}: HTTP {status} — {_explain(status, detail)}"
    log.warning(f"Supabase read failed — {msg}")
    return [], msg


# ── /api/track  ·  public, write-only, rate-limited ────────────────────────────
SESSION_ID_RE = re.compile(r"^s_\d{10,16}_[a-z0-9]{1,10}$")
TRACK_PER_IP_PER_MIN = 120
TRACK_GLOBAL_PER_HOUR = 3000

_rl_lock = threading.Lock()
_ip_hits: Dict[str, deque] = {}
_global_hits: deque = deque()
_reg_lock = threading.Lock()
_registered_sessions: set = set()


class TrackEvent(BaseModel):
    session_id: str
    module: str
    action: str
    job_title: Optional[str] = None
    user_name: Optional[str] = None
    meta: Dict[str, Any] = {}
    device: Optional[str] = None
    browser: Optional[str] = None
    screen_size: Optional[str] = None


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def _allow_track(ip: str) -> bool:
    """Soft abuse guard: this endpoint is public and writes to a free-tier DB."""
    now = time.time()
    with _rl_lock:
        q = _ip_hits.setdefault(ip, deque())
        while q and now - q[0] > 60:
            q.popleft()
        while _global_hits and now - _global_hits[0] > 3600:
            _global_hits.popleft()
        if len(q) >= TRACK_PER_IP_PER_MIN or len(_global_hits) >= TRACK_GLOBAL_PER_HOUR:
            return False
        q.append(now)
        _global_hits.append(now)
        if len(_ip_hits) > 5000:   # keep memory bounded
            for k in [k for k, v in _ip_hits.items() if not v or now - v[-1] > 60][:2500]:
                _ip_hits.pop(k, None)
        return True


def _clip(v, n: int):
    if v is None:
        return None
    v = str(v).strip()
    return v[:n] if v else None


def _record_event(ev: dict) -> None:
    """Runs in the background after the HTTP response has already gone out."""
    sid = ev["session_id"]
    with _reg_lock:
        known = sid in _registered_sessions
    if not known:
        # Make sure the session row exists first, or the event's foreign key fails.
        ok = sb_insert(
            "apex_sessions",
            {"id": sid, "device": ev["device"], "browser": ev["browser"], "screen_size": ev["screen_size"]},
            ignore_duplicates=True,
        )
        if not ok:
            return   # don't mark it registered — the next event will retry
        with _reg_lock:
            if len(_registered_sessions) > 5000:
                _registered_sessions.clear()
            _registered_sessions.add(sid)
    if ev["action"] == "session_start":
        return       # registering the session was the whole point
    sb_insert("apex_events", {
        "session_id": sid, "module": ev["module"], "action": ev["action"],
        "job_title": ev["job_title"], "user_name": ev["user_name"], "metadata": ev["meta"],
    })


@app.post("/api/track")
async def track_event(ev: TrackEvent, request: Request, background: BackgroundTasks):
    """Fire-and-forget usage analytics. Always answers 204 so the app never waits on it."""
    if not (SUPABASE_URL and SUPABASE_KEY):
        return Response(status_code=204)
    if not SESSION_ID_RE.match(ev.session_id):
        return Response(status_code=204)
    if not _allow_track(_client_ip(request)):
        return Response(status_code=204)
    meta = ev.meta if isinstance(ev.meta, dict) else {}
    try:
        if len(json.dumps(meta)) > 1000:
            meta = {}
    except Exception:
        meta = {}
    background.add_task(_record_event, {
        "session_id": ev.session_id,
        "module": _clip(ev.module, 60) or "unknown",
        "action": _clip(ev.action, 60) or "unknown",
        "job_title": _clip(ev.job_title, 120),
        "user_name": _clip(ev.user_name, 120),
        "meta": meta,
        "device": _clip(ev.device, 30),
        "browser": _clip(ev.browser, 60),
        "screen_size": _clip(ev.screen_size, 20),
    })
    return Response(status_code=204)


# ── /api/keepalive  ·  stops a free Supabase project from auto-pausing ─────────
_keepalive_cache = {"t": 0.0, "result": None}


@app.get("/api/keepalive")
def keepalive():
    """One tiny read. Point a free uptime pinger at this every few days: a free
    Supabase project is paused after 7 days with no database activity."""
    now = time.time()
    if _keepalive_cache["result"] is not None and now - _keepalive_cache["t"] < 60:
        return _keepalive_cache["result"]
    if not (SUPABASE_URL and SUPABASE_KEY):
        result = {"supabase": "not_configured"}
    else:
        status, detail = sb_request("GET", "apex_sessions?select=id&limit=1")
        result = {"supabase": "ok"} if status == 200 else \
                 {"supabase": "error", "status": status, "hint": _explain(status, detail)}
    _keepalive_cache["t"] = now
    _keepalive_cache["result"] = result
    return result


# ── ADMIN DASHBOARD  ·  backend-only, never in the React bundle ────────────────
class AdminLoginRequest(BaseModel):
    password: str


ADMIN_MAX_FAILS = 5
ADMIN_LOCK_SECONDS = 600
_admin_lock = threading.Lock()
_admin_fails: Dict[str, list] = {}   # ip -> [failure_count, window_start]


def _admin_wait_seconds(ip: str) -> int:
    with _admin_lock:
        rec = _admin_fails.get(ip)
        if not rec:
            return 0
        age = time.time() - rec[1]
        if age > ADMIN_LOCK_SECONDS:
            _admin_fails.pop(ip, None)
            return 0
        return int(ADMIN_LOCK_SECONDS - age) if rec[0] >= ADMIN_MAX_FAILS else 0


@app.post("/admin/data")
def admin_data(req: AdminLoginRequest, request: Request):
    """The ONLY way analytics data can be read back out. Password is checked
    here, server-side, against the environment — never in the browser."""
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="DEV_DASHBOARD_PASSWORD not configured on server.")
    ip = _client_ip(request)
    wait = _admin_wait_seconds(ip)
    if wait:
        raise HTTPException(status_code=429, detail=f"Too many wrong attempts — try again in {wait // 60 + 1} min.")
    if not hmac.compare_digest(req.password.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8")):
        with _admin_lock:
            rec = _admin_fails.setdefault(ip, [0, time.time()])
            rec[0] += 1
        raise HTTPException(status_code=401, detail="Incorrect password.")
    with _admin_lock:
        _admin_fails.pop(ip, None)

    sessions, err1 = sb_fetch("apex_sessions")
    events, err2 = sb_fetch("apex_events")
    return {"sessions": sessions, "events": events, "errors": [e for e in (err1, err2) if e]}


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """Self-contained login + dashboard page rendered by the backend. Every value
    that came from a visitor is HTML-escaped before it is displayed."""
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"/><title>Apex Suite — Admin</title>
<meta name="robots" content="noindex,nofollow"/>
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:#14100C; color:#EFE6D2; font-family:-apple-system,Inter,sans-serif; min-height:100vh; }
  .wrap { max-width:1000px; margin:0 auto; padding:3rem 1.5rem; }
  h1 { font-size:1.4rem; font-weight:800; margin-bottom:1.5rem; }
  h2 { font-size:1rem; font-weight:800; margin-bottom:0.8rem; }
  .login { max-width:340px; margin:8rem auto; text-align:center; }
  .login p { color:#9C8D77; font-size:13px; margin-bottom:1.2rem; }
  input { width:100%; padding:0.7rem 0.9rem; border-radius:8px; border:1px solid #3A322A;
    background:#1E1712; color:#EFE6D2; font-size:14px; margin-bottom:0.75rem; }
  button { width:100%; padding:0.7rem; border-radius:8px; border:none;
    background:#C97F4C; color:#14100C; font-weight:700; font-size:14px; cursor:pointer; }
  button:hover { opacity:0.9; }
  .err { color:#E07856; font-size:12px; margin-top:8px; min-height:16px; }
  .banner { background:#3A1F18; border:1px solid #7A3B2A; color:#F0B4A0; border-radius:8px;
    padding:10px 14px; font-size:12px; line-height:1.6; margin-bottom:1.2rem; }
  .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:2rem; }
  .card { background:#1E1712; border:1px solid #3A322A; border-radius:10px; padding:1rem; }
  .card .lbl { font-size:11px; color:#9C8D77; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px; }
  .card .val { font-size:22px; font-weight:800; }
  table { width:100%; border-collapse:collapse; font-size:12px; margin-bottom:2rem; }
  th { text-align:left; padding:8px 10px; color:#9C8D77; text-transform:uppercase;
    font-size:10px; border-bottom:1px solid #3A322A; }
  td { padding:8px 10px; border-bottom:1px solid #2A231C; word-break:break-word; }
  .hidden { display:none; }
  .top { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; }
  .lock { background:none; border:1px solid #3A322A; color:#9C8D77; width:auto; padding:6px 14px; font-size:12px; }
</style></head>
<body>
  <div class="wrap">
    <div id="loginBox" class="login">
      <h1>Apex Suite — Admin</h1>
      <p>Backend-only dashboard. Not linked from the app.</p>
      <input id="pw" type="password" placeholder="Password" onkeydown="if(event.key==='Enter')login()"/>
      <button onclick="login()">Unlock</button>
      <div class="err" id="err"></div>
    </div>

    <div id="dashBox" class="hidden">
      <div class="top">
        <h1>Apex Suite — Admin Dashboard</h1>
        <button class="lock" onclick="location.reload()">Lock</button>
      </div>
      <div id="banner" class="banner hidden"></div>
      <div class="grid" id="stats"></div>
      <h2>Recent Events</h2>
      <table id="eventsTable"><thead><tr>
        <th>Time</th><th>Module</th><th>Action</th><th>Job Title</th><th>Name</th>
      </tr></thead><tbody></tbody></table>
      <h2>Sessions</h2>
      <table id="sessionsTable"><thead><tr>
        <th>Session</th><th>Device</th><th>Browser</th><th>Screen</th><th>Time</th>
      </tr></thead><tbody></tbody></table>
    </div>
  </div>

<script>
// Everything a visitor can influence (names, job titles, browser strings) goes
// through esc() before it touches the page — never straight into innerHTML.
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const when = v => { const d = new Date(v); return isNaN(d) ? '' : d.toLocaleString(); };

async function login() {
  const pw = document.getElementById('pw').value;
  const errEl = document.getElementById('err');
  errEl.textContent = '';
  try {
    const res = await fetch('/admin/data', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({password: pw})
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      errEl.textContent = e.detail || 'Login failed.';
      return;
    }
    render(await res.json());
  } catch(e) {
    errEl.textContent = 'Could not reach server.';
  }
}

function render(data) {
  document.getElementById('loginBox').classList.add('hidden');
  document.getElementById('dashBox').classList.remove('hidden');

  const sessions = data.sessions || [];
  const events = data.events || [];
  const problems = (data.errors || []).slice();
  if (!problems.length && !sessions.length && !events.length) {
    problems.push('No rows yet. If you expect data, run "python check_supabase.py" in the backend folder to test the connection.');
  }
  const banner = document.getElementById('banner');
  if (problems.length) {
    banner.innerHTML = problems.map(esc).join('<br>');
    banner.classList.remove('hidden');
  }

  const jobTitles = events.filter(e => e.job_title).length;
  const modules = new Set(events.map(e => e.module)).size;
  document.getElementById('stats').innerHTML = `
    <div class="card"><div class="lbl">Sessions</div><div class="val">${sessions.length}</div></div>
    <div class="card"><div class="lbl">Total Events</div><div class="val">${events.length}</div></div>
    <div class="card"><div class="lbl">Modules Used</div><div class="val">${modules}</div></div>
    <div class="card"><div class="lbl">Job Titles Logged</div><div class="val">${jobTitles}</div></div>
  `;

  document.querySelector('#eventsTable tbody').innerHTML = events.slice(0, 100).map(e => `
    <tr>
      <td>${esc(when(e.created_at))}</td>
      <td>${esc(e.module)}</td>
      <td>${esc(e.action)}</td>
      <td>${esc(e.job_title || '—')}</td>
      <td>${esc(e.user_name || '—')}</td>
    </tr>`).join('');

  document.querySelector('#sessionsTable tbody').innerHTML = sessions.slice(0, 100).map(s => `
    <tr>
      <td>${esc((s.id || '').slice(0, 14))}…</td>
      <td>${esc(s.device)}</td>
      <td>${esc(s.browser)}</td>
      <td>${esc(s.screen_size)}</td>
      <td>${esc(when(s.created_at))}</td>
    </tr>`).join('');
}
</script>
</body></html>"""


# ── STATIC FRONTEND  ·  serves the built React app from this same server ────────
# This is what makes the app deployable as ONE process on ONE port — required
# for platforms like Replit that expect a single run command. Locally, you can
# still run `npm run dev` separately for hot-reload (vite.config.js's proxy
# handles that case) — this mount only matters once `npm run build` has run
# and produced a dist/ folder to serve.
#
# Mounted LAST, after every /api/* and /admin route above, so those always
# take priority — StaticFiles only catches requests nothing else matched.
_DIST_DIR = Path(__file__).parent.parent / "dist"
if _DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST_DIR), html=True), name="frontend")
    log.info(f"Serving built frontend from {_DIST_DIR}")
else:
    log.warning(
        f"No dist/ folder found at {_DIST_DIR} — frontend will not be served. "
        f"Run 'npm run build' in the project root first, or use "
        f"'npm run dev' separately for local development."
    )

# ── ENTRY POINT  ·  respects Replit's (or any platform's) PORT env var ────────
# Lets this run as `python main.py` in addition to the usual
# `uvicorn main:app` — Replit's run command uses this form, and it correctly
# picks up whatever port Replit assigns rather than a hardcoded one.
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
