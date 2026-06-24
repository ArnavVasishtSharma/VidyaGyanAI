import os
import re
import datetime
from config import client, MODEL
from prompt import SYSTEM_PROMPT

# ── Session State ────────────────────────────────────────────────────────────
session = {
    "student_name": None,
    "student_class": None,
    "current_subject": None,
    "checkin_done": False,
    "topics_covered": [],
    "name_locked": False,   # once True, stop trying to extract name
}

SUBJECTS = ["maths", "math", "science", "physics", "chemistry", "biology",
            "history", "geography", "social studies", "english", "hindi",
            "computer", "economics", "civics"]

# ── Utilities ────────────────────────────────────────────────────────────────
def extract_name(text: str) -> str | None:
    """
    Pull student name — only runs on first 2 messages to avoid
    false positives like extracting movie/celebrity names later.
    """
    patterns = [
        r"(?:main|mera naam|my name is|i am|i'm)\s+([A-Za-z]{2,15})\b",
        r"\bnaam\s+(?:hai\s+)?([A-Za-z]{2,15})\b",
    ]
    BAD_WORDS = {"hai", "hoon", "is", "am", "the", "and", "class", "mein",
                 "se", "ko", "ka", "ki", "ho", "hu", "tha", "thi"}
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip().capitalize()
            if name.lower() not in BAD_WORDS and len(name) > 1:
                return name
    return None

def extract_class(text: str) -> str | None:
    match = re.search(
        r"class\s*(\d{1,2})|(\d{1,2})(?:th|st|nd|rd)?\s*class",
        text, re.IGNORECASE
    )
    if match:
        return match.group(1) or match.group(2)
    return None

def detect_subject(text: str) -> str | None:
    text_lower = text.lower()
    for subj in SUBJECTS:
        if subj in text_lower:
            return subj.capitalize()
    return None

def build_context_prefix() -> str:
    lines = []
    if session["student_name"]:
        lines.append(f"Student's confirmed name: {session['student_name']}")
    else:
        lines.append("Student's name: UNKNOWN — do not invent or assume a name.")
    if session["student_class"]:
        lines.append(f"Student's class: Class {session['student_class']}")
    if session["current_subject"]:
        lines.append(f"Current subject: {session['current_subject']}")
    if session["topics_covered"]:
        lines.append(f"Topics this session: {', '.join(session['topics_covered'][-5:])}")
    if not session["checkin_done"]:
        lines.append("REMINDER: Ask the emotional check-in ('Aaj kaisa feel ho raha hai?') "
                     "after learning name and class — only once.")
    return "\n".join(lines)

def save_log(messages: list):
    os.makedirs("logs", exist_ok=True)
    name = (session["student_name"] or "Unknown").replace(" ", "_")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"logs/session_{name}_{date_str}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 55 + "\n")
        f.write("       AI-BOT SESSION LOG — VidyaGyan\n")
        f.write("=" * 55 + "\n")
        f.write(f"Student  : {session['student_name'] or 'Not given'}\n")
        f.write(f"Class    : {session['student_class'] or 'Not specified'}\n")
        f.write(f"Subject  : {session['current_subject'] or 'General'}\n")
        f.write(f"Date     : {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}\n")
        if session["topics_covered"]:
            f.write(f"Topics   : {', '.join(session['topics_covered'])}\n")
        f.write("=" * 55 + "\n\n")
        for msg in messages:
            role = "Student" if msg["role"] == "user" else "AI-BOT"
            f.write(f"{role}:\n{msg['content']}\n\n")
    print(f"\n[Session log saved → {filename}]")
    return filename

# ── Main Chat Loop ───────────────────────────────────────────────────────────
def chat():
    print("\n" + "=" * 55)
    print("        AI-BOT — VidyaGyan Study Companion")
    print("=" * 55)
    print("Type 'bye' to end the session.\n")

    messages = []
    msg_count = 0

    opening = ("Namaste! Main hoon AI-BOT, tumhara study companion. "
               "Pehle batao — tumhara naam kya hai aur tum konsi class mein ho?")
    print(f"AI-BOT: {opening}\n")
    messages.append({"role": "assistant", "content": opening})

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n[Session interrupted]")
            save_log(messages)
            break

        if not user_input:
            continue

        if user_input.lower() in ["bye", "exit", "quit", "goodbye", "band karo"]:
            name_str = session["student_name"] or "yaar"
            farewell = (f"Bahut accha kiya aaj, {name_str}! "
                        "Kal phir milenge. Padhai karte raho — tu kar sakta hai!")
            print(f"\nAI-BOT: {farewell}")
            save_log(messages)
            break

        msg_count += 1

        # Name extraction — ONLY first 2 user messages
        if msg_count <= 2 and not session["name_locked"]:
            name = extract_name(user_input)
            if name:
                session["student_name"] = name
                session["name_locked"] = True

        # Lock name extraction after msg 2 regardless
        if msg_count > 2:
            session["name_locked"] = True

        # Class extraction — first 3 messages only
        if msg_count <= 3 and not session["student_class"]:
            cls = extract_class(user_input)
            if cls:
                session["student_class"] = cls

        # Subject detection — always active
        detected = detect_subject(user_input)
        if detected and detected != session["current_subject"]:
            session["current_subject"] = detected

        # Checkin tracking
        if not session["checkin_done"] and len(messages) > 3:
            recent_bot = messages[-1]["content"] if messages else ""
            if any(kw in recent_bot.lower() for kw in ["kaisa feel", "sab theek", "feel ho raha"]):
                session["checkin_done"] = True

        # Topic logging
        if len(user_input) > 20:
            hint = user_input[:45].strip()
            if hint not in session["topics_covered"]:
                session["topics_covered"].append(hint)

        messages.append({"role": "user", "content": user_input})

        # Build system prompt with live context
        context = build_context_prefix()
        dynamic_system = f"=== CURRENT SESSION CONTEXT ===\n{context}\n\n{SYSTEM_PROMPT}"

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": dynamic_system}] + messages,
                temperature=0.75,
                max_tokens=350,
            )
            reply = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": reply})
            print(f"\nAI-BOT: {reply}\n")

        except Exception as e:
            print(f"\n[Groq API error: {e}]\n")

if __name__ == "__main__":
    chat()