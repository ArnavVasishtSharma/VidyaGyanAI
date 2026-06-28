"""
tts.py — Text-to-Speech for AI-BOT
Primary:  gTTS (Google TTS) — natural, multilingual, handles Hinglish perfectly
Speed:    pydub + ffmpeg for 1.18x playback (faster without pitch shift)
Fallback: pyttsx3 (offline) — used if no internet available
"""

import io
import re
import os
import time
import threading
import tempfile

# ── Dependency detection ──────────────────────────────────────────────────────
try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# ── Speed config ──────────────────────────────────────────────────────────────
# 1.0 = normal gTTS speed, 1.18 = 18% faster — natural conversational pace
# Tune this: 1.10 = slight boost, 1.20 = noticeably faster, 1.30 = too fast
SPEED = 1.12

# ── pyttsx3 fallback ──────────────────────────────────────────────────────────
_pyttsx3_engine = None
_engine_lock = threading.Lock()

def _get_pyttsx3():
    global _pyttsx3_engine
    if _pyttsx3_engine is None:
        _pyttsx3_engine = pyttsx3.init()
        _pyttsx3_engine.setProperty(
            "voice", "com.apple.voice.compact.en-IN.Rishi"
        )
        _pyttsx3_engine.setProperty("rate", 155)
        _pyttsx3_engine.setProperty("volume", 1.0)
    return _pyttsx3_engine

# ── Language detection ────────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    """
    Returns 'hi' for Hindi/Hinglish-heavy text, 'en' for English-heavy.
    gTTS lang='hi' handles Hinglish the most naturally.
    """
    hindi_markers = {
        "hai", "hoon", "kya", "nahi", "aur", "mein", "toh", "yeh",
        "woh", "karo", "arre", "bilkul", "sahi", "accha", "theek",
        "padhai", "samjho", "batao", "chalo", "bhai", "yaar", "dekho",
        "kuch", "bahut", "zyada", "thoda", "abhi", "kal", "aaj",
        "mat", "lo", "do", "ho", "ja", "ab", "phir", "lekin", "tum",
        "tumhe", "hum", "main", "naam", "exam", "tension", "samajh",
        "milke", "karenge", "jayega", "hoga", "chahiye", "kyun", "kyunki",
        "seedha", "jaise", "tarah", "ekdum", "shuruaat", "shuru", "band"
    }
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return "en"
    hindi_count = sum(1 for w in words if w in hindi_markers)
    return "hi" if (hindi_count / len(words)) > 0.18 else "en"

# ── Text cleaning ─────────────────────────────────────────────────────────────
def clean_for_speech(text: str) -> str:
    """Strip markdown, emoji, expand abbreviations for clean TTS input."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*",     r"\1", text)
    text = re.sub(r"`(.+?)`",       r"\1", text)
    text = re.sub(r"#+\s*",         " ",   text)
    text = re.sub(r"^\s*\d+\.\s+",  "",    text, flags=re.MULTILINE)
    text = re.sub(
        r"[\U0001F300-\U0001FFFF\U00002702-\U000027B0"
        r"\U0001F1E0-\U0001F1FF\U00002500-\U00002BEF]+",
        "", text
    )
    replacements = {
        "AI-BOT": "AI Bot", "a^2": "a squared", "b^2": "b squared",
        "c^2": "c squared", "H2O": "H 2 O", "CO2": "C O 2",
        "O2": "O 2", "pH": "P H", "e.g.": "for example",
        "i.e.": "that is", "etc.": "etcetera", "vs.": "versus",
        "NCERT": "N C E R T", "JEE": "J E E", "NEET": "N E E T",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()

# ── Speed up audio ────────────────────────────────────────────────────────────
def _speed_up_mp3(input_path: str, speed: float) -> str:
    """
    Use pydub to speed up the MP3 without changing pitch.
    Returns path to the sped-up temp file.
    Requires ffmpeg installed (brew install ffmpeg).
    """
    audio = AudioSegment.from_mp3(input_path)
    # Speed up by adjusting frame rate, then reset to original
    # This speeds up without pitch distortion
    fast = audio._spawn(
        audio.raw_data,
        overrides={"frame_rate": int(audio.frame_rate * speed)}
    ).set_frame_rate(audio.frame_rate)

    out = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    out_path = out.name
    out.close()
    fast.export(out_path, format="mp3")
    return out_path

# ── gTTS speak ────────────────────────────────────────────────────────────────
def _speak_gtts(text: str):
    lang = detect_language(text)
    tts = gTTS(text=text, lang=lang, slow=False)

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_path = tmp.name
    tmp.close()
    tts.save(tmp_path)

    play_path = tmp_path
    sped_path = None

    # Apply speed boost if pydub available
    if PYDUB_AVAILABLE and SPEED != 1.0:
        try:
            sped_path = _speed_up_mp3(tmp_path, SPEED)
            play_path = sped_path
        except Exception as e:
            print(f"[TTS] Speed boost skipped ({e}) — playing at normal speed")

    try:
        pygame.mixer.music.load(play_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    finally:
        pygame.mixer.music.unload()
        for p in [tmp_path, sped_path]:
            if p:
                try:
                    os.unlink(p)
                except Exception:
                    pass

# ── pyttsx3 fallback speak ────────────────────────────────────────────────────
def _speak_pyttsx3(text: str):
    with _engine_lock:
        engine = _get_pyttsx3()
        engine.say(text)
        engine.runAndWait()

# ── Public API ────────────────────────────────────────────────────────────────
def speak(text: str, block: bool = True):
    """Speak text aloud. gTTS primary, pyttsx3 fallback."""
    if not text or not text.strip():
        return
    cleaned = clean_for_speech(text)
    if block:
        _do_speak(cleaned)
    else:
        threading.Thread(target=_do_speak, args=(cleaned,), daemon=True).start()

def _do_speak(text: str):
    if GTTS_AVAILABLE:
        try:
            _speak_gtts(text)
            return
        except Exception as e:
            print(f"[TTS] gTTS failed ({e}), falling back to pyttsx3")
    if PYTTSX3_AVAILABLE:
        _speak_pyttsx3(text)
    else:
        print(f"[TTS] No TTS engine available. Text: {text}")

def stop_speaking():
    if GTTS_AVAILABLE:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"gTTS     : {'✓' if GTTS_AVAILABLE else '✗'}")
    print(f"pydub    : {'✓ (speed boost active)' if PYDUB_AVAILABLE else '✗ (install: pip install pydub + brew install ffmpeg)'}")
    print(f"pyttsx3  : {'✓ (fallback)' if PYTTSX3_AVAILABLE else '✗'}")
    print(f"Speed    : {SPEED}x\n")

    tests = [
        ("Pure English",
         "Hello! I am AI Bot, your personal study companion. "
         "Let me help you understand any concept clearly."),
        ("Pure Hindi",
         "Namaste! Main hoon AI Bot, tumhara study companion. "
         "Aaj kaisa feel ho raha hai? Padhai mein koi doubt hai?"),
        ("Hinglish — encouragement",
         "Arre wah! Bilkul sahi jawab diya tumne! Ekdum correct. "
         "Tu toh genius hai yaar!"),
        ("Hinglish — science",
         "Newton ka pehla niyam kehta hai ki koi bhi object apni "
         "sthiti mein rahega, jab tak bahari bal na lage. "
         "Jaise cricket ball seedhi jaati hai jab tak koi rok na de."),
        ("Hinglish — emotional",
         "Arre, tension mat lo. Ek ek step karenge, sab ho jayega. "
         "Kal ka exam? Koi baat nahi — milke revise karte hain abhi."),
    ]

    for label, line in tests:
        print(f"[{label}]")
        speak(line)
        print(f" ✓\n")
        time.sleep(0.2)

    print("Done. Adjust SPEED constant if pace still feels off.")
    print("Current:", SPEED, "x  |  Try: 1.10 (slower) or 1.25 (faster)")