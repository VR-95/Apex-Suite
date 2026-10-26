#!/usr/bin/env python3
"""
Apex Suite - Supabase check.

Run it from the backend folder (the folder that holds your .env):

    python check_supabase.py

It reads the SAME settings the server uses (SUPABASE_URL plus SUPABASE_SERVICE_KEY
or SUPABASE_ANON_KEY) and tells you in plain English what is wrong and how to fix it.
It writes one clearly-labelled diagnostic row (module "diagnostic") to prove writes work.
"""
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

OK, BAD, WARN = "[ OK ]", "[FAIL]", "[WARN]"
problems = 0

URL = re.sub(r"/rest/v1/?$", "", os.getenv("SUPABASE_URL", "").strip().rstrip("/"))
KEY = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
       or os.getenv("SUPABASE_PUBLISHABLE_KEY") or "").strip()


def say(tag, msg):
    print(f"{tag} {msg}", flush=True)


def fail(msg, fix=""):
    global problems
    problems += 1
    say(BAD, msg)
    if fix:
        print(f"         -> {fix}", flush=True)


def request(method, path, body=None, prefer=None, timeout=12):
    """Same request shape the server uses. Returns (status, parsed_body); status 0 = no HTTP response."""
    headers = {"apikey": KEY, "Content-Type": "application/json", "Accept": "application/json",
               "User-Agent": "ApexSuite/2.0 (check_supabase)"}
    if KEY.startswith("eyJ"):          # legacy JWT keys also go in the bearer header; sb_ keys must NOT
        headers["Authorization"] = f"Bearer {KEY}"
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{URL}/rest/v1/{path}", data=data, method=method, headers=headers)
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


def explain(status, detail):
    text = detail if isinstance(detail, str) else (json.dumps(detail)[:240] if detail is not None else "")
    low = text.lower()
    if status == 0:
        return (f"{text}. A free Supabase project pauses after 7 days with no activity - open the "
                "Supabase dashboard and click Restore project (check your internet connection too).")
    if status == 403 and "1010" in low:
        return "blocked at the network edge (bot filter), not by Supabase's own rules"
    if "row-level security" in low or "42501" in low:
        return "a row-level-security policy is missing - run backend/supabase_setup.sql in the Supabase SQL editor"
    if "invalid jwt" in low:
        return "Supabase rejected how the key was sent (Invalid JWT) - use the sb_publishable_ key or a legacy anon key"
    if status == 401 or "invalid api key" in low:
        return ("Supabase rejected the API key - copy it again from Project Settings > API Keys "
                "(legacy keys can disappear when a paused project is restored)")
    if status == 404 or "pgrst205" in low or "42p01" in low:
        return "table not found - run backend/supabase_setup.sql in the Supabase SQL editor"
    if status in (502, 503, 504, 520, 521, 522, 523, 525):
        return ("Supabase is unreachable or paused (free projects pause after 7 days idle) - open the "
                "Supabase dashboard and click Restore project")
    return (text or "unexpected response")[:160]


def describe_key(key):
    if key.startswith("sb_publishable_"):
        return "publishable key (new format)", ""
    if key.startswith("sb_secret_"):
        return "SECRET key (new format) - full database access", \
            "Secret keys must only ever live on the server - never in frontend code or a public repo."
    if key.startswith("eyJ"):
        role = "unknown"
        try:
            seg = key.split(".")[1]
            seg += "=" * (-len(seg) % 4)
            role = json.loads(base64.urlsafe_b64decode(seg)).get("role", "unknown")
        except Exception:
            pass
        extra = ("Legacy JWT keys are being retired by Supabase (end of 2026). Consider switching to the "
                 "sb_publishable_ key: Project Settings > API Keys.")
        if role == "service_role":
            extra += " This is the service_role key: full access, server-side only."
        return f"legacy JWT key (role: {role})", extra
    return "unrecognised key format", \
        "Keys normally start with sb_publishable_, sb_secret_ or eyJ - check you copied the whole key."


def finish():
    print()
    if problems == 0:
        say(OK, "Everything works. Usage will be recorded and the /admin dashboard will show it.")
        print("       This run added one diagnostic row (module 'diagnostic'); delete it in Supabase > Table Editor if you like.")
        print("       Reminder: a free project pauses after 7 days with no activity - ping /api/keepalive every few days.")
        sys.exit(0)
    print(f"{problems} problem(s) found. Fix the [FAIL] line(s) above, then run this again.")
    sys.exit(1)


def main():
    print("Apex Suite - Supabase check\n")
    if not URL:
        fail("SUPABASE_URL is not set.",
             "Add it to backend/.env (or the Render environment). Find it in Supabase > Project Settings > API.")
    if not KEY:
        fail("No Supabase key is set.",
             "Set SUPABASE_ANON_KEY (the publishable key) in backend/.env or the Render environment.")
    if not (URL and KEY):
        finish()

    kind, note = describe_key(KEY)
    masked = (KEY[:12] + "..." + KEY[-4:]) if len(KEY) > 24 else "***"
    say(OK, f"URL: {URL}")
    say(OK, f"Key: {masked} - {kind}")
    if note:
        say(WARN, note)
    if not re.match(r"^https://[a-z0-9]+\.supabase\.co$", URL) and "localhost" not in URL and "127.0.0.1" not in URL:
        say(WARN, "URL does not look like https://<project-ref>.supabase.co - double-check it.")

    for table in ("apex_sessions", "apex_events"):
        status, detail = request("GET", f"{table}?select=id&limit=1")
        if status == 200:
            say(OK, f"table {table}: reachable, key accepted, readable")
        else:
            fail(f"table {table}: HTTP {status} - {explain(status, detail)}")
            finish()

    sid = "s_0000000000_check"
    status, detail = request("POST", "apex_sessions?on_conflict=id",
                             {"id": sid, "device": "diagnostic", "browser": "check_supabase.py", "screen_size": "0x0"},
                             "return=minimal,resolution=ignore-duplicates")
    if status in (200, 201, 204):
        say(OK, "write test: session row accepted")
    else:
        fail(f"write test (session): HTTP {status} - {explain(status, detail)}")
        finish()

    status, detail = request("POST", "apex_events",
                             {"session_id": sid, "module": "diagnostic", "action": "supabase_check",
                              "metadata": {"checked_at": datetime.now(timezone.utc).isoformat()}},
                             "return=minimal")
    if status in (200, 201, 204):
        say(OK, "write test: event row accepted (link to the session works)")
    else:
        fail(f"write test (event): HTTP {status} - {explain(status, detail)}")
        finish()

    status, detail = request("GET", f"apex_events?session_id=eq.{sid}&order=created_at.desc&limit=1")
    if status == 200 and isinstance(detail, list) and detail:
        say(OK, "read-back test: the row just written can be read - the admin dashboard will show data")
    elif status == 200:
        fail("read-back test: the write worked but the database returned NO rows.",
             "A SELECT policy is missing, so the /admin dashboard would always look empty. "
             "Run backend/supabase_setup.sql in the Supabase SQL editor.")
    else:
        fail(f"read-back test: HTTP {status} - {explain(status, detail)}")
    finish()


if __name__ == "__main__":
    main()
