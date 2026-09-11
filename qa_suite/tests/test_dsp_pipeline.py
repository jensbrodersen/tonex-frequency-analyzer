import subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile

def test_guitar_rig_analyzer_headless():
    # Projekt-Root korrekt über 2 Ebenen nach oben ermitteln
    project_root = Path(__file__).resolve().parents[2]
    exe_path = project_root / "build/juce_plugin/GuitarRigAnalyzer_artefacts/Release/Standalone/GuitarRigAnalyzer.exe"
    input_wav = project_root / "qa_suite/assets/test_input.wav"
    output_wav = project_root / "qa_suite/assets/test_output.wav"

    # Sicherstellen, dass die Testdatei existiert
    assert input_wav.exists(), f"Eingabedatei fehlt: {input_wav}"

    # Headless-Prozess aufrufen
    cmd = [str(exe_path.resolve()), "--process", str(input_wav.resolve()), str(output_wav.resolve())]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Debug-Ausgaben für die Konsole anzeigen
    print("\n--- C++ STDOUT ---")
    print(result.stdout)
    print("--- C++ STDERR ---")
    print(result.stderr)
    print("------------------")

    # Prüfen ob der Prozess erfolgreich war
    assert result.returncode == 0, f"CLI-Fehler (Exit Code {result.returncode}): {result.stderr}"
    assert output_wav.exists(), f"Ausgabedatei wurde nicht erstellt unter: {output_wav}"

    # Numerische DSP-Verifikation mit NumPy/SciPy
    _, input_data = wavfile.read(input_wav)
    _, output_data = wavfile.read(output_wav)

    # Prüfen auf DSP-Integrität (keine NaNs und aktive Filterung)
    assert not np.isnan(output_data).any(), "Ausgabe enthält NaN-Werte!"
    assert not np.array_equal(input_data, output_data), "Der Filter hat das Signal nicht verändert."