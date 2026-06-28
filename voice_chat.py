"""
voice_chat.py — Full voice-enabled AI-BOT chat loop
The complete pipeline: wake → listen → transcribe → AI → speak → repeat
This is the Day 11 "magic moment" file — everything wired together.
"""

import time
import sys
import threading
from stt import listen
from tts import speak, stop_speaking
from config import client, MODEL
from prompt import SYSTEM_PROMPT

# ── Session State ─────────────────────────────────────────────────────────────
session = {
    "student_name": None,
    "student_class": None,
    "current_subject": None,
    "checkin_done": False,
    "topics_covered": [],
    "msg_count": 0,
}

# ── Visual status indicators ──────────────────────────────────────────────────
def status(msg: str):
    """Print a clear status line so user knows what AI-BOT is doing."""
    print(f"\n  [{msg}]")

# ── AI response ───────────────────────────────────────────────────────────────
def get_ai_response(messages: list) -> str:
    """Call Groq with full conversation history. Returns reply string."""
    # Build context prefix
    context_lines = []
    if session["student_name"]:
        context_lines.append(f"Student's name: {session['student_name']}")
    else:
        context_lines.append("Student's name: UNKNOWN — do not invent a name.")
    if session["student_class"]:
        context_lines.append(f"Student's class: Class {session['student_class']}")
    if session["current_subject"]:
        context_lines.append(f"Current subject: {session['current_subject']}")
    if not session["checkin_done"]:
        context_lines.append(
            "REMINDER: After learning name and class, ask the emotional "
            "check-in ('Aaj kaisa feel ho raha hai?') — only once."
        )

    context_prefix = "\n".join(context_lines)
    dynamic_system = f"=== CURRENT SESSION CONTEXT ===\n{context_prefix}\n\n{SYSTEM_PROMPT}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": dynamic_system}] + messages,
        temperature=0.75,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

# ── Main voice loop ───────────────────────────────────────────────────────────
def voice_chat():
    print("\n" + "="*55)
    print("     AI-BOT — Voice Mode | VidyaGyan")
    print("="*55)
    print("Press Ctrl+C to end the session.")
    print("⚠  macOS: Allow microphone access if prompted.\n")

    messages = []

    # Opening greeting — spoken aloud
    opening = ("Namaste! Main hoon AI-BOT, tumhara study companion. "
               "Pehle batao — tumhara naam kya hai aur tum konsi class mein ho?")

    status("AI-BOT is speaking...")
    print(f"\nAI-BOT: {opening}")
    speak(opening)
    messages.append({"role": "assistant", "content": opening})

    while True:
        try:
            # ── LISTEN ───────────────────────────────────────────────────────
            status("Listening... speak now")
            user_text = listen()

            if not user_text or not user_text.strip():
                status("Nothing heard — try again")
                prompt = "Kuch suna nahi — dobara bolo?"
                speak(prompt)
                continue

            session["msg_count"] += 1
            print(f"\nYou: {user_text}")

            # ── EXIT DETECTION ────────────────────────────────────────────────
            exit_words = ["bye", "goodbye", "band karo", "stop", "exit",
                          "alvida", "baad mein milte hain"]
            if any(w in user_text.lower() for w in exit_words):
                name = session["student_name"] or "yaar"
                farewell = (f"Bahut accha kiya aaj, {name}! "
                            "Padhai karte raho — tu kar sakta hai! Alvida!")
                status("AI-BOT is speaking...")
                print(f"\nAI-BOT: {farewell}")
                speak(farewell)
                break

            # ── NAME EXTRACTION (first 2 messages only) ───────────────────────
            if session["msg_count"] <= 2 and not session["student_name"]:
                import re
                patterns = [
                    r"(?:main|mera naam|my name is|i am|i'm)\s+([A-Za-z]{2,15})\b",
                    r"\bnaam\s+(?:hai\s+)?([A-Za-z]{2,15})\b",
                ]
                BAD = {"hai", "hoon", "is", "am", "the", "and", "class", "mein"}
                for pat in patterns:
                    m = re.search(pat, user_text, re.IGNORECASE)
                    if m:
                        candidate = m.group(1).strip().capitalize()
                        if candidate.lower() not in BAD and len(candidate) > 1:
                            session["student_name"] = candidate
                            break

            # ── CLASS EXTRACTION (first 3 messages) ───────────────────────────
            if session["msg_count"] <= 3 and not session["student_class"]:
                import re
                m = re.search(
                    r"class\s*(\d{1,2})|(\d{1,2})(?:th|st|nd|rd)?\s*class",
                    user_text, re.IGNORECASE
                )
                if m:
                    session["student_class"] = m.group(1) or m.group(2)

            # ── CHECKIN TRACKING ──────────────────────────────────────────────
            if not session["checkin_done"] and messages:
                last_bot = messages[-1]["content"]
                if any(kw in last_bot.lower()
                       for kw in ["kaisa feel", "sab theek", "feel ho raha"]):
                    session["checkin_done"] = True

            messages.append({"role": "user", "content": user_text})

            # ── GET AI RESPONSE ───────────────────────────────────────────────
            status("Thinking...")
            t0 = time.time()
            try:
                reply = get_ai_response(messages)
                latency = round(time.time() - t0, 2)
            except Exception as e:
                error_msg = "Ek second, kuch technical problem aa gayi. Dobara try karo."
                print(f"\n[Groq error: {e}]")
                speak(error_msg)
                messages.pop()  # Remove failed user message
                continue

            messages.append({"role": "assistant", "content": reply})
            print(f"\nAI-BOT ({latency}s): {reply}")

            # ── SPEAK RESPONSE ────────────────────────────────────────────────
            status("AI-BOT is speaking...")
            speak(reply)

        except KeyboardInterrupt:
            print("\n\n[Session ended by user]")
            name = session["student_name"] or "yaar"
            farewell = f"Theek hai {name}, kal phir milenge. Alvida!"
            speak(farewell)
            break

    # ── SESSION SUMMARY ───────────────────────────────────────────────────────
    print("\n" + "="*55)
    print("Session Summary")
    print("="*55)
    print(f"Student : {session['student_name'] or 'Not given'}")
    print(f"Class   : {session['student_class'] or 'Not given'}")
    print(f"Subject : {session['current_subject'] or 'General'}")
    print(f"Messages: {session['msg_count']} exchanges")
    print("="*55)

if __name__ == "__main__":
    voice_chat()