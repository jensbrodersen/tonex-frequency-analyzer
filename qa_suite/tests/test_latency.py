import numpy as np
import pytest
from scipy.signal import correlate

def test_latency_estimation():
    """Prüft, ob die Latenz (Sample-Verzögerung) via Kreuzkorrelation korrekt berechnet wird."""
    # Erstelle ein synthetisches Testsignal (z.B. einen kurzen Impuls oder Rauschen)
    np.random.seed(42)
    reference_signal = np.random.randn(44100)  # 1 Sekunde Rauschen
    
    # Definiere eine bekannte Testlatenz von exakt 150 Samples
    true_delay = 150
    delayed_signal = np.pad(reference_signal, (true_delay, 0), mode='constant')[:-true_delay]

    # Kreuzkorrelation zur Bestimmung des Delays (analog zur Implementierung im Analyzer)
    cross_corr = correlate(delayed_signal, reference_signal, mode='full')
    lag = np.argmax(cross_corr) - (len(reference_signal) - 1)

    assert lag == true_delay, f"Erwartete Latenz von {true_delay} Samples, berechnet wurden aber {lag} Samples."