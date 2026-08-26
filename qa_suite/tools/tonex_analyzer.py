import argparse
import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
import numpy as np
import scipy.signal as signal
import sounddevice as sd

# --- STANDARD-KONFIGURATION ---
SAMPLE_RATE = 44100
SWEEP_DURATION = 1.5
GUITAR_DURATION = 3.0
FREQ_START = 20.0
FREQ_STOP = 20000.0

# Standard-Geräte-IDs (Scarlett)
DEFAULT_INPUT_ID = 10   # Analogue 1 + 2
DEFAULT_OUTPUT_ID = 12  # Lautsprecher / Line Out


class ToneXAnalyzerEngine:

    def __init__(
        self,
        sample_rate=SAMPLE_RATE,
        sweep_duration=SWEEP_DURATION,
        input_id=DEFAULT_INPUT_ID,
        output_id=DEFAULT_OUTPUT_ID,
        channel=1,
    ):
        self.sr = sample_rate
        self.duration = sweep_duration
        self.input_id = input_id
        self.output_id = output_id
        self.channel = channel
        self.num_samples = int(self.sr * self.duration)

        # 1. Logarithmischen Sine-Sweep für Closed Loop generieren
        t = np.linspace(0, self.duration, self.num_samples, endpoint=False)
        self.sweep = signal.chirp(
            t, f0=FREQ_START, t1=self.duration, f1=FREQ_STOP, method='logarithmic'
        )
        window = signal.windows.tukey(len(self.sweep), alpha=0.05)
        self.sweep = self.sweep * window * 0.7  # Pegel leicht absenken gegen Clipping

    def measure_sweep(self):
        """Führt eine präzise Log-Sweep Messung mit logarithmischer Glättung durch."""
        import scipy.signal as signal

        dev_out_info = sd.query_devices(self.output_id, 'output')
        out_channels = int(dev_out_info['max_output_channels'])
        
        dev_in_info = sd.query_devices(self.input_id, 'input')
        in_channels = int(dev_in_info['max_input_channels'])

        out_signal = np.zeros((len(self.sweep), out_channels), dtype=np.float32)
        out_signal[:, 0] = self.sweep

        recording = sd.playrec(
            out_signal,
            samplerate=self.sr,
            channels=in_channels,
            device=(self.input_id, self.output_id),
            dtype='float32',
            blocking=True,
        )

        max_rec = np.max(np.abs(recording))
        print(f"[Signal Check] Sent Peak: {np.max(np.abs(self.sweep)):.4f} | Rec Peak: {max_rec:.6f}")

        in_ch_idx = min(self.channel - 1, in_channels - 1)
        rec_signal = recording[:, in_ch_idx].flatten()

        # 1. Inverses Filter für Log-Sweep
        inv_sweep = self.sweep[::-1]
        num_samples = len(self.sweep)
        time_axis = np.linspace(0, 1, num_samples)
        envelope = 10 ** ((-6 * np.log2(20000 / 20) * time_axis) / 20)
        inv_filter = inv_sweep * envelope

        # 2. Impulsantwort berechnen
        ir = signal.fftconvolve(rec_signal, inv_filter, mode='full')
        peak_idx = np.argmax(np.abs(ir))
        delay = max(0, peak_idx - len(self.sweep))

        # 3. Fensterung um den Hauptpeak
        win_size = 4096
        start_idx = max(0, peak_idx - 16)
        end_idx = min(len(ir), start_idx + win_size)
        
        ir_windowed = ir[start_idx:end_idx]
        if len(ir_windowed) < win_size:
            ir_windowed = np.pad(ir_windowed, (0, win_size - len(ir_windowed)))

        ir_windowed = ir_windowed * np.hanning(len(ir_windowed))

        # 4. Frequenzgang via FFT
        fft_ir = np.fft.rfft(ir_windowed, n=win_size)
        magnitude_db = 20 * np.log10(np.abs(fft_ir) + 1e-6)
        freqs = np.fft.rfftfreq(win_size, 1 / self.sr)

        # Nur hörbaren Bereich betrachten
        valid_mask = (freqs >= 20) & (freqs <= 20000)
        freqs = freqs[valid_mask]
        magnitude_db = magnitude_db[valid_mask]

        # 5. Logarithmische Glättung (1/6 Oktave) - eliminiert Kammfilter und Wellen im Hochton perfekt!
        from scipy.ndimage import uniform_filter1d
        # Da die Frequenzen logarithmisch skaliert sind, machen wir ein gleitendes Fenster,
        # das sich anpasst oder nutzen einen angepassten Savitzky-Golay auf die Log-Kurve:
        magnitude_db = signal.savgol_filter(magnitude_db, window_length=51, polyorder=3)

        # 6. Normierung auf 0 dB Peak
        if max_rec > 0.005:
            magnitude_db -= np.max(magnitude_db)

        return freqs, magnitude_db, delay
    

    def measure_guitar(self, duration=GUITAR_DURATION, normalize=True):
        """Nimmt direktes Gitarrenspiel auf und berechnet das gemittelte Spektrum (Welch PSD)."""
        # Dynamische Abfrage der vom Interface unterstützten Kanalanzahl
        dev_info = sd.query_devices(self.input_id, 'input')
        supported_channels = int(dev_info['max_input_channels'])

        recording = sd.rec(
            int(duration * self.sr),
            samplerate=self.sr,
            channels=supported_channels,
            device=self.input_id,
            blocking=True,
        )

        # Den gewählten Kanal isolieren (channel - 1 wegen 0-basierter Indizierung)
        channel_idx = min(self.channel - 1, supported_channels - 1)
        recorded_signal = recording[:, channel_idx]

        # Welch-Methode für fülliges, glattes Gitarrenspektrum
        freqs, psd = signal.welch(
            recorded_signal,
            fs=self.sr,
            window='hann',
            nperseg=8192,
            scaling='spectrum',
        )

        magnitude_db = 10 * np.log10(psd + 1e-12)

        if normalize:
            max_val = np.max(magnitude_db)
            if max_val > -100:  # Nur normieren, wenn echtes Signal anliegt
                magnitude_db -= max_val

        return freqs, magnitude_db


def find_focusrite_devices(user_input_id=None, user_output_id=None):
    devices = sd.query_devices()

    # 1. Geräteliste ausgeben
    print("\n" + "=" * 60)
    print("AVAILABLE AUDIO DEVICES".center(60))
    print("=" * 60)
    for idx, dev in enumerate(devices):
        host_api_name = sd.query_hostapis(dev['hostapi'])['name']
        print(f"[{idx:2d}] {dev['name']} ({host_api_name}) | In: {dev['max_input_channels']} ch, Out: {dev['max_output_channels']} ch")
    print("=" * 60)

    # Wenn der User explizit IDs per CLI vorgibt, nutze diese!
    input_id = user_input_id
    output_id = user_output_id

    # Falls keine Vorgabe da ist: Automatisch per WASAPI suchen
    if input_id is None or output_id is None:
        for idx, dev in enumerate(devices):
            name = dev['name'].lower()
            host_api = sd.query_hostapis(dev['hostapi'])['name'].lower()
            if ('focusrite' in name or 'scarlett' in name) and 'wasapi' in host_api:
                if dev['max_input_channels'] > 0 and input_id is None:
                    input_id = idx
                if dev['max_output_channels'] > 0 and output_id is None:
                    output_id = idx

    # Debug-Output der final genutzten Geräte
    in_dev = devices[input_id]
    out_dev = devices[output_id]
    in_api = sd.query_hostapis(in_dev['hostapi'])['name']
    out_api = sd.query_hostapis(out_dev['hostapi'])['name']

    print("DEBUG: SELECTED AUDIO DEVICES".center(60))
    print(f"  -> INPUT  : ID {input_id:2d} | '{in_dev['name']}' ({in_api})")
    print(f"  -> OUTPUT : ID {output_id:2d} | '{out_dev['name']}' ({out_api})")
    print("=" * 60 + "\n")

    return input_id, output_id


def run_app(mode, input_id, output_id, channel, normalize):
    engine = ToneXAnalyzerEngine(
        input_id=input_id, output_id=output_id, channel=channel
    )
    captured_data = []

    fig, ax = plt.subplots(figsize=(10, 6))
    # Platz unten schaffen für Button und das neue Textfeld
    plt.subplots_adjust(bottom=0.25)

    ax.set_xscale('log')
    ax.set_xlim(20, 20000)
    ax.set_ylim(-100, 10)

    title_mode = (
        'Closed-Loop Sweep' if mode == 'sweep' else 'Live-Guitar Recording'
    )
    ax.set_title(
        f'ToneX Analyzer [{title_mode}] (Input: {input_id}, Output: {output_id})'
    )
    ax.set_xlabel('Frequenz (Hz)')
    ax.set_ylabel('Amplitude (dB / Normalized)')
    ax.grid(True, which='both', ls='--', alpha=0.6)

    # Variable zum Zwischenspeichern des eingetippten Preset-Namens
    current_custom_label = ['']

    def text_submit_callback(text):
        current_custom_label[0] = text.strip()

    def capture_callback(event):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        user_text = current_custom_label[0]

        if mode == 'sweep':
            print('\n[...] Sende Sweep durch ToneX und nehme auf...')
            freqs, mag_db, delay = engine.measure_sweep()
            
            # Label-Logik: Nutze Custom-Text falls eingegeben, sonst Standard
            if user_text:
                label_name = f'{user_text} (Delay: {delay} Smpl)'
            else:
                label_name = f'Sweep {timestamp} (Delay: {delay} Smpl)'
        else:
            btn_capture.label.set_text('Nimmt auf... JETZT SPIELEN!')
            fig.canvas.draw_idle()
            plt.pause(0.1)

            freqs, mag_db = engine.measure_guitar(normalize=normalize)
            
            if user_text:
                label_name = f'{user_text} (Guitar Take)'
            else:
                label_name = f'Guitar Take {timestamp}'
                
            btn_capture.label.set_text('Capture Guitar (3s)')

        captured_data.append((label_name, freqs, mag_db))
        
        # Signal plotten
        ax.plot(freqs, mag_db, label=label_name, alpha=0.85)

        # Dynamisches Y-Limit anpassen
        valid_mags = mag_db[np.isfinite(mag_db)]
        if len(valid_mags) > 0:
            min_val = np.min(valid_mags)
            max_val = np.max(valid_mags)
            ax.set_ylim(max(min_val - 5, -120), max_val + 5)

        ax.legend(loc='lower left')
        
        # Canvas neu zeichnen
        fig.canvas.draw()
        fig.canvas.flush_events()
        
        print(f'[OK] {label_name} erfolgreich geplottet.')

    def export_html_callback(event):
        if not captured_data:
            print('[!] Keine Captures vorhanden zum Exportieren.')
            return

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>ToneX QA Report ({mode.upper()})</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; background: #121212; color: #eee; padding: 20px; }}
        h1 {{ color: #00bcd4; }}
        #chart {{ width: 100%; height: 600px; }}
    </style>
</head>
<body>
    <h1>ToneX Preset Frequenzanalyse ({title_mode})</h1>
    <p>Erstellt am: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <div id="chart"></div>
    <script>
        var data = [
"""
        for label, freqs, mag_db in captured_data:
            step = 10
            html_content += f"""       {{
            x: {freqs[::step].tolist()},
            y: {mag_db[::step].tolist()},
            type: 'scatter',
            mode: 'lines',
            name: '{label}'
        }},
"""
        html_content += """    ];
        var layout = {
            title: 'Frequenzgang-Vergleich',
            xaxis: { type: 'log', title: 'Frequenz (Hz)', range: [Math.log10(20), Math.log10(20000)] },
            yaxis: { title: 'Amplitude (dB)' },
            paper_bgcolor: '#1e1e1e',
            plot_bgcolor: '#1e1e1e',
            font: { color: '#ccc' }
        };
        Plotly.newPlot('chart', data, layout);
    </script>
</body>
</html>
"""
        filepath = os.path.join(os.path.dirname(__file__), 'tonex_report.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f'\n[SUCCESS] HTML-Report gespeichert unter: {filepath}')

    # --- UI Layout Ergänzung ---
    # 1. Textfeld für Preset-Namen (links unten)
    ax_box = plt.axes([0.15, 0.04, 0.25, 0.05])
    text_box = TextBox(ax_box, 'Preset Name: ', initial='')
    text_box.on_submit(text_submit_callback)
    text_box.text_disp.set_fontsize(10)

    # 2. Sweep/Capture Button (mittig)
    ax_btn_sweep = plt.axes([0.43, 0.04, 0.25, 0.075])
    btn_label = 'Sweep & Capture' if mode == 'sweep' else 'Capture Guitar (3s)'
    btn_capture = Button(ax_btn_sweep, btn_label)
    btn_capture.on_clicked(capture_callback)

    # 3. Export HTML Button (rechts)
    ax_btn_export = plt.axes([0.70, 0.04, 0.18, 0.075])
    btn_export = Button(ax_btn_export, 'Export HTML')
    btn_export.on_clicked(export_html_callback)

    print(f'--- ToneX Analyzer gestartet im Modus: [{mode.upper()}] ---')
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='ToneX Rig Analyzer (Sweep oder Gitarren-Input)'
    )
    parser.add_argument(
        '--mode',
        choices=['sweep', 'guitar'],
        default='guitar',
        help="Messmodus: 'sweep' (Closed Loop Kabel) oder 'guitar' (Gitarrenspiel)",
    )
    parser.add_argument(
        '--input',
        type=int,
        default=None,
        help='Sounddevice Input ID (Standard: Auto-Detect Focusrite)',
    )
    parser.add_argument(
        '--output',
        type=int,
        default=None,
        help='Sounddevice Output ID (Standard: Auto-Detect Focusrite)',
    )
    parser.add_argument(
        '--channel',
        type=int,
        default=1,
        help='Eingangskanal des Interfaces (Default: 1)',
    )
    parser.add_argument(
        '--no-norm',
        action='store_true',
        help='Deaktiviert die Peak-Normierung im Gitarren-Modus',
    )

    args = parser.parse_args()

    # Auto-Detect durchführen, falls keine IDs übergeben wurden
    auto_in, auto_out = find_focusrite_devices(args.input, args.output)
    input_id = args.input if args.input is not None else auto_in
    output_id = args.output if args.output is not None else auto_out

    print(f"[Audio Devices] Verwendet Input ID {input_id} ({sd.query_devices(input_id)['name']})")
    print(f"[Audio Devices] Verwendet Output ID {output_id} ({sd.query_devices(output_id)['name']})")

    run_app(
        mode=args.mode,
        input_id=input_id,
        output_id=output_id,
        channel=args.channel,
        normalize=not args.no_norm,
    )