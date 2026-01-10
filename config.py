import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class GameConfig:
    """Manages game configuration loaded from YAML."""

    def __init__(self, config_path: str = 'data/config.yml'):
        self.config_path = config_path
        self.data: Dict[str, Any] = {}
        self.load()

    def _load_defaults(self):
        """Load default configuration values."""
        self.data = {
            'time': {
                'start_year': 1800,
                'years_per_real_second': 1.0,
                'default_speed': 1.0,
                'max_speed': 16.0,
                'min_speed': 0.25
            },
            'ui': {
                'resource_panel_scale': 1.5,
                'tree_node_width': 220,
                'tree_node_height': 90
            },
            'game': {
                'auto_save_interval': 300,
                'show_debug_info': False
            }
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Example:
            config.get('time.start_year')
            config.get('ui.resource_panel_scale', 1.0)
        """
        keys = key_path.split('.')
        value = self.data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_time_config(self) -> Dict[str, Any]:
        """Get all time-related configuration."""
        return self.data.get('time', {})

    def get_ui_config(self) -> Dict[str, Any]:
        """Get all UI-related configuration."""
        return self.data.get('ui', {})

    def get_game_config(self) -> Dict[str, Any]:
        """Get all game-related configuration."""
        return self.data.get('game', {})

    def save(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, default_flow_style=False, sort_keys=False)
            print(f"✓ Saved configuration to {self.config_path}")
        except Exception as e:
            print(f"✗ Error saving config: {e}")

    def load(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f) or {}
            print(f"✓ Loaded configuration from {self.config_path}")
        except FileNotFoundError:
            print(f"⚠ Config file not found: {self.config_path}, using defaults")
            self._load_defaults()
        except yaml.YAMLError as e:
            print(f"✗ Error parsing config file: {e}")
            self._load_defaults()

    def set(self, key_path: str, value: Any):
        """
        Set a configuration value using dot notation.

        Example:
            config.set('time.start_year', 1850)
        """
        keys = key_path.split('.')
        data = self.data

        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]

        data[keys[-1]] = value


# Global config instance
_config: Optional[GameConfig] = None

def get_config() -> GameConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = GameConfig()
    return _config


def load_config(config_path: str = 'data/config.yml') -> GameConfig:
    """Load configuration from a specific path."""
    global _config
    _config = GameConfig(config_path)
    return _config
