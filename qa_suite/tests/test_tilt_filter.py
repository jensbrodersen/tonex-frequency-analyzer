import subprocess
import os
import numpy as np
from scipy.io import wavfile

def get_bin_path():
    """Ermittelt den Pfad zur kompilierten GuitarRigAnalyzer.exe im Release-Ordner."""
    # Pfad relativ zur qa_suite/tests/ Struktur angepasst an das Projekt-Root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    exe_path = os.path.join(
        base_dir, 
        "build", 
        "juce_plugin", 
        "GuitarRigAnalyzer_artefacts", 
        "Release", 
        "Standalone", 
        "GuitarRigAnalyzer.exe"
    )
    return exe_path

def generate_test_noise(filename, duration_sec=1.0, samplerate=44100):
    """Erzeugt ein weisses Rauschen als Test-Audiodatei."""
    num_samples = int(duration_sec * samplerate)
    # Weißes Rauschen enthält alle Frequenzen gleichmäßig
    noise = np.random.uniform(-0.5, 0.5, num_samples).astype(np.float32)
    wavfile.write(filename, samplerate, noise)

def measure_high_low_ratio(wav_path):
    """Misst das Energieverhältnis von Höhen zu Tiefen via FFT."""
    sr, data = wavfile.read(wav_path)
    if len(data.shape) > 1:
        data = data[:, 0]  # Auf Mono reduzieren
        
    # FFT durchführen
    fft_vals = np.fft.rfft(data)
    fft_freqs = np.fft.rfftfreq(len(data), 1/sr)
    
    fft_mag = np.abs(fft_vals)
    
    # Frequenzbereiche definieren
    low_mask = (fft_freqs >= 200) & (fft_freqs < 1000)
    high_mask = (fft_freqs >= 5000) & (fft_freqs < 15000)
    
    low_energy = np.mean(fft_mag[low_mask]) if np.any(low_mask) else 1.0
    high_energy = np.mean(fft_mag[high_mask]) if np.any(high_mask) else 1.0
    
    return high_energy / low_energy

def test_tilt_filter_cli():
    exe_path = get_bin_path()
    assert os.path.exists(exe_path), f"Executable nicht gefunden unter: {exe_path}. Wurde CMake Build ausgeführt?"

    input_file = "test_input_tilt.wav"
    output_flat = "test_output_flat.wav"
    output_bright = "test_output_bright.wav"

    try:
        # Test-Rauschen generieren
        generate_test_noise(input_file)

        # 1. Durchlauf: Neutraler Tilt (--tilt 0.0)
        cmd_flat = [exe_path, "--process", input_file, output_flat, "--tilt", "0.0"]
        res_flat = subprocess.run(cmd_flat, capture_output=True, text=True, timeout=10)
        assert res_flat.returncode == 0, f"CLI Prozess fehlgeschlagen (Flat): {res_flat.stderr}"

        # 2. Durchlauf: Hellerer Tilt (--tilt 0.9 / Höhenanhebung)
        cmd_bright = [exe_path, "--process", input_file, output_bright, "--tilt", "0.9"]
        res_bright = subprocess.run(cmd_bright, capture_output=True, text=True, timeout=10)
        assert res_bright.returncode == 0, f"CLI Prozess fehlgeschlagen (Bright): {res_bright.stderr}"

        # Analysieren und Vergleichen
        ratio_flat = measure_high_low_ratio(output_flat)
        ratio_bright = measure_high_low_ratio(output_bright)

        # Das Höhen/Tiefen-Verhältnis beim hellen Tilt muss höher sein als beim neutralen Tilt
        assert ratio_bright > ratio_flat, (
            f"Tilt-Filter zeigt nicht die erwartete Höhenanhebung! "
            f"Flat Ratio: {ratio_flat:.4f}, Bright Ratio: {ratio_bright:.4f}"
        )

    finally:
        # Cleanup temporäre Dateien
        for f in [input_file, output_flat, output_bright]:
            if os.path.exists(f):
                os.remove(f)