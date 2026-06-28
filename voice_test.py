"""
voice_test.py — Full voice loop test for AI-BOT
Tests: mic → faster-whisper → Groq → pyttsx3 → speaker
Run this BEFORE voice_chat.py to verify every component works end-to-end.
"""

import time
from stt import listen
from tts import speak
from config import client, MODEL
from prompt import SYSTEM_PROMPT

def test_stt():
    print("\n" + "="*50)
    print("TEST 1 — Speech to Text (STT)")
    print("="*50)
    print("Say something in Hindi, English, or Hinglish.")
    text = listen()
    if text:
        print(f"✓ STT working. Transcript: {text!r}")
        return text
    else:
        print("✗ STT returned empty. Check mic permissions.")
        return None

def test_tts():
    print("\n" + "="*50)
    print("TEST 2 — Text to Speech (TTS)")
    print("="*50)
    test_line = ("Namaste! Main hoon AI-BOT, tumhara study companion. "
                 "Aaj kaisa feel ho raha hai? Sab theek hai?")
    print(f"Speaking: {test_line!r}")
    speak(test_line)
    result = input("✓ Did you hear AI-BOT speak? (y/n): ").strip().lower()
    return result == "y"

def test_groq(user_text: str):
    print("\n" + "="*50)
    print("TEST 3 — Groq API Response")
    print("="*50)
    print(f"Sending to Groq: {user_text!r}")
    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_text},
            ],
            temperature=0.75,
            max_tokens=200,
        )
        reply = response.choices[0].message.content.strip()
        latency = round(time.time() - t0, 2)
        print(f"✓ Groq replied in {latency}s")
        print(f"  Reply: {reply[:100]}...")
        return reply
    except Exception as e:
        print(f"✗ Groq error: {e}")
        return None

def test_full_loop():
    print("\n" + "="*50)
    print("TEST 4 — FULL LOOP (voice in → AI → voice out)")
    print("="*50)
    print("This is the MAGIC MOMENT. Say something to AI-BOT.\n")

    # Step 1: Listen
    print("Step 1/3 — Listening...")
    user_text = listen()
    if not user_text:
        print("✗ No speech detected. Try again.")
        return

    print(f"\nStep 2/3 — Sending to Groq: {user_text!r}")

    # Step 2: Get AI response
    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_text},
            ],
            temperature=0.75,
            max_tokens=200,
        )
        reply = response.choices[0].message.content.strip()
        latency = round(time.time() - t0, 2)
        print(f"Groq replied in {latency}s")
        print(f"AI-BOT: {reply}")
    except Exception as e:
        print(f"✗ Groq error: {e}")
        return

    # Step 3: Speak the reply
    print("\nStep 3/3 — Speaking response...")
    speak(reply)
    print("\n✓ FULL LOOP COMPLETE.")

def main():
    print("\n" + "="*50)
    print("   AI-BOT — Voice Component Tests")
    print("="*50)
    print("Running each component independently first,")
    print("then the full loop together.\n")

    # Grant mic permission prompt
    print("⚠ macOS may ask for microphone permission — click Allow if prompted.\n")
    input("Press Enter to begin...")

    # Test 1: STT
    stt_text = test_stt()
    stt_ok = stt_text is not None

    # Test 2: TTS
    tts_ok = test_tts()

    # Test 3: Groq (uses stt_text if available, else a default)
    test_input = stt_text if stt_text else "Newton ka 3rd law kya hota hai?"
    reply = test_groq(test_input)
    groq_ok = reply is not None

    # Summary before full loop
    print("\n" + "="*50)
    print("Component Status:")
    print(f"  STT (faster-whisper): {'✓ OK' if stt_ok else '✗ FAILED'}")
    print(f"  TTS (pyttsx3):        {'✓ OK' if tts_ok else '✗ FAILED'}")
    print(f"  Groq API (Llama):     {'✓ OK' if groq_ok else '✗ FAILED'}")
    print("="*50)

    if stt_ok and tts_ok and groq_ok:
        print("\nAll components OK! Running full loop test...")
        input("Press Enter when ready to speak to AI-BOT...")
        test_full_loop()

        # Let user repeat the full loop
        while True:
            again = input("\nRun full loop again? (y/n): ").strip().lower()
            if again != "y":
                break
            test_full_loop()
    else:
        print("\n✗ Fix failing components above before running full loop.")
        if not stt_ok:
            print("  → STT fix: Check mic permissions in System Settings > Privacy > Microphone")
        if not tts_ok:
            print("  → TTS fix: Run python tts.py and check list_voices() output")
        if not groq_ok:
            print("  → Groq fix: Check your GROQ_API_KEY in .env file")

    print("\nVoice test complete.")

if __name__ == "__main__":
    main()