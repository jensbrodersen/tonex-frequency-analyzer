#include "PluginProcessor.h"
#include "PluginEditor.h"

GuitarRigAnalyzerAudioProcessor::GuitarRigAnalyzerAudioProcessor()
#ifndef JucePlugin_PreferredChannelConfigurations
     : AudioProcessor (BusesProperties()
                     #if ! JucePlugin_IsMidiEffect
                      #if ! JucePlugin_IsSynth
                       .withInput  ("Input",  juce::AudioChannelSet::stereo(), true)
                      #endif
                       .withOutput ("Output", juce::AudioChannelSet::stereo(), true)
                     #endif
                       )
#endif
{
}

GuitarRigAnalyzerAudioProcessor::~GuitarRigAnalyzerAudioProcessor() = default;

const juce::String GuitarRigAnalyzerAudioProcessor::getName() const {
    return JucePlugin_Name;
}

bool GuitarRigAnalyzerAudioProcessor::acceptsMidi() const {
   #if JucePlugin_WantsMidiInput
    return true;
   #else
    return false;
   #endif
}

bool GuitarRigAnalyzerAudioProcessor::producesMidi() const {
   #if JucePlugin_ProducesMidiOutput
    return true;
   #else
    return false;
   #endif
}

bool GuitarRigAnalyzerAudioProcessor::isMidiEffect() const {
   #if JucePlugin_IsMidiEffect
    return true;
   #else
    return false;
   #endif
}

double GuitarRigAnalyzerAudioProcessor::getTailLengthSeconds() const {
    return 0.0;
}

int GuitarRigAnalyzerAudioProcessor::getNumPrograms() {
    return 1;
}

int GuitarRigAnalyzerAudioProcessor::getCurrentProgram() {
    return 0;
}

void GuitarRigAnalyzerAudioProcessor::setCurrentProgram (int index) {
    juce::ignoreUnused (index);
}

const juce::String GuitarRigAnalyzerAudioProcessor::getProgramName (int index) {
    juce::ignoreUnused (index);
    return {};
}

void GuitarRigAnalyzerAudioProcessor::changeProgramName (int index, const juce::String& newName) {
    juce::ignoreUnused (index, newName);
}

void GuitarRigAnalyzerAudioProcessor::prepareToPlay (double sampleRate, int samplesPerBlock) {
    jassert(sampleRate == 44100.0);
    tiltFilter.prepare(sampleRate, samplesPerBlock);
}

void GuitarRigAnalyzerAudioProcessor::releaseResources() {
    tiltFilter.reset();
}

bool GuitarRigAnalyzerAudioProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const {
   #if JucePlugin_IsMidiEffect
    ignoreUnused (layouts);
    return true;
   #else
    if (layouts.getMainOutputChannelSet() != juce::AudioChannelSet::mono()
     && layouts.getMainOutputChannelSet() != juce::AudioChannelSet::stereo())
        return false;

    #if ! JucePlugin_IsSynth
    if (layouts.getMainOutputChannelSet() != layouts.getMainInputChannelSet())
        return false;
   #endif

    return true;
   #endif
}

void GuitarRigAnalyzerAudioProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midiMessages) {
    juce::ignoreUnused (midiMessages);
    juce::ScopedNoDenormals noDenormals;
    auto totalNumInputChannels  = getTotalNumInputChannels();
    auto totalNumOutputChannels = getTotalNumOutputChannels();

    for (auto i = totalNumInputChannels; i < totalNumOutputChannels; ++i)
        buffer.clear (i, 0, buffer.getNumSamples());

    tiltFilter.process(buffer);
}

bool GuitarRigAnalyzerAudioProcessor::hasEditor() const {
    return true;
}

juce::AudioProcessorEditor* GuitarRigAnalyzerAudioProcessor::createEditor() {
    return new GuitarRigAnalyzerAudioProcessorEditor (*this);
}

void GuitarRigAnalyzerAudioProcessor::getStateInformation (juce::MemoryBlock& destData) {
    juce::ignoreUnused (destData);
}

void GuitarRigAnalyzerAudioProcessor::setStateInformation (const void* data, int sizeInBytes) {
    juce::ignoreUnused (data, sizeInBytes);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() {
    return new GuitarRigAnalyzerAudioProcessor();
}

bool GuitarRigAnalyzerAudioProcessor::processOfflineFile (const juce::File& inputFile, const juce::File& outputFile, float tiltValue)
{
    if (!inputFile.existsAsFile())
        return false;

    juce::AudioFormatManager formatManager;
    formatManager.registerBasicFormats();

    std::unique_ptr<juce::AudioFormatReader> reader (formatManager.createReaderFor(inputFile));
    if (reader == nullptr)
        return false;

    // Ziel-SampleRate für den DSP-Kontext erzwingen (44.1 kHz)
    const double targetSampleRate = 44100.0;
    const int blockSiz = 512;

    prepareToPlay(targetSampleRate, blockSiz);

    juce::AudioBuffer<float> buffer ((int) reader->numChannels, (int) reader->lengthInSamples);
    reader->read(&buffer, 0, (int) reader->lengthInSamples, 0, true, true);

    tiltFilter.setTiltDb(tiltValue * 6.0f); // Tilt-Wert setzen
    tiltFilter.process(buffer);            // Audio-Puffer filtern

    // Optional: Tilt-Filter vorab auf den gesamten Puffer anwenden (oder direkt im Block-Loop, 
    // je nachdem, wie dein Tilt-Filter implementiert ist. Hier als Vorbereitung vor der Block-Verarbeitung):
    // applyTiltFilter(buffer, tiltValue); 
    // Alternativ, falls du eine Methode im Processor hast, die den Tilt-Wert setzt:
    // setTiltParameter(tiltValue);

    // Blockweise Verarbeitung simulieren wie in processBlock
    juce::MidiBuffer dummyMidi;
    const int numSamples = buffer.getNumSamples();
    
    for (int startSample = 0; startSample < numSamples; startSample += blockSiz) {
        int currentBlockSize = juce::jmin (blockSiz, numSamples - startSample);
        
        // Temporären Sub-Buffer für den aktuellen Block erzeugen (mit getArrayOfWritePointers)
        juce::AudioBuffer<float> blockBuffer (buffer.getArrayOfWritePointers(), buffer.getNumChannels(), startSample, currentBlockSize);
        processBlock(blockBuffer, dummyMidi);
    }
    
    // Ausgabe-WAV schreiben (24-bit PCM über modernen AudioFormatWriterOptions)
    if (outputFile.exists())
        outputFile.deleteFile();

    std::unique_ptr<juce::OutputStream> fileStream (outputFile.createOutputStream());
    if (fileStream == nullptr)
        return false;

    juce::WavAudioFormat wavFormat;
    
    auto options = juce::AudioFormatWriterOptions()
        .withSampleRate(targetSampleRate)
        .withNumChannels(buffer.getNumChannels())
        .withBitsPerSample(24);

    std::unique_ptr<juce::AudioFormatWriter> writer (wavFormat.createWriterFor(fileStream, options));

    if (writer == nullptr)
        return false;

    writer->writeFromAudioSampleBuffer(buffer, 0, numSamples);
    return true;
}