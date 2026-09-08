#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"

class GuitarRigAnalyzerAudioProcessorEditor : public juce::AudioProcessorEditor {
public:
    GuitarRigAnalyzerAudioProcessorEditor (GuitarRigAnalyzerAudioProcessor&);
    ~GuitarRigAnalyzerAudioProcessorEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    GuitarRigAnalyzerAudioProcessor& audioProcessor;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (GuitarRigAnalyzerAudioProcessorEditor)
};