# ToneX Frequency Analyzer & QA Suite

> Hybrid audio analysis & QA suite for ToneX hardware. Combines a Python DSP engine for automated sweep/guitar frequency analysis with a native JUCE C++ application for real-time rig testing and interactive HTML reporting.

---

## Features

* **Closed-Loop Sweep Measurement:** Precise frequency response analysis using logarithmic sweeps, inverse filtering, and peak delay detection.
* **Live Guitar Testing:** Real-time capture and normalization modes for testing actual playing dynamics.
* **Equipment Safety:** Real-time detection of signal anomalies and clipping to protect monitors and speakers (like HeadRush).
* **Interactive HTML Reports:** Export high-resolution comparison charts powered by **Plotly**, complete with custom preset labels (e.g., Vox AC30, SLO Lead, Fender Twin). Check out the sample files in the [`example_logs/`](example_logs/) folder!
* **Hybrid Architecture:**
  * `qa_suite/`: Python-based DSP engine, visualization, and reporting.
  * `juce_plugin/`: Native C++ application for high-performance audio handling.

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

## Project Structure

```text
├── qa_suite/            # Python DSP engine & analysis tools
├── juce_plugin/         # Native JUCE C++ application
├── cmake/               # CMake configuration files
├── example_logs/        # Interactive HTML reports for offline viewing
├── assets/              # Visual assets & screenshots for documentation
├── CMakeLists.txt       # Root CMake build configuration
└── .gitignore