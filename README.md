# ToneX Frequency Analyzer & QA Suite

[![CI & DSP Verification](https://github.com/jensbrodersen/tonex-frequency-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/jensbrodersen/tonex-frequency-analyzer/actions/workflows/ci.yml)

> Hybrid audio analysis & QA suite for ToneX hardware. Combines a Python DSP engine for automated sweep/guitar frequency analysis with a native JUCE C++ application for real-time rig testing, automated CLI verification, and interactive HTML reporting.

---

## Features

* **Closed-Loop Sweep Measurement:** Precise frequency response analysis using logarithmic sweeps, inverse filtering, and peak delay detection.
* **Headless CLI Pipeline:** Automated offline audio processing via command-line flags (`--process`) integrated directly into the standalone JUCE lifecycle for continuous testing.
* **Live Guitar Testing:** Real-time capture and normalization modes for testing actual playing dynamics.
* **Equipment Safety:** Real-time detection of signal anomalies and clipping to protect monitors and speakers (like HeadRush).
* **Interactive HTML Reports:** Export high-resolution comparison charts powered by **Plotly**, complete with custom preset labels (e.g., Vox AC30, SLO Lead, Fender Twin). Check out the sample files in the [`example_logs/`](example_logs/) folder!
* **Hybrid Architecture:**
  * `qa_suite/`: Python-based DSP engine, visualization, and reporting.
  * `juce_plugin/`: Native C++ application for high-performance audio handling and headless test execution.

---

## Preview / Example Report

<p align="center">
  <img src="assets/report_preview_clean.html.png" width="48%" alt="ToneX Clean Analysis Report Preview">
  <img src="assets/report_preview_gain.html.png" width="48%" alt="ToneX Gain Analysis Report Preview">
</p>

*Example frequency response analyses comparing various amp models: The left report shows the behavior of different clean stages (including Vox AC30, Bogner XTC, and Fender Twin), while the right report illustrates higher gain behaviors (featuring Soldano SLO Crunch/High Gain and Friedman High Gain).*

---

## Diagnostics & Quality Assurance: Clipping & Speaker Safety

The analyzer functions not only as a pure measurement tool but also exposes how time-based effects and improper headroom impact a signal. The following example demonstrates a direct comparison:

<p align="center">
  <img src="assets/twin_goodcapture_versus_bad.png" width="750" alt="Fender Twin: Good Capture vs. Bad Capture with Clipping">
</p>

* **Modulated / Problematic Preset (Blue):** Shows a preset with active modulation (Chorus), resulting in heavy comb-filtering artifacts and phase cancellations across the mid and high frequencies. While great for tone shaping during play, such modulation sweeps or overly hot-levelled signals can introduce chaotic energy spikes that clutter frequency responses and strain speaker components at high volumes.
* **Clean Measurement (Orange):** The smooth, unmodulated curve reveals the true, open frequency response of an intact amp model without phase-related interference or digital distortion.

---

## Automated QA & Test Suite

The `qa_suite/` includes an automated test framework powered by **pytest** interacting directly with the compiled native headless binary:

* **DSP Pipeline Verification (`test_dsp_pipeline.py`):** Executes automated headless rendering passes through `GuitarRigAnalyzer.exe` to validate end-to-end signal processing integrity.
* **Frequency Response & Clipping Protection (`test_frequency_response.py`):** Validates clean curves against abrupt comb-filtering and detects hazardous 0 dB high-frequency clipping plateaus to safeguard FRFR monitors and speakers.
* **Latency Estimation (`test_latency.py`):** Verifies precise sample-delay tracking using cross-correlation (`scipy.signal.correlate`) between reference and response signals.
* **Harmonic Distortion (`test_distortion.py`):** Simulates and monitors non-linear saturation thresholds and harmonic behavior across gain stages.
* **System Alignment (`test_config.py`, `test_audio_sample_rate.py`):** Ensures configuration consistency (strictly locked to **44.1 kHz** to avoid resampling drift or clock mismatches between Windows and audio hardware).

### Running Tests Locally

Navigate into the QA suite and run the test harness via Python:

```bash
cd qa_suite
python -m pytest
```

### Continuous Integration (CI/CD)

The project utilizes **GitHub Actions** (`.github/workflows/ci.yml`) to ensure cross-platform integrity on every push to the `main` branch. The automated pipeline performs the following actions on a fresh Windows runner (`windows-latest`):
1. **Environment Setup:** Clones the JUCE framework and sets up Python 3.13.
2. **Dependency Management:** Installs minimal required QA suite dependencies (`pyyaml`, `numpy`, `scipy`).
3. **Headless Compilation:** Configures CMake and compiles the native `GuitarRigAnalyzer.exe` (Standalone & VST3) in Release mode using Visual Studio toolchains.
4. **Automated Verification:** Executes the complete `pytest` test harness against the freshly built binary to guarantee zero regressions in DSP processing.

---

## Building the Native JUCE C++ Application

Prerequisites include **Visual Studio 2026** with C++ workload and **CMake**.

### Build & Run Instructions (Windows x64)

Open your x64 Native Tools Command Prompt for Visual Studio and run the following commands from the project root:

```cmd
:: Clean any existing build artifacts
rmdir /s /q build

:: Configure the project with CMake
cmake -B build -G "Visual Studio 18 2026" -A x64

:: Build the release binaries (VST3 & Standalone)
cmake --build build --config Release
```

### Launching the Standalone App & Headless Usage

Once built successfully, you can launch the interactive graphical application:

```cmd
cd build\juce_plugin\GuitarRigAnalyzer_artefacts\Release\Standalone\
GuitarRigAnalyzer.exe
```

For automated CLI processing (used by the test suite), invoke the executable with input and output file parameters:

```cmd
cd build\juce_plugin\GuitarRigAnalyzer_artefacts\Release\Standalone\
GuitarRigAnalyzer.exe --process input.wav output.wav
```

---

## Project Structure

```text
├── qa_suite/              # Python DSP engine & analysis tools
│   ├── assets/            # Test assets & generated reference wav files
│   ├── pyproject.toml
│   ├── tests/             # Automated pytest suite (DSP pipeline, clipping, latency, distortion, config)
│   └── tools/             # Core analyzer scripts & config.yaml
├── juce_plugin/           # Native JUCE C++ application
│   └── Source/            # Main.cpp, PluginProcessor, PluginEditor, DSP filters
├── cmake/                 # CMake configuration files
├── example_logs/          # Interactive HTML reports for offline viewing
├── assets/                # Visual assets & screenshots for documentation
├── CMakeLists.txt         # Root CMake build configuration
└── .gitignore
```

---
