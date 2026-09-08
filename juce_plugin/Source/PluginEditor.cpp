#include "PluginProcessor.h"
#include "PluginEditor.h"

GuitarRigAnalyzerAudioProcessorEditor::GuitarRigAnalyzerAudioProcessorEditor (GuitarRigAnalyzerAudioProcessor& p)
    : AudioProcessorEditor (&p), audioProcessor (p) {
    
    // Base window size of the plugin editor
    setSize (400, 300);
}

GuitarRigAnalyzerAudioProcessorEditor::~GuitarRigAnalyzerAudioProcessorEditor() = default;

void GuitarRigAnalyzerAudioProcessorEditor::paint (juce::Graphics& g) {
    // Dark background suitable for the audio engineering context
    g.fillAll (juce::Colours::darkgrey);

    g.setColour (juce::Colours::white);
    g.setFont (16.0f);
    g.drawFittedText ("ToneX Rig Analyzer", getLocalBounds(), juce::Justification::centredTop, 1);
    
    g.setFont (12.0f);
    g.setColour (juce::Colours::lightgrey);
    g.drawFittedText ("System Sample Rate: 44.1 kHz (Locked)", getLocalBounds().reduced(0, 40), juce::Justification::centred, 1);
}

void GuitarRigAnalyzerAudioProcessorEditor::resized() {
    // Layout logic for controls (sliders, etc.) will follow here later
}