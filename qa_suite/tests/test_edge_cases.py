import subprocess
from pathlib import Path
import pytest

def find_executable():
    # Sucht die kompilierte exe im Standard-Build-Pfad des Projekts
    root_dir = Path(__file__).parent.parent.parent
    exe_path = root_dir / "build" / "juce_plugin" / "GuitarRigAnalyzer_artefacts" / "Release" / "Standalone" / "GuitarRigAnalyzer.exe"
    return exe_path

def test_cli_invalid_arguments():
    exe = find_executable()
    if not exe.exists():
        pytest.skip(f"Executable not found at {exe}, skipping CLI edge case test.")

    # Test 1: Aufruf komplett ohne Argumente oder mit ungültigem Flag
    result = subprocess.run([str(exe), "--invalid-flag"], capture_output=True, text=True)
    # Der Prozess sollte nicht einfach crashen, sondern einen nicht-zero exit code liefern oder graceful reagieren
    assert result.returncode != 0

def test_cli_missing_input_file():
    exe = find_executable()
    if not exe.exists():
        pytest.skip(f"Executable not found at {exe}, skipping missing file test.")

    # Test 2: Übergabe einer nicht existierenden Input-Datei
    result = subprocess.run([str(exe), "--process", "non_existent_input.wav", "output.wav"], capture_output=True, text=True)
    assert result.returncode != 0