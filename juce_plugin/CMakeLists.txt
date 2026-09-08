cmake_minimum_required(VERSION 3.22)

project(GuitarRigAnalyzer VERSION 0.1.0)

# JUCE plugin target definition supporting Standalone and VST3
juce_add_plugin(GuitarRigAnalyzer
    COMPANY_NAME "JensAudio"
    PLUGIN_NAME "GuitarRigAnalyzer"
    FORMATS Standalone VST3
    PRODUCT_NAME "GuitarRigAnalyzer"
    BUNDLE_IDENTIFIER "com.jensaudio.guitarriganalyzer"
    VST3_CAN_REPLACE_VST2 FALSE
)

# Wichtig: Generiert die von den Include-Dateien erwartete JuceHeader.h
juce_generate_juce_header(GuitarRigAnalyzer)

# Source files mapping to the created architecture
target_sources(GuitarRigAnalyzer PRIVATE
    Source/PluginProcessor.cpp
    Source/PluginProcessor.h
    Source/PluginEditor.cpp
    Source/PluginEditor.h
    Source/dsp/TiltFilter.cpp
    Source/dsp/TiltFilter.h
)

# Link necessary JUCE modules for DSP, audio handling, and GUI rendering
target_link_libraries(GuitarRigAnalyzer PRIVATE
    juce::juce_audio_utils
    juce::juce_dsp
    juce::juce_opengl
    juce::juce_recommended_config_flags
    juce::juce_recommended_lto_flags
    juce::juce_recommended_warning_flags
)

# Suppress forced VST2/VST3-Parametervalidation for new Plugins
target_compile_definitions(GuitarRigAnalyzer PRIVATE
    JUCE_IGNORE_VST3_MISMATCHED_PARAMETER_ID_WARNING=1
)