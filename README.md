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
  <img src="assets/report_preview.png" width="750" alt="ToneX Analysis Report Preview">
</p>

---

## Diagnostics & Quality Assurance: Clipping & Speaker Safety

The analyzer functions not only as a pure measurement tool but also exposes flawed ToneX captures. The following example demonstrates a direct comparison between a faulty, clipped Fender Twin capture and a clean measurement:

<p align="center">
  <img src="assets/twin_goodcapture_versus_bad.png" width="750" alt="Fender Twin: Good Capture vs. Bad Capture with Clipping">
</p>

* **Bad Capture (Blue):** A poorly or overly hot-levelled capture results in massive, uncontrolled comb-filtering artifacts and phase breaks across the entire frequency spectrum. Such digital signal distortions can lead to unhealthy energy spikes during live operation or at high volumes, which in the worst case can **damage studio monitors and speaker cabinets** or severely muddy the sound.
* **Good Capture (Orange):** The clean, smooth curve proves mathematical integrity and reveals the true, open frequency response of an intact amp without digital artifacts.

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