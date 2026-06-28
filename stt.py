"""
stt.py — Speech-to-Text for AI-BOT
Uses faster-whisper (local, offline) + sounddevice for mic input.
Handles Hindi, English, and Hinglish out of the box.
"""

import io
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

# ── Model config ──────────────────────────────────────────────────────────────
WHISPER_MODEL_SIZE  = "small"
SAMPLE_RATE         = 16000
CHANNELS            = 1
SILENCE_THRESHOLD   = 0.015   # RMS below this = silence (raised from 0.01)
SILENCE_DURATION    = 1.5     # Seconds of quiet before stopping
MAX_DURATION        = 30      # Hard cap
MIN_SPEECH_DURATION = 0.3     # Ignore recordings shorter than this (seconds)

# ── Load model once ───────────────────────────────────────────────────────────
print("[STT] Loading Whisper model...")
_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("[STT] Whisper ready.\n")

# ── Mic calibration ───────────────────────────────────────────────────────────
def calibrate_silence(duration: float = 1.0) -> float:
    """
    Sample ambient noise for 1 second and return a dynamic threshold.
    Call once at startup so the threshold adapts to the room.
    """
    print("[STT] Calibrating mic — stay quiet for 1 second...")
    chunk_size = int(SAMPLE_RATE * 0.1)
    chunks = int(duration / 0.1)
    rms_values = []

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype="float32", blocksize=chunk_size) as stream:
        for _ in range(chunks):
            chunk, _ = stream.read(chunk_size)
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            rms_values.append(rms)

    ambient = float(np.mean(rms_values))
    # Set threshold to 3x ambient noise level — enough headroom for speech
    threshold = max(ambient * 3.0, 0.012)
    print(f"[STT] Ambient noise: {ambient:.4f} | Threshold set: {threshold:.4f}")
    return threshold

# ── Recording ─────────────────────────────────────────────────────────────────
def record_until_silence(threshold: float = SILENCE_THRESHOLD) -> np.ndarray:
    """
    Record from mic, stop automatically after silence.
    Returns numpy audio array, or empty array if nothing captured.
    """
    print("\n[🎤 Listening... speak now]")

    chunk_size        = int(SAMPLE_RATE * 0.1)   # 100ms chunks
    max_chunks        = int(MAX_DURATION / 0.1)
    silence_needed    = int(SILENCE_DURATION / 0.1)

    audio_chunks      = []
    silence_count     = 0
    speaking_started  = False
    speech_chunks     = 0

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
        print("[STT] No speech detected above threshold.")
        return np.array([])

    audio = np.concatenate(audio_chunks, axis=0)

    # Reject clips that are too short to be real speech
    speech_seconds = speech_chunks * 0.1
    if speech_seconds < MIN_SPEECH_DURATION:
        print(f"[STT] Too short ({speech_seconds:.1f}s) — ignoring.")
        return np.array([])

    return audio

# ── Transcription ─────────────────────────────────────────────────────────────
def transcribe(audio: np.ndarray) -> str:
    """Transcribe audio numpy array → text via faster-whisper."""
    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV")
    buf.seek(0)

    segments, info = _model.transcribe(
        buf,
        language        = None,       # Auto-detect Hindi/English/Hinglish
        task            = "transcribe",
        beam_size       = 5,
        vad_filter      = True,
        vad_parameters  = {
            "min_silence_duration_ms": 400,
            "speech_pad_ms": 200,
            "threshold": 0.5,
        },
        no_speech_threshold     = 0.6,   # Discard segments that are likely silence
        log_prob_threshold      = -0.8,  # Discard low-confidence segments
        compression_ratio_threshold = 2.4,
    )

    # Filter out hallucinated punctuation-only transcripts like ', , ,'
    raw_segments = [seg.text.strip() for seg in segments]
    clean_segments = []
    for seg in raw_segments:
        # Skip if segment is only punctuation/spaces/commas
        if re.sub(r'[^\w\s]', '', seg).strip():
            clean_segments.append(seg)

    text = " ".join(clean_segments).strip()

    lang       = info.language
    confidence = round(info.language_probability * 100, 1)
    print(f"[STT] Language: {lang} ({confidence}%) | Transcript: {text!r}")

    return text

# ── Import re for filtering ───────────────────────────────────────────────────
import re

# ── Combined listen pipeline ──────────────────────────────────────────────────
_calibrated_threshold = SILENCE_THRESHOLD   # Updated after calibrate()

def calibrate():
    """Run once at startup to set dynamic silence threshold."""
    global _calibrated_threshold
    _calibrated_threshold = calibrate_silence()

def listen() -> str:
    """Full pipeline: mic → audio → whisper → clean text."""
    audio = record_until_silence(threshold=_calibrated_threshold)
    if audio.size == 0:
        return ""
    text = transcribe(audio)
    return text

# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== STT Standalone Test ===")
    print("Tests mic calibration + transcription in Hindi/English/Hinglish.\n")

    calibrate()
    print()

    test_prompts = [
        "Say: 'Newton ka 3rd law samajh nahi aaya'",
        "Say: 'Photosynthesis explain karo like I am 12'",
        "Say: 'Mera naam Arnav hai, Class 10 mein hoon'",
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nTest {i}/3 — {prompt}")
        text = listen()
        if text:
            print(f"✓ Got: {text!r}")
        else:
            print("✗ Nothing detected")

        if i < len(test_prompts):
            input("Press Enter for next test...")

    print("\nSTT test complete.")