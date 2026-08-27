import argparse
import datetime
import os
import yaml
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
import numpy as np
import scipy.signal as signal
import sounddevice as sd

# --- KONFIGURATION LADEN ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

def load_config(path=CONFIG_PATH):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        print(f"[Warnung] Config-Datei '{path}' nicht gefunden. Verwende Standardwerte.")
        return {
            'audio': {
                'sample_rate': 44100,
                'sweep_duration': 1.5,
                'guitar_duration': 3.0,
                'channel': 1,
                'default_input_id': 10,
                'default_output_id': 12
            },
            'dsp': {
                'freq_start': 20.0,
                'freq_stop_generation': 40000.0,
                'freq_stop_analysis': 20000.0,
                'target_fft_size': 32768,
                'savgol_window': 51,
                'savgol_polyorder': 3,
                'tukey_alpha': 0.3
            }
        }

CONFIG = load_config()

# Werte aus Config extrahieren
SAMPLE_RATE = CONFIG['audio']['sample_rate']
SWEEP_DURATION = CONFIG['audio']['sweep_duration']
GUITAR_DURATION = CONFIG['audio']['guitar_duration']
DEFAULT_INPUT_ID = CONFIG['audio']['default_input_id']
DEFAULT_OUTPUT_ID = CONFIG['audio']['default_output_id']
DEFAULT_CHANNEL = CONFIG['audio']['channel']

FREQ_START = CONFIG['dsp']['freq_start']
FREQ_STOP_GENERATION = CONFIG['dsp']['freq_stop_generation']
FREQ_STOP_ANALYSIS = CONFIG['dsp']['freq_stop_analysis']
TARGET_FFT_SIZE = CONFIG['dsp']['target_fft_size']
SAVGOL_WINDOW = CONFIG['dsp']['savgol_window']
SAVGOL_POLYORDER = CONFIG['dsp']['savgol_polyorder']
TUKEY_ALPHA = CONFIG['dsp']['tukey_alpha']


class ToneXAnalyzerEngine:

    def __init__(
        self,
        sample_rate=SAMPLE_RATE,
        sweep_duration=SWEEP_DURATION,
        input_id=DEFAULT_INPUT_ID,
        output_id=DEFAULT_OUTPUT_ID,
        channel=DEFAULT_CHANNEL,
    ):
        self.sr = sample_rate
        self.duration = sweep_duration
        self.input_id = input_id
        self.output_id = output_id
        self.channel = channel
        self.num_samples = int(self.sr * self.duration)

        # Logarithmischen Sine-Sweep für Closed Loop generieren (bis 40 kHz)
        t = np.linspace(0, self.duration, self.num_samples, endpoint=False)
        self.sweep = signal.chirp(
            t, f0=FREQ_START, t1=self.duration, f1=FREQ_STOP_GENERATION, method='logarithmic'
        )
        window = signal.windows.tukey(len(self.sweep), alpha=0.05)
        self.sweep = self.sweep * window * 0.7  # Pegel leicht absenken gegen Clipping

    def measure_sweep(self):
        """Führt eine präzise Log-Sweep Messung mit logarithmischer Glättung durch."""
        dev_out_info = sd.query_devices(self.output_id, 'output')
        out_channels = int(dev_out_info['max_output_channels'])
        
        dev_in_info = sd.query_devices(self.input_id, 'input')
        in_channels = int(dev_in_info['max_input_channels'])

        out_signal = np.zeros((len(self.sweep), out_channels), dtype=np.float32)
        out_signal[:, 0] = self.sweep

        # Exklusiven WASAPI-Modus versuchen, um Windows-Filter zu umgehen
        try:
            extra_settings = sd.WasapiSettings(exclusive=True)
            print("[Audio Engine] Versuche WASAPI Exclusive Mode...")
            
            recording = sd.playrec(
                out_signal,
                samplerate=self.sr,
                channels=in_channels,
                device=(self.input_id, self.output_id),
                dtype='float32',
                blocking=True,
                extra_settings=extra_settings,
            )
            print("[Audio Engine] -> WASAPI Exclusive Mode erfolgreich gestartet!")
            
        except Exception as e:
            print(f"[Audio Engine] [!] Exclusive Mode fehlgeschlagen ({e}). Fallback auf Shared Mode...")
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

        # 1. Korrektes Farina-Inversfilter basierend auf dem 40kHz-Sweep
        inv_sweep = self.sweep[::-1]
        t_inv = np.linspace(0, 1, len(inv_sweep))
        rate = np.log(FREQ_STOP_GENERATION / FREQ_START)
        envelope = np.exp(-t_inv * rate)
        inv_filter = inv_sweep * envelope
        inv_filter /= np.max(np.abs(inv_filter))

        # 2. Impulsantwort berechnen
        ir = signal.fftconvolve(rec_signal, inv_filter, mode='full')
        peak_idx = np.argmax(np.abs(ir))
        delay = max(0, peak_idx - len(self.sweep))

        # 3. Analysefenster um den Hauptpeak
        half_win = TARGET_FFT_SIZE // 2

        start_idx = peak_idx - half_win
        end_idx = peak_idx + half_win

        if start_idx < 0 or end_idx > len(ir):
            ir_windowed = np.zeros(TARGET_FFT_SIZE)
            src_start = max(0, start_idx)
            src_end = min(len(ir), end_idx)
            dst_start = src_start - start_idx
            ir_windowed[dst_start:dst_start + (src_end - src_start)] = ir[src_start:src_end]
        else:
            ir_windowed = ir[start_idx:end_idx]

        # Sanftes Tukey-Fenster aus Config
        ir_windowed = ir_windowed * signal.windows.tukey(len(ir_windowed), alpha=TUKEY_ALPHA)

        # 4. Hochpräzise FFT und strikter Schnitt bei FREQ_STOP_ANALYSIS
        fft_ir = np.fft.rfft(ir_windowed, n=TARGET_FFT_SIZE)
        magnitude_db = 20 * np.log10(np.abs(fft_ir) + 1e-6)
        freqs = np.fft.rfftfreq(TARGET_FFT_SIZE, 1 / self.sr)

        valid_mask = (freqs >= FREQ_START) & (freqs <= FREQ_STOP_ANALYSIS)
        freqs = freqs[valid_mask]
        magnitude_db = magnitude_db[valid_mask]

        # 5. Logarithmische Glättung (Savitzky-Golay)
        magnitude_db = signal.savgol_filter(magnitude_db, window_length=SAVGOL_WINDOW, polyorder=SAVGOL_POLYORDER)

        # 6. Normierung auf 0 dB Peak
        if max_rec > 0.005:
            magnitude_db -= np.max(magnitude_db)

        return freqs, magnitude_db, delay
    

    def measure_guitar(self, duration=GUITAR_DURATION, normalize=True):
        """Nimmt direktes Gitarrenspiel auf und berechnet das gemittelte Spektrum (Welch PSD)."""
        dev_info = sd.query_devices(self.input_id, 'input')
        supported_channels = int(dev_info['max_input_channels'])

        recording = sd.rec(
            int(duration * self.sr),
            samplerate=self.sr,
            channels=supported_channels,
            device=self.input_id,
            blocking=True,
        )

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
            if max_val > -100:  
                magnitude_db -= max_val

        return freqs, magnitude_db


def find_focusrite_devices(user_input_id=None, user_output_id=None):
    devices = sd.query_devices()

    print("\n" + "=" * 60)
    print("AVAILABLE HOST APIS".center(60))
    print("=" * 60)
    for api_idx, api in enumerate(sd.query_hostapis()):
        print(f"[{api_idx}] {api['name']} (Default Output Devices: {api.get('default_output_device', 'N/A')})")
    print("=" * 60)

    print("\n" + "=" * 60)
    print("AVAILABLE AUDIO DEVICES".center(60))
    print("=" * 60)
    for idx, dev in enumerate(devices):
        host_api_name = sd.query_hostapis(dev['hostapi'])['name']
        print(f"[{idx:2d}] {dev['name']} ({host_api_name}) | In: {dev['max_input_channels']} ch, Out: {dev['max_output_channels']} ch")
    print("=" * 60)

    input_id = user_input_id
    output_id = user_output_id

    if input_id is None or output_id is None:
        for idx, dev in enumerate(devices):
            name = dev['name'].lower()
            host_api = sd.query_hostapis(dev['hostapi'])['name'].lower()
            if ('focusrite' in name or 'scarlett' in name) and 'asio' in host_api:
                if dev['max_input_channels'] > 0 and input_id is None:
                    input_id = idx
                if dev['max_output_channels'] > 0 and output_id is None:
                    output_id = idx

        if input_id is None or output_id is None:
            for idx, dev in enumerate(devices):
                name = dev['name'].lower()
                host_api = sd.query_hostapis(dev['hostapi'])['name'].lower()
                if ('focusrite' in name or 'scarlett' in name) and 'wasapi' in host_api:
                    if dev['max_input_channels'] > 0 and input_id is None:
                        input_id = idx
                    if dev['max_output_channels'] > 0 and output_id is None:
                        output_id = idx

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
    plt.subplots_adjust(bottom=0.25)

    ax.set_xscale('log')
    ax.set_xlim(20, 20000)
    ax.set_ylim(-80, 10)

    title_mode = (
        'Closed-Loop Sweep' if mode == 'sweep' else 'Live-Guitar Recording'
    )
    ax.set_title(
        f'ToneX Analyzer [{title_mode}] (Input: {input_id}, Output: {output_id})'
    )
    ax.set_xlabel('Frequenz (Hz)')
    ax.set_ylabel('Amplitude (dB / Normalized)')
    ax.grid(True, which='both', ls='--', alpha=0.6)

    current_custom_label = ['']

    def text_submit_callback(text):
        current_custom_label[0] = text.strip()

    def capture_callback(event):
        # 1. Aktuellen Zoom/Ansichts-Bereich des Users zwischenspeichern, 
        # damit manuelle Zooms beim nächsten Capture nicht verloren gehen!
        current_xlim = ax.get_xlim()
        current_ylim = ax.get_ylim()

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        user_text = current_custom_label[0]

        if mode == 'sweep':
            print('\n[...] Sende Sweep durch ToneX und nehme auf...')
            freqs, mag_db, delay = engine.measure_sweep()
            
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
                
            btn_capture.label.set_text(f'Capture Guitar ({GUITAR_DURATION}s)')

        captured_data.append((label_name, freqs, mag_db))
        
        # 2. Alle Captures neu einzeichnen
        ax.clear()  # Achse leeren, damit sich Kurven bei mehreren Captures sauber stacken
        
        # Grid und Skalierung wiederherstellen
        ax.set_xscale('log')
        ax.set_xlim(current_xlim)  # Benutzer-Zoom beibehalten!
        ax.set_ylim(current_ylim)  # Benutzer-Zoom beibehalten!
        
        ax.set_title(f'ToneX Analyzer [{title_mode}] (Input: {input_id}, Output: {output_id})')
        ax.set_xlabel('Frequenz (Hz)')
        ax.set_ylabel('Amplitude (dB / Normalized)')
        ax.grid(True, which='both', ls='--', alpha=0.6)

        # Alle bisherigen Captures neu zeichnen
        for lbl, f_data, m_data in captured_data:
            # Das neueste Capture hervorheben, ältere etwas transparenter
            alpha_val = 1.0 if lbl == label_name else 0.5
            lw = 1.8 if lbl == label_name else 1.0
            ax.plot(f_data, m_data, label=lbl, alpha=alpha_val, linewidth=lw)

        ax.legend(loc='lower left')
        
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
        body {{ font-family: Arial, sans-serif; background: #121212; color: #eee; padding: 20px; margin: 0; }}
        h1 {{ color: #00bcd4; margin-bottom: 5px; }}
        p {{ color: #888; margin-top: 0; }}
        #chart {{ width: 100%; height: 750px; max-height: 85vh; }}
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
            step = 5
            html_content += f"""      {{
            x: {freqs[::step].tolist()},
            y: {mag_db[::step].tolist()},
            type: 'scatter',
            mode: 'lines',
            name: '{label}'
        }},
"""
        html_content += """    ];
        var layout = {
            title: { text: 'Frequenzgang-Vergleich (dB ueber Frequenz)', font: { size: 16 } },
            xaxis: { 
                type: 'log', 
                title: 'Frequenz (Hz)', 
                range: [Math.log10(20), Math.log10(20000)],
                dtick: 'D1'
            },
            yaxis: { 
                title: 'Amplitude (dB)', 
                range: [-80, 10],  // Fester Initial-Zoom im HTML Report
                zeroline: true,
                zerolinecolor: '#444'
            },                        
            paper_bgcolor: '#1e1e1e',
            plot_bgcolor: '#1e1e1e',
            font: { color: '#ccc' },
            legend: { x: 0.02, y: 0.05, bgcolor: 'rgba(30,30,30,0.8)' },
            margin: { t: 50, b: 50, l: 60, r: 30 }
        };
        var config = { responsive: true, displayModeBar: true };
        Plotly.newPlot('chart', data, layout, config);
    </script>
</body>
</html>
"""
        filepath = os.path.join(os.path.dirname(__file__), 'tonex_report.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f'\n[SUCCESS] HTML-Report gespeichert unter: {filepath}')

    ax_box = plt.axes([0.15, 0.04, 0.25, 0.05])
    text_box = TextBox(ax_box, 'Preset Name: ', initial='')
    text_box.on_submit(text_submit_callback)
    text_box.text_disp.set_fontsize(10)

    ax_btn_sweep = plt.axes([0.43, 0.04, 0.25, 0.075])
    btn_label = 'Sweep & Capture' if mode == 'sweep' else f'Capture Guitar ({GUITAR_DURATION}s)'
    btn_capture = Button(ax_btn_sweep, btn_label)
    btn_capture.on_clicked(capture_callback)

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
        default=DEFAULT_CHANNEL,
        help=f'Eingangskanal des Interfaces (Default: {DEFAULT_CHANNEL})',
    )
    parser.add_argument(
        '--no-norm',
        action='store_true',
        help='Deaktiviert die Peak-Normierung im Gitarren-Modus',
    )

    args = parser.parse_args()

    auto_in, auto_out = find_focusrite_devices(args.input, args.output)
    input_id = args.input if args.input is not None else auto_in
    output_id = args.output if args.output is not None else auto_out

    print(f"[Audio Devices] Verwendet Input ID {input_id} ({sd.query_devices(input_id)['name']})")
    print(f"[Audio Devices] Verwendet Output ID {output_id} ({sd.query_devices(output_id)['name']})")

    out_info = sd.query_devices(output_id, 'output')
    in_info = sd.query_devices(input_id, 'input')
        
    host_apis = sd.query_hostapis()
    out_api_name = host_apis[out_info['hostapi']]['name']
    in_api_name = host_apis[in_info['hostapi']]['name']

    print("============================================================")
    print("            AKTIVE AUDIO-PARAMETER & SAMPLE-RATES            ")
    print("============================================================")
    print(f" -> OUTPUT Device: {out_info['name']}")
    print(f"    Host-API: {out_api_name} | Max Channels: {out_info['max_output_channels']}")
    print(f"    Default Sample Rate: {out_info['default_samplerate']} Hz")
    print(f" -> INPUT Device: {in_info['name']}")
    print(f"    Host-API: {in_api_name} | Max Channels: {in_info['max_input_channels']}")
    print(f"    Default Sample Rate: {in_info['default_samplerate']} Hz")
    print(f"    Skript-Samplerate (Config): {SAMPLE_RATE} Hz")
    print("============================================================")

    run_app(
        mode=args.mode,
        input_id=input_id,
        output_id=output_id,
        channel=args.channel,
        normalize=not args.no_norm,
    )