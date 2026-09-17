import subprocess
from pathlib import Path
import numpy as np
import scipy.io.wavfile as wav
import pytest

def test_dsp_extreme_noise_stress():
    root_dir = Path(__file__).parent.parent.parent
    exe = root_dir / "build" / "juce_plugin" / "GuitarRigAnalyzer_artefacts" / "Release" / "Standalone" / "GuitarRigAnalyzer.exe"
    
    if not exe.exists():
        pytest.skip("GuitarRigAnalyzer.exe not built yet, skipping stress test.")

    sample_rate = 44100
    duration_sec = 1.0
    num_samples = int(sample_rate * duration_sec)

    # Erzeuge extremes Rauschen mit hoher Amplitude
    np.random.seed(42)
    noise_input = np.random.uniform(-1.5, 1.5, num_samples).astype(np.float32)

    input_path = root_dir / "qa_suite" / "assets" / "stress_input.wav"
    output_path = root_dir / "qa_suite" / "assets" / "stress_output.wav"

    wav.write(input_path, sample_rate, noise_input)

    try:
        # Headless Verarbeitung direkt über den CLI-Aufruf der .exe
        result = subprocess.run(
            [str(exe), "--process", str(input_path), str(output_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Process failed with stderr: {result.stderr}"

        # Prüfen, ob Output generiert wurde und keine NaNs/Infs enthält
        assert output_path.exists(), "Output audio file was not generated."
        sr_out, data_out = wav.read(output_path)
        assert not np.isnan(data_out).any(), "DSP output contains NaN values!"
        assert not np.isinf(data_out).any(), "DSP output contains Inf values!"
    finally:
        # Aufräumen
        if input_path.exists(): input_path.unlink()
        if output_path.exists(): output_path.unlink()