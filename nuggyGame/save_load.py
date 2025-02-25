# main.py
import json
import os
from config import SAVE_FILE

def save_game_state(data):
    """Save the game state to a JSON file."""
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving game data: {e}")

def load_game_state():
    """Load the game state from a JSON file."""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading game data: {e}")
            return None
    return None

def main():
    """Demo of saving and loading game data."""
    game_data = load_game_state()
    if not game_data:
        game_data = {'current_level': 1, 'score': 0}
    print(f"Current game data: {game_data}")
    game_data['score'] += 10
    print(f"Updated game data: {game_data}")
    save_game_state(game_data)

if __name__ == "__main__":
    main()

# config.py
SAVE_FILE = 'save_game.json'
