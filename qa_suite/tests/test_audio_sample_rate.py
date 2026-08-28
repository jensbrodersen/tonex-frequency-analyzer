from pathlib import Path
import yaml

def test_config_and_system_samplerate_alignment():
    """Stellt sicher, dass die Konfiguration konsistent auf 44.1 kHz ausgelegt ist."""
    config_path = Path(__file__).parent.parent / "tools" / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        if "sample_rate" in config:
            assert config["sample_rate"] == 44100, f"Samplerate in config.yaml muss 44100 Hz sein, ist aber {config['sample_rate']} Hz."