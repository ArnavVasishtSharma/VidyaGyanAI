"""
eval.py — AI-BOT Day 2 Evaluation Script
Runs 20 structured test inputs through the full chat pipeline.
Saves findings to findings.md automatically.
Usage: python eval.py
"""

import os
import time
import datetime
from config import client, MODEL
from prompt import SYSTEM_PROMPT

# ── 20 Test Cases ────────────────────────────────────────────────────────────
TEST_CASES = [
    # (category, input, what_to_check)
    ("Hindi",           "Newton ka pehla niyam kya hota hai?",
                        "Responds in Hinglish, gives example, ends with quiz"),
    ("Hindi",           "Photosynthesis kya hoti hai?",
                        "Simple analogy, quiz question at the end"),
    ("Hindi",           "Bharat ki rajdhani kahan hai?",
                        "Quick answer, then asks if they want to explore more"),
    ("English",         "Explain the water cycle to me",
                        "Clear explanation, real-life example, quiz"),
    ("English",         "What is the Pythagoras theorem?",
                        "Formula + example + quiz"),
    ("English",         "What causes earthquakes?",
                        "Tectonic plates explained simply, quiz"),
    ("Hinglish",        "Bhaiya, osmosis samajh nahi aaya",
                        "Responds to 'bhaiya', uses relatable analogy (raisin/water)"),
    ("Hinglish",        "Mujhe acids aur bases ka difference batao",
                        "pH scale, everyday examples like nimbu/soap, quiz"),
    ("Hinglish",        "Electricity ka concept simple mein samjhao",
                        "Water-pipe analogy, volts/current, quiz"),
    ("Emotional-stress","Bahut dar lag raha hai, kal exam hai",
                        "Acknowledges fear FIRST, then offers help — does NOT jump to content"),
    ("Emotional-tired", "Aaj bahut thaka hua hoon, padhne ka mann nahi",
                        "Empathy first, gently motivates, short session offer"),
    ("Emotional-happy", "Aaj maths mein 95 marks aaye!",
                        "Celebrates enthusiastically before studying"),
    ("Quiz-correct",    "Mitochondria is the powerhouse of the cell",
                        "Celebrates, reinforces, maybe goes deeper"),
    ("Quiz-wrong",      "Photosynthesis happens in the roots of plants",
                        "Never shames, corrects gently, re-explains"),
    ("Off-topic-sport", "IPL mein kaun jeetega is baar?",
                        "Warm redirect, not cold refusal"),
    ("Off-topic-movie", "Pushpa 2 dekhi hai kya tumne?",
                        "Playful redirect to studies"),
    ("Off-topic-personal","Tumhari girlfriend hai kya?",
                        "Handles gracefully, redirects without being awkward"),
    ("Subject-switch",  "Ab Science chhodo, Mughal Empire padhna hai",
                        "Acknowledges switch, pivots to History naturally"),
    ("Hard-concept",    "Explain quantum mechanics to a Class 10 student",
                        "Breaks it down, doesn't say 'too hard', gives simplified version"),
    ("Revision-mode",   "Kal Chemistry ka exam hai — Chapter 4 revise karo",
                        "Asks which chapter, gives 3-5 point summary, then quiz"),
]

# ── Run Eval ─────────────────────────────────────────────────────────────────
def run_evaluation():
    print("\n" + "="*60)
    print("   AI-BOT — Day 2 Bilingual Evaluation (20 Questions)")
    print("="*60)
    print(f"Model: {MODEL}")
    print(f"Date:  {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}")
    print("="*60 + "\n")

    results = []

    for i, (category, question, check) in enumerate(TEST_CASES, 1):
        print(f"[{i:2}/20] [{category}]")
        print(f"       Q: {question}")

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": question},
                ],
                temperature=0.75,
                max_tokens=300,
            )
            reply = response.choices[0].message.content.strip()
            print(f"       A: {reply[:120]}{'...' if len(reply) > 120 else ''}")
            results.append((category, question, check, reply, "OK"))
        except Exception as e:
            print(f"       ERROR: {e}")
            results.append((category, question, check, str(e), "ERROR"))

        print()
        time.sleep(0.4)  # Respect rate limits

    # ── Save findings.md ─────────────────────────────────────────────────────
    save_findings(results)
    print("="*60)
    print(f"Evaluation complete. {len(results)} tests run.")
    print("findings.md saved.")

def save_findings(results):
    date_str = datetime.datetime.now().strftime("%d %B %Y")
    lines = [
        "# AI-BOT — Day 2 Evaluation Findings",
        f"**Date:** {date_str}  ",
        f"**Model:** {MODEL}  ",
        f"**Total tests:** {len(results)}  ",
        "",
        "---",
        "",
    ]

    categories = {}
    for cat, q, check, reply, status in results:
        categories.setdefault(cat, []).append((q, check, reply, status))

    for cat, items in categories.items():
        lines.append(f"## {cat}")
        for q, check, reply, status in items:
            lines.append(f"**Q:** {q}  ")
            lines.append(f"**Expected:** {check}  ")
            lines.append(f"**Response:**  ")
            lines.append(f"> {reply}  ")
            lines.append(f"**Status:** {status}  ")
            lines.append("")

    lines += [
        "---",
        "",
        "## Summary Notes",
        "",
        "*(Fill these in after reviewing responses above)*",
        "",
        "**What works well:**",
        "- ",
        "",
        "**Needs tuning:**",
        "- ",
        "",
        "**Tone observations:**",
        "- ",
        "",
        "**Hindi/Hinglish quality:**",
        "- ",
        "",
        "**Quiz triggers:**",
        "- ",
    ]

    with open("findings.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    run_evaluation()