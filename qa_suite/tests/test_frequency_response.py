import numpy as np
import pytest

def test_peak_clipping_detection():
    """Prüft, ob harte 0-dB-Spitzen (Clipping) korrekt erkannt werden."""
    frequencies = np.linspace(100, 20000, 1000)
    amplitude_response = -5.0 + np.sin(frequencies / 1000)
    amplitude_response[frequencies > 10000] = 0.0  # Flat-top Clipping bei 0 dB

    has_clipping = np.any(amplitude_response >= 0.0)
    max_amplitude = np.max(amplitude_response)

    # Korrigiert: Nutze direkt den Boolean-Check statt 'is True'
    assert has_clipping, "Clipping im Hochtonbereich wurde nicht erkannt!"
    assert max_amplitude == 0.0, f"Maximalamplitude sollte exakt 0.0 dB sein, ist aber {max_amplitude}"

def test_linear_frequency_response():
    """Prüft eine saubere Kurve auf Integrität ohne abrupte Kammfilter-Sprünge."""
    f = np.linspace(20, 20000, 500)
    response = -20 - 10 * np.log10(f / 100)
    
    derivatives = np.diff(response)
    assert np.max(np.abs(derivatives)) < 5.0, "Unerwartet abrupte Sprünge im Frequenzgang."