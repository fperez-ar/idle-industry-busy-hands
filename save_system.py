# save_system.py
import json
from datetime import datetime
from typing import Dict, Any
from state import GameState
from resources import ResourceManager

class SaveSystem:
    """Handles saving and loading game state."""
    
    SAVE_VERSION = 1
    
    @staticmethod
    def save(game_state: GameState, resource_manager: ResourceManager, filepath: str):
        """Save current game state to file."""
        save_data = {
            'version': SaveSystem.SAVE_VERSION,
            'timestamp': datetime.now().isoformat(),
            'resources': {
                res_id: res.current_value 
                for res_id, res in resource_manager.resources.items()
            },
            'owned_upgrades': list(game_state.owned_upgrades),
            'selected_exclusive': game_state.selected_exclusive,
            'current_year': game_state.current_year
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2)
    
    @staticmethod
    def load(filepath: str) -> Dict[str, Any]:
        """Load game state from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def apply_save(
        save_data: Dict[str, Any], 
        game_state: GameState, 
        resource_manager: ResourceManager
    ):
        """Apply loaded save data to game state."""
        # Restore resources
        for res_id, value in save_data.get('resources', {}).items():
            if res_id in resource_manager.resources:
                resource_manager.resources[res_id].current_value = value
        
        # Restore owned upgrades
        game_state.owned_upgrades = set(save_data.get('owned_upgrades', []))
        game_state.selected_exclusive = save_data.get('selected_exclusive', {})
        game_state.current_year = save_data.get('current_year', 1800)
        
        # Recalculate production based on owned upgrades
        resource_manager.recalculate_production(
            game_state.owned_upgrades,
            game_state.all_upgrades
        )

