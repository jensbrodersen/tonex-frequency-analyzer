cmake_minimum_required(VERSION 3.22)

project(ToneXAnalyzerSuite VERSION 0.1.0 LANGUAGES C CXX)

# Globale Konfiguration einbinden
include(cmake/AudioPluginConfig.cmake OPTIONAL)

# JUCE-Framework lokal oder als Submodul/Fallback für GitHub Actions einbinden
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../juce_environment/JUCE")
    add_subdirectory(../../juce_environment/JUCE JUCE)
elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/JUCE")
    add_subdirectory(JUCE JUCE)
else()
    message(FATAL_ERROR "JUCE framework not found! Please ensure JUCE is available locally or as a submodule.")
endif()

# Das Plugin-Unterverzeichnis einbinden
add_subdirectory(juce_plugin)