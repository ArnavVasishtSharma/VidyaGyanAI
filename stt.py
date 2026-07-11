"""
stt.py — Speech-to-Text for AI-BOT
Uses faster-whisper (local, offline) + sounddevice for mic input.
language forced to 'en' → Whisper outputs Roman script for ALL input:
  Hindi speech    → Romanized Hindi  (not Devanagari)
  English speech  → English text
  Hinglish speech → Romanized Hinglish
Groq / Llama 3.3 70B understands all three perfectly.
"""

import io
import re
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

# ── Config ────────────────────────────────────────────────────────────────────
WHISPER_MODEL_SIZE   = "small"
SAMPLE_RATE          = 16000
CHANNELS             = 1
SILENCE_THRESHOLD    = 0.015
SILENCE_DURATION     = 1.5
MAX_DURATION         = 30
MIN_SPEECH_DURATION  = 0.3

# ── Load model once ───────────────────────────────────────────────────────────
print("[STT] Loading Whisper small model...")
_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("[STT] Whisper ready.\n")

_calibrated_threshold = SILENCE_THRESHOLD

# ── Calibration ───────────────────────────────────────────────────────────────
def calibrate():
    global _calibrated_threshold
    print("[STT] Calibrating mic — stay quiet for 1 second...")
    chunk_size = int(SAMPLE_RATE * 0.1)
    rms_values = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype="float32", blocksize=chunk_size) as stream:
        for _ in range(10):
            chunk, _ = stream.read(chunk_size)
            rms_values.append(float(np.sqrt(np.mean(chunk ** 2))))
    ambient   = float(np.mean(rms_values))
    threshold = max(ambient * 3.0, 0.012)
    _calibrated_threshold = threshold
    print(f"[STT] Ambient: {ambient:.4f} | Threshold: {threshold:.4f}\n")

# ── Recording ─────────────────────────────────────────────────────────────────
def record_until_silence(threshold: float = None) -> np.ndarray:
    if threshold is None:
        threshold = _calibrated_threshold

    print("\n[🎤 Listening... speak now]")
    chunk_size       = int(SAMPLE_RATE * 0.1)
    max_chunks       = int(MAX_DURATION / 0.1)
    silence_needed   = int(SILENCE_DURATION / 0.1)
    audio_chunks     = []
    silence_count    = 0
    speaking_started = False
    speech_chunks    = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype="float32", blocksize=chunk_size) as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            audio_chunks.append(chunk.copy())
            if rms > threshold:
                speaking_started = True
                silence_count    = 0
                speech_chunks   += 1
            elif speaking_started:
                silence_count += 1
                if silence_count >= silence_needed:
                    break

    print("[🔴 Stopped]")

    if not speaking_started:
        print("[STT] No speech detected.")
        return np.array([])

    speech_seconds = speech_chunks * 0.1
    if speech_seconds < MIN_SPEECH_DURATION:
        print(f"[STT] Too short ({speech_seconds:.1f}s) — ignoring.")
        return np.array([])

    return np.concatenate(audio_chunks, axis=0)

# ── Transcription ─────────────────────────────────────────────────────────────
def transcribe(audio: np.ndarray) -> str:
    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV")
    buf.seek(0)

    segments, info = _model.transcribe(
        buf,
        language                    = "en",   # Roman script output always
        task                        = "transcribe",
        beam_size                   = 5,
        vad_filter                  = True,
        vad_parameters              = {
            "min_silence_duration_ms": 400,
            "speech_pad_ms"          : 200,
            "threshold"              : 0.45,
        },
        no_speech_threshold         = 0.6,
        log_prob_threshold          = -0.8,
        compression_ratio_threshold = 2.4,
    )

    raw   = [seg.text.strip() for seg in segments]
    clean = [s for s in raw if re.sub(r'[^\w\s]', '', s).strip()]
    text  = " ".join(clean).strip()

    confidence = round(info.language_probability * 100, 1)
    print(f"[STT] Confidence: {confidence}% | Transcript: {text!r}")
    return text

# ── Public API ────────────────────────────────────────────────────────────────
def listen() -> str:
    audio = record_until_silence()
    if audio.size == 0:
        return ""
    return transcribe(audio)

# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== STT Standalone Test ===\n")
    calibrate()

    tests = [
        "Say: 'Newton ka 3rd law samajh nahi aaya'",
        "Say: 'Photosynthesis explain karo like I am 12'",
        "Say: 'Mera naam Arnav hai, Class 10 mein hoon'",
    ]

    for i, prompt in enumerate(tests, 1):
        print(f"Test {i}/3 — {prompt}")
        text = listen()
        print(f"{'✓ Got' if text else '✗ Nothing'}: {text!r}\n")
        if i < len(tests):
            input("Press Enter for next test...")

    print("STT test complete.")