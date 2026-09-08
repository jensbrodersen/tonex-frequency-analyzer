#pragma once

#include <JuceHeader.h>

class TiltFilter {
public:
    TiltFilter();
    ~TiltFilter() = default;

    void prepare(double sampleRate, int samplesPerBlock);
    void reset();
    
    // Set Tilt-Parameter (e. g. in dB, positiv = treble up/bass down)
    void setTiltDb(float tiltDb);
    
    // Processes a single audio block
    void process(juce::AudioBuffer<float>& buffer);

private:
    double sampleRate = 44100.0;
    float currentTiltDb = 0.0f;

    // Usage of IIR filter from the JUCE DSP module
    juce::dsp::IIR::Filter<float> lowShelf;
    juce::dsp::IIR::Filter<float> highShelf;

    void updateCoefficients();
};