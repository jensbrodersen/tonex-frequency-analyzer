#include <JuceHeader.h>
#include "PluginProcessor.h"

class GuitarRigAnalyzerApplication : public juce::JUCEApplication {
public:
    GuitarRigAnalyzerApplication() {}

    const juce::String getApplicationName() override { return "GuitarRigAnalyzer"; }
    const juce::String getApplicationVersion() override { return "1.0.0"; }
    bool moreThanOneInstanceAllowed() override { return true; }

    void initialise (const juce::String& commandLine) override {
        juce::StringArray args;
        args.addTokens(commandLine, true);
        args.trim();

        int processIndex = args.indexOf("--process");
        if (processIndex != -1) {
            // Prüfen, ob die Parameter für --process vollständig sind
            if (args.size() < processIndex + 3) {
                std::cerr << "Error: Missing input or output file for --process." << std::endl;
                std::exit(1);
            }

            juce::File inputFile (args[processIndex + 1]);
            juce::File outputFile (args[processIndex + 2]);

            // Wenn die Eingabedatei nicht existiert, direkt mit Fehler abbrechen
            if (!inputFile.existsAsFile()) {
                std::cerr << "Error: Input file does not exist: " << inputFile.getFullPathName() << std::endl;
                std::exit(1);
            }

            // Optionalen --tilt Parameter auslesen (Standard: 0.0)
            float tiltValue = 0.0f;
            int tiltIndex = args.indexOf("--tilt");
            if (tiltIndex != -1 && args.size() > tiltIndex + 1) {
                tiltValue = args[tiltIndex + 1].getFloatValue();
            }

            GuitarRigAnalyzerAudioProcessor processor;
            // Tilt-Wert an processOfflineFile übergeben
            bool success = processor.processOfflineFile(inputFile, outputFile, tiltValue);

            if (!success) {
                std::exit(1);
            }

            std::exit(0);
        }

        // Wenn andere Argumente übergeben wurden, die kein gültiges Kommando sind:
        if (args.size() > 0) {
            std::cerr << "Error: Unknown or invalid command line arguments." << std::endl;
            std::exit(1); // Verhindert das Öffnen des GUI-Fensters bei falschen Parametern
        }

        // Nur wenn gar keine Argumente übergeben wurden, das GUI normal öffnen
        mainWindow.reset (new StandaloneWindow (getApplicationName(),
                             std::unique_ptr<juce::AudioProcessor>(createPluginFilter()),
                             *this));
    }

    void shutdown() override {
        mainWindow = nullptr;
    }

private:
    class StandaloneWindow : public juce::DocumentWindow {
    public:
        StandaloneWindow (const juce::String& title, std::unique_ptr<juce::AudioProcessor> p, JUCEApplication& app)
            : DocumentWindow (title, juce::Desktop::getInstance().getDefaultLookAndFeel()
                                   .findColour (juce::ResizableWindow::backgroundColourId),
                              DocumentWindow::allButtons),
              appRef (app)
        {
            auto* const contentComp = new juce::AudioProcessorPlayer();
            contentComp->setProcessor (p.get());
            
            auto* editor = dynamic_cast<GuitarRigAnalyzerAudioProcessor*>(p.get())->createEditor();
            setContentOwned (editor != nullptr ? editor : new juce::GenericAudioProcessorEditor (*p), true);
            
            centreWithSize (getWidth(), getHeight());
            setVisible (true);
            setResizable (true, true);
        }

        void closeButtonPressed() override {
            appRef.systemRequestedQuit();
        }

    private:
        JUCEApplication& appRef;
        JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (StandaloneWindow)
    };

    std::unique_ptr<StandaloneWindow> mainWindow;
};

START_JUCE_APPLICATION (GuitarRigAnalyzerApplication)