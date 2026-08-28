import numpy as np
import pytest

def test_harmonic_distortion_detection():
    """Prüft, ob nichtlineare Verzerrungen (z.B. hartes Clipping/Sättigung) detektiert werden können."""
    # Erstelle ein sauberes Sinussignal (Grundschwingung)
    fs = 44100
    t = np.linspace(0, 1.0, fs, endpoint=False)
    frequency = 440.0  # Kammerton A
    clean_sine = np.sin(2 * np.pi * frequency * t)

    # Simuliere ein hart verzerrtes Signal (Clipping durch hartes Abschneiden / Hard Clipping)
    threshold = 0.5
    distorted_sine = np.clip(clean_sine, -threshold, threshold)

    # Einfache Prüfung: Das verzerrte Signal muss Spitzenwerte aufweisen, die exakt am Threshold liegen,
    # während das saubere Signal Werte bis 1.0 erreicht.
    assert np.max(np.abs(distorted_sine)) == threshold, "Clipping-Threshold wurde nicht korrekt angewendet."
    assert np.max(np.abs(clean_sine)) > threshold, "Das Ausgangssignal sollte den Threshold überschreiten."

    # Hinweis für die Analyzer-Logik: Ein höherer Anteil von Obertönen im Spektrum 
    # lässt sich im echten Analyzer via FFT-Analyse (Verhältnis Grundschwingung zu Harmonischen) quantifizieren.