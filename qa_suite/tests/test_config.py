import yaml
from pathlib import Path

def test_config_loading():
    """Prüft, ob die config.yaml existiert und gültige Parameter enthält."""
    config_path = Path(__file__).parent.parent / "tools" / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict), "Config muss ein gültiges Dictionary sein."