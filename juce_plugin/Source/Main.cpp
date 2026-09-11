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
        if (processIndex != -1 && args.size() >= processIndex + 3) {
            juce::File inputFile (args[processIndex + 1]);
            juce::File outputFile (args[processIndex + 2]);

            GuitarRigAnalyzerAudioProcessor processor;
            [[maybe_unused]] bool success = processor.processOfflineFile(inputFile, outputFile);

            juce::JUCEApplication::quit();
            return;
        }

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