cmake_minimum_required(VERSION 3.22)

project(GuitarRigAnalyzer VERSION 0.1.0)

juce_add_plugin(GuitarRigAnalyzer
    COMPANY_NAME "JensAudio"
    PLUGIN_NAME "GuitarRigAnalyzer"
    FORMATS Standalone VST3
    PRODUCT_NAME "GuitarRigAnalyzer"
    BUNDLE_IDENTIFIER "com.jensaudio.guitarriganalyzer"
    VST3_CAN_REPLACE_VST2 FALSE
)

juce_generate_juce_header(GuitarRigAnalyzer)

target_sources(GuitarRigAnalyzer PRIVATE
    Source/Main.cpp
    Source/PluginProcessor.cpp
    Source/PluginProcessor.h
    Source/PluginEditor.cpp
    Source/PluginEditor.h
    Source/dsp/TiltFilter.cpp
    Source/dsp/TiltFilter.h
)

target_link_libraries(GuitarRigAnalyzer PRIVATE
    juce::juce_audio_utils
    juce::juce_dsp
    juce::juce_opengl
    juce::juce_recommended_config_flags
    juce::juce_recommended_lto_flags
    juce::juce_recommended_warning_flags
)

target_compile_definitions(GuitarRigAnalyzer PRIVATE
    JUCE_IGNORE_VST3_MISMATCHED_PARAMETER_ID_WARNING=1
    JUCE_USE_CUSTOM_PLUGIN_STANDALONE_APP=1
    JUCE_ALLOW_CUSTOM_STANDALONE_WINDOW=1
)

if(TARGET GuitarRigAnalyzer_Standalone)
    set_target_properties(GuitarRigAnalyzer_Standalone PROPERTIES WIN32_EXECUTABLE TRUE)
endif()