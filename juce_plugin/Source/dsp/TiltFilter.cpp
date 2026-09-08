#include "TiltFilter.h"

TiltFilter::TiltFilter() {
    // Konstruktor
}

void TiltFilter::prepare(double newSampleRate, int samplesPerBlock) {
    // hard-coded 44.1 kHz check analogous to your Python specification
    jassert(newSampleRate == 44100.0);
    sampleRate = newSampleRate;

    juce::dsp::ProcessSpec spec;
    spec.sampleRate = sampleRate;
    spec.maximumBlockSize = static_cast<uint32>(samplesPerBlock);
    spec.numChannels = 2; // Standard Stereo

    lowShelf.prepare(spec);
    highShelf.prepare(spec);

    updateCoefficients();
    reset();
}

void TiltFilter::reset() {
    lowShelf.reset();
    highShelf.reset();
}

void TiltFilter::setTiltDb(float tiltDb) {
    if (currentTiltDb != tiltDb) {
        currentTiltDb = tiltDb;
        updateCoefficients();
    }
}

void TiltFilter::updateCoefficients() {
    // hard-coded center frequency for the tilt point (e.g., 1 kHz)
    const double centerFreq = 1000.0;

    // Low-Shelf takes the counter-movement, High-Shelf applies the tilt
    auto lowCoeffs = juce::dsp::IIR::Coefficients<float>::makeLowShelf(
        sampleRate, centerFreq, 0.707f, juce::Decibels::decibelsToGain(-currentTiltDb * 0.5f)
    );
    auto highCoeffs = juce::dsp::IIR::Coefficients<float>::makeHighShelf(
        sampleRate, centerFreq, 0.707f, juce::Decibels::decibelsToGain(currentTiltDb * 0.5f)
    );

    *lowShelf.coefficients = *lowCoeffs;
    *highShelf.coefficients = *highCoeffs;
}

void TiltFilter::process(juce::AudioBuffer<float>& buffer) {
    juce::dsp::AudioBlock<float> block(buffer);
    juce::dsp::ProcessContextReplacing<float> context(block);

    // Apply filters sequentially to the buffer
    lowShelf.process(context);
    highShelf.process(context);
}