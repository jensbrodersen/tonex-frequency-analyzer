cmake_minimum_required(VERSION 3.22)

project(ToneXAnalyzerSuite VERSION 0.1.0 LANGUAGES C CXX)

# Globale Konfiguration einbinden
include(cmake/AudioPluginConfig.cmake OPTIONAL)

# JUCE-Framework über den Pfad im Nachbarordner einbinden
add_subdirectory(../../juce_environment/JUCE JUCE)

# Das Plugin-Unterverzeichnis einbinden
add_subdirectory(juce_plugin)