"""Generate original WAV cues and a quiet repeating melody; no downloads."""

from math import pi, sin
from pathlib import Path
import struct
import wave


SAMPLE_RATE = 22050
ASSETS = Path(__file__).resolve().parent / "assets"


def write_tones(path: Path, notes: list[tuple[float, float]], volume=0.2):
    """Write (frequency, duration) notes with fades to mono 16-bit PCM WAV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = bytearray()
    for frequency, duration in notes:
        count = int(SAMPLE_RATE * duration)
        for index in range(count):
            time = index / SAMPLE_RATE
            fade = min(1.0, time / 0.025, (duration - time) / 0.045)
            sample = sin(2 * pi * frequency * time) if frequency else 0
            frames.extend(struct.pack("<h", int(32767 * volume * fade * sample)))
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(SAMPLE_RATE)
        audio.writeframes(frames)


def generate_assets():
    """Create only absent files, preserving any user-supplied replacements."""
    files = {
        "sounds/click.wav": ([(660, 0.055)], 0.18),
        "sounds/correct.wav": ([(523.25, 0.12), (659.25, 0.12), (783.99, 0.23)], 0.22),
        "sounds/wrong.wav": ([(293.66, 0.16), (220, 0.24)], 0.20),
        "music/background.wav": (
            [(note, 0.4) for note in
             (261.63, 329.63, 392, 329.63, 220, 261.63, 329.63, 261.63,
              174.61, 220, 261.63, 220, 196, 246.94, 293.66, 0)], 0.12),
    }
    for relative, (notes, volume) in files.items():
        path = ASSETS / relative
        if not path.exists():
            write_tones(path, notes, volume)


if __name__ == "__main__":
    generate_assets()
    print(f"Original WAV assets ready in {ASSETS}")
