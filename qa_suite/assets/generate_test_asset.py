import numpy as np
from scipy.io import wavfile
from pathlib import Path

# Pfad zum assets-Ordner innerhalb von qa_suite
assets_dir = Path("assets")
assets_dir.mkdir(exist_ok=True)

# 1 Sekunde Sinuston (440 Hz) bei 44.1 kHz erzeugen
sample_rate = 44100
t = np.linspace(0, 1.0, sample_rate, endpoint=False)
audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

# Als WAV speichern
wavfile.write(assets_dir / "test_input.wav", sample_rate, audio_data.astype(np.float32))
print("assets/test_input.wav erfolgreich generiert!")