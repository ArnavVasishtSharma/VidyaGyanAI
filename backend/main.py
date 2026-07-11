"""
main.py — AI-BOT FastAPI Backend
Endpoints:
  POST /chat        — send message, get AI reply + audio
  POST /session     — update session (name, class, subject)
  GET  /log         — download session log
  GET  /health      — health check
"""

import os
import re
import io
import base64
import datetime
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="AI-BOT API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Groq client ───────────────────────────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are AI-BOT, a warm and friendly study companion for students of Class 7 to 12
at VidyaGyan schools run by Shiv Nadar Foundation.

=== WHO YOU ARE ===
You are like a helpful, encouraging older sibling (bhaiya/didi) — never a textbook.
You genuinely care about the student's wellbeing, not just their marks.
You make learning feel like a conversation, not a lecture.

=== HOW YOU TALK ===
- Speak in natural Hinglish: mix Hindi and English mid-sentence exactly the way Indian students do
- Always use Romanized Hindi, never Devanagari script (write "kya" not "क्या")
- Keep replies SHORT — max 4-5 sentences. Students don't read walls of text.
- Use relatable, everyday Indian examples (cricket, chai, rickshaw, phone, roti, auto, etc.)
- Rotate encouragement phrases — never repeat the same one twice in a row:
  "Arre wah!", "Bilkul sahi!", "Ekdum correct!", "Bahut accha socha!", "Perfect yaar!",
  "Sahi pakda!", "100 marks!", "Tu toh genius hai!", "Kya baat hai!", "Zabardast!"

=== EMOTIONAL CHECK-IN ===
- At the START of every session, after learning name and class, ask ONCE:
  "Aaj kaisa feel ho raha hai? Sab theek hai?"
- If stressed/tired: acknowledge FIRST, then transition to studying
- If happy news: celebrate FIRST, do NOT repeat the check-in question

=== SUBJECT RULES ===
- Help with: Maths, Science (Physics, Chemistry, Biology), Social Studies, History,
  Geography, English, Hindi, Computer Science — Class 7 to 12 only
- Off-topic (movies, cricket, personal): warm playful redirect, vary the phrasing
- NEVER refuse a school subject. Hard topic? Break it into smaller pieces.

=== SCIENCE ACCURACY ===
- Osmosis: ALWAYS use raisin-in-water or skin-wrinkling analogy. NEVER chai/chini (that is diffusion)
- Electricity direction: Class 9-10 = conventional current only; Class 11-12 = both
- Revision: NEVER assume chapter topic — always confirm first

=== QUIZ MODE (MANDATORY) ===
- After explaining ANY concept: end with "Ab ek quick question —" + ONE question
- Correct answer: celebrate + reinforce
- Wrong answer: "Koi baat nahi!" + gentle correction with new example

=== SESSION MEMORY ===
- Use student's name naturally — ONLY if clearly stated by student
- Remember class, pitch explanations at that level
- Class 7-8: super simple, fun analogies
- Class 9-10: concept + example + quiz, board exam awareness
- Class 11-12: slightly technical ok, extra encouraging (JEE/NEET pressure)

=== REVISION MODE ===
- "Kal exam hai" / "revise karo": confirm chapter → 3-5 point summary → quiz

=== NEVER ===
- No formal/robotic language ("Certainly!", "Of course!")
- No long paragraphs
- No Devanagari script
- No invented names
- No chapter assumptions
"""

# ── Session state (in-memory, per-server) ─────────────────────────────────────
sessions: dict[str, dict] = {}

def get_session(session_id: str) -> dict:
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "student_name": None,
            "student_class": None,
            "current_subject": None,
            "checkin_done": False,
            "topics_covered": [],
            "msg_count": 0,
            "started_at": datetime.datetime.now().isoformat(),
        }
    return sessions[session_id]

# ── TTS ───────────────────────────────────────────────────────────────────────
HINDI_MARKERS = {
    "hai", "hoon", "kya", "nahi", "aur", "mein", "toh", "yeh", "woh",
    "karo", "arre", "bilkul", "sahi", "accha", "theek", "padhai",
    "samjho", "batao", "chalo", "bhai", "yaar", "kuch", "bahut",
    "thoda", "abhi", "kal", "aaj", "mat", "lo", "ab", "phir",
    "lekin", "tum", "hum", "main", "naam", "exam", "tension",
    "milke", "karenge", "jayega", "ekdum", "shuru"
}

def detect_lang(text: str) -> str:
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return "en"
    count = sum(1 for w in words if w in HINDI_MARKERS)
    return "hi" if (count / len(words)) > 0.18 else "en"

def clean_text(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*",     r"\1", text)
    text = re.sub(r"`(.+?)`",       r"\1", text)
    text = re.sub(r"#+\s*",         " ",   text)
    text = re.sub(r"[\U0001F300-\U0001FFFF\U00002702-\U000027B0]+", "", text)
    replacements = {
        "AI-BOT": "AI Bot", "a^2": "a squared", "b^2": "b squared",
        "c^2": "c squared", "H2O": "H 2 O", "CO2": "C O 2",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()

def text_to_audio_b64(text: str) -> str:
    """Convert text to gTTS audio, return as base64 MP3 string."""
    cleaned = clean_text(text)
    lang    = detect_lang(cleaned)
    tts     = gTTS(text=cleaned, lang=lang, slow=False)
    buf     = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# ── Name/class extraction ─────────────────────────────────────────────────────
def extract_name(text: str) -> str | None:
    BAD = {"hai", "hoon", "is", "am", "the", "and", "class", "mein", "in"}
    patterns = [
        r"(?:main|mera naam|my name is|i am|i'm)\s+([A-Za-z]{2,15})\b",
        r"\bnaam\s+(?:hai\s+)?([A-Za-z]{2,15})\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip().capitalize()
            if name.lower() not in BAD:
                return name
    return None

def extract_class(text: str) -> str | None:
    m = re.search(
        r"class\s*(\d{1,2})|(\d{1,2})(?:th|st|nd|rd)?\s*class",
        text, re.IGNORECASE
    )
    return (m.group(1) or m.group(2)) if m else None

SUBJECTS = ["maths","math","science","physics","chemistry","biology",
            "history","geography","social","english","hindi","computer"]

def extract_subject(text: str) -> str | None:
    tl = text.lower()
    for s in SUBJECTS:
        if s in tl:
            return s.capitalize()
    return None

# ── Pydantic models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    message:    str
    tts:        bool = True   # Return audio?

class SessionUpdate(BaseModel):
    session_id:  str
    name:        str | None = None
    student_class: str | None = None
    subject:     str | None = None

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}

@app.post("/session")
def update_session(req: SessionUpdate):
    sess = get_session(req.session_id)
    if req.name:           sess["student_name"]  = req.name
    if req.student_class:  sess["student_class"] = req.student_class
    if req.subject:        sess["current_subject"] = req.subject
    return {"ok": True, "session": {
        "name": sess["student_name"],
        "class": sess["student_class"],
        "subject": sess["current_subject"],
    }}

@app.post("/chat")
def chat(req: ChatRequest):
    sess = get_session(req.session_id)
    sess["msg_count"] += 1

    # Extract name/class from early messages
    if sess["msg_count"] <= 2 and not sess["student_name"]:
        name = extract_name(req.message)
        if name:
            sess["student_name"] = name

    if sess["msg_count"] <= 3 and not sess["student_class"]:
        cls = extract_class(req.message)
        if cls:
            sess["student_class"] = cls

    # Subject detection
    subj = extract_subject(req.message)
    if subj:
        sess["current_subject"] = subj

    # Topic tracking
    if len(req.message) > 20:
        hint = req.message[:45].strip()
        if hint not in sess["topics_covered"]:
            sess["topics_covered"].append(hint)

    # Checkin tracking
    if not sess["checkin_done"] and sess["messages"]:
        last = sess["messages"][-1].get("content", "")
        if any(k in last.lower() for k in ["kaisa feel", "sab theek", "feel ho raha"]):
            sess["checkin_done"] = True

    # Build dynamic context
    ctx = []
    if sess["student_name"]:
        ctx.append(f"Student's name: {sess['student_name']}")
    else:
        ctx.append("Student name: UNKNOWN — do not invent a name.")
    if sess["student_class"]:
        ctx.append(f"Student's class: Class {sess['student_class']}")
    if sess["current_subject"]:
        ctx.append(f"Current subject: {sess['current_subject']}")
    if not sess["checkin_done"]:
        ctx.append("REMINDER: Ask emotional check-in after name+class — only once.")
    if sess["topics_covered"]:
        ctx.append(f"Topics this session: {', '.join(sess['topics_covered'][-5:])}")

    dynamic_system = "=== SESSION CONTEXT ===\n" + "\n".join(ctx) + "\n\n" + SYSTEM_PROMPT

    # Add user message
    sess["messages"].append({"role": "user", "content": req.message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": dynamic_system}] + sess["messages"],
            temperature=0.75,
            max_tokens=300,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    sess["messages"].append({"role": "assistant", "content": reply})

    # Generate audio if requested
    audio_b64 = None
    if req.tts:
        try:
            audio_b64 = text_to_audio_b64(reply)
        except Exception:
            pass   # TTS failure is non-fatal

    # Save log
    _save_log(sess)

    return {
        "reply":       reply,
        "audio_b64":   audio_b64,
        "session_info": {
            "name":    sess["student_name"],
            "class":   sess["student_class"],
            "subject": sess["current_subject"],
        }
    }

@app.get("/log/{session_id}")
def get_log(session_id: str):
    from fastapi.responses import PlainTextResponse
    sess = get_session(session_id)
    return PlainTextResponse(_build_log_text(sess), media_type="text/plain")

def _build_log_text(sess: dict) -> str:
    lines = [
        "=" * 55,
        "       AI-BOT SESSION LOG — VidyaGyan",
        "=" * 55,
        f"Student  : {sess.get('student_name') or 'Not given'}",
        f"Class    : {sess.get('student_class') or 'Not given'}",
        f"Subject  : {sess.get('current_subject') or 'General'}",
        f"Started  : {sess.get('started_at', '')}",
        f"Topics   : {', '.join(sess.get('topics_covered', []))}",
        "=" * 55, "",
    ]
    for msg in sess.get("messages", []):
        role = "Student" if msg["role"] == "user" else "AI-BOT"
        lines += [f"{role}:", msg["content"], ""]
    return "\n".join(lines)

def _save_log(sess: dict):
    os.makedirs("logs", exist_ok=True)
    name     = (sess.get("student_name") or "unknown").replace(" ", "_")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    path     = f"logs/session_{name}_{date_str}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(_build_log_text(sess))
